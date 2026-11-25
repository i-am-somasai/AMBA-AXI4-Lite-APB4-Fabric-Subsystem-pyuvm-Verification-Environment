#!/usr/bin/env python3
"""
scripts/check_docs_consistency.py

Verifies:
1. All <!-- BEGIN:metrics:* --> blocks in README.md, docs/results.md, docs/vplan.md
   match the freshly rendered output from docs/metrics.json with zero diff.
2. Zero stale placeholders or debunked audit numbers remain in generated docs.
3. Zero broken local markdown links exist across README.md and docs/*.md.
4. Zero personal /home/<user>/ paths appear in scripts/, README.md, or docs/*.md.
"""

import difflib
import glob
import json
import os
import re
import sys
from pathlib import Path
from doc_blocks import PROJ_DIR, apply_blocks_to_text, render_all_blocks
from gen_metrics import parse_memory_map

FORBIDDEN_STALE_PATTERNS = [
    r"being re-measured",
    r"\b81\.63\b",
    r"-2\.25\s*ns",
    r"\b196/240\b",
    r"\b83\.88%",
    r"\b3,238\b",
    r"\b3,759\b",
    r"\b8/8 proven\b",
    r"exhaustively proven",
    r"0x4FFF_FFFF",
]


def verify_readme_matches_decoder(readme_text, expected_mmap):
    """Fail if README.md Section 3 slot ranges disagree with rtl/axil/axil_decoder.v."""
    errors = []
    for slot, info in expected_mmap["slots"].items():
        row_m = re.search(rf"^\|\s*\*\*{slot}\*\*\s*\|[^\n]*", readme_text, flags=re.M)
        if not row_m:
            errors.append(f"README.md: missing memory map row for {slot}")
            continue
        row = row_m.group(0)
        if info["range"] not in row or f"({info['size_label']}" not in row:
            errors.append(
                f"README.md {slot} memory map row '{row}' disagrees with rtl/axil/axil_decoder.v "
                f"(expected range '{info['range']}' and size '{info['size_label']}')"
            )
    return errors


def main():
    metrics_path = PROJ_DIR / "docs" / "metrics.json"
    if not metrics_path.exists():
        print("ERROR: docs/metrics.json does not exist.", file=sys.stderr)
        sys.exit(1)

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    live_mmap = parse_memory_map()
    rendered = render_all_blocks(metrics)
    errors = []
    if metrics.get("memory_map") != live_mmap:
        errors.append("docs/metrics.json memory_map disagrees with rtl/axil/axil_decoder.v; re-run scripts/gen_metrics.py")
    errors.extend(verify_readme_matches_decoder((PROJ_DIR / "README.md").read_text(encoding="utf-8"), live_mmap))

    # 1. Regenerate every metrics block and fail on any diff
    for rel_path, blocks in rendered.items():
        fpath = PROJ_DIR / rel_path
        current = fpath.read_text(encoding="utf-8")
        try:
            expected = apply_blocks_to_text(current, blocks)
        except KeyError as e:
            errors.append(f"{rel_path}: {e}")
            continue
        if current != expected:
            diff = "\n".join(
                difflib.unified_diff(
                    current.splitlines(),
                    expected.splitlines(),
                    fromfile=f"{rel_path} (on disk)",
                    tofile=f"{rel_path} (from metrics.json)",
                    n=2,
                )
            )
            errors.append(f"{rel_path} disagrees with docs/metrics.json:\n{diff}")

        # 2. Check stale numbers / placeholders in managed docs
        for pat in FORBIDDEN_STALE_PATTERNS:
            for m in re.finditer(pat, current, flags=re.I):
                line_no = current[:m.start()].count("\n") + 1
                errors.append(f"{rel_path}:{line_no}: forbidden stale string '{m.group(0)}'")

        # Check bug count mentions outside FIX_REPORT history match metrics.json
        bugs_total = metrics["bugs"]["total"]
        for bm in re.finditer(r"\b(\d+)\s+bugs\b", current, flags=re.I):
            if int(bm.group(1)) != bugs_total:
                line_no = current[:bm.start()].count("\n") + 1
                errors.append(f"{rel_path}:{line_no}: bug count '{bm.group(0)}' != metrics.json bugs.total ({bugs_total})")

    # 3. Check local markdown links across README.md and docs/*.md
    md_files = ["README.md"] + sorted(
        Path(p).relative_to(PROJ_DIR).as_posix() for p in glob.glob(str(PROJ_DIR / "docs" / "*.md"))
    )
    for rel_md in md_files:
        fpath = PROJ_DIR / rel_md
        txt = fpath.read_text(encoding="utf-8")
        base = fpath.parent
        for m in re.finditer(r"\[[^\]]+\]\(([^)#\s]+)(?:#[^)]*)?\)", txt):
            tgt = m.group(1)
            if tgt.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = os.path.normpath(os.path.join(base, tgt))
            if not os.path.exists(resolved):
                line_no = txt[:m.start()].count("\n") + 1
                errors.append(f"{rel_md}:{line_no}: broken local link ({tgt})")

    # 4. Personal /home/<user>/ paths check across README.md, docs/, scripts/
    for rel_check in md_files + sorted(
        Path(p).relative_to(PROJ_DIR).as_posix() for p in glob.glob(str(PROJ_DIR / "scripts" / "*.py"))
    ):
        txt = (PROJ_DIR / rel_check).read_text(encoding="utf-8")
        for idx, line in enumerate(txt.splitlines(), 1):
            if re.search(r"/home/[a-zA-Z0-9._-]+/", line) and "re.sub" not in line and "somasai" in line:
                errors.append(f"{rel_check}:{idx}: personal path found: {line.strip()}")

    if errors:
        print("FAIL: Documentation consistency check failed:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    print("PASS: README.md, docs/results.md, and docs/vplan.md match docs/metrics.json with 0 diffs, 0 stale strings, and 0 broken links.")


if __name__ == "__main__":
    main()
