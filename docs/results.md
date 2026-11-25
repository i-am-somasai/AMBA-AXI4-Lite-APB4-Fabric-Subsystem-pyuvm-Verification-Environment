# Verification & Implementation Results

<!-- BEGIN:metrics:results_status_banner -->
This document records **real, measured results** generated strictly from [`docs/metrics.json`](metrics.json) (no hand-typed constants).
**Status:** R3 Release-Prep | **CI Status:** **PASS** ([run `45665895644`](https://github.com/i-am-somasai/AMBA-AXI4-Lite-APB4-Fabric-Subsystem-pyuvm-Verification-Environment/actions/runs/45665895644), commit `4bd08534f3a7ebb5f99c3322843b2703eab7ac96`, `4m 37s`: Covers check_no_synthetic_cov, check_bug_refs, check_docs_consistency, Verilator lint, L0 unit, L1 block, 3-seed Icarus regress, 17 sanity mutants, 10/10 formal, 24-mutant sampled mutation smoke, and artifact upload; SKY130 synthesis/STA, full 20-seed coverage, and the full 240-mutant run are local only). Raw tool logs are archived under [`docs/logs/`](logs/).
<!-- END:metrics:results_status_banner -->

---

## 1. Overall Metrics Summary

<!-- BEGIN:metrics:results_summary_table -->
| Metric | Measured Value | Spec Reference | Log / Source |
|---|---|---|---|
| RTL Modules / Non-Blank Non-Comment Lines | **17 modules / 3,200 lines** | Section 17 | [`docs/metrics.json`](metrics.json) |
| Test Definitions / XML Runs / Spec Map | **61 defs / 96 XML runs (96 PASS, 0 FAIL) / 40/40 PASS** | Section 9 | [`docs/test_map.csv`](test_map.csv), [`docs/vplan.md`](vplan.md) |
| Random Transactions Executed | **200,000** (Verilator seeds `1..20`, 0 mismatches) + **200,000** (Icarus seeds `601..620`, 0 mismatches) | Section 9.1 (XB-13) | [`docs/logs/phase_c_cov_report.log`](logs/phase_c_cov_report.log), [`docs/logs/regression_20seeds.log`](logs/regression_20seeds.log) |
| Functional Coverage | **100.00% (267/267 reachable)**, 36 waived, 24 merged YAMLs | Section 10 | [`docs/logs/func_cov.log`](logs/func_cov.log), [`docs/coverage_waivers.md`](coverage_waivers.md) |
| Code Coverage (Verilator) | **Line 92.4% \| Branch 91.6% \| Expr 93.8% \| Toggle 76.2% \| FSM State 100.0%** | Section 10 | [`docs/logs/code_cov_summary.txt`](logs/code_cov_summary.txt) |
| Formal Verification (SymbiYosys) | **10/10 suites PASS** (3 `k-induction (prove)`, 1 `PDR (prove)`, 1 `k-induction (prove) + BMC depth 20`, 5 `BMC depth 20..30`; 84 covers) | Section 11 | [`docs/logs/formal_suite.log`](logs/formal_suite.log) |
| CDC Sweeps | **3 periods (25.0 ns, 10.3 ns, 6.0 ns) × 3 phases**; formal depth 25 / 30 | Section 9.1 (CD-01) | [`docs/logs/func_cov.log`](logs/func_cov.log) |
| Mutation Testing (240 Frozen Mutants) | **Baseline 165/240 (68.75%) → Final 219/240 (91.25% raw / 98.21% conservative adj, 98.21% bounded-incl)**; Sanity Gate: **17/17 KILLED** | Section 12 | [`docs/mutation_report.md`](mutation_report.md), [`docs/logs/sanity.log`](logs/sanity.log) |
| Bugs Logged & Reference-Verified | **24 (`BUG-001`–`BUG-024`)** | Section 6 | [`docs/bugs.md`](bugs.md) |
| Synthesis (SKY130, `RAM_DEPTH=64`) | **9,237 cells / 3,630 flops (2,048 RAM) / 138,086.19 µm²** | Section 13 | [`docs/logs/synth.log`](logs/synth.log) |
| STA (100 MHz Target, OpenSTA) | **VIOLATED: WNS -18.60 ns / TNS -54046.39 ns / 34.97 MHz** (`62.89 MHz` datapath+I/O ref; `clk_slow` & hold MET) | Section 13 | [`docs/logs/sta.log`](logs/sta.log), [`docs/logs/fmax_sweep.log`](logs/fmax_sweep.log) |
| CI Status | **PASS** ([run `45665895644`](https://github.com/i-am-somasai/AMBA-AXI4-Lite-APB4-Fabric-Subsystem-pyuvm-Verification-Environment/actions/runs/45665895644), commit `4bd08534f3a7ebb5f99c3322843b2703eab7ac96`, `4m 37s`: Covers check_no_synthetic_cov, check_bug_refs, check_docs_consistency, Verilator lint, L0 unit, L1 block, 3-seed Icarus regress, 17 sanity mutants, 10/10 formal, 24-mutant sampled mutation smoke, and artifact upload; SKY130 synthesis/STA, full 20-seed coverage, and the full 240-mutant run are local only) | Section 14 | [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) |
<!-- END:metrics:results_summary_table -->

---

## 2. RTL Codebase Inventory (Non-Blank, Non-Comment Lines)

<!-- BEGIN:metrics:results_rtl_table -->
| Module | File | Non-Blank, Non-Comment Lines |
|---|---|---:|
| `amba_fabric_top` | `rtl/amba_fabric_top.v` | 365 |
| `apb_decoder` | `rtl/apb/apb_decoder.v` | 56 |
| `apb_gpio` | `rtl/apb/apb_gpio.v` | 89 |
| `apb_timer` | `rtl/apb/apb_timer.v` | 155 |
| `apb_uart` | `rtl/apb/apb_uart.v` | 450 |
| `axil2apb_bridge` | `rtl/apb/axil2apb_bridge.v` | 171 |
| `axil_csr` | `rtl/axil/axil_csr.v` | 278 |
| `axil_decoder` | `rtl/axil/axil_decoder.v` | 31 |
| `axil_default_slave` | `rtl/axil/axil_default_slave.v` | 78 |
| `axil_ram` | `rtl/axil/axil_ram.v` | 204 |
| `axil_xbar` | `rtl/axil/axil_xbar.v` | 424 |
| `axil_cdc_bridge` | `rtl/cdc/axil_cdc_bridge.v` | 383 |
| `slow_regs` | `rtl/cdc/slow_regs.v` | 107 |
| `async_fifo` | `rtl/common/async_fifo.v` | 151 |
| `rr_arbiter` | `rtl/common/rr_arbiter.v` | 102 |
| `rst_sync` | `rtl/common/rst_sync.v` | 19 |
| `sync_fifo` | `rtl/common/sync_fifo.v` | 137 |
| **TOTAL (17 modules)** | `rtl/**/*.v` | **3,200** |
<!-- END:metrics:results_rtl_table -->

---

## 3. Formal Verification Matrix (SymbiYosys + Boolector / ABC PDR)

<!-- BEGIN:metrics:results_formal_table -->
| Module | Proof / Checking Method | Depth | Result | Covers Reached | Runtime |
|---|---|---:|---|---:|---:|
| `apb_timer` | `k-induction (prove)` | 20 | **PASS** | 4 | 1s |
| `apb_uart` | `BMC depth 25` | 25 | **PASS** | 9 | 5s |
| `async_fifo` | `BMC depth 25, multiclock` | 25 | **PASS** | 4 | 8s |
| `axil2apb_bridge` | `PDR (prove, abc pdr)` | 25 | **PASS** | 10 | 3s |
| `axil_cdc_bridge` | `BMC depth 30, multiclock` | 30 | **PASS** | 5 | 82s |
| `axil_csr` | `k-induction (prove) + BMC depth 20` | 20 | **PASS** | 5 | 3s |
| `axil_ram` | `BMC depth 20` | 20 | **PASS** | 5 | 3s |
| `axil_xbar` | `BMC depth 20` | 20 | **PASS** | 31 | 43s |
| `rr_arbiter` | `k-induction (prove)` | 20 | **PASS** | 3 | 1s |
| `sync_fifo` | `k-induction (prove)` | 20 | **PASS** | 8 | 3s |
| **TOTAL** | **10 suites** | - | **10/10 PASS** | **84** | **152s** |
<!-- END:metrics:results_formal_table -->

---

## 4. Functional & Code Coverage Summary

### 4.1 Functional Coverage (`cocotb-coverage`, Merged Real Runs)

<!-- BEGIN:metrics:results_func_cov_table -->
| Covergroup | Leaf Sub-Metrics | Defined Pre-Waiver | Waived | Reachable Target | Covered | Coverage % |
|---|---:|---:|---:|---:|---:|---:|
| `cg_apb` | 6 | 36 | 3 | 33 | 33 | **100.00%** |
| `cg_backpressure` | 3 | 29 | 0 | 29 | 29 | **100.00%** |
| `cg_cdc` | 4 | 25 | 6 | 19 | 19 | **100.00%** |
| `cg_contention` | 3 | 15 | 3 | 12 | 12 | **100.00%** |
| `cg_order` | 3 | 19 | 0 | 19 | 19 | **100.00%** |
| `cg_reset` | 1 | 5 | 0 | 5 | 5 | **100.00%** |
| `cg_txn` | 5 | 72 | 24 | 48 | 48 | **100.00%** |
| `cg_uart` | 4 | 18 | 0 | 18 | 18 | **100.00%** |
| `cg_wstrb` | 3 | 84 | 0 | 84 | 84 | **100.00%** |
| **TOTAL** | **32** | **303** | **36** | **267** | **267** | **100.00%** |
<!-- END:metrics:results_func_cov_table -->

### 4.2 Verilator HDL Code Coverage

<!-- BEGIN:metrics:results_code_cov_table -->
| Verilator Code Coverage Metric | Covered Points | Total Points | Coverage % |
|---|---:|---:|---:|
| Line | 496 | 537 | **92.4%** |
| Branch | 501 | 547 | **91.6%** |
| Expression | 1,036 | 1,105 | **93.8%** |
| Toggle | 10,821 | 14,202 | **76.2%** |
| FSM State | 5 | 5 | **100.0%** |
| FSM Arc | 1 | 4 | **25.0%** |
<!-- END:metrics:results_code_cov_table -->

---

## 5. Mutation Testing Matrix (Frozen 240-Mutant Suite)

<!-- BEGIN:metrics:results_mutation_table -->
| Module | Gen | Baseline Kill / Score | Final Kill | Final Surv | Tmo | BldErr | Raw Score | Equiv | Adj. Score |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| `rr_arbiter` | 30 | 19/30 (63.33%) | 24 | 6 | 0 | 0 | 80.00% | 6 | **100.00% (24/24)** |
| `sync_fifo` | 30 | 25/30 (83.33%) | 29 | 1 | 0 | 0 | 96.67% | 1 | **100.00% (29/29)** |
| `async_fifo` | 30 | 18/30 (60.00%) | 30 | 0 | 0 | 0 | 100.00% | 0 | **100.00% (30/30)** |
| `axil_decoder` | 30 | 26/30 (86.67%) | 27 | 3 | 0 | 0 | 90.00% | 3 | **100.00% (27/27)** |
| `axil_ram` | 30 | 17/30 (56.67%) | 30 | 0 | 0 | 0 | 100.00% | 0 | **100.00% (30/30)** |
| `axil_csr` | 30 | 15/30 (50.00%) | 28 | 2 | 0 | 0 | 93.33% | 2 | **100.00% (28/28)** |
| `axil2apb_bridge` | 30 | 23/30 (76.67%) | 28 | 2 | 0 | 0 | 93.33% | 2 | **100.00% (28/28)** |
| `axil_xbar` | 30 | 22/30 (73.33%) | 23 | 7 | 0 | 0 | 76.67% | 3 | **85.19% (23/27)** |
| **TOTAL** | **240** | **165/240 (68.75%)** | **219** | **21** | **0** | **0** | **91.25%** | **17** | **98.21% (219/223)** |
<!-- END:metrics:results_mutation_table -->

---

## 6. Synthesis & OpenSTA Timing Summary (SKY130 HD)

<!-- BEGIN:metrics:results_synth_sta_section -->
- **Yosys SKY130 HD Synthesis (`RAM_DEPTH=64`, [`synth/synth.ys`](../synth/synth.ys)):**
  - Total Cells: **9,237**
  - Sequential Flip-Flops: **3,630** (`1,140` `dfrtp_1` + `10` `dfstp_1` + `2,480` `edfxtp_1`, including **2,048** RAM flops for `u_ram.mem[0..63]`)
  - Total Cell Area: **138,086.19 µm²** (`103,261.54 µm²` / **74.78%** sequential)
- **OpenSTA Timing Analysis (`100.00 MHz` / `10.00 ns` `clk_sys`, `41.67 MHz` / `24.00 ns` `clk_slow`):**
  - Full Timed Netlist (`rst_n -> rst_sync` false-pathed only; `rst_sys_n`/`rst_slow_n` recovery timed): **WNS = `-18.60 ns`**, **TNS = `-54046.39 ns`** (**`VIOLATED`**), achieved $F_{\max}$ = **`34.97 MHz` (`28.60 ns`)**.
  - Pre-Layout Bottleneck: Unbuffered reset net `rst_sys_n` driving `958` loads (`cap=3.46 pF`, `slew=29.27 ns`) violates reset recovery; `clk_sys` sync setup slack = `-15.48 ns`, `clk_slow` setup slack = **`+16.64 ns` (MET)**, min hold slack = **`+0.23 ns` (MET)**, `check_setup` unconstrained constant-1 endpoints = `5` (`DEC-011`).
  - Datapath + I/O Reference (`rst_sync` Q isolated in STA only): **WNS = `-5.89 ns`**, **TNS = `-16999.71 ns`**, achieved $F_{\max}$ = **`62.89 MHz` (`15.90 ns`)**; pure reg-to-reg worst slack = `-4.15 ns`.
<!-- END:metrics:results_synth_sta_section -->

---

## 7. Historical Archive (Superseded)

Initial Phases 0–4 bring-up logs are archived under `docs/logs/phase0_gate.log` .. `docs/logs/phase4_gate.log` for historical traceability only and are superseded by the R2 remediation measurements reported above (`docs/FIX_REPORT_R2.md`).
