#!/usr/bin/env python3
"""
mutation/run_mutants.py
Yosys-based Scaled Parallel Mutation Testing Driver for AMBA-Fabric

Target modules:
  - rr_arbiter
  - sync_fifo
  - async_fifo
  - axil_decoder
  - axil_ram
  - axil_csr
  - axil2apb_bridge
  - axil_xbar
"""

import argparse
import json
import multiprocessing
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

PROJ_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BUILD_DIR = os.environ.get("BUILD_DIR", os.path.join(PROJ_DIR, "build"))

TARGETS = [
    {
        "name": "rr_arbiter",
        "sources": ["rtl/common/rr_arbiter.v"],
        "prep_top": "rr_arbiter",
        "toplevel": "rr_arbiter",
        "test_dir": "tb/unit",
        "makefile": "Makefile.single",
        "module": "test_rr_arbiter",
    },
    {
        "name": "sync_fifo",
        "sources": ["rtl/common/sync_fifo.v"],
        "prep_top": "sync_fifo",
        "toplevel": "sync_fifo",
        "test_dir": "tb/unit",
        "makefile": "Makefile.single",
        "module": "test_sync_fifo",
    },
    {
        "name": "async_fifo",
        "sources": ["rtl/common/async_fifo.v"],
        "prep_top": "async_fifo",
        "toplevel": "async_fifo",
        "test_dir": "tb/unit",
        "makefile": "Makefile.single",
        "module": "test_async_fifo",
    },
    {
        "name": "axil_decoder",
        "sources": ["rtl/axil/axil_decoder.v"],
        "prep_top": "axil_decoder",
        "toplevel": "axil_decoder",
        "test_dir": "tb/unit",
        "makefile": "Makefile.single",
        "module": "test_axil_decoder",
    },
    {
        "name": "axil_ram",
        "sources": ["rtl/axil/axil_ram.v"],
        "prep_top": "axil_ram",
        "toplevel": "axil_ram",
        "test_dir": "tb/unit",
        "makefile": "Makefile.single",
        "module": "test_axil_ram",
    },
    {
        "name": "axil_csr",
        "sources": ["rtl/axil/axil_csr.v"],
        "prep_top": "axil_csr",
        "toplevel": "axil_csr",
        "test_dir": "tb/unit",
        "makefile": "Makefile.single",
        "module": "test_axil_csr",
    },
    {
        "name": "axil2apb_bridge",
        "sources": ["rtl/apb/axil2apb_bridge.v"],
        "prep_top": "axil2apb_bridge",
        "toplevel": "axil2apb_bridge",
        "test_dir": "tb/block",
        "makefile": "Makefile.single",
        "module": "test_axil2apb_bridge",
    },
    {
        "name": "axil_xbar",
        "sources": [
            "rtl/axil/axil_decoder.v",
            "rtl/axil/axil_default_slave.v",
            "rtl/axil/axil_xbar.v",
            "tb/block/tb_axil_xbar.v",
        ],
        "prep_top": "tb_axil_xbar",
        "toplevel": "tb_axil_xbar",
        "test_dir": "tb/block",
        "makefile": "Makefile.single",
        "module": "test_axil_xbar",
        "hierarchical": True,
        "mutate_select": "$paramod*axil_xbar",
    },
]


def strip_proj_path(text):
    """Strip PROJ_DIR and any home directory paths to ensure clean relative paths."""
    if not text:
        return ""
    text = text.replace(PROJ_DIR + "/", "")
    text = text.replace(PROJ_DIR, ".")
    text = re.sub(r"/home/[^/\s]+/", "", text)
    return text


def _write_yosys_prelude(f, target):
    # Always pass repo-relative RTL paths with cwd=PROJ_DIR so cell IDs never embed /home/ paths
    for src in target["sources"]:
        f.write(f"read_verilog -sv {src}\n")
    if target.get("hierarchical"):
        f.write(f"hierarchy -check -top {target['prep_top']}\n")
        f.write("proc\n")
        f.write("opt\n")
    else:
        f.write(f"prep -top {target['prep_top']}\n")


