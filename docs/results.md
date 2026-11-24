# Verification & Implementation Results

This document records **real, measured results** from actual tool execution.
**Non-negotiable rule:** No fabricated numbers. If a metric has not been measured yet, it is marked as "Not measured". Raw logs are archived in `docs/logs/`.

---

## 1. Overall Metrics Summary

| Metric | Measured Value | Spec Reference | Log Reference / Command |
|---|---|---|---|
| RTL Modules / Total Lines | 17 modules / 3238 lines | Section 17 | `find rtl/ -name "*.v" \| xargs wc -l` |
| Total Tests (Directed / Random) | 48 tests (8 L0 unit + 26 L1 block/top + 14 pyuvm directed across Icarus & Verilator: all PASS) | Section 9 | `docs/logs/phase3_gate.log`, `docs/logs/phase4_gate.log` |
| Random Transactions Executed | 50,000 transactions (5 seeds x 10,000 transactions, zero mismatches) | Section 9.1 (XB-13) | `docs/logs/xb13_stress.log`, `docs/logs/phase4_gate.log` |
| Multi-seed Regression Seeds Passed | 5/5 seeds (42, 123, 777, 2024, 9999: 100% PASS) | Section 9.1 (XB-13 Gate) | `docs/logs/xb13_stress.log` |
| Functional Coverage (Bins Hit / Total) | Not measured (Phase 5) | Section 10 (100% goal) | `docs/logs/func_cov.log` |
| Code Coverage (Verilator Line / Toggle) | Not measured (Phase 5) | Section 10 | `docs/logs/code_cov/` |
| Formal Properties Proven / BMC Depth | 4 modules proven (100% PASS), 19 cover traces reached: `rr_arbiter` (k-induction depth 20, 5 covers), `async_fifo` (BMC depth 25, 4 covers), `axil_xbar` (BMC depth 20, 5 covers), `axil2apb_bridge` (BMC depth 25, 5 covers) | Section 11 | `docs/logs/phase2_gate.log` |
| CDC Clock Ratios & Phases Swept | Not measured (Phase 3-4) | Section 9.1 (CD-01) | `docs/logs/cdc_sweep.log` |
| Mutants Generated / Killed / Score | Not measured (Phase 6) | Section 12 | `docs/logs/mutation_summary.log` |
| Crossbar Added Latency (Cycles) | 0 cycles added latency (measured in XB-06) | Section 7.2 (≤1 cycle) | `docs/img/contention.png`, `tb/block/test_axil_xbar.py` |
| Synthesis: Cell Count / Flop Count / Area | Not measured (Phase 6) | Section 13 (SKY130) | `synth/results/synth.log` |
| STA: Target Period / WNS / TNS / $F_{\max}$ | Not measured (Phase 6) | Section 13 (100 MHz target) | `synth/results/sta.log` |
| CI Status | In progress (Phase 6) | Section 14 | GitHub Actions workflow |

---

## 2. Acceptance Gate Records

### Phase 0: Setup and Contract
- **Date Completed:** 2026-11-23
- **Gate Command:** `make lint && make unit SIM=icarus && make unit SIM=verilator`
- **Status:** **PASS** (1/1 tests passed on both Icarus Verilog 14.0 and Verilator 5.055)
- **Artifacts:** `docs/interfaces.md` (FROZEN), `docs/vplan.md`, `Makefile`, `scripts/env.sh`
- **Tag:** `phase-0-done`

### Phase 1: Common Blocks and AXI-Lite Basics
- **Date Completed:** 2026-11-23
- **Gate Command:** `make lint && make unit SIM=icarus && make formal`
- **Status:** **PASS**
  - Verilator Lint: 9 modules clean, 0 warnings.
  - L0 Unit Tests: 8/8 PASS on Icarus Verilog; 8/8 PASS on Verilator.
  - Formal Verification: 2/2 modules PASS (`rr_arbiter`: k-induction depth 20; `async_fifo`: BMC depth 25, 4 cover traces).
- **Log Reference:** `docs/logs/phase1_gate.log`
- **Tag:** `phase-1-done`

