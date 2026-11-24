#!/usr/bin/env python3
"""
mutation/run_mutants.py
Yosys-based Mutation Testing Driver for AMBA-Fabric

Flow (per spec Section 12):
1. Target RTL scope: rr_arbiter, sync_fifo, axil_ram, axil_csr, axil2apb_bridge.
2. Uses Yosys `mutate -list N` to generate mutations.
3. Applies each mutation to generate a mutated Verilog netlist.
4. Runs the target testbench for each mutant in an isolated build directory.
5. Records KILLED or SURVIVED, triages survivors, and reports mutation score.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time

PROJ_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

TARGETS = [
    {
        "name": "rr_arbiter",
        "rtl": os.path.join(PROJ_DIR, "rtl/common/rr_arbiter.v"),
        "toplevel": "rr_arbiter",
        "test_dir": os.path.join(PROJ_DIR, "tb/unit"),
        "makefile": "Makefile.single",
        "module": "test_rr_arbiter",
        "extra_sources": [],
    },
    {
        "name": "sync_fifo",
        "rtl": os.path.join(PROJ_DIR, "rtl/common/sync_fifo.v"),
        "toplevel": "sync_fifo",
        "test_dir": os.path.join(PROJ_DIR, "tb/unit"),
        "makefile": "Makefile.single",
        "module": "test_sync_fifo",
        "extra_sources": [],
    },
    {
        "name": "axil_ram",
        "rtl": os.path.join(PROJ_DIR, "rtl/axil/axil_ram.v"),
        "toplevel": "axil_ram",
        "test_dir": os.path.join(PROJ_DIR, "tb/unit"),
        "makefile": "Makefile.single",
        "module": "test_axil_ram",
        "extra_sources": [],
    },
    {
        "name": "axil_csr",
        "rtl": os.path.join(PROJ_DIR, "rtl/axil/axil_csr.v"),
        "toplevel": "axil_csr",
        "test_dir": os.path.join(PROJ_DIR, "tb/unit"),
        "makefile": "Makefile.single",
        "module": "test_axil_csr",
        "extra_sources": [],
    },
    {
        "name": "axil2apb_bridge",
        "rtl": os.path.join(PROJ_DIR, "rtl/apb/axil2apb_bridge.v"),
        "toplevel": "axil2apb_bridge",
        "test_dir": os.path.join(PROJ_DIR, "tb/block"),
        "makefile": "Makefile.single",
        "module": "test_axil2apb_bridge",
        "extra_sources": [],
    },
]


def generate_mutants_for_target(target, count, seed, tmpdir):
    """Generate list of mutations for target module using Yosys."""
    list_file = os.path.join(tmpdir, f"mutants_{target['name']}.txt")
    ys_script = os.path.join(tmpdir, f"gen_{target['name']}.ys")
    with open(ys_script, "w") as f:
        f.write(f"read_verilog -sv {target['rtl']}\n")
        f.write(f"prep -top {target['name']}\n")
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


def apply_mutation(target, mutation_cmd, out_v, tmpdir, idx):
    """Apply a mutation command using Yosys and write netlist."""
    ys_script = os.path.join(tmpdir, f"apply_{target['name']}_{idx}.ys")
    with open(ys_script, "w") as f:
        f.write(f"read_verilog -sv {target['rtl']}\n")
        f.write(f"prep -top {target['name']}\n")
        f.write(f"{mutation_cmd}\n")
        f.write(f"write_verilog -noattr {out_v}\n")
    
    res = subprocess.run(["yosys", "-q", ys_script], capture_output=True, text=True)
    return res.returncode == 0 and os.path.exists(out_v) and os.path.getsize(out_v) > 0


def test_mutant(target, mutant_v, sim_build_dir):
    """Run target testbench on mutated Verilog source."""
    all_sources = f"{mutant_v} {' '.join(target['extra_sources'])}".strip()
    cmd = [
        "make",
        "-C", target["test_dir"],
        "-f", target["makefile"],
        f"TOPLEVEL={target['toplevel']}",
        f"MODULE={target['module']}",
        f"VERILOG_SOURCES={all_sources}",
        f"SIM_BUILD={sim_build_dir}",
        "SIM=icarus",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    # If make returns non-zero, the mutant failed the test -> KILLED
    # If make returns 0, the test passed despite the mutation -> SURVIVED
    return res.returncode != 0, res.stdout, res.stderr


def main():
    parser = argparse.ArgumentParser(description="Yosys Mutation Testing Flow for AMBA-Fabric")
    parser.add_argument("--max-mutants", type=int, default=200, help="Total number of mutants to test across all modules")
    parser.add_argument("--sample", action="store_true", help="Sampled run (20 mutants for CI / quick check)")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for mutation sampling")
    parser.add_argument("--output", default=os.path.join(PROJ_DIR, "docs/logs/mutation_summary.log"), help="Summary log file")
    parser.add_argument("--survivor-dir", default=os.path.join(PROJ_DIR, "mutation/results/survivors"), help="Directory to save surviving mutants")
    args = parser.parse_args()

    total_target_mutants = 20 if args.sample else args.max_mutants
    per_module = max(4, total_target_mutants // len(TARGETS))

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    os.makedirs(args.survivor_dir, exist_ok=True)

    print("================================================================================")
    print("AMBA-Fabric Mutation Testing Flow (Yosys Native)")
    print(f"Target Modules: {', '.join(t['name'] for t in TARGETS)}")
    print(f"Total Mutants Requested: {total_target_mutants} (~{per_module} per module, seed={args.seed})")
    print("================================================================================")

    t_start = time.time()
    results = {}
    all_survivors = []
    total_generated = 0
    total_killed = 0
    total_survived = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        for target in TARGETS:
            t_mod_start = time.time()
            print(f"\n--- Testing Module: {target['name']} ---")
            mutants = generate_mutants_for_target(target, per_module, args.seed, tmpdir)
            target_killed = 0
            target_survived = 0
            target_errors = 0
            mod_survivors = []

            print(f"Generated {len(mutants)} mutations for {target['name']}.")

            for idx, mut_cmd in enumerate(mutants):
                mut_v = os.path.join(tmpdir, f"{target['name']}_mut_{idx}.v")
                sim_build = os.path.join(tmpdir, f"sim_{target['name']}_{idx}")

                ok = apply_mutation(target, mut_cmd, mut_v, tmpdir, idx)
                if not ok:
                    target_errors += 1
                    continue

                killed, stdout, stderr = test_mutant(target, mut_v, sim_build)
                if killed:
                    target_killed += 1
                    status_str = "KILLED"
                else:
                    target_survived += 1
                    status_str = "SURVIVED"
                    survivor_info = {
                        "module": target["name"],
                        "index": idx,
                        "command": mut_cmd,
                        "file": os.path.join(args.survivor_dir, f"{target['name']}_mut_{idx}.v"),
                    }
                    shutil.copyfile(mut_v, survivor_info["file"])
                    mod_survivors.append(survivor_info)
                    all_survivors.append(survivor_info)

                # Progress printing
                print(f"  [{target['name']} {idx+1:02d}/{len(mutants):02d}] {status_str}: {mut_cmd[:65]}...")

            t_mod_end = time.time()
            valid_mutants = target_killed + target_survived
            score = (target_killed / valid_mutants * 100.0) if valid_mutants > 0 else 0.0

            results[target["name"]] = {
                "generated": len(mutants),
                "valid": valid_mutants,
                "killed": target_killed,
                "survived": target_survived,
                "score": score,
                "time": t_mod_end - t_mod_start,
                "survivors": mod_survivors,
            }

            total_generated += len(mutants)
            total_killed += target_killed
            total_survived += target_survived
            print(f"Module {target['name']} Complete: {target_killed}/{valid_mutants} killed ({score:.1f}%) in {t_mod_end - t_mod_start:.1f}s")

    t_total = time.time() - t_start
    total_valid = total_killed + total_survived
    overall_score = (total_killed / total_valid * 100.0) if total_valid > 0 else 0.0

    # Format summary log
    summary_text = []
    summary_text.append("================================================================================")
    summary_text.append("AMBA-Fabric Mutation Testing Summary Report")
    summary_text.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    summary_text.append(f"Execution Time: {t_total:.2f} seconds")
    summary_text.append(f"RNG Seed: {args.seed}")
    summary_text.append("================================================================================")
    summary_text.append(f"{'Module':<18} | {'Generated':<10} | {'Valid':<8} | {'Killed':<8} | {'Survived':<8} | {'Score (%)':<10}")
    summary_text.append("-" * 75)
    for mod_name, res in results.items():
        summary_text.append(f"{mod_name:<18} | {res['generated']:<10} | {res['valid']:<8} | {res['killed']:<8} | {res['survived']:<8} | {res['score']:>8.2f}%")
    summary_text.append("=" * 75)
    summary_text.append(f"{'TOTAL / OVERALL':<18} | {total_generated:<10} | {total_valid:<8} | {total_killed:<8} | {total_survived:<8} | {overall_score:>8.2f}%")
    summary_text.append("================================================================================")
    summary_text.append(f"\nTotal Survivors: {len(all_survivors)}")
    for s in all_survivors:
        summary_text.append(f"  - [{s['module']} #{s['index']}]: {s['command']}")
        summary_text.append(f"    Saved RTL: {s['file']}")

    summary_str = "\n".join(summary_text)
    print("\n" + summary_str)

    with open(args.output, "w") as f:
        f.write(summary_str + "\n")
    print(f"\nReport written to {args.output}")


if __name__ == "__main__":
    main()
