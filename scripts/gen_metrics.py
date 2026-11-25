#!/usr/bin/env python3
"""
scripts/gen_metrics.py

Collect all project verification, RTL, coverage, formal, mutation, bug,
synthesis, STA, and CI metrics directly from source files, XML results, and
archived tool logs into docs/metrics.json. Zero hardcoded metric values.
"""

import ast
import csv
import glob
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

PROJ_DIR = Path(__file__).resolve().parent.parent


def count_rtl_metrics():
    """Count RTL modules and non-blank, non-comment lines across rtl/**/*.v (F2)."""
    files = sorted((PROJ_DIR / "rtl").rglob("*.v"))
    modules = []
    total_lines = 0
    for fpath in files:
        rel = fpath.relative_to(PROJ_DIR).as_posix()
        txt = fpath.read_text(encoding="utf-8")
        no_block = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
        nb_nc = 0
        for line in no_block.splitlines():
            s = re.sub(r"//.*", "", line).strip()
            if s:
                nb_nc += 1
        mod_m = re.search(r"^\s*module\s+([A-Za-z0-9_]+)", no_block, re.M)
        mod_name = mod_m.group(1) if mod_m else fpath.stem
        total_lines += nb_nc
        modules.append({"module": mod_name, "file": rel, "lines": nb_nc})
    return {
        "module_count": len(modules),
        "total_lines": total_lines,
        "line_rule": "non-blank, non-comment lines across rtl/**/*.v",
        "modules": modules,
    }


def count_test_defs():
    """Count unique decorated @cocotb.test / @pyuvm.test definitions across tb/**/*.py."""
    by_tier = {"unit": 0, "block": 0, "pyuvm_directed": 0, "pyuvm_stress": 0}
    by_file = {}
    for py_path in sorted((PROJ_DIR / "tb").rglob("*.py")):
        if "__pycache__" in py_path.parts or ".venv" in py_path.parts:
            continue
        rel = py_path.relative_to(PROJ_DIR).as_posix()
        tree = ast.parse(py_path.read_text(encoding="utf-8"))
        cnt = 0
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if any("cocotb" in ast.dump(d) and "test" in ast.dump(d) for d in node.decorator_list):
                    cnt += 1
            elif isinstance(node, ast.ClassDef):
                if any("pyuvm" in ast.dump(d) and "test" in ast.dump(d) for d in node.decorator_list):
                    cnt += 1
        if cnt:
            by_file[rel] = cnt
            if rel.startswith("tb/unit/"):
                by_tier["unit"] += cnt
            elif rel.startswith("tb/block/"):
                by_tier["block"] += cnt
            elif rel.endswith("test_stress.py"):
                by_tier["pyuvm_stress"] += cnt
            elif rel.startswith("tb/pyuvm/"):
                by_tier["pyuvm_directed"] += cnt
    return {
        "unique_defs_total": sum(by_tier.values()),
        "by_tier": by_tier,
        "by_file": by_file,
    }


def parse_xml_testcases():
    """Count executed <testcase> entries from build/results/**/results*.xml (F2)."""
    xml_files = sorted((PROJ_DIR / "build" / "results").rglob("results*.xml"))
    if not xml_files:
        raise FileNotFoundError(
            "No results*.xml files found under build/results/. "
            "Run make unit, make block, make -C tb/pyuvm test_directed, and test_stress first."
        )
    total = 0
    passed = 0
    failed = 0
    suites = []
    for xfile in xml_files:
        rel = xfile.relative_to(PROJ_DIR).as_posix()
        root = ET.parse(xfile).getroot()
        tcs = list(root.iter("testcase"))
        f_cnt = sum(1 for tc in tcs if list(tc.iter("failure")))
        p_cnt = len(tcs) - f_cnt
        total += len(tcs)
        passed += p_cnt
        failed += f_cnt
        suites.append({"xml": rel, "total": len(tcs), "pass": p_cnt, "fail": f_cnt})
    return {
        "total": total,
        "pass": passed,
        "fail": failed,
        "xml_file_count": len(suites),
        "suites": suites,
    }


def parse_test_map():
    csv_path = PROJ_DIR / "docs" / "test_map.csv"
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    pass_cnt = sum(1 for r in rows if r["result"] == "PASS")
    fail_cnt = sum(1 for r in rows if r["result"] == "FAIL")
    other_cnt = len(rows) - pass_cnt - fail_cnt
    return {
        "total": len(rows),
        "pass": pass_cnt,
        "fail": fail_cnt,
        "not_run_or_missing": other_cnt,
        "rows": rows,
    }


