#!/usr/bin/env python3
"""
run_sanity_mutants.py - Runs project tests against 5 deliberate mutants in audit/mutants/
Verifies whether the testbench catches:
1. M1: rr_arbiter (broken round-robin rotation, fixed priority)
2. M2: axil_ram (dropped write strobe byte 0)
3. M3: async_fifo (binary pointer instead of Gray code across CDC)
4. M4: axil2apb_bridge (PSLVERR masked to RESP_OKAY)
5. M5: apb_timer (off-by-one timer expiry, fires at 1 instead of 0)
"""
import os
import sys
import subprocess
import time
import json

PROJ_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AUDIT_DIR = os.path.join(PROJ_DIR, "audit")
LOG_DIR = os.path.join(AUDIT_DIR, "logs")

MUTANTS = [
    {
        "id": "MUTANT-01",
        "name": "rr_arbiter priority rotation broken",
        "module": "rr_arbiter",
        "test_dir": os.path.join(PROJ_DIR, "tb/unit"),
        "test_mod": "test_rr_arbiter",
        "top": "rr_arbiter",
        "v_src": os.path.join(AUDIT_DIR, "mutants/m1_rr_arbiter/rr_arbiter.v")
    },
    {
        "id": "MUTANT-02",
        "name": "axil_ram dropped WSTRB[0]",
        "module": "axil_ram",
        "test_dir": os.path.join(PROJ_DIR, "tb/unit"),
        "test_mod": "test_axil_ram",
        "top": "axil_ram",
        "v_src": os.path.join(AUDIT_DIR, "mutants/m2_axil_ram/axil_ram.v")
    },
    {
        "id": "MUTANT-03",
        "name": "async_fifo binary pointer across CDC",
        "module": "async_fifo",
        "test_dir": os.path.join(PROJ_DIR, "tb/unit"),
        "test_mod": "test_async_fifo",
        "top": "async_fifo",
        "v_src": os.path.join(AUDIT_DIR, "mutants/m3_async_fifo/async_fifo.v")
    },
    {
        "id": "MUTANT-04",
        "name": "axil2apb_bridge PSLVERR masked to OKAY",
        "module": "axil2apb_bridge",
        "test_dir": os.path.join(PROJ_DIR, "tb/block"),
        "test_mod": "test_axil2apb_bridge",
        "top": "axil2apb_bridge",
        "v_src": os.path.join(AUDIT_DIR, "mutants/m4_axil2apb_bridge/axil2apb_bridge.v")
    },
    {
        "id": "MUTANT-05",
        "name": "apb_timer off-by-one expiry (LOAD instead of LOAD+1)",
        "module": "apb_timer",
        "test_dir": os.path.join(PROJ_DIR, "tb/block"),
        "test_mod": "test_apb_timer",
        "top": "apb_timer",
        "v_src": os.path.join(AUDIT_DIR, "mutants/m5_apb_timer/apb_timer.v")
    }
]

def main():
    print("=== Running Sanity Mutants Audit (Step F) ===")
    results = {}
    
    for m in MUTANTS:
        mid = m["id"]
        print(f"\n--- Testing {mid}: {m['name']} ---")
        log_file = os.path.join(LOG_DIR, f"sanity_{mid.lower()}.log")
        sim_build = os.path.join(AUDIT_DIR, f"sim_build_{mid.lower()}")
        
        cmd = f"""source {PROJ_DIR}/scripts/env.sh && \
make -C {m['test_dir']} -f Makefile.single clean SIM_BUILD={sim_build} && \
make -C {m['test_dir']} -f Makefile.single \
    TOPLEVEL={m['top']} \
    MODULE={m['test_mod']} \
    VERILOG_SOURCES="{m['v_src']}" \
    SIM=icarus \
    SIM_BUILD={sim_build}
"""
        start = time.time()
        with open(log_file, "w") as lf:
            proc = subprocess.run(cmd, shell=True, cwd=m["test_dir"], stdout=lf, stderr=subprocess.STDOUT, text=True)
        elapsed = time.time() - start
        
        # A test failure means the mutant was CAUGHT (KILLED)
        caught = (proc.returncode != 0)
        
        # Parse failure reason
        catch_reason = "Test exited with failure"
        if os.path.exists(log_file):
            with open(log_file) as lf:
                for line in lf:
                    if "AssertionError" in line or "failed" in line.lower() or "error" in line.lower():
                        if "assert" in line or "fail" in line.lower():
                            catch_reason = line.strip()
                            break
                            
        status = "KILLED (CAUGHT)" if caught else "SURVIVED (ESCAPED)"
        print(f"Result for {mid}: {status} in {elapsed:.2f}s")
        print(f"Details: {catch_reason}")
        
        results[mid] = {
            "id": mid,
            "name": m["name"],
            "module": m["module"],
            "test": m["test_mod"],
            "status": status,
            "caught": caught,
            "catch_reason": catch_reason,
            "log": log_file,
            "elapsed_s": round(elapsed, 2)
        }
        
    out_json = os.path.join(LOG_DIR, "sanity_mutants_summary.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSanity mutants completed. Summary saved to {out_json}")

if __name__ == "__main__":
    main()