### Phase 2: Crossbar and APB Bridge
- **Date Completed:** 2026-11-23
- **Gate Command:** `make lint && make unit SIM=icarus && make block SIM=icarus && make block SIM=verilator && make formal`
- **Status:** **PASS**
  - Verilator Lint: 13 RTL modules clean, 0 errors, 0 warnings.
  - L0 Unit Tests: 8/8 PASS on Icarus Verilog.
  - L1 Block Tests: 11/11 PASS on Icarus Verilog (`test_axil2apb_bridge` 3/3, `test_axil_xbar` 8/8); 11/11 PASS on Verilator 5.055.
  - Formal Verification: 4/4 modules PASS (`async_fifo` BMC depth 25, `axil2apb_bridge` BMC depth 25, `axil_xbar` BMC depth 20, `rr_arbiter` k-induction depth 20).
  - Waveform Artifacts: Contention waveform generated and verified (`docs/img/contention.png`, `docs/img/contention.vcd`).
- **Log Reference:** `docs/logs/phase2_gate.log`
- **Tag:** `phase-2-done`

### Phase 3: Peripherals, CDC, and Top Level
- **Date Completed:** 2026-11-23
- **Gate Command:** `make lint && make unit SIM=icarus && make block SIM=icarus && make block SIM=verilator && make formal`
- **Status:** **PASS**
  - Verilator Lint: 17 RTL modules clean, 0 errors, 0 warnings across entire SoC.
  - L0 Unit Tests: 8/8 PASS on Icarus Verilog (100%).
  - L1 Block & Subsystem Tests: 26/26 PASS on Icarus Verilog (100%):
    - `test_axil2apb_bridge`: 3/3 PASS (BR-01, BR-02, BR-03)
    - `test_axil_xbar`: 8/8 PASS (XB-01 through XB-08)
    - `test_apb_timer`: 3/3 PASS (TM-01, TM-02, TM-03)
    - `test_apb_gpio`: 3/3 PASS (GP-01, GP-02, GP-03)
    - `test_apb_uart`: 4/4 PASS (UA-01, UA-02, UA-03, UA-05)
    - `test_axil_cdc_bridge`: 3/3 PASS (CD-01, CD-04, CD-05)
    - `test_amba_fabric_top`: 2/2 PASS (TOP-01, TOP-02)
  - L1 Block & Subsystem Tests: 26/26 PASS on Verilator 5.055 (100%).
  - Formal Verification: 4/4 modules PASS (`async_fifo` BMC depth 25, `axil2apb_bridge` BMC depth 25, `axil_xbar` BMC depth 20, `rr_arbiter` k-induction depth 20).
  - Register Map Exercised: 100% of register-map entries across UART, Timer, GPIO, RAM, CSR, CDC Slow Regs, and Default Slave exercised and verified from both masters.
  - Interrupt Aggregation: UART, Timer, and GPIO interrupts verified propagating to top-level `irq_o` pin.
- **Log Reference:** `docs/logs/phase3_gate.log`
- **Tag:** `phase-3-done`

### Phase 4: pyuvm Environment
- **Date Completed:** 2026-11-24
- **Gate Command:** `bash scripts/run_phase4_gate.sh`
- **Status:** **PASS**
  - Directed pyuvm Tests (Icarus Verilog): 7/7 PASS (`test_directed.py`: TestSlverr, TestProtPassThrough, TestUnalignedLSBs, TestByteStrobes, TestWriteOrdering, TestResetRecovery, TestContentionHandshake).
  - Directed pyuvm Tests (Verilator 5.055): 7/7 PASS.
  - XB-13 Multi-Seed Stress Regression: 5/5 seeds PASS with **0 scoreboard mismatches**:
    - Seed 42: Total=10,000 (Writes=4,985, Reads=5,015, Mismatches=0)
    - Seed 123: Total=10,000 (Writes=5,005, Reads=4,995, Mismatches=0)
    - Seed 777: Total=10,000 (Writes=4,972, Reads=5,028, Mismatches=0)
    - Seed 2024: Total=10,000 (Writes=4,961, Reads=5,039, Mismatches=0)
    - Seed 9999: Total=10,000 (Writes=5,131, Reads=4,869, Mismatches=0)
    - **Total Random Transactions:** 50,000 transactions verified against independent reference models.
  - L0 Unit Regression: 8/8 PASS on Icarus Verilog.
  - L1 Block Regression: 26/26 PASS on Icarus Verilog.
  - Formal Verification: 4/4 SBY formal suites PASS (`async_fifo`, `axil2apb_bridge`, `axil_xbar`, `rr_arbiter`).
- **Log Reference:** `docs/logs/phase4_gate.log`, `docs/logs/xb13_stress.log`
- **Tag:** `phase-4-done`