def generate_mutants_for_target(target, count, seed, tmpdir):
    """Generate mutation command list for target module using Yosys."""
    list_file = os.path.join(tmpdir, f"mutants_{target['name']}.txt")
    ys_script = os.path.join(tmpdir, f"gen_{target['name']}.ys")

    with open(ys_script, "w") as f:
        _write_yosys_prelude(f, target)
        sel = target.get("mutate_select", "")
        sel_arg = f" {sel}" if sel else ""
        f.write(f"mutate -list {count} -seed {seed} -o {list_file}{sel_arg}\n")

    subprocess.run(["yosys", "-q", ys_script], cwd=PROJ_DIR, check=True)

    mutants = []
    if os.path.exists(list_file):
        with open(list_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("mutate"):
                    mutants.append(line)
    return mutants


def worker_evaluate_mutant(task_arg):
    """Worker function executing in parallel process with isolated process group."""
    (
        target,
        idx,
        mut_cmd,
        base_tmpdir,
        survivor_dir,
    ) = task_arg

    mod_name = target["name"]
    workdir = os.path.join(base_tmpdir, f"{mod_name}_{idx}")
    os.makedirs(workdir, exist_ok=True)

    mut_v = os.path.join(workdir, f"{mod_name}_mut_{idx}.v")
    ys_script = os.path.join(workdir, f"apply_{mod_name}_{idx}.ys")

    with open(ys_script, "w") as f:
        _write_yosys_prelude(f, target)
        # Re-anchor any relative paths if list came from relative storage
        f.write(f"{mut_cmd}\n")
        f.write(f"write_verilog -noattr {mut_v}\n")

    res = subprocess.run(["yosys", "-q", ys_script], cwd=PROJ_DIR, capture_output=True, text=True)
    clean_cmd = strip_proj_path(mut_cmd)
    if res.returncode != 0 or not os.path.exists(mut_v) or os.path.getsize(mut_v) == 0:
        return {
            "module": mod_name,
            "index": idx,
            "command": clean_cmd,
            "status": "BUILD_ERROR",
            "killed": False,
            "survivor_file": None,
        }

    sim_build = os.path.join(workdir, "sim_build")
    results_xml = os.path.join(workdir, "results.xml")
    test_dir = os.path.join(PROJ_DIR, target["test_dir"])

    cmd = [
        "make",
        "-C", test_dir,
        "-f", target["makefile"],
        f"TOPLEVEL={target['toplevel']}",
        f"MODULE={target['module']}",
        f"VERILOG_SOURCES={mut_v}",
        f"SIM_BUILD={sim_build}",
        f"COCOTB_RESULTS_FILE={results_xml}",
        "SIM=icarus",
    ]

    env = os.environ.copy()
    py_paths = [
        os.path.join(PROJ_DIR, "tb/models"),
        os.path.join(PROJ_DIR, "tb/pyuvm"),
        test_dir,
    ]
    if "PYTHONPATH" in env and env["PYTHONPATH"]:
        py_paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = ":".join(py_paths)
    env["TMPDIR"] = os.path.join(BUILD_DIR, "tmp")

    proc = None
    timed_out = False
    out_text = ""
    try:
        proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        _stdout, _stderr = proc.communicate(timeout=40)
        out_text = (_stdout or "") + "\n" + (_stderr or "")
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        if proc is not None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
        rc = -9

    sim_vvp = os.path.join(sim_build, "sim.vvp")
    ran_sim = os.path.exists(sim_vvp) and ("Initialized cocotb" in out_text or "Running tests" in out_text)
    test_failed_in_log = ("FAIL=" in out_text and "FAIL=0" not in out_text) or ("AssertionError" in out_text) or ("TimeoutError" in out_text)

    if timed_out:
        status = "TIMEOUT"
    elif rc != 0:
        # Distinguish genuine compile/setup errors from test failures
        # (GNU Make deletes results.xml if cocotb/Icarus teardown segfaults after printing FAIL=1)
        if ran_sim and (os.path.exists(results_xml) or test_failed_in_log):
            status = "KILLED"
        else:
            status = "BUILD_ERROR"
    else:
        status = "SURVIVED"

    if status == "SURVIVED":
        survivor_file = os.path.join(survivor_dir, f"{mod_name}_mut_{idx}.v")
        shutil.copyfile(mut_v, survivor_file)
        rel_survivor_file = strip_proj_path(survivor_file)
    else:
        rel_survivor_file = None

    return {
        "module": mod_name,
        "index": idx,
        "command": clean_cmd,
        "status": status,
        "killed": (status == "KILLED"),
        "survivor_file": rel_survivor_file,
    }


def main():
    parser = argparse.ArgumentParser(description="Yosys Scaled Mutation Testing Driver for AMBA-Fabric")
    parser.add_argument("--max-mutants", type=int, default=240, help="Total number of mutants across all modules")
    parser.add_argument("--sample", action="store_true", help="Sampled run (24 mutants total)")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for Yosys mutate")
    parser.add_argument("--jobs", "-j", type=int, default=4, help="Parallel worker jobs (max 4)")
    parser.add_argument("--output", type=str, default=os.path.join(PROJ_DIR, "docs/logs/mutation.log"), help="Summary log output")
    parser.add_argument("--survivor-dir", type=str, default=os.path.join(PROJ_DIR, "mutation/results/survivors"), help="Survivor save dir")
    parser.add_argument("--generate-list", type=str, default=None, help="Generate frozen mutant list JSON and exit")
    parser.add_argument("--mutant-list", type=str, default=None, help="Evaluate pre-generated frozen mutant list JSON")
    args = parser.parse_args()

    jobs = min(max(1, args.jobs), 4)
    total_requested = 24 if args.sample else args.max_mutants
    per_module = max(1, total_requested // len(TARGETS))

    tmp_root = os.path.join(BUILD_DIR, "tmp")
    os.makedirs(tmp_root, exist_ok=True)
    os.makedirs(args.survivor_dir, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    # Clear survivor dir before a run unless only generating list
    if not args.generate_list:
        for fn in os.listdir(args.survivor_dir):
            fp = os.path.join(args.survivor_dir, fn)
            if os.path.isfile(fp):
                os.remove(fp)

    if args.generate_list:
        with tempfile.TemporaryDirectory(dir=tmp_root) as base_tmpdir:
            frozen = {
                "seed": args.seed,
                "per_module": per_module,
                "total": per_module * len(TARGETS),
                "modules": {},
            }
            for target in TARGETS:
                muts = generate_mutants_for_target(target, per_module, args.seed, base_tmpdir)
                frozen["modules"][target["name"]] = [strip_proj_path(m) for m in muts]
            os.makedirs(os.path.dirname(os.path.abspath(args.generate_list)), exist_ok=True)
            with open(args.generate_list, "w") as fp:
                json.dump(frozen, fp, indent=2)
            print(f"Generated frozen mutant list ({frozen['total']} mutants) at {strip_proj_path(args.generate_list)}")
        return

    loaded_list = None
    if args.mutant_list:
        with open(args.mutant_list, "r") as fp:
            loaded_list = json.load(fp)
        per_module = loaded_list.get("per_module", per_module)

    print("================================================================================")
    print("AMBA-Fabric Scaled Parallel Mutation Testing (Yosys Native)")
    print(f"Target Modules ({len(TARGETS)}): {', '.join(t['name'] for t in TARGETS)}")
    src_desc = f"frozen list ({strip_proj_path(args.mutant_list)})" if loaded_list else f"seed={args.seed}"
    print(f"Total Mutants Requested: {per_module * len(TARGETS)} ({per_module} per module, {src_desc}, parallel jobs={jobs})")
    print("================================================================================")

    t_start = time.time()
    results = {}
    all_survivors = []
    all_timeouts = []
    all_build_errs = []
    total_generated = 0
    total_valid = 0
    total_killed = 0
    total_survived = 0
    total_timeout = 0
    total_build_err = 0

    with tempfile.TemporaryDirectory(dir=tmp_root) as base_tmpdir:
        for target in TARGETS:
            t_mod_start = time.time()
            if loaded_list is not None:
                mutants = list(loaded_list["modules"][target["name"]])
                print(f"\n--- Loaded {len(mutants)} frozen mutations for: {target['name']} (jobs={jobs}) ---")
            else:
                print(f"\n--- Generating Mutants for: {target['name']} ---")
                mutants = generate_mutants_for_target(target, per_module, args.seed, base_tmpdir)
                print(f"Generated {len(mutants)} mutations for {target['name']}. Running evaluation (jobs={jobs})...")

            tasks = [
                (target, idx, m_cmd, base_tmpdir, args.survivor_dir)
                for idx, m_cmd in enumerate(mutants)
            ]

            target_killed = 0
            target_survived = 0
            target_timeout = 0
            target_build_err = 0
            mod_survivors = []

            with multiprocessing.Pool(processes=jobs) as pool:
                for res in pool.imap_unordered(worker_evaluate_mutant, tasks):
                    idx = res["index"]
                    status = res["status"]
                    cmd_preview = res["command"][:65]
                    print(f"  [{res['module']} {idx+1:02d}/{len(mutants):02d}] {status}: {cmd_preview}...")

                    if status == "KILLED":
                        target_killed += 1
                    elif status == "SURVIVED":
                        target_survived += 1
                        mod_survivors.append(res)
                        all_survivors.append(res)
                    elif status == "TIMEOUT":
                        target_timeout += 1
                        all_timeouts.append(res)
                    else:
                        target_build_err += 1
                        all_build_errs.append(res)

            t_mod_end = time.time()
            valid_mod = len(mutants) - target_build_err
            score = (target_killed / valid_mod * 100.0) if valid_mod > 0 else 0.0

            results[target["name"]] = {
                "generated": len(mutants),
                "build_err": target_build_err,
                "timeout": target_timeout,
                "valid": valid_mod,
                "killed": target_killed,
                "survived": target_survived,
                "score": score,
                "time": t_mod_end - t_mod_start,
                "survivors": mod_survivors,
            }

            total_generated += len(mutants)
            total_valid += valid_mod
            total_killed += target_killed
            total_survived += target_survived
            total_timeout += target_timeout
            total_build_err += target_build_err

            print(
                f"Module {target['name']} Complete: {target_killed}/{valid_mod} killed "
                f"(survived={target_survived}, timeout={target_timeout}, build_err={target_build_err}, {score:.1f}%) "
                f"in {t_mod_end - t_mod_start:.1f}s"
            )

    t_total = time.time() - t_start
    overall_score = (total_killed / total_valid * 100.0) if total_valid > 0 else 0.0

    summary_text = [
        "================================================================================",
        "AMBA-Fabric Scaled Mutation Testing Summary Report",
        f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Execution Time: {t_total:.2f} seconds",
        f"RNG Seed: {loaded_list.get('seed', args.seed) if loaded_list else args.seed}",
        f"Parallel Jobs: {jobs}",
        "================================================================================",
        f"{'Module':<16} | {'Gen':<5} | {'Valid':<5} | {'Kill':<5} | {'Surv':<5} | {'Tmo':<4} | {'BldErr':<6} | {'Score (%)':<9}",
        "-" * 78,
    ]

    for mod_name, res in results.items():
        summary_text.append(
            f"{mod_name:<16} | {res['generated']:<5} | {res['valid']:<5} | {res['killed']:<5} | "
            f"{res['survived']:<5} | {res['timeout']:<4} | {res['build_err']:<6} | {res['score']:>8.2f}%"
        )
    summary_text.append("=" * 78)
    summary_text.append(
        f"{'TOTAL / OVERALL':<16} | {total_generated:<5} | {total_valid:<5} | {total_killed:<5} | "
        f"{total_survived:<5} | {total_timeout:<4} | {total_build_err:<6} | {overall_score:>8.2f}%"
    )
    summary_text.append("================================================================================")
    summary_text.append(f"\nTotal Survivors: {len(all_survivors)} (Timeouts: {len(all_timeouts)}, BuildErrors: {len(all_build_errs)})")
    for s in sorted(all_survivors, key=lambda x: (x["module"], x["index"])):
        summary_text.append(f"  - [{s['module']} #{s['index']}]: {s['command']}")
        summary_text.append(f"    Saved RTL: {s['survivor_file']}")
    if all_timeouts:
        summary_text.append("\nTimed-out Mutants (NOT counted as killed):")
        for s in sorted(all_timeouts, key=lambda x: (x["module"], x["index"])):
            summary_text.append(f"  - [{s['module']} #{s['index']}]: {s['command']}")
    if all_build_errs:
        summary_text.append("\nBuild-Error Mutants (NOT counted as killed):")
        for s in sorted(all_build_errs, key=lambda x: (x["module"], x["index"])):
            summary_text.append(f"  - [{s['module']} #{s['index']}]: {s['command']}")

    summary_str = "\n".join(summary_text)
    print("\n" + summary_str)

    with open(args.output, "w") as f:
        f.write(summary_str + "\n")
    print(f"\nReport written to {strip_proj_path(args.output)}")

    if os.path.abspath(args.output) == os.path.abspath(os.path.join(PROJ_DIR, "docs/logs/mutation.log")):
        summary_log_path = os.path.join(PROJ_DIR, "docs/logs/mutation_summary.log")
        with open(summary_log_path, "w") as f:
            f.write(summary_str + "\n")


if __name__ == "__main__":
    main()
