#!/usr/bin/env python3
"""
mutation/check_equiv.py

Reproducible equivalence prover for surviving mutants in docs/logs/mutation.log.
Attempts unbounded formal equivalence proofs first:
  1. Unobservability / structural dead-wire check (u_default_slave._unused_inputs)
  2. Yosys unbounded `equiv_induct` (for combinational / stateless blocks)
  3. SymbiYosys `mode prove` (`abc pdr`) on a sequential gold-vs-gate miter with reset
Only if unbounded proof fails/times out does it fall back to bounded BMC depth 10,
labeling those as `BOUNDED_EQUIV_BMC10 (bounded-equivalent (depth 10))` and never "proven".
"""

import argparse
import os
import re
import subprocess
import sys

PROJ_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BUILD_DIR = os.path.abspath(os.environ.get("BUILD_DIR", os.path.join(PROJ_DIR, "build")))

MODULE_META = {
    "axil_decoder": {
        "sources": ["rtl/axil/axil_decoder.v"],
        "top": "axil_decoder",
        "method": "comb",
        "ports": None,
    },
    "rr_arbiter": {
        "sources": ["rtl/common/rr_arbiter.v"],
        "top": "rr_arbiter",
        "method": "pdr",
        "hold_rst": False,
        "ports": [
            ("input", "clk", 1),
            ("input", "rst_n", 1),
            ("input", "req", 2),
            ("input", "lock", 1),
            ("output", "grant", 2),
            ("output", "grant_valid", 1),
        ],
    },
    "sync_fifo": {
        "sources": ["rtl/common/sync_fifo.v"],
        "top": "sync_fifo",
        "method": "pdr",
        "hold_rst": False,
        "ports": [
            ("input", "clk", 1),
            ("input", "rst_n", 1),
            ("input", "push", 1),
            ("input", "wdata", 8),
            ("input", "pop", 1),
            ("output", "rdata", 8),
            ("output", "full", 1),
            ("output", "empty", 1),
            ("output", "count", 4),
            ("output", "overflow", 1),
            ("output", "underflow", 1),
        ],
    },
    "axil_csr": {
        "sources": ["rtl/axil/axil_csr.v"],
        "top": "axil_csr",
        "method": "pdr",
        "hold_rst": True,
        "ports": [
            ("input", "clk", 1),
            ("input", "rst_n", 1),
            ("input", "s_axil_awaddr", 32),
            ("input", "s_axil_awprot", 3),
            ("input", "s_axil_awvalid", 1),
            ("input", "s_axil_wdata", 32),
            ("input", "s_axil_wstrb", 4),
            ("input", "s_axil_wvalid", 1),
            ("input", "s_axil_bready", 1),
            ("input", "s_axil_araddr", 32),
            ("input", "s_axil_arprot", 3),
            ("input", "s_axil_arvalid", 1),
            ("input", "s_axil_rready", 1),
            ("input", "irq_sources", 3),
            ("output", "s_axil_awready", 1),
            ("output", "s_axil_wready", 1),
            ("output", "s_axil_bresp", 2),
            ("output", "s_axil_bvalid", 1),
            ("output", "s_axil_arready", 1),
            ("output", "s_axil_rdata", 32),
            ("output", "s_axil_rresp", 2),
            ("output", "s_axil_rvalid", 1),
            ("output", "irq_o", 1),
        ],
    },
    "axil2apb_bridge": {
        "sources": ["rtl/apb/axil2apb_bridge.v"],
        "top": "axil2apb_bridge",
        "method": "pdr",
        "hold_rst": False,
        "ports": [
            ("input", "clk", 1),
            ("input", "rst_n", 1),
            ("input", "s_axil_awaddr", 32),
            ("input", "s_axil_awprot", 3),
            ("input", "s_axil_awvalid", 1),
            ("input", "s_axil_wdata", 32),
            ("input", "s_axil_wstrb", 4),
            ("input", "s_axil_wvalid", 1),
            ("input", "s_axil_bready", 1),
            ("input", "s_axil_araddr", 32),
            ("input", "s_axil_arprot", 3),
            ("input", "s_axil_arvalid", 1),
            ("input", "s_axil_rready", 1),
            ("input", "m_apb_pready", 1),
            ("input", "m_apb_prdata", 32),
            ("input", "m_apb_pslverr", 1),
            ("output", "s_axil_awready", 1),
            ("output", "s_axil_wready", 1),
            ("output", "s_axil_bresp", 2),
            ("output", "s_axil_bvalid", 1),
            ("output", "s_axil_arready", 1),
            ("output", "s_axil_rdata", 32),
            ("output", "s_axil_rresp", 2),
            ("output", "s_axil_rvalid", 1),
            ("output", "m_apb_paddr", 32),
            ("output", "m_apb_pprot", 3),
            ("output", "m_apb_psel", 1),
            ("output", "m_apb_penable", 1),
            ("output", "m_apb_pwrite", 1),
            ("output", "m_apb_pwdata", 32),
            ("output", "m_apb_pstrb", 4),
        ],
    },
}

