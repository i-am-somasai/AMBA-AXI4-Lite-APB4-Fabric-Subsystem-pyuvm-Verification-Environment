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
import multiprocessing
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

PROJ_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

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
            "rtl/common/rr_arbiter.v",
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


def generate_mutants_for_target(target, count, seed, tmpdir):
    """Generate mutation command list for target module using Yosys."""
    list_file = os.path.join(tmpdir, f"mutants_{target['name']}.txt")
    ys_script = os.path.join(tmpdir, f"gen_{target['name']}.ys")
    
    with open(ys_script, "w") as f:
        for src in target["sources"]:
            abs_src = os.path.join(PROJ_DIR, src)
            f.write(f"read_verilog -sv {abs_src}\n")
        f.write(f"prep -top {target['prep_top']}\n")
        f.write(f"mutate -list {count} -seed {seed} -o {list_file}\n")
    
    subprocess.run(["yosys", "-q", ys_script], check=True)
    
    mutants = []
    if os.path.exists(list_file):
        with open(list_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("mutate"):
                    mutants.append(line)
    return mutants


def worker_evaluate_mutant(task_arg):
    """Worker function executing in parallel process."""
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
        for src in target["sources"]:
            abs_src = os.path.join(PROJ_DIR, src)
            f.write(f"read_verilog -sv {abs_src}\n")
        f.write(f"prep -top {target['prep_top']}\n")
        f.write(f"{mut_cmd}\n")
        f.write(f"write_verilog -noattr {mut_v}\n")

    res = subprocess.run(["yosys", "-q", ys_script], capture_output=True, text=True)
    if res.returncode != 0 or not os.path.exists(mut_v) or os.path.getsize(mut_v) == 0:
        return {
            "module": mod_name,
            "index": idx,
            "command": strip_proj_path(mut_cmd),
            "status": "ERROR_APPLY",
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

    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=40)
        killed = (proc.returncode != 0)
    except subprocess.TimeoutExpired:
        killed = True

    clean_cmd = strip_proj_path(mut_cmd)

    if killed:
        return {
            "module": mod_name,
            "index": idx,
            "command": clean_cmd,
            "status": "KILLED",
            "killed": True,
            "survivor_file": None,
        }
    else:
        survivor_file = os.path.join(survivor_dir, f"{mod_name}_mut_{idx}.v")
        shutil.copyfile(mut_v, survivor_file)
        rel_survivor_file = strip_proj_path(survivor_file)
        return {
            "module": mod_name,
            "index": idx,
            "command": clean_cmd,
            "status": "SURVIVED",
            "killed": False,
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
    args = parser.parse_args()

    jobs = min(max(1, args.jobs), 4)
    total_requested = 24 if args.sample else args.max_mutants
    per_module = max(1, total_requested // len(TARGETS))

    os.makedirs(args.survivor_dir, exist_ok=True)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    print("================================================================================")
    print("AMBA-Fabric Scaled Parallel Mutation Testing (Yosys Native)")
    print(f"Target Modules ({len(TARGETS)}): {', '.join(t['name'] for t in TARGETS)}")
    print(f"Total Mutants Requested: {per_module * len(TARGETS)} ({per_module} per module, seed={args.seed}, parallel jobs={jobs})")
    print("================================================================================")

    t_start = time.time()
    results = {}
    all_survivors = []
    total_generated = 0
    total_valid = 0
    total_killed = 0
    total_survived = 0

    with tempfile.TemporaryDirectory() as base_tmpdir:
        for target in TARGETS:
            t_mod_start = time.time()
            print(f"\n--- Generating Mutants for: {target['name']} ---")
            mutants = generate_mutants_for_target(target, per_module, args.seed, base_tmpdir)
            print(f"Generated {len(mutants)} mutations for {target['name']}. Running evaluation (jobs={jobs})...")

            tasks = [
                (target, idx, m_cmd, base_tmpdir, args.survivor_dir)
                for idx, m_cmd in enumerate(mutants)
            ]

            target_killed = 0
            target_survived = 0
            target_errors = 0
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
                    else:
                        target_errors += 1

            t_mod_end = time.time()
            valid_mod = target_killed + target_survived
            score = (target_killed / valid_mod * 100.0) if valid_mod > 0 else 0.0

            results[target["name"]] = {
                "generated": len(mutants),
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

            print(f"Module {target['name']} Complete: {target_killed}/{valid_mod} killed ({score:.1f}%) in {t_mod_end - t_mod_start:.1f}s")

    t_total = time.time() - t_start
    overall_score = (total_killed / total_valid * 100.0) if total_valid > 0 else 0.0

    summary_text = [
        "================================================================================",
        "AMBA-Fabric Scaled Mutation Testing Summary Report",
        f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Execution Time: {t_total:.2f} seconds",
        f"RNG Seed: {args.seed}",
        f"Parallel Jobs: {jobs}",
        "================================================================================",
        f"{'Module':<18} | {'Generated':<10} | {'Valid':<8} | {'Killed':<8} | {'Survived':<8} | {'Score (%)':<10}",
        "-" * 75,
    ]

    for mod_name, res in results.items():
        summary_text.append(
            f"{mod_name:<18} | {res['generated']:<10} | {res['valid']:<8} | {res['killed']:<8} | {res['survived']:<8} | {res['score']:>8.2f}%"
        )
    summary_text.append("=" * 75)
    summary_text.append(
        f"{'TOTAL / OVERALL':<18} | {total_generated:<10} | {total_valid:<8} | {total_killed:<8} | {total_survived:<8} | {overall_score:>8.2f}%"
    )
    summary_text.append("================================================================================")
    summary_text.append(f"\nTotal Survivors: {len(all_survivors)}")
    for s in all_survivors:
        summary_text.append(f"  - [{s['module']} #{s['index']}]: {s['command']}")
        summary_text.append(f"    Saved RTL: {s['survivor_file']}")

    summary_str = "\n".join(summary_text)
    print("\n" + summary_str)

    with open(args.output, "w") as f:
        f.write(summary_str + "\n")
    print(f"\nReport written to {strip_proj_path(args.output)}")

    # Also update docs/logs/mutation_summary.log for consistency
    summary_log_path = os.path.join(PROJ_DIR, "docs/logs/mutation_summary.log")
    with open(summary_log_path, "w") as f:
        f.write(summary_str + "\n")


if __name__ == "__main__":
    main()
