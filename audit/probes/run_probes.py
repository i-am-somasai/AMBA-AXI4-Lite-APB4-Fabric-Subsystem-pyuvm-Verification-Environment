#!/usr/bin/env python3
"""
run_probes.py - Runner for Independent Black-Box Probe Tests (Step E)
Runs probe tests against amba_fabric_top:
1. test_probe_addr_decode.py
2. test_probe_registers.py
3. test_probe_peripherals.py
4. test_probe_cdc.py
5. test_probe_contention.py
Saves logs to audit/logs/probe_*.log and records results in audit/logs/probe_summary.json.
"""
import os
import sys
import time
import subprocess
import json

PROJ_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
AUDIT_DIR = os.path.join(PROJ_DIR, "audit")
PROBES_DIR = os.path.join(AUDIT_DIR, "probes")
LOG_DIR = os.path.join(AUDIT_DIR, "logs")

RTL_SOURCES = [
    os.path.join(PROJ_DIR, "rtl/common/rst_sync.v"),
    os.path.join(PROJ_DIR, "rtl/common/sync_fifo.v"),
    os.path.join(PROJ_DIR, "rtl/common/async_fifo.v"),
    os.path.join(PROJ_DIR, "rtl/common/rr_arbiter.v"),
    os.path.join(PROJ_DIR, "rtl/axil/axil_default_slave.v"),
    os.path.join(PROJ_DIR, "rtl/axil/axil_decoder.v"),
    os.path.join(PROJ_DIR, "rtl/axil/axil_xbar.v"),
    os.path.join(PROJ_DIR, "rtl/axil/axil_ram.v"),
    os.path.join(PROJ_DIR, "rtl/axil/axil_csr.v"),
    os.path.join(PROJ_DIR, "rtl/apb/axil2apb_bridge.v"),
    os.path.join(PROJ_DIR, "rtl/apb/apb_decoder.v"),
    os.path.join(PROJ_DIR, "rtl/apb/apb_uart.v"),
    os.path.join(PROJ_DIR, "rtl/apb/apb_timer.v"),
    os.path.join(PROJ_DIR, "rtl/apb/apb_gpio.v"),
    os.path.join(PROJ_DIR, "rtl/cdc/slow_regs.v"),
    os.path.join(PROJ_DIR, "rtl/cdc/axil_cdc_bridge.v"),
    os.path.join(PROJ_DIR, "rtl/amba_fabric_top.v")
]

PROBE_TESTS = [
    ("PROBE-ADDR-DECODE", "test_probe_addr_decode", "Spec Section 5.3: Address Decode & Region Mapping"),
    ("PROBE-REGISTERS", "test_probe_registers", "Spec Section 7: Register Reset Values & Access Types"),
    ("PROBE-PERIPHERALS", "test_probe_peripherals", "Spec Section 7.3: Timer LOAD+1, GPIO 2-FF Sync, UART Loopback"),
    ("PROBE-CDC", "test_probe_cdc", "Spec Section 7.4: CDC Bridge Clock Ratios & Free-running Counter"),
    ("PROBE-CONTENTION", "test_probe_contention", "Spec Section 7.2 / XB-05, XB-06: Two-Master Contention & Parallelism")
]

def main():
    print("=== Running Independent Black-Box Probe Tests (Step E) ===")
    results = {}
    
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{PROBES_DIR}:{env.get('PYTHONPATH', '')}"
    
    sim_build_base = os.path.join(AUDIT_DIR, "sim_build_probes")
    
    for pid, mod_name, desc in PROBE_TESTS:
        print(f"\n--- Running Probe: {pid} ({desc}) ---")
        log_file = os.path.join(LOG_DIR, f"{pid.lower()}.log")
        sim_build = f"{sim_build_base}_{mod_name}"
        
        cmd = f"""source {PROJ_DIR}/scripts/env.sh && \
make -f {PROJ_DIR}/tb/block/Makefile.single \
    TOPLEVEL=amba_fabric_top \
    MODULE={mod_name} \
    VERILOG_SOURCES="{' '.join(RTL_SOURCES)}" \
    SIM=icarus \
    COMPILE_ARGS="-g2012" \
    SIM_BUILD={sim_build}
"""
        start = time.time()
        with open(log_file, "w") as lf:
            p = subprocess.run(cmd, shell=True, cwd=PROBES_DIR, stdout=lf, stderr=subprocess.STDOUT, text=True, env=env)
        elapsed = time.time() - start
        
        passed = (p.returncode == 0)
        status = "PASS" if passed else "FAIL"
        print(f"Result for {pid}: {status} in {elapsed:.2f}s (Log: {log_file})")
        
        results[pid] = {
            "id": pid,
            "module": mod_name,
            "description": desc,
            "status": status,
            "elapsed_s": round(elapsed, 2),
            "log": log_file
        }
        
    summary_path = os.path.join(LOG_DIR, "probe_summary.json")
    with open(summary_path, "w") as sf:
        json.dump(results, sf, indent=2)
    print(f"\nProbe execution finished. Summary saved to {summary_path}")

if __name__ == "__main__":
    main()