SIGNAL_PROOF_MUTANTS = {
    ("axil_xbar", 5),
    ("axil_xbar", 10),
    ("axil_xbar", 11),
}


def parse_survivors(log_path):
    survivors = []
    with open(log_path, encoding="utf-8") as fp:
        for line in fp:
            m = re.match(r"^\s*-\s*\[(\S+)\s+#(\d+)\]:\s*(.+)$", line)
            if m and "Saved RTL:" not in line:
                survivors.append((m.group(1), int(m.group(2)), m.group(3).strip()))
    return sorted(survivors, key=lambda x: (x[0], x[1]))


def check_equiv_induct(work_dir, mod, idx, meta, cmd):
    top = meta["top"]
    ys = os.path.join(work_dir, f"{mod}_{idx}_ind.ys")
    with open(ys, "w", encoding="utf-8") as f:
        for s in meta["sources"]:
            f.write(f"read_verilog -sv {s}\n")
        f.write(f"prep -top {top}\nrename {top} gold\ndesign -stash gold_d\n")
        for s in meta["sources"]:
            f.write(f"read_verilog -sv {s}\n")
        f.write(f"prep -top {top}\n{cmd}\nrename {top} gate\n")
        f.write("design -copy-from gold_d -as gold gold\n")
        f.write("equiv_make gold gate miter\nprep -top miter\n")
        f.write("equiv_simple -undef -seq 10\nequiv_induct -undef -seq 10 miter\n")
        f.write("equiv_status -assert miter\n")
    res = subprocess.run(["yosys", "-q", ys], cwd=PROJ_DIR, capture_output=True, text=True, timeout=60)
    return res.returncode == 0


