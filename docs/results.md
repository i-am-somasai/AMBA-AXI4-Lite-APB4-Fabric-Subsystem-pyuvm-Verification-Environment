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
| Functional Coverage (Bins Hit / Total) | 100.00% (280/280 bins hit, 0 holes across all Section 10 covergroups) | Section 10 (100% goal) | `docs/logs/func_cov.log` |
| Code Coverage (Verilator Line / Toggle) | Line: 87.8% (430/490), Toggle: 75.1% (10,155/13,514), Branch: 86.9% (433/498), Expr: 92.9% (1,016/1,094), FSM State: 100.0% (5/5) | Section 10 | `docs/logs/code_cov_summary.txt`, `docs/logs/code_cov/` |
| Formal Properties Proven / BMC Depth | 8/8 modules proven (100% PASS), 37 cover traces reached: `apb_timer` (k-induction depth 20, 4 covers), `async_fifo` (BMC depth 25, 4 covers), `axil2apb_bridge` (BMC depth 25, 5 covers), `axil_csr` (k-induction depth 20, 4 covers), `axil_ram` (BMC depth 20, 4 covers), `axil_xbar` (BMC depth 20, 5 covers), `rr_arbiter` (k-induction depth 20, 5 covers), `sync_fifo` (k-induction depth 20, 6 covers) | Section 11 | `docs/logs/formal_suite.log` |
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

### Phase 5: Coverage and Formal Closure
- **Date Completed:** 2026-11-24
- **Gate Command:** `make formal && make cov-report`
- **Status:** **PASS**
  - **Formal Verification (8/8 Modules PASS, 37 Cover Scenarios Reached):**
    | Module | Mode | Depth | Solver | Result | Cover Traces |
    |---|---|---|---|---|---|
    | `apb_timer` | k-induction (prove) + cover | 20 | boolector | **PASS** | 4 traces reached |
    | `async_fifo` | bmc (multiclock) + cover | 25 | boolector | **PASS** | 4 traces reached |
    | `axil2apb_bridge` | bmc + cover | 25 | boolector | **PASS** | 5 traces reached |
    | `axil_csr` | k-induction (prove) + cover | 20 | boolector | **PASS** | 4 traces reached |
    | `axil_ram` | bmc + cover | 20 | boolector | **PASS** | 4 traces reached |
    | `axil_xbar` | bmc + cover | 20 | boolector | **PASS** | 5 traces reached |
    | `rr_arbiter` | k-induction (prove) + cover | 20 | boolector | **PASS** | 5 traces reached |
    | `sync_fifo` | k-induction (prove) + cover | 20 | boolector | **PASS** | 6 traces reached |
    - **Total:** 8/8 tasks passed, 0 failed.

  - **Functional Coverage (100.00% across all 9 Section 10 Covergroups, 0 Holes):**
    | Covergroup / Metric | Defined Bins | Covered Bins | Coverage % |
    |---|---|---|---|
    | `cg_txn.cross` (master x target x op x resp) | 36 | 36 | 100.00% |
    | `cg_wstrb.cross` (16 strobes x 4 targets) | 64 | 64 | 100.00% |
    | `cg_order.cross` (3 orders x 4 targets) | 12 | 12 | 100.00% |
    | `cg_backpressure.cross` (5 channels x 4 buckets) | 20 | 20 | 100.00% |
    | `cg_contention.cross` (3 contention x 3 op combos) | 9 | 9 | 100.00% |
    | `cg_apb.wait_cross` (4 wait buckets x 2 err x 2 op) | 16 | 16 | 100.00% |
    | `cg_apb.strb_cross` (4 strb classes x 2 op) | 8 | 8 | 100.00% |
    | `cg_cdc.cross` (3 ratio x 3 occupancy x 2 op) | 18 | 18 | 100.00% |
    | `cg_uart.cross` (3 baud x 3 fifo states) | 9 | 9 | 100.00% |
    | `cg_uart.err` (none, frame_err, overflow) | 3 | 3 | 100.00% |
    | `cg_reset.phase` (idle, aw, w, b, r pending) | 5 | 5 | 100.00% |
    | Component coverpoints (master, target, op, resp, strb, order, channel, bucket, etc.) | 80 | 80 | 100.00% |
    | **TOTAL AGGREGATE COVERAGE** | **280** | **280** | **100.00%** |
    - Coverage Waivers: **None needed** (100% achieved).

  - **HDL Code Coverage (Verilator 5.055 Line / Toggle / Branch / Expr / FSM):**
    | Coverage Metric | Covered / Total Points | Percentage |
    |---|---|---|
    | Line Coverage | 430 / 490 | 87.8% |
    | Toggle Coverage | 10,155 / 13,514 | 75.1% |
    | Branch Coverage | 433 / 498 | 86.9% |
    | Expression Coverage | 1,016 / 1,094 | 92.9% |
    | FSM State Coverage | 5 / 5 | 100.0% |
    | FSM Transition Arc Coverage | 1 / 4 | 25.0% |
    - Annotation report generated for all 17 RTL modules in `docs/logs/code_cov/`.

- **Log References:**
  - `docs/logs/formal_suite.log`: SBY formal suite log (8/8 PASS)
  - `docs/logs/func_cov.log`: cocotb-coverage functional coverage log (100.00%)
  - `docs/logs/code_cov_summary.txt`: Verilator code coverage summary
  - `docs/logs/code_cov/`: Annotated RTL source files
- **Tag:** `phase-5-done`

