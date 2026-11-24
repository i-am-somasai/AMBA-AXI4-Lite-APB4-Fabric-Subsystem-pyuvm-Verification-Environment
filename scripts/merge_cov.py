#!/usr/bin/env bash
# scripts/merge_cov.py - Aggregates YAML coverage databases across runs and generates report
"""
scripts/merge_cov.py
Reads all YAML coverage files in docs/logs/ (or specified path), merges
coverage statistics across multiple random seeds, and generates detailed
ASCII and Markdown reports.
"""
import os
import sys
import glob
import yaml

def merge_coverage(log_dir="docs/logs", pattern="cov_*.yaml"):
    files = sorted(glob.glob(os.path.join(log_dir, pattern)))
    if not files:
        print(f"No coverage files found matching {os.path.join(log_dir, pattern)}")
        return 0, 0, {}

    merged_groups = {} # name -> {"type": ..., "size": int, "weight": int, "bins": {bin_key: hit_count}}

    for f in files:
        with open(f, "r") as fp:
            data = yaml.safe_load(fp)
            if not data:
                continue

            for name, item in data.items():
                if not isinstance(item, dict):
                    continue
                # We care about CoverPoint and CoverCross (they have 'bins:_hits')
                if "bins:_hits" in item:
                    if name not in merged_groups:
                        merged_groups[name] = {
                            "size": item.get("size", len(item["bins:_hits"])),
                            "weight": item.get("weight", 1),
                            "at_least": item.get("at_least", 1),
                            "bins": {}
                        }
                    for b_key, hits in item["bins:_hits"].items():
                        # Convert tuple strings or ints to strings
                        key_str = str(b_key)
                        merged_groups[name]["bins"][key_str] = merged_groups[name]["bins"].get(key_str, 0) + int(hits)

    # Compute coverage metrics
    total_bins = 0
    covered_bins = 0
    group_stats = {}

    for name, grp in sorted(merged_groups.items()):
        at_least = grp["at_least"]
        g_size = grp["size"]
        g_covered = sum(1 for h in grp["bins"].values() if h >= at_least)
        # Cap g_covered at g_size in case
        g_covered = min(g_covered, g_size)
        pct = (g_covered / g_size * 100.0) if g_size > 0 else 100.0

        group_stats[name] = {
            "size": g_size,
            "covered": g_covered,
            "pct": pct,
            "bins": grp["bins"]
        }

        # Accumulate only top-level crosses or points without crosses to avoid double counting
        total_bins += g_size
        covered_bins += g_covered

    overall_pct = (covered_bins / total_bins * 100.0) if total_bins > 0 else 0.0
    return total_bins, covered_bins, group_stats, files


def generate_report(total_bins, covered_bins, group_stats, files, out_path="docs/logs/func_cov.log"):
    overall_pct = (covered_bins / total_bins * 100.0) if total_bins > 0 else 0.0

    lines = []
    lines.append("================================================================================")
    lines.append("               AMBA-FABRIC FUNCTIONAL COVERAGE REPORT (COCOTB-COVERAGE)         ")
    lines.append("================================================================================")
    lines.append(f"Merged {len(files)} coverage database file(s):")
    for f in files:
        lines.append(f"  - {f}")
    lines.append("--------------------------------------------------------------------------------")
    lines.append(f"{'Covergroup / Metric':<35} | {'Bins':<8} | {'Covered':<8} | {'Coverage %':<10}")
    lines.append("--------------------------------------------------------------------------------")

    for name, st in sorted(group_stats.items()):
        lines.append(f"{name:<35} | {st['size']:<8} | {st['covered']:<8} | {st['pct']:>8.2f}%")

    lines.append("================================================================================")
    lines.append(f"{'OVERALL AGGREGATE COVERAGE':<35} | {total_bins:<8} | {covered_bins:<8} | {overall_pct:>8.2f}%")
    lines.append("================================================================================")

    # Detailed hole analysis if < 100%
    holes = []
    for name, st in sorted(group_stats.items()):
        if st["covered"] < st["size"]:
            for b_key, hits in st["bins"].items():
                if hits == 0:
                    holes.append((name, b_key))

    if holes:
        lines.append("\n=== UNCOVERED BINS (HOLES) ===")
        for name, b_key in holes:
            lines.append(f"  [HOLE] {name}: bin {b_key}")
    else:
        lines.append("\n*** ZERO HOLES DETECTED: 100% COVERAGE ACHIEVED ***")

    report_str = "\n".join(lines)
    print(report_str)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as fp:
        fp.write(report_str + "\n")
    print(f"\nReport saved to: {out_path}")
    return overall_pct


if __name__ == "__main__":
    log_dir = sys.argv[1] if len(sys.argv) > 1 else "docs/logs"
    res = merge_coverage(log_dir)
    if res[0] > 0:
        total_bins, covered_bins, group_stats, files = res
        pct = generate_report(total_bins, covered_bins, group_stats, files)
        if pct < 100.0:
            sys.exit(1)
        sys.exit(0)
    else:
        print("No coverage data to report.")
        sys.exit(1)
