#!/usr/bin/env python3
"""
generate_audit_report.py
Generates the comprehensive, rigorous sign-off audit report docs/AUDIT_REPORT.md
following the strict 17-section layout defined in spec Section 6.3.
"""
import os
import sys

PROJ_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(PROJ_DIR, "docs")
REPORT_PATH = os.path.join(DOCS_DIR, "AUDIT_REPORT.md")

REPORT_CONTENT = """# Independent Verification Sign-Off Audit Report: AMBA-Fabric Subsystem

**Project:** AMBA AXI4-Lite / APB4 Interconnect Fabric Subsystem & pyuvm Verification Environment  
**Repository:** `amba-fabric`  
**Auditor:** Senior Verification Engineer / Independent Auditor  
**Audit Date:** 2026-11-24  
**Authoritative Contract:** `docs/spec.md`  

---

## 1. Verdict

### **Verdict: READY WITH MINOR ISSUES**

**Sign-Off Assessment:**  
The AMBA-Fabric implementation and verification suite demonstrate exceptional engineering rigor, passing all static structure checks (101/101), multi-tool compilation/lint checks (Verilator, Icarus, Yosys), exhaustive formal property verification (8/8 SBY modules PASS, 37/37 cover traces reached), clean-state stress regression (100,000 transactions with zero mismatches across 10 brand-new seeds), 100% functional coverage (280/280 bins, zero holes, zero waivers), 100% independent probe test pass rate (5/5 black-box probes), and complete gate-level synthesis and timing closure reproduction on SKY130 HD (9,376 cells, 3,623 flops, 137,867 µm², Fmax 81.63 MHz).

However, sign-off as unconditional `READY` is precluded by **two MAJOR verification honesty defects**:
1. Spec Section 9.1 test **`UA-04`** (UART framing error detection) was omitted from the repository despite being falsely reported as **PASS** in `docs/vplan.md`.
2. Spec Section 9.1 test **`XB-10`** (Delayed BREADY / RREADY handshake holding) was omitted from the test suite despite being falsely reported as **PASS** in `docs/vplan.md`.

In addition, a **MINOR** documentation typo exists in `README.md` listing APB Timer at `0x4000_0100` (instead of `0x4000_1000`) and APB GPIO at `0x4000_0200` (instead of `0x4000_2000`). Because the physical RTL, formal proofs, and 5 independent probe tests fully confirm correct hardware operation, these defects represent testbench/documentation gaps rather than silicon defects. Remediation is straightforward.

---

## 2. Scorecard

| Category | Total Checked | PASS | FAIL | PARTIAL | NOT FOUND | NOT RUN | N/A | Blockers | Majors | Minors | Info | Evidence Log |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Specification Features (Sec 3)** | 28 | 28 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | `audit/logs/step_b_structure.log` |
| **Architecture & Decoder (Sec 5, 7)** | 35 | 35 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | `audit/logs/probe-addr-decode.log` |
| **AXI4-Lite Protocol (Sec 6)** | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | `audit/logs/repro_pyuvm_directed_icarus.log` |
| **Verification Test Suite (Sec 9)** | 40 | 38 | 0 | 0 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | `audit/logs/repro_summary.json` |
| **Functional Coverage (Sec 10)** | 11 | 11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | `audit/logs/coverage_repro.log` |
| **Formal Verification (Sec 11)** | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | `audit/logs/formal_repro.log` |
| **Mutation Testing (Sec 12)** | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | `audit/logs/mutation_repro.log` |
| **Synthesis & STA (Sec 13)** | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | `audit/logs/synth_repro.log` |
| **CI & Repository Layout (Sec 14, 15)**| 11 | 11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | `audit/logs/step_b_structure.log` |
| **Definition of Done (Sec 17, 21)** | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | `docs/audit_results.json` |
| **Independent Probe Tests (Step E)** | 5 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | `audit/logs/probe_summary.json` |
| **Sanity Deliberate Mutants (Step F)**| 5 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | `audit/logs/sanity_mutants_summary.json` |
| **TOTAL** | **185** | **183** | **0** | **0** | **2** | **0** | **0** | **0** | **2** | **1** | **1** | Multi-log index in Section 17 |

---

## 3. Environment

The entire audit was executed in a clean environment from first principles using open-source EDA tools:
- **Host OS:** Linux 6.6.137+ x86_64
- **Host Memory & Compute:** 8.0 GB RAM, 4 CPU cores
- **Toolchain Versions:**
  - **Icarus Verilog:** version 14.0 (devel) (`/home/somasai/oss-cad-suite/bin/iverilog`)
  - **Verilator:** version 5.055 (`/home/somasai/oss-cad-suite/bin/verilator`)
  - **Yosys:** version 0.71+77 (`/home/somasai/oss-cad-suite/bin/yosys`)
  - **SymbiYosys (SBY):** version 0.71-7 (`/home/somasai/oss-cad-suite/bin/sby`)
  - **OpenSTA:** version 2.6.0 (`/nix/store/q5ycjmn0d9awbcq05c75z2rmgwjgbc9g-opensta/bin/sta`)
  - **Python:** 3.11.6 (`tabbypy3`)
  - **Python EDA Packages:** `cocotb 2.1.0.dev0+41564633`, `pyuvm 5.0.0`, `cocotb-coverage 2.0`
- **PDK / Standard Cell Library:**
  - SkyWater SKY130 HD (`sky130_fd_sc_hd__tt_025C_1v80.lib` at `/home/somasai/.volare/volare/sky130/...`)
- **Clean State Isolation:**
  - All temporary audit runs, probe simulations, mutant builds, and reproduction runs were isolated under `audit/` with dedicated build directories (`audit/sim_build_*`) and outputs directed to `audit/logs/`.

---

## 4. Feature Matrix (Spec Section 3)

| Feature ID | Description | Priority | Spec Ref | Status | Evidence | Measured vs Claimed |
|---|---|---|---|---|---|---|
| **F-01** | AXI4-Lite 2Mx4S Crossbar with address decode | P0 | Sec 3.1 | **PASS** | `rtl/axil/axil_xbar.v:1-512` | 2 masters to 4 slaves + default slave |
| **F-02** | Per-slave round-robin arbiter with transaction lock | P0 | Sec 3.1 | **PASS** | `rtl/common/rr_arbiter.v:1-130` | Fairness and atomic lock verified |
| **F-03** | Default slave returning DECERR on unmapped space | P0 | Sec 3.1 | **PASS** | `rtl/axil/axil_default_slave.v:1-105`| Consumes write data, returns DECERR |
| **F-04** | AXI4-Lite scratch RAM with WSTRB and SLVERR | P0 | Sec 3.1 | **PASS** | `rtl/axil/axil_ram.v:1-218` | All 16 strobe patterns + OOR SLVERR |
| **F-05** | AXI4-Lite System CSR & IRQ aggregation to `irq_o` | P0 | Sec 3.1 | **PASS** | `rtl/axil/axil_csr.v:1-295` | RO, RW, W1C, W1C_SET, IRQ masking |
| **F-06** | AXI4-Lite to APB4 Bridge with wait states, PSLVERR | P0 | Sec 3.1 | **PASS** | `rtl/apb/axil2apb_bridge.v:1-199` | APB SETUP->ACCESS, PSLVERR->SLVERR |
| **F-07** | APB Decoder with PSLVERR on unmapped APB address | P0 | Sec 3.1 | **PASS** | `rtl/apb/apb_decoder.v:1-68` | 3 peripheral selects + error decode |
| **F-08** | APB UART (8N1, 16x oversampling, TX/RX FIFOs, loopback) | P0 | Sec 3.1 | **PASS** | `rtl/apb/apb_uart.v:1-285` | Full loopback and baudrate scaling |
| **F-09** | APB Timer (one-shot, periodic, IRQ, W1C status) | P0 | Sec 3.1 | **PASS** | `rtl/apb/apb_timer.v:1-196` | Deterministic timeout at LOAD+1 cycles |
| **F-10** | APB GPIO (programmable dir, 2-FF sync, rising-edge IRQ)| P1 | Sec 3.1 | **PASS** | `rtl/apb/apb_gpio.v:1-188` | 2-FF latency, IRQ detection, W1C |
| **F-11** | CDC Bridge: Gray-pointer async FIFOs to `clk_slow` | P0 | Sec 3.1 | **PASS** | `rtl/cdc/axil_cdc_bridge.v:1-210` | 2-FF Gray pointer CDC across ratios |
| **F-12** | Reset Synchronizers per clock domain (async assert) | P0 | Sec 3.1 | **PASS** | `rtl/common/rst_sync.v:1-42` | Async assert, 2-cycle sync deassert |
| **F-13** | Top-level fabric subsystem integration (`amba_fabric_top`)| P0 | Sec 3.1 | **PASS** | `rtl/amba_fabric_top.v:1-466` | Top SoC integration with `irq_o` |
| **V-01** | Dual AXI4-Lite master agents in pyuvm | P0 | Sec 3.2 | **PASS** | `tb/pyuvm/agents/` | M0 & M1 drivers, sequencers, monitors |
| **V-02** | Independent reference model in scoreboard | P0 | Sec 3.2 | **PASS** | `tb/models/fabric_ref_model.py:1-95`| Software model, data/resp compare |
| **V-03** | Concurrent random stress test (XB-13, 10k txns/seed) | P0 | Sec 3.2 | **PASS** | `tb/pyuvm/tests/test_stress.py:1-75`| 100,000 txns reproduced, 0 mismatch |
| **V-04** | Formal property suite with SymbiYosys (8 modules) | P0 | Sec 3.2 | **PASS** | `formal/*.sby` | 8/8 suites PASS (37 cover traces) |
| **V-05** | Functional coverage with cocotb-coverage (9 groups) | P0 | Sec 3.2 | **PASS** | `tb/pyuvm/func_cov/fabric_cov.py` | 280/280 bins hit (100.00%) |
| **V-06** | HDL code coverage with Verilator 5.055 | P1 | Sec 3.2 | **PASS** | `docs/logs/code_cov_summary.txt` | Line 87.8%, Toggle 75.1%, FSM 100% |
| **V-07** | Mutation testing flow (Yosys `mutate`, score >=60%)| P0 | Sec 3.2 | **PASS** | `mutation/run_mutants.py:1-247` | 65.00% score (13/20 killed) |
| **V-08** | Automated GitHub Actions CI workflow | P0 | Sec 3.2 | **PASS** | `.github/workflows/ci.yml:1-63` | Clean YAML, lint, regress, formal, mut |
| **V-09** | Waveform generation (VCD) and trace inspection | P1 | Sec 3.2 | **PASS** | `docs/img/contention.png`, `.vcd` | Parallel access waveform verified |
| **V-10** | Dual simulator compatibility (Icarus & Verilator) | P0 | Sec 3.2 | **PASS** | `Makefile:53-76` | Clean runs on both simulators |
| **S-01** | Yosys synthesis for SKY130 HD library | P0 | Sec 3.3 | **PASS** | `synth/synth.ys:1-40` | 9,376 cells, 3,623 flops, 137,867 um2 |
| **S-02** | OpenSTA static timing analysis with dual clocks SDC | P0 | Sec 3.3 | **PASS** | `synth/amba_fabric.sdc:1-21` | Async clock groups, WNS -2.25ns @100M |
| **S-03** | Frequency sweep script for Fmax determination | P0 | Sec 3.3 | **PASS** | `synth/fmax_sweep.py:1-120` | Achieved Fmax 81.63 MHz (reg 95.15M) |
| **X-01** | Stretch: APB GPIO interrupt generation | P2 | Sec 3.4 | **PASS** | `rtl/apb/apb_gpio.v:100-140` | Rising-edge interrupt logic verified |
| **X-02** | Stretch: UART baud rate divisor sweep test | P2 | Sec 3.4 | **PASS** | `tb/block/test_apb_uart.py:65-95` | UA-03 sweeps BAUDDIV 0, 1, 2 |

---

## 5. Test Matrix (Spec Section 9)

| Test ID | Description | Suite / File | Status | Severity | Seed(s) | Runtime | Log Path |
|---|---|---|---|---|---|---|---|
| **XB-01** | Single Master Write/Read to all 4 Slaves | `tb/block/test_axil_xbar.py` | **PASS** | - | - | 0.05s | `audit/logs/repro_block_icarus.log` |
| **XB-02** | Master 1 Write/Read to all 4 Slaves | `tb/block/test_axil_xbar.py` | **PASS** | - | - | 0.05s | `audit/logs/repro_block_icarus.log` |
| **XB-03** | Unmapped Address Read/Write -> DECERR | `tb/block/test_axil_xbar.py` | **PASS** | - | - | 0.04s | `audit/logs/repro_block_icarus.log` |
| **XB-04** | Out-of-Range RAM Access -> SLVERR | `tb/block/test_axil_xbar.py` | **PASS** | - | - | 0.04s | `audit/logs/repro_block_icarus.log` |
| **XB-05** | Multi-Master Contention to Same Slave | `tb/block/test_axil_xbar.py` | **PASS** | - | - | 0.06s | `audit/logs/repro_block_icarus.log` |
| **XB-06** | Multi-Master Parallel Transfer to Diff Slaves| `tb/block/test_axil_xbar.py` | **PASS** | - | - | 0.05s | `audit/logs/repro_block_icarus.log` |
| **XB-07** | Write Handshake Permutations (AW/W skew)| `tb/block/test_axil_xbar.py` | **PASS** | - | - | 0.06s | `audit/logs/repro_block_icarus.log` |
| **XB-08** | All 16 WSTRB Strobe Patterns on RAM | `tb/block/test_axil_xbar.py` | **PASS** | - | - | 0.06s | `audit/logs/repro_block_icarus.log` |
| **XB-09** | Unaligned Address Access (LSBs [1:0] != 0)| `tb/pyuvm/tests/test_directed.py` | **PASS** | - | - | 0.12s | `audit/logs/repro_pyuvm_directed_icarus.log` |
| **XB-10** | Delayed BREADY / RREADY Handshake | `tb/pyuvm/tests/test_directed.py` | **NOT_FOUND** | **MAJOR** | - | - | `audit/logs/repro_pyuvm_directed_icarus.log` |
| **XB-11** | Protection Pass-Through (AxPROT) | `tb/pyuvm/tests/test_directed.py` | **PASS** | - | - | 0.11s | `audit/logs/repro_pyuvm_directed_icarus.log` |
| **XB-12** | Reset During Active Transaction Recovery | `tb/pyuvm/tests/test_directed.py` | **PASS** | - | - | 0.15s | `audit/logs/repro_pyuvm_directed_icarus.log` |
| **XB-13** | Multi-Seed Random Stress (10,000 txns/seed)| `tb/pyuvm/tests/test_stress.py` | **PASS** | - | 10 seeds | 95.5s | `audit/logs/repro_stress_icarus_seed_*.log` |
| **BR-01** | Single Write/Read with 0 Wait States | `tb/block/test_axil2apb_bridge.py` | **PASS** | - | - | 0.04s | `audit/logs/repro_block_icarus.log` |
| **BR-02** | Wait-State Sweep (PREADY delays 1..8) | `tb/block/test_axil2apb_bridge.py` | **PASS** | - | - | 0.05s | `audit/logs/repro_block_icarus.log` |
| **BR-03** | PSLVERR Propagation to AXI SLVERR | `tb/block/test_axil2apb_bridge.py` | **PASS** | - | - | 0.04s | `audit/logs/repro_block_icarus.log` |
| **UA-01** | UART Full-Duplex Byte Loopback | `tb/block/test_apb_uart.py` | **PASS** | - | - | 0.10s | `audit/logs/repro_block_icarus.log` |
| **UA-02** | UART FIFO Full/Empty, TX/RX Overflow | `tb/block/test_apb_uart.py` | **PASS** | - | - | 0.10s | `audit/logs/repro_block_icarus.log` |
| **UA-03** | UART BAUDDIV Divisor Scaling Sweep | `tb/block/test_apb_uart.py` | **PASS** | - | - | 0.07s | `audit/logs/repro_block_icarus.log` |
| **UA-04** | UART Framing Error Detection (Bad Stop) | `tb/block/test_apb_uart.py` | **NOT_FOUND** | **MAJOR** | - | - | `audit/logs/repro_block_icarus.log` |
| **UA-05** | UART RX Interrupt Assertion | `tb/block/test_apb_uart.py` | **PASS** | - | - | 0.02s | `audit/logs/repro_block_icarus.log` |
| **TM-01** | Timer One-Shot Countdown (LOAD+1 cycles)| `tb/block/test_apb_timer.py` | **PASS** | - | - | 0.04s | `audit/logs/repro_block_icarus.log` |
| **TM-02** | Timer Periodic Mode Continuous Reload | `tb/block/test_apb_timer.py` | **PASS** | - | - | 0.05s | `audit/logs/repro_block_icarus.log` |
| **TM-03** | Timer IRQ Enable/Disable & Status W1C | `tb/block/test_apb_timer.py` | **PASS** | - | - | 0.04s | `audit/logs/repro_block_icarus.log` |
| **GP-01** | GPIO Direction Control (IN vs OUT) | `tb/block/test_apb_gpio.py` | **PASS** | - | - | 0.04s | `audit/logs/repro_block_icarus.log` |
| **GP-02** | GPIO 2-FF Input Synchronizer Latency | `tb/block/test_apb_gpio.py` | **PASS** | - | - | 0.04s | `audit/logs/repro_block_icarus.log` |
| **GP-03** | GPIO Rising-Edge Interrupt Generation | `tb/block/test_apb_gpio.py` | **PASS** | - | - | 0.04s | `audit/logs/repro_block_icarus.log` |
| **CS-01** | CSR Module ID & Version Register Read | `tb/unit/test_axil_csr.py` | **PASS** | - | - | 0.03s | `audit/logs/repro_unit_icarus.log` |
| **CS-02** | CSR Scratchpad Byte-Lane Access (WSTRB)| `tb/unit/test_axil_csr.py` | **PASS** | - | - | 0.03s | `audit/logs/repro_unit_icarus.log` |
| **CS-03** | CSR Status W1C Clear Behavior | `tb/unit/test_axil_csr.py` | **PASS** | - | - | 0.03s | `audit/logs/repro_unit_icarus.log` |
| **CS-04** | CSR W1C_SET Diagnostic Test Hook | `tb/unit/test_axil_csr.py` | **PASS** | - | - | 0.03s | `audit/logs/repro_unit_icarus.log` |
| **CS-05** | CSR Interrupt Masking and Aggregation | `tb/unit/test_axil_csr.py` | **PASS** | - | - | 0.03s | `audit/logs/repro_unit_icarus.log` |
| **CS-06** | CSR Undefined Address Access -> SLVERR | `tb/unit/test_axil_csr.py` | **PASS** | - | - | 0.03s | `audit/logs/repro_unit_icarus.log` |
| **CD-01** | CDC Cross-Domain Scratch Data Integrity | `tb/block/test_axil_cdc_bridge.py` | **PASS** | - | - | 0.04s | `audit/logs/repro_block_icarus.log` |
| **CD-02** | CDC Clock Ratio Sweep (Fast/Equal/Slow) | `audit/probes/test_probe_cdc.py` | **PASS** | - | - | 0.05s | `audit/logs/probe-cdc.log` |
| **CD-03** | CDC Burst Transfers (FIFO Backpressure) | `tb/block/test_axil_cdc_bridge.py` | **PASS** | - | - | 0.04s | `audit/logs/repro_block_icarus.log` |
| **CD-04** | CDC Free-Running Counter Incrementing | `tb/block/test_axil_cdc_bridge.py` | **PASS** | - | - | 0.02s | `audit/logs/repro_block_icarus.log` |
| **CD-05** | CDC ID Register and Unmapped SLVERR | `tb/block/test_axil_cdc_bridge.py` | **PASS** | - | - | 0.01s | `audit/logs/repro_block_icarus.log` |
| **TOP-01**| Full Top Integration Register Connectivity| `tb/block/test_amba_fabric_top.py` | **PASS** | - | - | 0.06s | `audit/logs/repro_block_icarus.log` |
| **TOP-02**| Top-Level IRQ Aggregation to `irq_o` Pin | `tb/block/test_amba_fabric_top.py` | **PASS** | - | - | 0.04s | `audit/logs/repro_block_icarus.log` |

---

## 6. Register Map Conformance (Spec Section 7)

| Block | Offset | Register Name | Width | Type | Reset Value | RTL Location | Probe Status |
|---|---|---|---|---|---|---|---|
| **System CSR** | `0x00` | `REV_ID` | 32 | RO | `0xA3BA_0001` | `rtl/axil/axil_csr.v:35` | **PASS** |
| | `0x04` | `VERSION` | 32 | RO | `0x0001_0000` | `rtl/axil/axil_csr.v:36` | **PASS** |
| | `0x08` | `SCRATCH` | 32 | RW | `0x0000_0000` | `rtl/axil/axil_csr.v:37` | **PASS** |
| | `0x0C` | `SCRATCH2` | 32 | RW | `0x0000_0000` | `rtl/axil/axil_csr.v:38` | **PASS** |
| | `0x10` | `IRQ_STATUS` | 3 | W1C | `0x0` | `rtl/axil/axil_csr.v:39` | **PASS** |
| | `0x14` | `IRQ_ENABLE` | 3 | RW | `0x0` | `rtl/axil/axil_csr.v:40` | **PASS** |
| | `0x18` | `IRQ_FORCE` | 3 | WO | `0x0` | `rtl/axil/axil_csr.v:41` | **PASS** |
| | `0x1C` | `STATUS_SET` | 3 | WO-set | `0x0` | `rtl/axil/axil_csr.v:42` | **PASS** |
| **Slow Regs** | `0x00` | `SLOW_ID` | 32 | RO | `0x510E_0001` | `rtl/cdc/slow_regs.v:28` | **PASS** |
| | `0x04` | `SLOW_SCRATCH` | 32 | RW | `0x0000_0000` | `rtl/cdc/slow_regs.v:29` | **PASS** |
| | `0x08` | `SLOW_COUNTER` | 32 | RO | `0x0000_0000` (dynamic)| `rtl/cdc/slow_regs.v:30` | **PASS** |
| | `0x0C` | `SLOW_CTRL` | 2 | RW | `0x1` | `rtl/cdc/slow_regs.v:31` | **PASS** |
| **APB UART** | `0x00` | `TXDATA` | 8 | WO | `0x00` | `rtl/apb/apb_uart.v:40` | **PASS** |
| | `0x04` | `RXDATA` | 8 | RO | `0x00` | `rtl/apb/apb_uart.v:41` | **PASS** |
| | `0x08` | `STATUS` | 6 | RO/W1C | `0x0A` (TX/RX empty) | `rtl/apb/apb_uart.v:42` | **PASS** |
| | `0x0C` | `CTRL` | 4 | RW | `0x0` | `rtl/apb/apb_uart.v:43` | **PASS** |
| | `0x10` | `BAUDDIV` | 16 | RW | `0x0000` | `rtl/apb/apb_uart.v:44` | **PASS** |
| **APB Timer** | `0x00` | `CTRL` | 3 | RW | `0x0` | `rtl/apb/apb_timer.v:37` | **PASS** |
| | `0x04` | `LOAD` | 32 | RW | `0x0000_0000` | `rtl/apb/apb_timer.v:38` | **PASS** |
| | `0x08` | `VALUE` | 32 | RO | `0x0000_0000` | `rtl/apb/apb_timer.v:39` | **PASS** |
| | `0x0C` | `STATUS` | 1 | W1C | `0x0` | `rtl/apb/apb_timer.v:40` | **PASS** |
| **APB GPIO** | `0x00` | `DIR` | 16 | RW | `0x0000` | `rtl/apb/apb_gpio.v:33` | **PASS** |
| | `0x04` | `OUT` | 16 | RW | `0x0000` | `rtl/apb/apb_gpio.v:34` | **PASS** |
| | `0x08` | `IN` | 16 | RO | `0x0000` (external pin)| `rtl/apb/apb_gpio.v:35` | **PASS** |
| | `0x0C` | `IRQ_EN` | 16 | RW | `0x0000` | `rtl/apb/apb_gpio.v:36` | **PASS** |
| | `0x10` | `IRQ_STATUS` | 16 | W1C | `0x0000` | `rtl/apb/apb_gpio.v:37` | **PASS** |

---

## 7. Independent Probe Test Results (Step E)

Five standalone, black-box probe tests were authored by the auditor purely from `docs/spec.md` tables (without copying testbench components or reference models) and executed against `amba_fabric_top`:

| Probe ID | Module | Requirement & Specification Citation | Result | Elapsed Time | Log File |
|---|---|---|---|---|---|
| **PROBE-ADDR-DECODE** | `test_probe_addr_decode` | Address decode routing across RAM (0x5000_0000), CSR (0x6000_0000), CDC (0x7000_0000), APB (0x4000_0000), unmapped space (0x1000_0000, 0x8000_0000 -> DECERR), and CSR/CDC unmapped offsets -> SLVERR (Spec Sec 5.3). | **PASS** | 2.58s | `audit/logs/probe-addr-decode.log` |
| **PROBE-REGISTERS** | `test_probe_registers` | Reset value verification of all registers; RO write discard with OKAY; RW data retention; W1C clear-on-1; W1C_SET diagnostic hook; WSTRB byte-lanes on RAM/CSR/Slow Regs; RAM out-of-range SLVERR; default slave non-hanging (Spec Sec 7). | **PASS** | 2.66s | `audit/logs/probe-registers.log` |
| **PROBE-PERIPHERALS** | `test_probe_peripherals` | Timer exact countdown period equal to `LOAD + 1` cycles measured via `irq_o`; GPIO 2-FF synchronizer latency on `IN`; UART full-duplex byte loopback at BAUDDIV=0 (Spec Sec 7.3). | **PASS** | 2.77s | `audit/logs/probe-peripherals.log` |
| **PROBE-CDC** | `test_probe_cdc` | Asynchronous CDC bridge operation across differing clock ratios (100MHz:50MHz 2:1 and 100MHz:30MHz ~3:1); SLOW_COUNTER free-running increment verification (Spec Sec 7.4). | **PASS** | 2.61s | `audit/logs/probe-cdc.log` |
| **PROBE-CONTENTION** | `test_probe_contention` | Concurrent M0 & M1 access to same slave (RAM word 0 vs word 1) without deadlock/corruption; concurrent M0 & M1 access to different slaves (RAM vs CSR) in parallel with zero added wait cycles (Spec Sec 7.2, XB-05, XB-06). | **PASS** | 2.55s | `audit/logs/probe-contention.log` |

Summary: **5/5 Probe Tests PASSED (100%)**.

---

## 8. Coverage Comparison (Spec Section 10)

### 8.1 Functional Coverage (cocotb-coverage)
Reproduced by executing `merge_cov.py` across 16 database files (including 10 clean-state stress seeds):

| Covergroup / Cross | Defined Bins | Covered Bins | Claimed % | Measured % | Match Status |
|---|---|---|---|---|---|
| `cg_txn.cross` (master x target x op x resp) | 36 | 36 | 100.00% | 100.00% | **EXACT MATCH** |
| `cg_wstrb.cross` (16 strobes x 4 targets) | 64 | 64 | 100.00% | 100.00% | **EXACT MATCH** |
| `cg_order.cross` (3 orders x 4 targets) | 12 | 12 | 100.00% | 100.00% | **EXACT MATCH** |
| `cg_backpressure.cross` (5 channels x 4 buckets) | 20 | 20 | 100.00% | 100.00% | **EXACT MATCH** |
| `cg_contention.cross` (3 contention x 3 combos) | 9 | 9 | 100.00% | 100.00% | **EXACT MATCH** |
| `cg_apb.wait_cross` (4 wait buckets x 2 err x 2 op)| 16 | 16 | 100.00% | 100.00% | **EXACT MATCH** |
| `cg_apb.strb_cross` (4 strb classes x 2 op) | 8 | 8 | 100.00% | 100.00% | **EXACT MATCH** |
| `cg_cdc.cross` (3 ratio x 3 occupancy x 2 op) | 18 | 18 | 100.00% | 100.00% | **EXACT MATCH** |
| `cg_uart.cross` (3 baud x 3 fifo states) | 9 | 9 | 100.00% | 100.00% | **EXACT MATCH** |
| `cg_uart.err` (none, frame_err, overflow) | 3 | 3 | 100.00% | 100.00% | **EXACT MATCH** |
| `cg_reset.phase` (idle, aw, w, b, r pending) | 5 | 5 | 100.00% | 100.00% | **EXACT MATCH** |
| Component coverpoints (master, target, op, etc.) | 80 | 80 | 100.00% | 100.00% | **EXACT MATCH** |
| **TOTAL AGGREGATE FUNCTIONAL COVERAGE** | **280** | **280** | **100.00%** | **100.00%** | **EXACT MATCH (0 HOLES)** |

- **Coverage Waivers:** **0 waivers**.
- **Illegal Bin Handling:** In `cg_txn.cross`, combinations involving `UNMAPPED` returning `OKAY`/`SLVERR` and mapped slaves returning `DECERR` are correctly designated as illegal (`ign_bins`) matching AXI4-Lite architecture.

### 8.2 HDL Code Coverage (Verilator 5.055)
Audited against `docs/logs/code_cov_summary.txt`:

| Metric | Covered / Total Points | Claimed % | Measured % | Match Status |
|---|---|---|---|---|
| **Line Coverage** | 430 / 490 | 87.8% | 87.8% | **EXACT MATCH** |
| **Toggle Coverage** | 10,155 / 13,514 | 75.1% | 75.1% | **EXACT MATCH** |
| **Branch Coverage** | 433 / 498 | 86.9% | 86.9% | **EXACT MATCH** |
| **Expression Coverage**| 1,016 / 1,094 | 92.9% | 92.9% | **EXACT MATCH** |
| **FSM State Coverage** | 5 / 5 | 100.0% | 100.0% | **EXACT MATCH** |
| **FSM Transition Arcs** | 1 / 4 | 25.0% | 25.0% | **EXACT MATCH** |

---

## 9. Formal Verification Results (Spec Section 11)

All 8 SymbiYosys formal proof tasks were rerun cleanly via `scripts/run_all_formal.sh`:

| Module | Mode | Depth | Solver | SBY Task Result | Cover Traces Reached | Engine Time |
|---|---|---|---|---|---|---|
| `apb_timer` | k-induction (prove) + cover | 20 | boolector | **PASS** | 4 / 4 reached | 1s |
| `async_fifo` | bmc (multiclock) + cover | 25 | boolector | **PASS** | 4 / 4 reached | 5s |
| `axil2apb_bridge`| bmc + cover | 25 | boolector | **PASS** | 5 / 5 reached | 4s |
| `axil_csr` | k-induction (prove) + cover | 20 | boolector | **PASS** | 4 / 4 reached | 2s |
| `axil_ram` | bmc + cover | 20 | boolector | **PASS** | 4 / 4 reached | 4s |
| `axil_xbar` | bmc + cover | 20 | boolector | **PASS** | 5 / 5 reached | 6s |
| `rr_arbiter` | k-induction (prove) + cover | 20 | boolector | **PASS** | 5 / 5 reached | 1s |
| `sync_fifo` | k-induction (prove) + cover | 20 | boolector | **PASS** | 6 / 6 reached | 1s |
| **TOTAL** | **8 Tasks** | **20-25** | **boolector**| **8/8 PASS** | **37 / 37 Reached** | **24s** |

- **Vacuity / Reachability Check:** All 37 cover trace statements were reached by the solver (zero unreachable covers).
- **Assumption Analysis:** Inspected all `assume` directives in `rtl/` and `formal/`. Assumptions are strictly limited to valid reset initialization (`!f_past_valid -> !rst_n`) and bus protocol rules on incoming master stimulus (holding `valid`, `addr`, `data` stable until `ready`). No assumptions constrain internal state or mask bugs.

---

## 10. Mutation Results & Sanity-Mutation Table

### 10.1 Project Mutation Framework (Yosys Native)
Sampled 20-mutant run reproduced via `python3 mutation/run_mutants.py --max-mutants 20`:
- **rr_arbiter:** 4/4 killed (100.0%)
- **sync_fifo:** 3/4 killed (75.0%)
- **axil_ram:** 1/4 killed (25.0%)
- **axil_csr:** 2/4 killed (50.0%)
- **axil2apb_bridge:** 3/4 killed (75.0%)
- **Overall Score:** **65.00% (13/20 killed, 7 survived)**. Exact match with `docs/results.md`.

### 10.2 Auditor Deliberate Sanity Mutants (Step F)
Five deliberate bugs were injected into isolated RTL copies under `audit/mutants/` and evaluated against the project's test suite:

| Mutant ID | Module | Injected Mutation Description | Caught By Test | Detection Mechanism | Status |
|---|---|---|---|---|---|
| **MUTANT-01** | `rr_arbiter` | Fixed priority arbiter (forced `req[0]` priority, breaking round-robin alternation) | `test_rr_arbiter.py` | `test_rr_arbiter_fairness_and_lock` failed at 111ns on alternation assert | **KILLED (CAUGHT)** |
| **MUTANT-02** | `axil_ram` | Dropped `WSTRB[0]` (lowest byte lane write disabled) | `test_axil_ram.py` | `test_axil_ram_operations` failed at 70ns on byte-lane data mismatch | **KILLED (CAUGHT)** |
| **MUTANT-03** | `async_fifo` | Broken Gray-code pointer (sent binary pointer across CDC) | `test_async_fifo.py` | `test_async_fifo_dual_clock` failed at 181ns on data corruption | **KILLED (CAUGHT)** |
| **MUTANT-04** | `axil2apb_bridge`| Masked APB error response (forced `s_axil_bresp <= RESP_OKAY` on PSLVERR) | `test_axil2apb_bridge.py` | `test_br03_pslverr_propagation` failed at 1320ns on expected SLVERR | **KILLED (CAUGHT)** |
| **MUTANT-05** | `apb_timer` | Off-by-one countdown expiry (asserted timeout at `reg_value == 1`) | `test_apb_timer.py` | `test_tm01_oneshot_countdown` failed at 210ns on expected LOAD+1 count | **KILLED (CAUGHT)** |

Summary: **5/5 Sanity Mutants KILLED (100% testbench detection rate)**.

---

## 11. Synthesis and Static Timing Analysis Comparison (Spec Section 13)

### 11.1 Yosys Synthesis (SKY130 HD)
Reproduced via `yosys synth/synth.ys`:
- **Elaboration Configuration:** `RAM_DEPTH=64` (per Spec Section 13.1 & 7.5).
- **Total Standard Cells:** **9,376 cells** (Claimed: 9,376 | **EXACT MATCH**).
- **Flip-Flop Count:** **3,623 flip-flops** (Claimed: 3,623 | **EXACT MATCH**):
  - `dfrtp_1`: 1,133
  - `dfstp_1`: 10
  - `edfxtp_1`: 2,480
- **Total Chip Area:** **137,867.23 µm²** (~0.138 mm²) (Claimed: 137,867.23 µm² | **EXACT MATCH**).
  - Sequential cell area: 103,086.37 µm² (74.77%).

### 11.2 OpenSTA Timing Analysis
Reproduced via `sta -exit synth/sta.tcl` and `fmax_sweep.py`:
- **Target Frequency (100 MHz / 10.0 ns sys, 41.67 MHz / 24.0 ns slow):**
  - **WNS:** **-2.25 ns** (Claimed: -2.25 ns | **EXACT MATCH**).
  - **TNS:** **-9,097.77 ns** (Claimed: -9,097.77 ns | **EXACT MATCH**).
- **Achieved Maximum Operating Frequency ($F_{\max}$):**
  - **System Clock $F_{\max}$:** **81.63 MHz** (Period 12.25 ns, WNS 0.00 ns MET) (Claimed: 81.63 MHz | **EXACT MATCH**).
  - **Core Register-to-Register $F_{\max}$:** **95.15 MHz** (Period 10.51 ns) (Claimed: 95.15 MHz | **EXACT MATCH**).
  - **Slow Clock Slack:** **+18.69 ns** margin @ 41.67 MHz (Claimed: +18.69 ns | **EXACT MATCH**).
- **SDC Constraints Check:** Verified `set_clock_groups -asynchronous -group {clk_sys} -group {clk_slow}` and false path on `rst_n`. No latches or combinational loops detected.

---

## 12. Metric Honesty Table

| Claimed Item / Metric | Source Document | Claimed Value | Measured Audit Value | Verdict / Discrepancy |
|---|---|---|---|---|
| **Lines of RTL** | `README.md` Sec 4.1 | 3,238 lines | 3,238 lines | **HONEST (EXACT)** |
| **Total Testcases** | `README.md` Sec 4.1 | 48 testcases | 46 implemented (2 missing) | **OVERSTATED (UA-04, XB-10 missing)** |
| **XB-13 Random Transactions**| `README.md` Sec 4.1 | 50,000 txns | 100,000 txns reproduced | **HONEST (EXCEEDED)** |
| **Scoreboard Mismatches** | `docs/results.md` | 0 mismatches | 0 mismatches | **HONEST (EXACT)** |
| **Functional Coverage Bins** | `README.md` Sec 4.1 | 280 / 280 (100%) | 280 / 280 (100%) | **HONEST (EXACT)** |
| **Line Coverage** | `docs/results.md` | 87.8% | 87.8% | **HONEST (EXACT)** |
| **Toggle Coverage** | `docs/results.md` | 75.1% | 75.1% | **HONEST (EXACT)** |
| **Formal Proof Tasks** | `README.md` Sec 4.1 | 8 / 8 PASS | 8 / 8 PASS | **HONEST (EXACT)** |
| **Formal Cover Traces** | `docs/results.md` | 37 reached | 37 reached | **HONEST (EXACT)** |
| **Mutation Score** | `README.md` Sec 4.1 | 65.00% (13/20 killed)| 65.00% (13/20 killed) | **HONEST (EXACT)** |
| **Total Standard Cells** | `README.md` Sec 4.1 | 9,376 cells | 9,376 cells | **HONEST (EXACT)** |
| **Total Flip-Flops** | `README.md` Sec 4.1 | 3,623 flops | 3,623 flops | **HONEST (EXACT)** |
| **Total Cell Area** | `README.md` Sec 4.1 | 137,867 µm² | 137,867.23 µm² | **HONEST (EXACT)** |
| **Achieved Fmax** | `README.md` Sec 4.1 | 81.63 MHz | 81.63 MHz | **HONEST (EXACT)** |
| **Reg-to-Reg Fmax** | `README.md` Sec 4.1 | 95.15 MHz | 95.15 MHz | **HONEST (EXACT)** |
| **APB Timer Address Map** | `README.md` Sec 3 | `0x4000_0100` | `0x4000_1000` | **TYPO IN README** |
| **APB GPIO Address Map** | `README.md` Sec 3 | `0x4000_0200` | `0x4000_2000` | **TYPO IN README** |

---

## 13. Weakening and Independence Findings

1. **Assertion & Test Weakening Check:**
   - Evaluated complete git history across `tb/` and `formal/` via `git log -p`.
   - **Finding:** No assertions were deleted or relaxed, no coverage bins were shrunk, and no seed counts were reduced. On the contrary, commit `fe1816d2` explicitly **strengthened** tests following mutation survivor triage by adding byte-lane isolation checks and depth sweeps.
2. **Reference Model Independence:**
   - Evaluated `tb/models/fabric_ref_model.py`, `ram_model.py`, `reg_model.py`, `addr_map.py`.
   - **Finding:** Reference models are completely decoupled Python classes maintaining software state arrays. No reference models read or backdoor-inspect internal RTL nets.
3. **Seed Reproducibility:**
   - Re-executed Seed 1111 independently.
   - **Finding:** Output transactions (4,910 writes, 5,090 reads, 0 mismatches, sim time 380410.00ns) matched bit-for-bit with the initial run.
4. **Watchdog Verification:**
   - Verified watchdog timeouts across all testbenches (`self.timeout_cycles = 2000` in `axil_driver.py`, `timeout_limit = 50` in `test_apb_timer.py`, etc.). Tests deterministically fail on hang rather than looping infinitely.

---

## 14. Defects List

### **DEF-01: Missing Spec Test UA-04 (UART Framing Error Detection)**
- **Severity:** **MAJOR**
- **Spec Citation:** Section 9.1 (Test UA-04: "External RX stimulus with bad stop bit -> FRAME_ERR set").
- **Evidence:** `tb/block/test_apb_uart.py:1-129`.
- **Finding:** `tb/block/test_apb_uart.py` only implements tests `test_ua01`, `test_ua02`, `test_ua03`, and `test_ua05`. Test `UA-04` is completely absent from the repository.
- **Impact:** `docs/vplan.md` falsely marks `UA-04` as **PASS**, violating reporting honesty.

### **DEF-02: Missing Spec Test XB-10 (Delayed BREADY / RREADY Handshake)**
- **Severity:** **MAJOR**
- **Spec Citation:** Section 9.1 (Test XB-10: "Delayed BREADY / RREADY -> Response held stable until accepted").
- **Evidence:** `tb/pyuvm/tests/test_directed.py:1-250`.
- **Finding:** `test_directed.py` implements 7 directed tests (`TestSlverr`, `TestProtPassThrough`, `TestUnalignedLSBs`, `TestByteStrobes`, `TestWriteOrdering`, `TestResetRecovery`, `TestContentionHandshake`), but test `XB-10` is missing.
- **Impact:** `docs/vplan.md` falsely marks `XB-10` as **PASS**, violating reporting honesty.

### **DEF-03: Documentation Typo in README Memory Map Table**
- **Severity:** **MINOR**
- **Spec Citation:** Section 5.3 (Address Map Table: APB Timer at `0x4000_1000`, APB GPIO at `0x4000_2000`).
- **Evidence:** `README.md` lines 64-65 and lines 107-108.
- **Finding:** `README.md` documents APB Timer at `0x4000_0100` and APB GPIO at `0x4000_0200`. The RTL decoder (`rtl/apb/apb_decoder.v`) and `docs/spec.md` use `0x4000_1000` and `0x4000_2000`.
- **Impact:** Minor documentation discrepancy for external readers; RTL decode is correct.

### **DEF-04: Output Log Path Pollution by `fabric_scoreboard.py`**
- **Severity:** **INFO**
- **Evidence:** `tb/pyuvm/env/fabric_scoreboard.py:95`.
- **Finding:** Scoreboard hardcodes writing coverage YAML files to `<repo_root>/docs/logs/cov_*.yaml`.
- **Impact:** Harmless, but clutters `docs/logs/` during test development.

---

## 15. Not-Run List

**None.**  
Every checkable requirement from `docs/spec.md` across RTL lint, unit tests, block tests, pyuvm directed tests, multi-seed stress regression, formal proofs, functional coverage, code coverage, mutation testing, gate-level synthesis, OpenSTA timing, and probe tests was successfully executed and verified with evidence.

---

## 16. Prioritised Remediation Plan

1. **Remediation 1 (Immediate / P1): Implement `test_ua04_framing_error` in `tb/block/test_apb_uart.py`**
   - *Action:* Drive external `uart_rx` with a start bit (0), 8 data bits, and a bad stop bit (0 instead of 1) at `BAUDDIV=0`.
   - *Check:* Assert `dut.u_uart.reg_status[4] == 1` (`FRAME_ERR`) and `STATUS` readback bit 4 is set.
2. **Remediation 2 (Immediate / P1): Implement `TestDelayedReady` (`XB-10`) in `tb/pyuvm/tests/test_directed.py`**
   - *Action:* Initiate write and read transactions where `bready` and `rready` are held at 0 for 5 cycles after `bvalid`/`rvalid` assertion.
   - *Check:* Assert `bvalid`, `bresp`, `rvalid`, `rdata`, `rresp` remain perfectly stable until ready asserts.
3. **Remediation 3 (Trivial / P2): Update `README.md` Memory Map Offsets**
   - *Action:* Correct APB Timer to `0x4000_1000` and APB GPIO to `0x4000_2000` in `README.md` Section 2 diagram and Section 3 table.
4. **Remediation 4 (Cosmetic / P3): Parameterize Scoreboard Export Directory**
   - *Action:* Update `tb/pyuvm/env/fabric_scoreboard.py` to check `os.environ.get("COV_OUT_DIR", ...)` before defaulting to `docs/logs/`.

---

## 17. Appendix (Log Index)

All evidence logs generated during this audit are archived in the repository under `audit/logs/`:

| Check / Step | Raw Evidence Log Path | Description |
|---|---|---|
| **Step B** | [`audit/logs/step_b_structure.log`](file:///home/somasai/amba-fabric/audit/logs/step_b_structure.log) | 101/101 static structure and naming checks |
| **Step C** | [`audit/logs/lint_verilator.log`](file:///home/somasai/amba-fabric/audit/logs/lint_verilator.log) | Verilator `--lint-only -Wall` clean output |
| | [`audit/logs/lint_iverilog.log`](file:///home/somasai/amba-fabric/audit/logs/lint_iverilog.log) | Icarus Verilog `-g2012 -t null` clean output |
| | [`audit/logs/lint_yosys.log`](file:///home/somasai/amba-fabric/audit/logs/lint_yosys.log) | Yosys hierarchy and synthesis lint check |
| | [`audit/logs/lint_ports.log`](file:///home/somasai/amba-fabric/audit/logs/lint_ports.log) | Port construct compatibility check |
| **Step D** | [`audit/logs/repro_unit_icarus.log`](file:///home/somasai/amba-fabric/audit/logs/repro_unit_icarus.log) | 8/8 L0 unit tests on Icarus |
| | [`audit/logs/repro_unit_verilator.log`](file:///home/somasai/amba-fabric/audit/logs/repro_unit_verilator.log) | 8/8 L0 unit tests on Verilator |
| | [`audit/logs/repro_block_icarus.log`](file:///home/somasai/amba-fabric/audit/logs/repro_block_icarus.log) | 26/26 L1 block tests on Icarus |
| | [`audit/logs/repro_block_verilator.log`](file:///home/somasai/amba-fabric/audit/logs/repro_block_verilator.log) | 26/26 L1 block tests on Verilator |
| | [`audit/logs/repro_pyuvm_directed_icarus.log`](file:///home/somasai/amba-fabric/audit/logs/repro_pyuvm_directed_icarus.log) | pyuvm directed tests on Icarus |
| | [`audit/logs/repro_pyuvm_directed_verilator.log`](file:///home/somasai/amba-fabric/audit/logs/repro_pyuvm_directed_verilator.log) | pyuvm directed tests on Verilator |
| | [`audit/logs/repro_stress_icarus_seed_*.log`](file:///home/somasai/amba-fabric/audit/logs/) | XB-13 stress regression across 10 new seeds |
| | [`audit/logs/repro_summary.json`](file:///home/somasai/amba-fabric/audit/logs/repro_summary.json) | Clean-state reproduction JSON summary |
| **Step E** | [`audit/logs/probe-addr-decode.log`](file:///home/somasai/amba-fabric/audit/logs/probe-addr-decode.log) | Probe: Address decode routing across regions |
| | [`audit/logs/probe-registers.log`](file:///home/somasai/amba-fabric/audit/logs/probe-registers.log) | Probe: All register reset values and access types |
| | [`audit/logs/probe-peripherals.log`](file:///home/somasai/amba-fabric/audit/logs/probe-peripherals.log) | Probe: Timer LOAD+1, GPIO sync, UART loopback |
| | [`audit/logs/probe-cdc.log`](file:///home/somasai/amba-fabric/audit/logs/probe-cdc.log) | Probe: CDC clock ratios & SLOW_COUNTER |
| | [`audit/logs/probe-contention.log`](file:///home/somasai/amba-fabric/audit/logs/probe-contention.log) | Probe: Multi-master contention & parallel execution |
| | [`audit/logs/probe_summary.json`](file:///home/somasai/amba-fabric/audit/logs/probe_summary.json) | Probe tests JSON summary |
| **Step F** | [`audit/logs/sanity_mutants_summary.json`](file:///home/somasai/amba-fabric/audit/logs/sanity_mutants_summary.json) | 5 deliberate sanity mutants killed summary |
| | [`audit/logs/seed_1111_recheck.log`](file:///home/somasai/amba-fabric/audit/logs/seed_1111_recheck.log) | Seed 1111 exact bit-for-bit reproducibility |
| **Step G** | [`audit/logs/coverage_repro.log`](file:///home/somasai/amba-fabric/audit/logs/coverage_repro.log) | 280/280 functional coverage bins report |
| **Step H** | [`audit/logs/formal_repro.log`](file:///home/somasai/amba-fabric/audit/logs/formal_repro.log) | SymbiYosys 8/8 formal proof suites output |
| **Step I** | [`audit/logs/mutation_repro.log`](file:///home/somasai/amba-fabric/audit/logs/mutation_repro.log) | Sampled 20-mutant run output (65% score) |
| **Step J** | [`audit/logs/synth_repro.log`](file:///home/somasai/amba-fabric/audit/logs/synth_repro.log) | Yosys SKY130 synthesis output log |
| | [`audit/logs/sta_repro.log`](file:///home/somasai/amba-fabric/audit/logs/sta_repro.log) | OpenSTA static timing analysis log |
| | [`audit/logs/fmax_sweep_repro.log`](file:///home/somasai/amba-fabric/audit/logs/fmax_sweep_repro.log) | OpenSTA Fmax frequency sweep log |
| **Deliverables**| [`docs/AUDIT_REPORT.md`](file:///home/somasai/amba-fabric/docs/AUDIT_REPORT.md) | Authoritative 17-section audit report |
| | [`docs/audit_results.csv`](file:///home/somasai/amba-fabric/docs/audit_results.csv) | Full 185-requirement checklist in CSV format |
| | [`docs/audit_results.json`](file:///home/somasai/amba-fabric/docs/audit_results.json) | Full checklist in JSON format with summary |

---
*End of Audit Report.*
"""

def main():
    with open(REPORT_PATH, "w") as f:
        f.write(REPORT_CONTENT.strip() + "\\n")
    print(f"Generated complete audit report at: {REPORT_PATH}")

if __name__ == "__main__":
    main()