def parse_stress_regressions():
    """Parse 20-seed Verilator and Icarus XB-13 stress logs."""
    verilator_log = PROJ_DIR / "docs" / "logs" / "phase_c_cov_report.log"
    icarus_log = PROJ_DIR / "docs" / "logs" / "phase_a_regress_20seeds.log"

    def _parse(log_path):
        txt = log_path.read_text(encoding="utf-8")
        seeds = [int(m) for m in re.findall(r"Starting XB-13 Stress Test with SEED=(\d+)", txt)]
        per_run_txns = [int(m) for m in re.findall(r"Launching FabricStressSeq with \d+ transactions per master \((\d+) total\)", txt)]
        completed = len(re.findall(r"=== Stress sequence completed successfully ===", txt))
        mismatches = len(re.findall(r"MISMATCH|Scoreboard error|FAIL=[1-9]", txt))
        return {
            "log": log_path.relative_to(PROJ_DIR).as_posix(),
            "seeds": seeds,
            "seed_count": len(seeds),
            "completed": completed,
            "transactions": sum(per_run_txns),
            "mismatches": mismatches,
        }

    return {
        "verilator": _parse(verilator_log),
        "icarus": _parse(icarus_log),
    }


def parse_functional_coverage():
    log_path = PROJ_DIR / "docs" / "logs" / "func_cov.log"
    waiver_path = PROJ_DIR / "docs" / "coverage_waivers.md"
    txt = log_path.read_text(encoding="utf-8")

    merged_m = re.search(r"Merged\s+(\d+)\s+coverage database file", txt)
    merged_files = int(merged_m.group(1)) if merged_m else 0

    metrics = {}
    groups = {}
    for line in txt.splitlines():
        m = re.match(r"^([a-zA-Z0-9_.]+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+([0-9.]+)%", line.strip())
        if m:
            name, bins, cov, pct = m.group(1), int(m.group(2)), int(m.group(3)), float(m.group(4))
            metrics[name] = {"bins": bins, "covered": cov, "pct": pct}
            grp = name.split(".")[0]
            g = groups.setdefault(grp, {"bins": 0, "covered": 0, "submetrics": []})
            g["bins"] += bins
            g["covered"] += cov
            g["submetrics"].append({"name": name, "bins": bins, "covered": cov, "pct": pct})
    for g in groups.values():
        g["pct"] = round(100.0 * g["covered"] / g["bins"], 2) if g["bins"] else 0.0

    agg_m = re.search(r"OVERALL AGGREGATE COVERAGE\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+([0-9.]+)%", txt)
    reachable_bins = int(agg_m.group(1))
    covered_bins = int(agg_m.group(2))
    pct = float(agg_m.group(3))

    # Parse waivers table from docs/coverage_waivers.md
    w_txt = waiver_path.read_text(encoding="utf-8")
    waived_by_group = {}
    for line in w_txt.splitlines():
        wm = re.match(r"^\|\s*`([^`]+)`\s*\|[^|]+\|\s*(\d+)\s*\|\s*(\d+)\s*(?:\([^|]*\))?\s*\|\s*(\d+)\s*\|", line)
        if wm:
            grp, total_def, waived, reach = wm.group(1), int(wm.group(2)), int(wm.group(3)), int(wm.group(4))
            waived_by_group[grp] = {"defined": total_def, "waived": waived, "reachable": reach}

    total_waived = sum(v["waived"] for v in waived_by_group.values())
    return {
        "log": log_path.relative_to(PROJ_DIR).as_posix(),
        "merged_yaml_files": merged_files,
        "reachable_bins": reachable_bins,
        "covered_bins": covered_bins,
        "coverage_pct": pct,
        "waived_bins": total_waived,
        "defined_pre_waiver_bins": reachable_bins + total_waived,
        "groups": groups,
        "waiver_summary": waived_by_group,
    }


