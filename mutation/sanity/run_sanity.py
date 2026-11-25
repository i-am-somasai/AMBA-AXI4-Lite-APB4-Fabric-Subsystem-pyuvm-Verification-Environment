#!/usr/bin/env python3
"""
mutation/sanity/run_sanity.py
Permanent sanity gate (SMUT-01..SMUT-17).
Every mutant must compile/lint cleanly with iverilog/verilator (otherwise marked
INVALID, never KILLED) and be KILLED by its target verification test.
All temporary builds and results stay strictly inside BUILD_DIR/sanity.
"""

import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

PROJ_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
BUILD_DIR = os.path.abspath(os.environ.get("BUILD_DIR", os.path.join(PROJ_DIR, "build")))
SANITY_DIR = os.path.join(BUILD_DIR, "sanity")

ALL_TOP_RTL = [
    "rtl/common/rst_sync.v",
    "rtl/common/sync_fifo.v",
    "rtl/common/async_fifo.v",
    "rtl/common/rr_arbiter.v",
    "rtl/axil/axil_default_slave.v",
    "rtl/axil/axil_decoder.v",
    "rtl/axil/axil_xbar.v",
    "rtl/axil/axil_ram.v",
    "rtl/axil/axil_csr.v",
    "rtl/apb/axil2apb_bridge.v",
    "rtl/apb/apb_decoder.v",
    "rtl/apb/apb_uart.v",
    "rtl/apb/apb_timer.v",
    "rtl/apb/apb_gpio.v",
    "rtl/cdc/slow_regs.v",
    "rtl/cdc/axil_cdc_bridge.v",
    "rtl/amba_fabric_top.v",
]

