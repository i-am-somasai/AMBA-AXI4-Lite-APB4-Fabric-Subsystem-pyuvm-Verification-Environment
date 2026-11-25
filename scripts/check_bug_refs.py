#!/usr/bin/env python3
"""
scripts/check_bug_refs.py

Verify that every entry in docs/bugs.md cites real, existing files, formal suites,
Makefile targets, and Python test functions/classes (preventing phantom test refs).
Also checks that BUG IDs are sequential and match docs/metrics.json (when present).
"""

import ast
import json
import os
import re
import sys
from pathlib import Path

PROJ_DIR = Path(__file__).resolve().parent.parent


def collect_python_symbols():
    """Return {rel_path: set(symbol_names)} and global_symbols set across tb/**/*.py."""
    by_file = {}
    all_syms = set()
    for py_path in sorted((PROJ_DIR / "tb").rglob("*.py")):
        if "__pycache__" in py_path.parts or ".venv" in py_path.parts:
            continue
        rel = py_path.relative_to(PROJ_DIR).as_posix()
        syms = set()
        tree = ast.parse(py_path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                syms.add(node.name)
            elif isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        syms.add(tgt.id)
        by_file[rel] = syms
        all_syms.update(syms)
    return by_file, all_syms


def parse_make_targets():
    makefile = PROJ_DIR / "Makefile"
    targets = set()
    for line in makefile.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Za-z0-9_.-]+)\s*:", line)
        if m:
            targets.add(m.group(1))
    return targets


def parse_bugs():
    bugs_md = PROJ_DIR / "docs" / "bugs.md"
    lines = bugs_md.read_text(encoding="utf-8").splitlines()
    entries = []
    cur = None
    for idx, line in enumerate(lines, 1):
        m = re.match(r"^###\s+\[(BUG-\d+)\]\s+(.+)$", line.strip())
        if m:
            if cur is not None:
                entries.append(cur)
            cur = {"id": m.group(1), "title": m.group(2), "line": idx, "reg_line": None, "reg_text": ""}
        elif cur is not None and line.strip().startswith("- **Regression Test:**"):
            cur["reg_line"] = idx
            cur["reg_text"] = line.split("**Regression Test:**", 1)[1].strip()
    if cur is not None:
        entries.append(cur)
    return entries


def main():
    by_file, all_syms = collect_python_symbols()
    make_targets = parse_make_targets()
    entries = parse_bugs()
    errors = []

    if not entries:
        print("ERROR: Zero BUG entries parsed from docs/bugs.md", file=sys.stderr)
        sys.exit(1)

    for idx, entry in enumerate(entries, 1):
        expected_id = f"BUG-{idx:03d}"
        if entry["id"] != expected_id:
            errors.append(f"docs/bugs.md:{entry['line']}: expected {expected_id}, found {entry['id']}")
        reg_text = entry["reg_text"]
        if not reg_text:
            errors.append(f"{entry['id']} (line {entry['line']}): missing '- **Regression Test:**' line")
            continue

        backticked = re.findall(r"`([^`]+)`", reg_text)
        if not backticked:
            errors.append(f"{entry['id']} (line {entry['reg_line']}): no backticked test reference in '{reg_text}'")
            continue

        cited_py_files = [t for t in backticked if t.endswith(".py")]
        for tok in backticked:
            if "/" in tok or tok.endswith((".py", ".sby", ".sh")):
                fpath = PROJ_DIR / tok
                if not fpath.exists():
                    errors.append(f"{entry['id']} (line {entry['reg_line']}): missing path '{tok}'")
            elif tok.startswith("make "):
                parts = tok.split()
                if len(parts) >= 2 and parts[1] not in make_targets:
                    errors.append(f"{entry['id']} (line {entry['reg_line']}): unknown Makefile target '{parts[1]}'")
            elif tok.endswith(".sby"):
                if not (PROJ_DIR / "formal" / tok).exists():
                    errors.append(f"{entry['id']} (line {entry['reg_line']}): missing formal suite 'formal/{tok}'")
            elif tok.startswith(("test_", "Test")):
                if cited_py_files:
                    if not any(tok in by_file.get(pf, set()) for pf in cited_py_files):
                        errors.append(
                            f"{entry['id']} (line {entry['reg_line']}): test '{tok}' not found in {cited_py_files}"
                        )
                elif tok not in all_syms:
                    errors.append(f"{entry['id']} (line {entry['reg_line']}): test symbol '{tok}' not found under tb/")
            else:
                # Module stem (e.g. `axil2apb_bridge` for make mutation-sample) or suite shorthand
                rtl_matches = list((PROJ_DIR / "rtl").rglob(f"{tok}.v"))
                test_matches = [p for p in by_file if os.path.basename(p) == f"test_{tok}.py"]
                if not rtl_matches and not test_matches:
                    errors.append(f"{entry['id']} (line {entry['reg_line']}): unrecognized ref '{tok}'")

    metrics_path = PROJ_DIR / "docs" / "metrics.json"
    if metrics_path.exists():
        data = json.loads(metrics_path.read_text(encoding="utf-8"))
        m_bugs = data.get("bugs", {}).get("total")
        if m_bugs is not None and int(m_bugs) != len(entries):
            errors.append(
                f"docs/metrics.json bugs.total={m_bugs} disagrees with docs/bugs.md count={len(entries)}"
            )

    if errors:
        print("FAIL: docs/bugs.md reference check failed:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    print(f"PASS: Verified {len(entries)} sequential bug entries ({entries[0]['id']}..{entries[-1]['id']}) and all regression test references.")


if __name__ == "__main__":
    main()