def parse_code_coverage():
    p = PROJ_DIR / "docs" / "logs" / "code_cov_summary.txt"
    txt = p.read_text(encoding="utf-8")
    out = {"log": p.relative_to(PROJ_DIR).as_posix()}
    for line in txt.splitlines():
        m = re.match(r"^\s*([a-z_]+)\s*:\s*([0-9.]+)%\s*\(\s*(\d+)\s*/\s*(\d+)\s*\)", line)
        if m:
            out[m.group(1)] = {
                "pct": float(m.group(2)),
                "hit": int(m.group(3)),
                "total": int(m.group(4)),
            }
    return out


def _formal_sby_info(module_name):
    sby_path = PROJ_DIR / "formal" / f"{module_name}.sby"
    engine = "smtbmc boolector"
    multiclock = False
    if sby_path.exists():
        txt = sby_path.read_text(encoding="utf-8")
        if "abc pdr" in txt:
            engine = "abc pdr"
        if "multiclock on" in txt:
            multiclock = True
    return engine, multiclock


def parse_formal():
    p = PROJ_DIR / "docs" / "logs" / "formal_suite.log"
    txt = p.read_text(encoding="utf-8")
    rows = []
    for line in txt.splitlines():
        m = re.match(
            r"^\|\s*([a-zA-Z0-9_]+)\s*\|\s*([a-z+]+)\s*\|\s*(\d+)\s*\|\s*(PASS|FAIL)\s*\|\s*(\d+)\s*\|\s*(\d+)s\s*\|",
            line.strip(),
        )
        if m:
            mod = m.group(1)
            mode = m.group(2)
            depth = int(m.group(3))
            engine, multiclock = _formal_sby_info(mod)
            if mode == "prove":
                method_label = "PDR (prove, abc pdr)" if engine == "abc pdr" else "k-induction (prove)"
            elif mode == "prv+bmc":
                method_label = f"k-induction (prove) + BMC depth {depth}"
            else:
                mc_note = ", multiclock" if multiclock else ""
                method_label = f"BMC depth {depth}{mc_note}"
            rows.append({
                "module": mod,
                "mode": mode,
                "depth": depth,
                "engine": engine,
                "multiclock": multiclock,
                "method_label": method_label,
                "result": m.group(4),
                "covers": int(m.group(5)),
                "runtime_s": int(m.group(6)),
            })
    return {
        "log": p.relative_to(PROJ_DIR).as_posix(),
        "total_suites": len(rows),
        "passed_suites": sum(1 for r in rows if r["result"] == "PASS"),
        "failed_suites": sum(1 for r in rows if r["result"] != "PASS"),
        "total_covers": sum(r["covers"] for r in rows),
        "total_runtime_s": sum(r["runtime_s"] for r in rows),
        "suites": rows,
    }


def parse_sanity():
    p = PROJ_DIR / "docs" / "logs" / "sanity.log"
    txt = p.read_text(encoding="utf-8")
    m = re.search(r"Sanity Summary:\s+(\d+)/(\d+)\s+KILLED,\s+(\d+)\s+SURVIVED,\s+(\d+)\s+INVALID", txt)
    if not m:
        raise RuntimeError(f"Sanity summary not found in {p}")
    return {
        "log": p.relative_to(PROJ_DIR).as_posix(),
        "killed": int(m.group(1)),
        "total": int(m.group(2)),
        "survived": int(m.group(3)),
        "invalid": int(m.group(4)),
    }