SANITY_MUTANTS = [
    {
        "id": "SMUT-01",
        "desc": "Inject arbiter priority swap in rr_arbiter.v",
        "file": "rtl/common/rr_arbiter.v",
        "target": "next_grant[(i + j) % NUM_REQS] = 1'b1;",
        "replacement": "next_grant[i] = 1'b1; // SMUT-01",
        "make_dir": "tb/unit",
        "toplevel": "rr_arbiter",
        "module": "test_rr_arbiter",
        "testcase": "",
        "sources": ["rtl/common/rr_arbiter.v"],
    },
    {
        "id": "SMUT-02",
        "desc": "Inject dropped WSTRB[2] bit in axil_ram.v",
        "file": "rtl/axil/axil_ram.v",
        "target": "if (write_strb_active[2]) mem[write_ram_addr][23:16] <= write_data_active[23:16];",
        "replacement": "if (1'b0 && write_strb_active[2]) mem[write_ram_addr][23:16] <= write_data_active[23:16]; // SMUT-02",
        "make_dir": "tb/unit",
        "toplevel": "axil_ram",
        "module": "test_axil_ram",
        "testcase": "",
        "sources": ["rtl/axil/axil_ram.v"],
    },
    {
        "id": "SMUT-03",
        "desc": "Inject Gray-pointer encoding error in async_fifo.v",
        "file": "rtl/common/async_fifo.v",
        "target": "wire [PTR_WIDTH-1:0] wgray_next = (wbin_next >> 1) ^ wbin_next;",
        "replacement": "wire [PTR_WIDTH-1:0] wgray_next = wbin_next; // SMUT-03",
        "make_dir": "tb/unit",
        "toplevel": "async_fifo",
        "module": "test_async_fifo",
        "testcase": "",
        "sources": ["rtl/common/async_fifo.v"],
    },
    {
        "id": "SMUT-04",
        "desc": "Inject PSLVERR mapped to OKAY in axil2apb_bridge.v",
        "file": "rtl/apb/axil2apb_bridge.v",
        "target": "s_axil_bresp  <= m_apb_pslverr ? 2'b10 : 2'b00;",
        "replacement": "s_axil_bresp  <= (1'b0 && m_apb_pslverr) ? 2'b10 : 2'b00; // SMUT-04",
        "make_dir": "tb/block",
        "toplevel": "axil2apb_bridge",
        "module": "test_axil2apb_bridge",
        "testcase": "test_br03_pslverr_propagation",
        "sources": ["rtl/apb/axil2apb_bridge.v"],
    },
    {
        "id": "SMUT-05",
        "desc": "Inject timer off-by-one LOAD period in apb_timer.v",
        "file": "rtl/apb/apb_timer.v",
        "target": "if (pwdata[0] && !reg_ctrl[0]) begin\n                            reg_value <= reg_load;",
        "replacement": "if (pwdata[0] && !reg_ctrl[0]) begin\n                            reg_value <= reg_load - 32'd1; // SMUT-05",
        "make_dir": "tb/block",
        "toplevel": "apb_timer",
        "module": "test_apb_timer",
        "testcase": "",
        "sources": ["rtl/apb/apb_timer.v"],
    },
    {
        "id": "SMUT-06",
        "desc": "Inject DECERR changed to SLVERR in axil_default_slave.v",
        "file": "rtl/axil/axil_default_slave.v",
        "target": "localparam [1:0] RESP_DECERR = 2'b11;",
        "replacement": "localparam [1:0] RESP_DECERR = 2'b10; // SMUT-06",
        "make_dir": "tb/unit",
        "toplevel": "axil_default_slave",
        "module": "test_axil_default_slave",
        "testcase": "",
        "sources": ["rtl/axil/axil_default_slave.v"],
    },
    {
        "id": "SMUT-07",
        "desc": "Inject APB PENABLE asserted one cycle early in axil2apb_bridge.v",
        "file": "rtl/apb/axil2apb_bridge.v",
        "target": "m_apb_psel    <= 1'b1;\n                    m_apb_penable <= 1'b0;",
        "replacement": "m_apb_psel    <= 1'b1;\n                    m_apb_penable <= 1'b1; // SMUT-07",
        "make_dir": "tb/block",
        "toplevel": "axil2apb_bridge",
        "module": "test_axil2apb_bridge",
        "testcase": "test_br01_single_rw_zero_wait",
        "sources": ["rtl/apb/axil2apb_bridge.v"],
    },
    {
        "id": "SMUT-08",
        "desc": "Inject FIFO full flag off-by-one in sync_fifo.v",
        "file": "rtl/common/sync_fifo.v",
        "target": "assign full  = (count == DEPTH_VAL);",
        "replacement": "assign full  = (count == (DEPTH_VAL - {{ADDR_WIDTH{1'b0}}, 1'b1})); // SMUT-08",
        "make_dir": "tb/unit",
        "toplevel": "sync_fifo",
        "module": "test_sync_fifo",
        "testcase": "",
        "sources": ["rtl/common/sync_fifo.v"],
    },
    {
        "id": "SMUT-09",
        "desc": "Inject m_apb_pprot forced to 3'b000 in axil2apb_bridge.v",
        "file": "rtl/apb/axil2apb_bridge.v",
        "target": "m_apb_pprot   <= reg_prot;",
        "replacement": "m_apb_pprot   <= (3'b000 & reg_prot); // SMUT-09",
        "make_dir": "tb/pyuvm",
        "toplevel": "amba_fabric_top",
        "module": "test_directed",
        "testcase": "test_xb14_prot_passthrough",
        "sources": ALL_TOP_RTL,
    },
    {
        "id": "SMUT-10",
        "desc": "Inject stuck write priority wr_prio[gt]<=0 in axil_xbar.v",
        "file": "rtl/axil/axil_xbar.v",
        "target": "wr_prio[gt]   <= ~active_wr_owner[gt]; // Rotate priority",
        "replacement": "wr_prio[gt]   <= (1'b0 & active_wr_owner[gt]); // SMUT-10",
        "make_dir": "tb/block",
        "toplevel": "tb_axil_xbar",
        "module": "test_axil_xbar",
        "testcase": "test_xb07_arbitration_fairness",
        "sources": [
            "rtl/axil/axil_decoder.v",
            "rtl/axil/axil_default_slave.v",
            "rtl/axil/axil_xbar.v",
            "tb/block/tb_axil_xbar.v",
        ],
    },
    {
        "id": "SMUT-11",
        "desc": "Inject CSR full-offset decode violation of Rule 6 in axil_csr.v",
        "file": "rtl/axil/axil_csr.v",
        "target": "wire [5:0] read_word = s_axil_araddr[7:2];",
        "replacement": "wire [5:0] read_word = (s_axil_araddr[1:0] == 2'b00) ? s_axil_araddr[7:2] : 6'h3F; // SMUT-11",
        "make_dir": "tb/pyuvm",
        "toplevel": "amba_fabric_top",
        "module": "test_directed",
        "testcase": "test_xb15_unaligned_address",
        "sources": ALL_TOP_RTL,
    },
    {
        "id": "SMUT-12",
        "desc": "Inject RX_OVF never set in apb_uart.v",
        "file": "rtl/apb/apb_uart.v",
        "target": "reg_rx_ovf <= 1'b1; // RX FIFO overflow",
        "replacement": "reg_rx_ovf <= 1'b0; // SMUT-12",
        "make_dir": "tb/block",
        "toplevel": "apb_uart",
        "module": "test_apb_uart",
        "testcase": "test_ua02_fifo_full_and_overflow_flags",
        "sources": ["rtl/common/sync_fifo.v", "rtl/apb/apb_uart.v"],
    },
    {
        "id": "SMUT-13",
        "desc": "Inject SCRATCH2 ignores WSTRB in axil_csr.v",
        "file": "rtl/axil/axil_csr.v",
        "target": "if (write_strb[0]) reg_scratch2[7:0]   <= write_data[7:0];\n                        if (write_strb[1]) reg_scratch2[15:8]  <= write_data[15:8];\n                        if (write_strb[2]) reg_scratch2[23:16] <= write_data[23:16];\n                        if (write_strb[3]) reg_scratch2[31:24] <= write_data[31:24];",
        "replacement": "if (|write_strb || !(|write_strb)) reg_scratch2 <= write_data; // SMUT-13 (ignores individual WSTRB lanes)",
        "make_dir": "tb/pyuvm",
        "toplevel": "amba_fabric_top",
        "module": "test_directed",
        "testcase": "test_sys_strobe_patterns",
        "sources": ALL_TOP_RTL,
    },
    {
        "id": "SMUT-14",
        "desc": "Inject xbar lock/pending not cleared by reset in axil_xbar.v",
        "file": "rtl/axil/axil_xbar.v",
        "target": "if (!rst_n) begin\n                    wr_locked[gt] <= 1'b0;\n                    wr_owner[gt]  <= 1'b0;\n                    aw_done[gt]   <= 1'b0;",
        "replacement": "if (!rst_n) begin\n                    if (!wr_locked[gt]) begin\n                        wr_locked[gt] <= 1'b0;\n                        wr_owner[gt]  <= 1'b0;\n                        aw_done[gt]   <= 1'b0;\n                    end // SMUT-14",
        "make_dir": "tb/pyuvm",
        "toplevel": "amba_fabric_top",
        "module": "test_directed",
        "testcase": "test_xb12_reset_recovery",
        "sources": ALL_TOP_RTL,
    },
    {
        "id": "SMUT-15",
        "desc": "Inject CDC bridge pending state not aborted/reset on rst_slow_n in axil_cdc_bridge.v",
        "file": "rtl/cdc/axil_cdc_bridge.v",
        "target": "if (slow_rst_aborted || !slow_rst_seen_n) begin\n                        // Abort slow-domain wait cleanly",
        "replacement": "if (1'b0 && (slow_rst_aborted || !slow_rst_seen_n)) begin // SMUT-15\n                        // Abort disabled",
        "make_dir": "tb/block",
        "toplevel": "axil_cdc_bridge",
        "module": "test_axil_cdc_bridge",
        "testcase": "test_cd03_reset_recovery",
        "sources": ["rtl/common/async_fifo.v", "rtl/cdc/slow_regs.v", "rtl/cdc/axil_cdc_bridge.v"],
    },
    {
        "id": "SMUT-16",
        "desc": "Inject bridge read/write arbitration stuck on write in axil2apb_bridge.v",
        "file": "rtl/apb/axil2apb_bridge.v",
        "target": "end else if (s_axil_arvalid) begin",
        "replacement": "end else if (1'b0 && s_axil_arvalid) begin // SMUT-16",
        "make_dir": "tb/block",
        "toplevel": "axil2apb_bridge",
        "module": "test_axil2apb_bridge",
        "testcase": "test_br05_back_to_back_mixed_rw",
        "sources": ["rtl/apb/axil2apb_bridge.v"],
    },
    {
        "id": "SMUT-17",
        "desc": "Reduce GPIO 2-FF input synchronizer to 1-FF in apb_gpio.v",
        "file": "rtl/apb/apb_gpio.v",
        "target": "sync_gpio_q2   <= sync_gpio_q1;",
        "replacement": "sync_gpio_q2   <= gpio_i | (sync_gpio_q1 & {GPIO_WIDTH{1'b0}}); // SMUT-17 (1-FF bypass)",
        "make_dir": "tb/block",
        "toplevel": "apb_gpio",
        "module": "test_apb_gpio",
        "testcase": "test_gp02_input_sync_latency",
        "sources": ["rtl/apb/apb_gpio.v"],
    },
]