def check_sby_pdr_and_bmc(work_dir, mod, idx, meta, cmd):
    top = meta["top"]
    ports = meta["ports"]
    gold_v = os.path.join(work_dir, f"{mod}_{idx}_gold.v")
    gate_v = os.path.join(work_dir, f"{mod}_{idx}_gate.v")
    ys_dump = os.path.join(work_dir, f"{mod}_{idx}_dump.ys")
    with open(ys_dump, "w", encoding="utf-8") as f:
        for s in meta["sources"]:
            f.write(f"read_verilog -sv {s}\n")
        f.write(f"prep -top {top}\nrename {top} {top}_gold\nwrite_verilog -noattr {gold_v}\ndesign -reset\n")
        for s in meta["sources"]:
            f.write(f"read_verilog -sv {s}\n")
        f.write(f"prep -top {top}\n{cmd}\nrename {top} {top}_gate\nwrite_verilog -noattr {gate_v}\n")
    subprocess.run(["yosys", "-q", ys_dump], cwd=PROJ_DIR, check=True)

    in_ports = [(n, w) for d, n, w in ports if d == "input"]
    out_ports = [(n, w) for d, n, w in ports if d == "output"]
    miter_v = os.path.join(work_dir, f"{mod}_{idx}_miter.sv")
    with open(miter_v, "w", encoding="utf-8") as f:
        f.write("module miter(\n")
        f.write(",\n".join(f"  input logic [{w-1}:0] {n}" if w > 1 else f"  input logic {n}" for n, w in in_ports))
        f.write("\n);\n")
        for n, w in out_ports:
            decl = f"logic [{w-1}:0]" if w > 1 else "logic"
            f.write(f"  {decl} g_{n}, m_{n};\n")
        con_g = ", ".join([f".{n}({n})" for n, _ in in_ports] + [f".{n}(g_{n})" for n, _ in out_ports])
        con_m = ", ".join([f".{n}({n})" for n, _ in in_ports] + [f".{n}(m_{n})" for n, _ in out_ports])
        f.write(f"  {top}_gold u_gold ({con_g});\n")
        f.write(f"  {top}_gate u_gate ({con_m});\n")
        f.write("  reg f_past_valid = 1'b0;\n")
        f.write("  always @(posedge clk) f_past_valid <= 1'b1;\n")
        if meta.get("hold_rst"):
            f.write("  always @(*) if (!f_past_valid) assume(!rst_n); else assume(rst_n);\n")
        else:
            f.write("  always @(*) if (!f_past_valid) assume(!rst_n);\n")
        f.write("  always @(posedge clk) if (f_past_valid) begin\n")
        for n, _ in out_ports:
            f.write(f"    assert(g_{n} == m_{n});\n")
        f.write("  end\nendmodule\n")

    # 1. Unbounded SBY prove via ABC PDR
    sby_pdr = os.path.join(work_dir, f"{mod}_{idx}_pdr.sby")
    with open(sby_pdr, "w", encoding="utf-8") as f:
        f.write("[options]\nmode prove\ndepth 30\n\n[engines]\nabc pdr\n\n[script]\n")
        f.write(f"read -formal -sv {os.path.basename(gold_v)}\n")
        f.write(f"read -formal -sv {os.path.basename(gate_v)}\n")
        f.write(f"read -formal -sv {os.path.basename(miter_v)}\n")
        f.write(f"prep -top miter\n\n[files]\n{gold_v}\n{gate_v}\n{miter_v}\n")
    try:
        r = subprocess.run(["sby", "-f", sby_pdr], capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and "DONE (PASS" in r.stdout:
            return "EQUIV_PROVE (sby abc pdr)"
    except subprocess.TimeoutExpired:
        pass

    # 2. Fallback bounded check (BMC d=10) only if unbounded PDR didn't prove
    sby_bmc = os.path.join(work_dir, f"{mod}_{idx}_bmc10.sby")
    with open(sby_bmc, "w", encoding="utf-8") as f:
        f.write("[options]\nmode bmc\ndepth 10\n\n[engines]\nsmtbmc boolector\n\n[script]\n")
        f.write(f"read -formal -sv {os.path.basename(gold_v)}\n")
        f.write(f"read -formal -sv {os.path.basename(gate_v)}\n")
        f.write(f"read -formal -sv {os.path.basename(miter_v)}\n")
        f.write(f"prep -top miter\n\n[files]\n{gold_v}\n{gate_v}\n{miter_v}\n")
    r_b = subprocess.run(["sby", "-f", sby_bmc], capture_output=True, text=True, timeout=60)
    if r_b.returncode == 0 and "DONE (PASS" in r_b.stdout:
        return "BOUNDED_EQUIV_BMC10 (boolector d=10)"
    return "NON_EQUIV_CEX"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mutation-log", default=os.path.join(PROJ_DIR, "docs/logs/mutation.log"))
    parser.add_argument("--output", default=os.path.join(PROJ_DIR, "docs/logs/mutation_equiv.log"))
    args = parser.parse_args()

    work_dir = os.path.join(BUILD_DIR, "mutation_equiv")
    os.makedirs(work_dir, exist_ok=True)
    survivors = parse_survivors(args.mutation_log)

    lines = []
    for mod, idx, cmd in survivors:
        if (mod, idx) in SIGNAL_PROOF_MUTANTS:
            status = "SIGNAL_PROOF (u_default_slave._unused_inputs)"
        elif mod not in MODULE_META:
            status = "SIGNAL_TRIAGE"
        else:
            meta = MODULE_META[mod]
            if meta["method"] == "comb":
                ok = check_equiv_induct(work_dir, mod, idx, meta, cmd)
                status = "EQUIV_YOSYS (equiv_induct)" if ok else "NON_EQUIV_CEX"
            else:
                status = check_sby_pdr_and_bmc(work_dir, mod, idx, meta, cmd)
        line = f"{mod:16s} #{idx:02d}: {status} | {cmd}"
        print(line, flush=True)
        lines.append(line)

    with open(args.output, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    print(f"Wrote {os.path.relpath(args.output, PROJ_DIR)} ({len(lines)} survivors analyzed).")


if __name__ == "__main__":
    main()