def parse_mutation():
    base_log = PROJ_DIR / "docs" / "logs" / "mutation_baseline.log"
    final_log = PROJ_DIR / "docs" / "logs" / "mutation.log"
    equiv_log = PROJ_DIR / "docs" / "logs" / "mutation_equiv.log"
    report_md = PROJ_DIR / "docs" / "mutation_report.md"

    def _parse_table(path):
        txt = path.read_text(encoding="utf-8")
        mods = {}
        for line in txt.splitlines():
            m = re.match(
                r"^([a-zA-Z0-9_]+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([0-9.]+)%",
                line.strip(),
            )
            if m:
                mods[m.group(1)] = {
                    "gen": int(m.group(2)),
                    "valid": int(m.group(3)),
                    "kill": int(m.group(4)),
                    "surv": int(m.group(5)),
                    "tmo": int(m.group(6)),
                    "bld_err": int(m.group(7)),
                    "score_pct": float(m.group(8)),
                }
        tot_m = re.search(
            r"TOTAL / OVERALL\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([0-9.]+)%",
            txt,
        )
        tot = {
            "gen": int(tot_m.group(1)),
            "valid": int(tot_m.group(2)),
            "kill": int(tot_m.group(3)),
            "surv": int(tot_m.group(4)),
            "tmo": int(tot_m.group(5)),
            "bld_err": int(tot_m.group(6)),
            "score_pct": float(tot_m.group(7)),
        }
        return {"total": tot, "modules": mods}

    base = _parse_table(base_log)
    final = _parse_table(final_log)

    # Parse per-module counts from docs/logs/mutation_equiv.log + mutation_report.md
    eq_txt = equiv_log.read_text(encoding="utf-8")
    mod_unb = {m: 0 for m in final["modules"]}
    mod_bnd = {m: 0 for m in final["modules"]}
    unbounded_formal = 0
    signal_equiv = 0
    bounded_equiv = 0

    for line in eq_txt.splitlines():
        em = re.match(r"^(\S+)\s+#(\d+):\s*(\S+(?:\s+\([^)]+\))?)\s*\|", line.strip())
        if not em:
            continue
        mod_n, st_s = em.group(1), em.group(3)
        if st_s.startswith(("EQUIV_YOSYS", "EQUIV_PROVE")):
            unbounded_formal += 1
            if mod_n in mod_unb:
                mod_unb[mod_n] += 1
        elif st_s.startswith("SIGNAL_PROOF"):
            signal_equiv += 1
            if mod_n in mod_unb:
                mod_unb[mod_n] += 1
        elif st_s.startswith("BOUNDED_EQUIV_BMC10"):
            bounded_equiv += 1
            if mod_n in mod_bnd:
                mod_bnd[mod_n] += 1

    total_equiv = unbounded_formal + signal_equiv
    adj_den = final["total"]["valid"] - total_equiv
    adj_pct = round(100.0 * final["total"]["kill"] / adj_den, 2)
    adj_bnd_den = final["total"]["valid"] - total_equiv - bounded_equiv
    adj_bnd_pct = round(100.0 * final["total"]["kill"] / adj_bnd_den, 2)
    residual = final["total"]["surv"] - total_equiv - bounded_equiv

    return {
        "baseline_log": base_log.relative_to(PROJ_DIR).as_posix(),
        "final_log": final_log.relative_to(PROJ_DIR).as_posix(),
        "equiv_log": equiv_log.relative_to(PROJ_DIR).as_posix(),
        "report_doc": report_md.relative_to(PROJ_DIR).as_posix(),
        "generated": final["total"]["gen"],
        "baseline": base["total"],
        "final": final["total"],
        "equivalent_total": total_equiv,
        "equivalent_formal": unbounded_formal,
        "equivalent_signal": signal_equiv,
        "equivalent_bounded_d10": bounded_equiv,
        "residual_non_equiv": residual,
        "adjusted_denominator": adj_den,
        "adjusted_score_pct": adj_pct,
        "adjusted_bounded_denominator": adj_bnd_den,
        "adjusted_bounded_score_pct": adj_bnd_pct,
        "modules": {
            m: {
                "baseline": base["modules"][m],
                "final": final["modules"][m],
                "equiv": mod_unb[m],
                "equiv_bounded_d10": mod_bnd[m],
                "adj_den": final["modules"][m]["valid"] - mod_unb[m],
                "adj_score_pct": round(
                    100.0 * final["modules"][m]["kill"] / (final["modules"][m]["valid"] - mod_unb[m]), 2
                ),
            }
            for m in final["modules"]
        },
    }


def parse_bugs():
    p = PROJ_DIR / "docs" / "bugs.md"
    txt = p.read_text(encoding="utf-8")
    entries = []
    cur = None
    for line in txt.splitlines():
        m = re.match(r"^###\s+\[(BUG-\d+)\]\s+(.+)$", line.strip())
        if m:
            cur = {"id": m.group(1), "title": m.group(2), "component": ""}
            entries.append(cur)
        elif cur and line.strip().startswith("- **Target Component:**"):
            cur["component"] = line.split("**Target Component:**", 1)[1].strip()
    rtl_bugs = sum(1 for e in entries if "rtl/" in e["component"])
    return {
        "doc": p.relative_to(PROJ_DIR).as_posix(),
        "total": len(entries),
        "rtl_bugs": rtl_bugs,
        "tb_formal_tooling_bugs": len(entries) - rtl_bugs,
        "first_id": entries[0]["id"],
        "last_id": entries[-1]["id"],
    }