def _extract_kill_reason(log_text, results_xml, mut):
    fallback_test = f"{mut['module']}.{mut['testcase'] or '*'}"
    tb_match = re.findall(r'File "([^"]+)", line (\d+), in (\S+)', log_text)
    loc_str = ""
    if tb_match:
        fpath, lineno, func = tb_match[-1]
        rel_path = fpath.replace(PROJ_DIR + "/", "")
        loc_str = f" ({rel_path}:{lineno} in {func})"

    if os.path.exists(results_xml):
        try:
            tree = ET.parse(results_xml)
            for tc in tree.getroot().iter("testcase"):
                fail = tc.find("failure")
                if fail is not None:
                    tc_name = f"{mut['module']}.{tc.attrib.get('name', '?')}"
                    msg = (fail.attrib.get("message") or fail.text or "").strip().splitlines()
                    line = msg[-1] if msg else "assertion failed"
                    if not loc_str:
                        f_m = re.findall(r'File "([^"]+)", line (\d+)', fail.text or "")
                        if f_m:
                            loc_str = f" ({f_m[-1][0].replace(PROJ_DIR + '/', '')}:{f_m[-1][1]})"
                    return f"{tc_name}{loc_str}: {line}"
        except Exception:
            pass
    for pat in (r"AssertionError:.*", r"TimeoutError:.*"):
        m = re.search(pat, log_text)
        if m:
            return f"{fallback_test}{loc_str}: {m.group(0).strip()}"
    return f"{fallback_test}{loc_str}: non-zero exit"


