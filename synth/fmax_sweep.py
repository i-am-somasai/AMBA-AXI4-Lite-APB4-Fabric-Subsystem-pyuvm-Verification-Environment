#!/usr/bin/env python3
"""
synth/fmax_sweep.py
Automated OpenSTA Frequency Sweep and Timing Analysis for AMBA-Fabric Top
Spec Section 13.3 & 13.4

All reported WNS, TNS, Fmax, unconstrained endpoints, fanout, slew, and critical
paths are parsed dynamically from OpenSTA stdout (zero hardcoded constants).
"""

import os
import re
import subprocess
import sys
import tempfile

PROJ_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NETLIST_REL = "synth/results/amba_fabric_netlist.v"
SDC_REL = "synth/amba_fabric.sdc"
LOG_OUT_REL = "synth/results/fmax_sweep.log"


def resolve_liberty_rel():
    """Return workspace-relative liberty symlink if present, else SKY130_LIB."""
    local_link = os.path.join(PROJ_DIR, "build", "sky130_tt.lib")
    if os.path.exists(local_link):
        return "build/sky130_tt.lib"
    env_lib = os.environ.get("SKY130_LIB", "")
    if env_lib and os.path.exists(env_lib):
        return env_lib
    default_lib = os.path.expanduser(
        "~/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/"
        "sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
    )
    if os.path.exists(default_lib):
        return default_lib
    raise FileNotFoundError("SKY130 liberty file not found; set SKY130_LIB or source scripts/env.sh")


def _common_setup_tcl(lib_path):
    return (
        'proc require_non_empty {desc objs} {\n'
        '    if {[llength $objs] == 0} {\n'
        '        puts stderr "ERROR: Constraint query matched nothing: $desc"\n'
        '        exit 1\n'
        '    }\n'
        '    return $objs\n'
        '}\n'
        f'read_liberty "{lib_path}"\n'
        f'read_verilog "{NETLIST_REL}"\n'
        'link_design amba_fabric_top\n'
        f'read_sdc "{SDC_REL}"\n'
        'require_non_empty "get_ports clk_sys"  [get_ports clk_sys]\n'
        'require_non_empty "get_ports clk_slow" [get_ports clk_slow]\n'
        'require_non_empty "get_ports rst_n"    [get_ports rst_n]\n'
        'require_non_empty "all_inputs -no_clocks" [all_inputs -no_clocks]\n'
        'require_non_empty "all_outputs"        [all_outputs]\n'
        'set rst_drv_cells {}\n'
        'foreach n {u_rst_sync_sys.sync_q1 rst_sys_n u_rst_sync_slow.sync_q1 rst_slow_n} {\n'
        '    set no [require_non_empty "get_nets $n" [get_nets $n]]\n'
        '    set po [require_non_empty "driver pin $n" [get_pins -of_objects $no -filter "direction == output"]]\n'
        '    set co [require_non_empty "driver cell $n" [get_cells -of_objects $po]]\n'
        '    lappend rst_drv_cells $co\n'
        '}\n'
    )