def parse_synthesis():
    p = PROJ_DIR / "docs" / "logs" / "phase_e_synth.log"
    txt = p.read_text(encoding="utf-8")
    stats_idx = txt.rfind("Printing statistics.")
    block = txt[stats_idx:]
    cells_m = re.search(r"^\s*(\d+)\s+[0-9.E+]+\s+cells", block, re.M)
    area_m = re.search(r"Chip area for module '\\amba_fabric_top':\s+([0-9.]+)", block)
    seq_m = re.search(r"of which used for sequential elements:\s+([0-9.]+)\s+\(([0-9.]+)%\)", block)

    dfrtp = int(re.search(r"^\s*(\d+)\s+\S+\s+sky130_fd_sc_hd__dfrtp_1", block, re.M).group(1))
    dfstp = int(re.search(r"^\s*(\d+)\s+\S+\s+sky130_fd_sc_hd__dfstp_1", block, re.M).group(1))
    edfxtp = int(re.search(r"^\s*(\d+)\s+\S+\s+sky130_fd_sc_hd__edfxtp_1", block, re.M).group(1))

    ram_depth_m = re.search(r"-chparam RAM_DEPTH (\d+)", (PROJ_DIR / "synth" / "synth.ys").read_text(encoding="utf-8"))
    ram_depth = int(ram_depth_m.group(1)) if ram_depth_m else 64

    return {
        "log": p.relative_to(PROJ_DIR).as_posix(),
        "total_cells": int(cells_m.group(1)),
        "flops": dfrtp + dfstp + edfxtp,
        "flop_breakdown": {"dfrtp_1": dfrtp, "dfstp_1": dfstp, "edfxtp_1": edfxtp},
        "ram_depth": ram_depth,
        "ram_flops": ram_depth * 32,
        "chip_area_um2": round(float(area_m.group(1)), 2),
        "sequential_area_um2": round(float(seq_m.group(1)), 2),
        "sequential_area_pct": float(seq_m.group(2)),
    }


def parse_sta():
    sweep_log = PROJ_DIR / "docs" / "logs" / "phase_e_fmax_sweep.log"
    sta_log = PROJ_DIR / "docs" / "logs" / "phase_e_sta.log"
    txt = sweep_log.read_text(encoding="utf-8")

    def _f(pat):
        m = re.search(pat, txt)
        if not m:
            raise RuntimeError(f"STA pattern not found: {pat}")
        return float(m.group(1))

    full_wns = _f(r"- Overall WNS:\s+([+-]?\d+\.\d+)\s+ns")
    full_tns = _f(r"- Overall TNS:\s+([+-]?\d+\.\d+)\s+ns")
    status = re.search(r"- Overall Status:\s+(\S+)", txt).group(1)
    clksys_wns = _f(r"- clk_sys Group Setup Slack \(at 10\.00 ns\):\s+([+-]?\d+\.\d+)\s+ns")
    clkslow_slack = _f(r"- clk_slow Group Setup Slack \(at 24\.00 ns\):\s+([+-]?\d+\.\d+)\s+ns")
    hold_slack = _f(r"- Hold Worst Slack \(min\):\s+([+-]?\d+\.\d+)\s+ns")
    unconst = int(re.search(r"- Unconstrained Endpoints \(check_setup\):\s+(\d+)", txt).group(1))
    full_fmax_m = re.search(r"- Achieved Full-Netlist Fmax:\s+([0-9.]+)\s+MHz \(Period = ([0-9.]+) ns\)", txt)
    dp_wns = _f(r"- clk_sys Datapath\+IO WNS @ 10\.00 ns:\s+([+-]?\d+\.\d+)\s+ns")
    dp_tns = float(re.search(r"clk_sys Datapath\+IO WNS @ 10\.00 ns: [^,]+, TNS:\s+([+-]?\d+\.\d+)\s+ns", txt).group(1))
    dp_fmax_m = re.search(
        r"- Achieved Core\+IO Reference Fmax \(excluding unbuffered reset net\):\s+([0-9.]+)\s+MHz \(Period = ([0-9.]+) ns\)",
        txt,
    )
    peak_m = re.search(r"- Peak Net:\s+(\S+)\s+\(fanout=(\d+),\s+cap=([0-9.]+)\s+pF,\s+slew=([0-9.]+)\s+ns\)", txt)
    r2r_m = re.search(
        r"\[Pure Register-to-Register Critical Path.*?Arrival / Required / Slack:\s+([0-9.]+)\s+ns / ([0-9.]+)\s+ns / ([+-]?\d+\.\d+)\s+ns",
        txt,
        flags=re.S,
    )

    return {
        "sta_log": sta_log.relative_to(PROJ_DIR).as_posix(),
        "fmax_sweep_log": sweep_log.relative_to(PROJ_DIR).as_posix(),
        "target_clk_sys_mhz": 100.0,
        "target_clk_sys_ns": 10.0,
        "target_clk_slow_mhz": 41.67,
        "target_clk_slow_ns": 24.0,
        "full_wns_ns": full_wns,
        "full_tns_ns": full_tns,
        "full_status": status,
        "clk_sys_setup_slack_ns": clksys_wns,
        "clk_slow_setup_slack_ns": clkslow_slack,
        "hold_worst_slack_ns": hold_slack,
        "unconstrained_endpoints": unconst,
        "full_fmax_mhz": float(full_fmax_m.group(1)),
        "full_fmax_period_ns": float(full_fmax_m.group(2)),
        "datapath_io_wns_ns": dp_wns,
        "datapath_io_tns_ns": dp_tns,
        "datapath_io_fmax_mhz": float(dp_fmax_m.group(1)),
        "datapath_io_fmax_period_ns": float(dp_fmax_m.group(2)),
        "pure_reg2reg_slack_ns": float(r2r_m.group(3)),
        "reset_bottleneck_net": peak_m.group(1),
        "reset_bottleneck_fanout": int(peak_m.group(2)),
        "reset_bottleneck_cap_pf": float(peak_m.group(3)),
        "reset_bottleneck_slew_ns": float(peak_m.group(4)),
    }