def run_one_mutant(mut):
    mid = mut["id"]
    work_dir = os.path.join(SANITY_DIR, mid)
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir, exist_ok=True)
    tmp_dir = os.path.join(BUILD_DIR, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    orig_path = os.path.join(PROJ_DIR, mut["file"])
    with open(orig_path, "r") as f:
        orig_src = f.read()

    if mut["target"] not in orig_src:
        return mid, "INVALID", f"Target snippet not found in {mut['file']}"

    mut_src = orig_src.replace(mut["target"], mut["replacement"], 1)
    mut_file = os.path.join(work_dir, os.path.basename(mut["file"]))
    with open(mut_file, "w") as f:
        f.write(mut_src)

    # Swap mutated source path into VERILOG_SOURCES
    sources = []
    for s in mut["sources"]:
        if s == mut["file"]:
            sources.append(mut_file)
        else:
            sources.append(os.path.join(PROJ_DIR, s))

    # 1. Compilation + Lint check (iverilog -g2012 + verilator --lint-only)
    # Any build or lint failure counts as INVALID, never KILLED.
    comp_vvp = os.path.join(work_dir, "compile_check.vvp")
    comp_cmd = ["iverilog", "-g2012", "-s", mut["toplevel"], "-o", comp_vvp] + sources
    comp_res = subprocess.run(comp_cmd, capture_output=True, text=True)
    if comp_res.returncode != 0:
        return mid, "INVALID", f"iverilog compile failed: {comp_res.stderr.strip()}"

    lint_cmd = [
        "verilator", "--lint-only", "-Wall", "-Wno-DECLFILENAME", "-Wno-MULTITOP",
        "--top-module", mut["toplevel"],
        f"-I{os.path.join(PROJ_DIR, 'rtl/common')}",
        f"-I{os.path.join(PROJ_DIR, 'rtl/axil')}",
        f"-I{os.path.join(PROJ_DIR, 'rtl/apb')}",
        f"-I{os.path.join(PROJ_DIR, 'rtl/cdc')}",
    ] + sources
    lint_res = subprocess.run(lint_cmd, capture_output=True, text=True)
    if lint_res.returncode != 0:
        return mid, "INVALID", f"verilator lint failed: {lint_res.stderr.strip()}"

    # 2. Run targeted verification test in isolated BUILD_DIR
    sim_build = os.path.join(work_dir, "sim_build")
    results_xml = os.path.join(work_dir, "results.xml")
    env = os.environ.copy()
    env["BUILD_DIR"] = BUILD_DIR
    env["TMPDIR"] = tmp_dir
    env["SIM_BUILD"] = sim_build
    env["COCOTB_RESULTS_FILE"] = results_xml

    make_cmd = [
        "make",
        "-C", os.path.join(PROJ_DIR, mut["make_dir"]),
        "-f", "Makefile.single",
        f"TOPLEVEL={mut['toplevel']}",
        f"MODULE={mut['module']}",
        f"SIM_BUILD={sim_build}",
        f"COCOTB_RESULTS_FILE={results_xml}",
        f"VERILOG_SOURCES={' '.join(sources)}",
        "SIM=icarus",
    ]
    if mut["testcase"]:
        make_cmd.append(f"COCOTB_TEST_FILTER={mut['testcase']}")

    try:
        res = subprocess.run(make_cmd, env=env, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return mid, "KILLED", f"{mut['module']}.{mut['testcase'] or '*'}: timeout (60s)"

    combined = res.stdout + "\n" + res.stderr
    # Check if XML exists and records a failure, or process failed cleanly at test runtime
    has_xml_fail = False
    if os.path.exists(results_xml):
        try:
            tree = ET.parse(results_xml)
            for tc in tree.getroot().iter("testcase"):
                if tc.find("failure") is not None:
                    has_xml_fail = True
                    break
        except Exception:
            pass

    if res.returncode != 0 or has_xml_fail:
        reason = _extract_kill_reason(combined, results_xml, mut)
        return mid, "KILLED", reason

    return mid, "SURVIVED", f"Test {mut['module']}.{mut['testcase'] or '*'} passed on mutant!"


def main():
    os.makedirs(SANITY_DIR, exist_ok=True)
    killed = 0
    invalid = 0
    survived = 0

    total = len(SANITY_MUTANTS)
    print(f"=== Running {total}-Mutant Sanity Gate ({SANITY_MUTANTS[0]['id']}..{SANITY_MUTANTS[-1]['id']}) ===")
    for mut in SANITY_MUTANTS:
        status_id, status, detail = run_one_mutant(mut)
        detail_sanitized = detail.replace(PROJ_DIR + "/", "").replace(os.path.expanduser("~"), "~")
        print(f"[{status_id}] {status:8s} | {mut['desc']} | {detail_sanitized}")
        if status == "KILLED":
            killed += 1
        elif status == "INVALID":
            invalid += 1
        else:
            survived += 1

    total = len(SANITY_MUTANTS)
    print(f"\nSanity Summary: {killed}/{total} KILLED, {survived} SURVIVED, {invalid} INVALID")
    return 0 if killed == total else 1


if __name__ == "__main__":
    sys.exit(main())
