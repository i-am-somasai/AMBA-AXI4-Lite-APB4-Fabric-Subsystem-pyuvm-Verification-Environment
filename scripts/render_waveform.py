#!/usr/bin/env python3
"""scripts/render_waveform.py - Parse VCD and render digital timing diagram."""

import sys
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def parse_vcd(vcd_path, tracked_signals):
    """Simple VCD parser for specified 1-bit or multi-bit signals."""
    var_map = {} # symbol -> signal_name
    sig_symbols = {} # signal_name -> symbol
    times = []
    sig_history = {sig: [] for sig in tracked_signals}

    with open(vcd_path, "r") as f:
        in_header = True
        for line in f:
            line = line.strip()
            if not line:
                continue
            if in_header:
                if line.startswith("$var"):
                    parts = line.split()
                    # e.g.: $var wire 1 ! clk $end or $var wire 1 # m0_awvalid $end
                    if len(parts) >= 5:
                        sym = parts[3]
                        name = parts[4]
                        if name in tracked_signals:
                            var_map[sym] = name
                            sig_symbols[name] = sym
                elif line.startswith("$enddefinitions"):
                    in_header = False
                    cur_time = 0
                    cur_vals = {sig: 0 for sig in tracked_signals}
            else:
                if line.startswith("#"):
                    t = int(line[1:])
                    # Record previous values for all signals at this new time point
                    cur_time = t
                elif line.startswith("$"):
                    continue
                else:
                    # Value change
                    if line.startswith("b") or line.startswith("B"):
                        # Multi-bit e.g. b1010 !
                        parts = line.split()
                        val_str = parts[0][1:]
                        sym = parts[1]
                        if sym in var_map:
                            sig = var_map[sym]
                            try:
                                val = int(val_str, 2)
                            except ValueError:
                                val = 0
                            cur_vals[sig] = val
                            sig_history[sig].append((cur_time, val))
                    else:
                        # 1-bit e.g. 1! or 0!
                        val_char = line[0]
                        sym = line[1:]
                        if sym in var_map:
                            sig = var_map[sym]
                            val = 1 if val_char == '1' else 0
                            cur_vals[sig].append((cur_time, val)) if isinstance(cur_vals[sig], list) else None
                            sig_history[sig].append((cur_time, val))

    return sig_history

def render_plot(sig_history, out_path, t_min=0, t_max=160000): # picoseconds: 160 ns = 160000 ps
    signals_to_plot = [
        ("CLK", "clk", "#444444"),
        ("M0 AWVALID", "m0_awvalid", "#1f77b4"),
        ("M0 AWREADY (Granted first)", "m0_awready", "#1f77b4"),
        ("M0 WVALID", "m0_wvalid", "#1f77b4"),
        ("M0 WREADY", "m0_wready", "#1f77b4"),
        ("M0 BVALID", "m0_bvalid", "#1f77b4"),
        ("M1 AWVALID", "m1_awvalid", "#d62728"),
        ("M1 AWREADY (Stalled until M0 completes)", "m1_awready", "#d62728"),
        ("M1 WVALID", "m1_wvalid", "#d62728"),
        ("M1 WREADY", "m1_wready", "#d62728"),
        ("M1 BVALID", "m1_bvalid", "#d62728"),
        ("S1 RAM AWVALID", "s1_awvalid", "#2ca02c"),
        ("S1 RAM WVALID", "s1_wvalid", "#2ca02c"),
        ("S1 RAM BVALID", "s1_bvalid", "#2ca02c"),
    ]

    fig, axes = plt.subplots(len(signals_to_plot), 1, figsize=(14, 10), sharex=True)
    plt.subplots_adjust(hspace=0.25, top=0.93, bottom=0.08, left=0.22, right=0.96)

    fig.suptitle("AXI4-Lite Crossbar Contention Serialization Waveform (XB-05)\n"
                 "M0 and M1 Contending Simultaneously for Slave 1 (RAM at 0x5000_0000)",
                 fontsize=14, fontweight="bold")

    # Time grid in nanoseconds (1 ns = 1000 ps)
    t_grid = np.linspace(t_min, t_max, 3200) # 0.05 ns steps

    for idx, (label, sig_name, color) in enumerate(signals_to_plot):
        ax = axes[idx]
        history = sig_history.get(sig_name, [])
        # Sample signal at t_grid
        vals = []
        hist_idx = 0
        cur_v = 0
        for t in t_grid:
            while hist_idx < len(history) and history[hist_idx][0] <= t:
                cur_v = history[hist_idx][1]
                hist_idx += 1
            vals.append(cur_v)

        t_ns = t_grid / 1000.0 # convert to ns
        ax.step(t_ns, vals, where='post', color=color, linewidth=1.8)
        ax.set_ylim(-0.2, 1.3)
        ax.set_yticks([0, 1])
        ax.set_yticklabels(['0', '1'], fontsize=9)
        ax.set_ylabel(label, rotation=0, ha='right', va='center', fontsize=10, fontweight='semibold')
        ax.grid(True, which='both', linestyle='--', alpha=0.5)

        # Highlight arbitration phases
        ax.axvspan(20, 50, color='#e0f2fe', alpha=0.3)  # M0 transaction
        ax.axvspan(50, 90, color='#fef2f2', alpha=0.3)  # M1 transaction

    axes[-1].set_xlabel("Simulation Time (ns)", fontsize=11, fontweight="bold")

    # Add phase annotations on top plot
    axes[0].text(35, 1.6, "Phase 1: M0 Granted (M1 Stalled)",
                 ha='center', va='bottom', fontsize=10, fontweight='bold', color='#0369a1',
                 bbox=dict(boxstyle="round,pad=0.3", fc="#e0f2fe", ec="#0284c7", lw=1))
    axes[0].text(70, 1.6, "Phase 2: M1 Granted after M0 Completes",
                 ha='center', va='bottom', fontsize=10, fontweight='bold', color='#b91c1c',
                 bbox=dict(boxstyle="round,pad=0.3", fc="#fef2f2", ec="#ef4444", lw=1))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=180)
    plt.close()
    print(f"Saved contention waveform to: {out_path}")

def main():
    vcd_path = sys.argv[1] if len(sys.argv) > 1 else "tb/block/dump.vcd"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "docs/img/contention.png"

    tracked = [
        "clk", "rst_n",
        "m0_awvalid", "m0_awready", "m0_wvalid", "m0_wready", "m0_bvalid", "m0_bready",
        "m1_awvalid", "m1_awready", "m1_wvalid", "m1_wready", "m1_bvalid", "m1_bready",
        "s1_awvalid", "s1_awready", "s1_wvalid", "s1_wready", "s1_bvalid", "s1_bready"
    ]

    sig_history = parse_vcd(vcd_path, tracked)
    render_plot(sig_history, out_path, t_min=0, t_max=160000)

if __name__ == "__main__":
    main()