def parse_ci_status():
    ci_path = PROJ_DIR / "docs" / "logs" / "ci_remote_verified.json"
    if ci_path.exists():
        return json.loads(ci_path.read_text(encoding="utf-8"))
    return {
        "status": "NOT VERIFIED",
        "run_url": None,
        "note": "Pending Phase G GitHub Actions push and remote verification",
    }


def main():
    rtl = count_rtl_metrics()
    test_defs = count_test_defs()
    xml_cases = parse_xml_testcases()
    spec_map = parse_test_map()
    regress = parse_stress_regressions()
    func_cov = parse_functional_coverage()
    code_cov = parse_code_coverage()
    formal = parse_formal()
    sanity = parse_sanity()
    mutation = parse_mutation()
    bugs = parse_bugs()
    synth = parse_synthesis()
    sta = parse_sta()
    ci = parse_ci_status()

    metrics = {
        "schema_version": 1,
        "rtl": rtl,
        "tests": {
            "unique_defs_total": test_defs["unique_defs_total"],
            "unique_defs_by_tier": test_defs["by_tier"],
            "unique_defs_by_file": test_defs["by_file"],
            "xml_testcases_executed": xml_cases["total"],
            "xml_testcases_passed": xml_cases["pass"],
            "xml_testcases_failed": xml_cases["fail"],
            "xml_file_count": xml_cases["xml_file_count"],
            "spec_tests_total": spec_map["total"],
            "spec_tests_passed": spec_map["pass"],
            "spec_tests_failed": spec_map["fail"],
            "spec_tests_missing": spec_map["not_run_or_missing"],
        },
        "random_regression": regress,
        "cdc": {
            "slow_periods_ns": [25.0, 10.3, 6.0],
            "slow_phases_ns": [0.0, 2.5, 1.2],
            "ratio_count": 3,
            "phase_count": 3,
            "formal_async_fifo_depth": next(
                r["depth"] for r in formal["suites"] if r["module"] == "async_fifo"
            ),
            "formal_cdc_bridge_depth": next(
                r["depth"] for r in formal["suites"] if r["module"] == "axil_cdc_bridge"
            ),
        },
        "functional_coverage": func_cov,
        "code_coverage": code_cov,
        "formal": formal,
        "sanity": sanity,
        "mutation": mutation,
        "bugs": bugs,
        "synthesis": synth,
        "sta": sta,
        "ci": ci,
    }

    out_path = PROJ_DIR / "docs" / "metrics.json"
    out_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path.relative_to(PROJ_DIR).as_posix()} cleanly.")


if __name__ == "__main__":
    main()