def run_sta_script(tcl_body):
    """Execute an OpenSTA Tcl script inside PROJ_DIR and fail on non-zero exit."""
    with tempfile.NamedTemporaryFile(
        "w", suffix=".tcl", dir=os.path.join(PROJ_DIR, "build", "tmp"), delete=False
    ) as f:
        tcl_path = f.name
        f.write(tcl_body)
    try:
        res = subprocess.run(
            ["sta", "-exit", tcl_path],
            cwd=PROJ_DIR,
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            raise RuntimeError(
                f"OpenSTA failed (rc={res.returncode}):\n{res.stderr}\n{res.stdout}"
            )
        return res.stdout
    finally:
        if os.path.exists(tcl_path):
            os.remove(tcl_path)


def parse_wns_tns(sta_stdout):
    wns = None
    tns = None
    for line in sta_stdout.splitlines():
        s = line.strip()
        if s.startswith("wns "):
            wns = float(s.split()[1])
        elif s.startswith("tns "):
            tns = float(s.split()[1])
    if wns is None or tns is None:
        raise RuntimeError(f"Failed to parse WNS/TNS from OpenSTA output:\n{sta_stdout}")
    return wns, tns


def parse_first_path_block(section_text):
    """Parse Startpoint, Endpoint, Path Group, Type, Arrival, Required, Slack, and peak Fanout/Cap/Slew."""
    start_m = re.search(r"Startpoint:\s+(.+)", section_text)
    end_m = re.search(r"Endpoint:\s+(.+)", section_text)
    grp_m = re.search(r"Path Group:\s+(\S+)", section_text)
    typ_m = re.search(r"Path Type:\s+(\S+)", section_text)
    arr_m = re.search(r"([+-]?\d+\.\d+)\s+data arrival time", section_text)
    req_m = re.search(r"([+-]?\d+\.\d+)\s+data required time", section_text)
    slk_m = re.search(r"([+-]?\d+\.\d+)\s+slack\s+\((MET|VIOLATED)\)", section_text)

    max_fanout = 0
    max_cap = 0.0
    max_slew = 0.0
    max_net = ""
    last_row = None
    for line in section_text.splitlines():
        row_m = re.match(
            r"^\s*(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+([+-]?\d+\.\d+)\s+([+-]?\d+\.\d+)\s+[\^v]\s+(\S+)",
            line,
        )
        if row_m:
            fo = int(row_m.group(1))
            cap = float(row_m.group(2))
            slew = float(row_m.group(3))
            last_row = (fo, cap, slew, row_m.group(6))
            if fo > max_fanout or (fo == max_fanout and slew > max_slew):
                max_fanout = fo
                max_cap = cap
                max_slew = slew
                max_net = row_m.group(6)
        elif last_row and "(net)" in line and max_net == last_row[3]:
            net_m = re.search(r"(\S+)\s+\(net\)", line)
            if net_m:
                max_net = net_m.group(1)

    return {
        "startpoint": start_m.group(1).strip() if start_m else "unknown",
        "endpoint": end_m.group(1).strip() if end_m else "unknown",
        "group": grp_m.group(1).strip() if grp_m else "unknown",
        "type": typ_m.group(1).strip() if typ_m else "unknown",
        "arrival": float(arr_m.group(1)) if arr_m else None,
        "required": float(req_m.group(1)) if req_m else None,
        "slack": float(slk_m.group(1)) if slk_m else None,
        "status": slk_m.group(2) if slk_m else "UNKNOWN",
        "max_fanout": max_fanout,
        "max_cap": max_cap,
        "max_slew": max_slew,
        "bottleneck_pin_or_net": max_net,
    }


def eval_period(lib_path, period, isolate_rst_q=False):
    tcl = [_common_setup_tcl(lib_path)]
    if isolate_rst_q:
        tcl.append('foreach n {rst_sys_n rst_slow_n} {\n')
        tcl.append('    set no [get_nets $n]\n')
        tcl.append('    set co [get_cells -of_objects [get_pins -of_objects $no -filter "direction == output"]]\n')
        tcl.append('    set_false_path -from $co\n')
        tcl.append('}\n')
    tcl.append(f'create_clock -name clk_sys -period {period:.3f} [get_ports clk_sys]\n')
    tcl.append('report_tns\n')
    tcl.append('report_wns\n')
    tcl.append('exit\n')
    out = run_sta_script("".join(tcl))
    wns, tns = parse_wns_tns(out)
    return wns, tns


def get_detailed_target_info(lib_path):
    """Run 10.0 ns detail report covering check_setup, full path, clk_sys, clk_slow, and isolated datapath."""
    tcl = [
        _common_setup_tcl(lib_path),
        'puts "===SECTION:CHECK_SETUP==="\n',
        'check_setup -verbose\n',
        'puts "===SECTION:FULL_WORST==="\n',
        'report_checks -path_delay max -fields {capacitance slew fanout input_pin net} -group_count 1\n',
        'puts "===SECTION:CLK_SYS_WORST==="\n',
        'report_checks -path_group clk_sys -path_delay max -fields {capacitance slew fanout input_pin net} -group_count 1\n',
        'puts "===SECTION:CLK_SLOW_WORST==="\n',
        'report_checks -path_group clk_slow -path_delay max -fields {capacitance slew fanout input_pin net} -group_count 1\n',
        'puts "===SECTION:MIN_HOLD==="\n',
        'report_checks -path_delay min -fields {capacitance slew fanout input_pin net} -group_count 1\n',
        'foreach n {rst_sys_n rst_slow_n} {\n',
        '    set co [get_cells -of_objects [get_pins -of_objects [get_nets $n] -filter "direction == output"]]\n',
        '    set_false_path -from $co\n',
        '}\n',
        'puts "===SECTION:DATAPATH_WNS_TNS==="\n',
        'report_tns\n',
        'report_wns\n',
        'puts "===SECTION:DATAPATH_WORST==="\n',
        'report_checks -path_group clk_sys -path_delay max -fields {capacitance slew fanout input_pin net} -group_count 1\n',
        'puts "===SECTION:REG2REG_WORST==="\n',
        'report_checks -from [all_registers] -to [all_registers] -path_group clk_sys -path_delay max -fields {capacitance slew fanout input_pin net} -group_count 1\n',
        'puts "===SECTION:END==="\n',
        'exit\n',
    ]
    out = run_sta_script("".join(tcl))
    sections = {}
    cur = None
    for line in out.splitlines():
        if line.startswith("===SECTION:") and line.endswith("==="):
            cur = line[len("===SECTION:"):-3]
            sections[cur] = []
        elif cur is not None:
            sections[cur].append(line)
    return {k: "\n".join(v) for k, v in sections.items()}


def parse_sweep_summary(periods, results):
    met = [r for r in results if r[4] == "MET"]
    if not met:
        return None, None
    best = min(met, key=lambda x: x[0])
    return best[0], best[1]


def main():
    os.makedirs(os.path.join(PROJ_DIR, "synth", "results"), exist_ok=True)
    netlist_abs = os.path.join(PROJ_DIR, NETLIST_REL)
    if not os.path.exists(netlist_abs):
        print(f"ERROR: Missing netlist {NETLIST_REL}; run 'make synth' first.", file=sys.stderr)
        sys.exit(1)

    lib_path = resolve_liberty_rel()
    log_out = os.path.join(PROJ_DIR, LOG_OUT_REL)

    print("================================================================================")
    print("AMBA-Fabric Top-Level STA and Fmax Sweep (SKY130 HD)")
    print(f"Library: {os.path.basename(lib_path)}")
    print(f"Netlist: {NETLIST_REL}")
    print("================================================================================")

    sec = get_detailed_target_info(lib_path)
    full_worst = parse_first_path_block(sec["FULL_WORST"])
    clksys_worst = parse_first_path_block(sec["CLK_SYS_WORST"])
    clkslow_worst = parse_first_path_block(sec["CLK_SLOW_WORST"])
    hold_worst = parse_first_path_block(sec["MIN_HOLD"])
    dp_wns, dp_tns = parse_wns_tns(sec["DATAPATH_WNS_TNS"])
    dp_worst = parse_first_path_block(sec["DATAPATH_WORST"])
    r2r_worst = parse_first_path_block(sec["REG2REG_WORST"])

    unconst_lines = [l.strip() for l in sec["CHECK_SETUP"].splitlines() if l.strip().startswith("_") or "/D" in l or "/RESET_B" in l]
    unconst_m = re.search(r"There are (\d+) unconstrained endpoints\.", sec["CHECK_SETUP"])
    unconst_cnt = int(unconst_m.group(1)) if unconst_m else len(unconst_lines)

    # 1. Full E2-compliant sweep (recovery/removal on rst_sys_n/rst_slow_n remains TIMED)
    print("\n--- Full Design Fmax Sweep (Recovery/Removal Timed, Pre-Layout Unbuffered Reset) ---")
    full_periods = [35.0, 32.0, 30.0, 29.0, 28.75, 28.60, 28.50, 26.0, 24.0, 20.0, 16.0, 14.0, 12.0, 10.0]
    full_results = []
    for p in full_periods:
        wns, tns = eval_period(lib_path, p, isolate_rst_q=False)
        freq = 1000.0 / p
        status = "MET" if wns >= 0.0 else "VIOLATED"
        full_results.append((p, freq, wns, tns, status))
        print(f"  Period: {p:6.2f} ns | Freq: {freq:6.2f} MHz | WNS: {wns:7.2f} ns | TNS: {tns:10.2f} ns | {status}")

    fmax_full_p, fmax_full_mhz = parse_sweep_summary(full_periods, full_results)
    target_full = [r for r in full_results if abs(r[0] - 10.0) < 1e-6][0]

    # 2. Secondary reference sweep isolating rst_sync Q outputs to inspect core synchronous datapath + I/O
    print("\n--- Core Datapath + I/O Reference Sweep (rst_sync Q isolated in STA only) ---")
    dp_periods = [20.0, 18.0, 16.5, 16.0, 15.9, 15.8, 15.0, 14.0, 13.0, 12.0, 10.0]
    dp_results = []
    for p in dp_periods:
        wns, tns = eval_period(lib_path, p, isolate_rst_q=True)
        freq = 1000.0 / p
        status = "MET" if wns >= 0.0 else "VIOLATED"
        dp_results.append((p, freq, wns, tns, status))
        print(f"  Period: {p:6.2f} ns | Freq: {freq:6.2f} MHz | WNS: {wns:7.2f} ns | TNS: {tns:10.2f} ns | {status}")

    fmax_dp_p, fmax_dp_mhz = parse_sweep_summary(dp_periods, dp_results)

    report = [
        "================================================================================",
        "OpenSTA Timing Analysis and Fmax Sweep Report (Dynamic Parsed Output)",
        f"Standard Cell Library: {os.path.basename(lib_path)}",
        "Target Clock: clk_sys @ 100.00 MHz (10.00 ns), clk_slow @ 41.67 MHz (24.00 ns)",
        "Constraint Scope: false_path ONLY on async port rst_n -> rst_sync flops (recovery/removal TIMED)",
        "================================================================================",
        "",
        "1. Target Timing at 100.00 MHz (clk_sys = 10.00 ns, Full Pre-Layout Netlist)",
        f"   - Overall WNS: {target_full[2]:.2f} ns ({full_worst['group']} / {full_worst['type']})",
        f"   - Overall TNS: {target_full[3]:.2f} ns",
        f"   - Overall Status: {target_full[4]}",
        f"   - clk_sys Group Setup Slack (at 10.00 ns): {clksys_worst['slack']:.2f} ns",
        f"   - clk_slow Group Setup Slack (at 24.00 ns): {clkslow_worst['slack']:.2f} ns ({clkslow_worst['status']})",
        f"   - Hold Worst Slack (min): {hold_worst['slack']:.2f} ns ({hold_worst['status']})",
        f"   - Unconstrained Endpoints (check_setup): {unconst_cnt} ({', '.join(unconst_lines[:10])})",
        "",
        "2. Full-Design Frequency Sweep (Recovery/Removal Timed, Pre-Layout Unbuffered Reset Tree):",
        f"{'Period (ns)':<12} | {'Freq (MHz)':<12} | {'WNS (ns)':<10} | {'TNS (ns)':<12} | {'Status':<10}",
        "-" * 68,
    ]
    for p, freq, wns, tns, status in full_results:
        report.append(f"{p:<12.2f} | {freq:<12.2f} | {wns:<10.2f} | {tns:<12.2f} | {status:<10}")
    report.append("-" * 68)
    if fmax_full_p is not None:
        report.append(f"   - Achieved Full-Netlist Fmax: {fmax_full_mhz:.2f} MHz (Period = {fmax_full_p:.2f} ns)")
    else:
        report.append(f"   - Achieved Full-Netlist Fmax: < {1000.0 / full_periods[0]:.2f} MHz")

    report.extend([
        "",
        "3. Datapath + I/O Reference Sweep (rst_sync Q isolated in STA only, Pre-CTS Estimate):",
        f"   - clk_sys Datapath+IO WNS @ 10.00 ns: {dp_wns:.2f} ns, TNS: {dp_tns:.2f} ns",
        f"{'Period (ns)':<12} | {'Freq (MHz)':<12} | {'WNS (ns)':<10} | {'TNS (ns)':<12} | {'Status':<10}",
        "-" * 68,
    ])
    for p, freq, wns, tns, status in dp_results:
        report.append(f"{p:<12.2f} | {freq:<12.2f} | {wns:<10.2f} | {tns:<12.2f} | {status:<10}")
    report.append("-" * 68)
    if fmax_dp_p is not None:
        report.append(f"   - Achieved Core+IO Reference Fmax (excluding unbuffered reset net): {fmax_dp_mhz:.2f} MHz (Period = {fmax_dp_p:.2f} ns)")
    else:
        report.append(f"   - Achieved Core+IO Reference Fmax: < {1000.0 / dp_periods[0]:.2f} MHz")

    report.extend([
        "",
        "4. Dynamically Parsed Critical Paths at 10.00 ns:",
        "   [Full Netlist Worst Path - Pre-Layout Unbuffered Reset Limitation]",
        f"   - Startpoint: {full_worst['startpoint']}",
        f"   - Endpoint:   {full_worst['endpoint']}",
        f"   - Group/Type: {full_worst['group']} / {full_worst['type']}",
        f"   - Arrival / Required / Slack: {full_worst['arrival']:.2f} ns / {full_worst['required']:.2f} ns / {full_worst['slack']:.2f} ns ({full_worst['status']})",
        f"   - Peak Net:   {full_worst['bottleneck_pin_or_net']} (fanout={full_worst['max_fanout']}, cap={full_worst['max_cap']:.2f} pF, slew={full_worst['max_slew']:.2f} ns)",
        "",
        "   [Datapath + I/O Critical Path (rst_sync Q isolated)]",
        f"   - Startpoint: {dp_worst['startpoint']}",
        f"   - Endpoint:   {dp_worst['endpoint']}",
        f"   - Arrival / Required / Slack: {dp_worst['arrival']:.2f} ns / {dp_worst['required']:.2f} ns / {dp_worst['slack']:.2f} ns ({dp_worst['status']})",
        f"   - Peak Net:   {dp_worst['bottleneck_pin_or_net']} (fanout={dp_worst['max_fanout']}, cap={dp_worst['max_cap']:.2f} pF, slew={dp_worst['max_slew']:.2f} ns)",
        "",
        "   [Pure Register-to-Register Critical Path (clk_sys, excluding I/O and rst_sync)]",
        f"   - Startpoint: {r2r_worst['startpoint']}",
        f"   - Endpoint:   {r2r_worst['endpoint']}",
        f"   - Arrival / Required / Slack: {r2r_worst['arrival']:.2f} ns / {r2r_worst['required']:.2f} ns / {r2r_worst['slack']:.2f} ns ({r2r_worst['status']})",
        f"   - Peak Net:   {r2r_worst['bottleneck_pin_or_net']} (fanout={r2r_worst['max_fanout']}, cap={r2r_worst['max_cap']:.2f} pF, slew={r2r_worst['max_slew']:.2f} ns)",
    ])

    report_str = "\n".join(report)
    print("\n" + report_str)
    with open(log_out, "w") as f:
        f.write(report_str + "\n")
    print(f"\nSweep log written to {LOG_OUT_REL}")


if __name__ == "__main__":
    main()
