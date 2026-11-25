# Verification & Implementation Results

This document records **real, measured results** from actual tool execution generated from `docs/metrics.json`.
**Status:** Metrics are currently **being re-measured (see [`docs/FIX_REPORT_R2.md`](docs/FIX_REPORT_R2.md))**. Raw logs are archived in `docs/logs/`.

---

## 1. Overall Metrics Summary

| Metric | Measured Value | Spec Reference | Log Reference / Command |
|---|---|---|---|
| RTL Modules / Total Lines | being re-measured (see [`docs/FIX_REPORT_R2.md`](docs/FIX_REPORT_R2.md)) | Section 17 | `scripts/gen_metrics.py` |
| Total Tests (Directed / Random) | being re-measured (see [`docs/FIX_REPORT_R2.md`](docs/FIX_REPORT_R2.md)) | Section 9 | `docs/test_map.csv`, `docs/vplan.md` |
| Random Transactions Executed | **200,000 transactions** (20 seeds × 10,000 transactions, re-run after Phase A) | Section 9.1 (XB-13) | `docs/logs/regression_20seeds.log` |
| Multi-seed Regression Seeds Passed | **20/20 seeds** (being re-measured after Phase A; see [`docs/FIX_REPORT_R2.md`](docs/FIX_REPORT_R2.md)) | Section 9.1 (XB-13 Gate) | `docs/logs/regression_20seeds.log` |
| Functional Coverage (Bins Hit / Total) | being re-measured (see [`docs/FIX_REPORT_R2.md`](docs/FIX_REPORT_R2.md)) | Section 10 | `docs/logs/func_cov.log` |
| Code Coverage (Verilator Line / Toggle) | being re-measured (see [`docs/FIX_REPORT_R2.md`](docs/FIX_REPORT_R2.md)) | Section 10 | `docs/logs/code_cov_summary.txt` |
| Formal Properties / BMC / k-induction | being re-measured (see [`docs/FIX_REPORT_R2.md`](docs/FIX_REPORT_R2.md)) | Section 11 | `docs/logs/formal_suite.log` |
| CDC Clock Ratios & Phases Swept | **3 ratios (25.0 ns, 10.3 ns, 6.0 ns) × 3 phases** (re-measured in Phase C) | Section 9.1 (CD-01) | `docs/logs/func_cov.log`, `formal/async_fifo.sby` |
| Mutants Generated / Killed / Score | being re-measured (see [`docs/FIX_REPORT_R2.md`](docs/FIX_REPORT_R2.md)) | Section 12 | `docs/logs/mutation.log`, `docs/mutation_report.md` |
| Crossbar Added Latency (Cycles) | **0 cycles added latency** (verified in XB-06 parallel transfer cycle check) | Section 7.2 (≤1 cycle) | `docs/img/contention.png`, `tb/block/test_axil_xbar.py` |
| Synthesis: Cell Count / Flop Count / Area | being re-measured (see [`docs/FIX_REPORT_R2.md`](docs/FIX_REPORT_R2.md)) | Section 13 (SKY130) | `docs/logs/synth.log` |
| STA: Target Period / WNS / TNS / $F_{\max}$ | being re-measured (see [`docs/FIX_REPORT_R2.md`](docs/FIX_REPORT_R2.md)) | Section 13 (100 MHz target) | `docs/logs/sta.log`, `docs/logs/fmax_sweep.log` |
| CI Status | **NOT VERIFIED** on GitHub remote (see [`docs/FIX_REPORT_R2.md`](docs/FIX_REPORT_R2.md)) | Section 14 | `.github/workflows/ci.yml` |

---

## 2. Detailed Re-Measurement Status (R2 Pass)

All detailed tables below (Formal, Functional Coverage, Verilator Code Coverage, Mutation Testing, Yosys Synthesis, and OpenSTA Timing/Fmax) are **being re-measured (see [`docs/FIX_REPORT_R2.md`](docs/FIX_REPORT_R2.md))** and will be regenerated strictly from `docs/metrics.json` in Phase F:

- **Formal Verification Table:** being re-measured (see [`docs/FIX_REPORT_R2.md`](docs/FIX_REPORT_R2.md)) — Phase B binds `formal/rr_arbiter_props.v`, adds `sync_fifo` data ordering, removes over-assumptions, and enforces exact wording.
- **Functional & Code Coverage Tables:** being re-measured (see [`docs/FIX_REPORT_R2.md`](docs/FIX_REPORT_R2.md)) — Phase C fixes `CdcMonitor` edge measurement, adds real stimulus for uncovered bins, and fixes `make cov-report`.
- **Mutation Testing Matrix:** being re-measured (see [`docs/FIX_REPORT_R2.md`](docs/FIX_REPORT_R2.md)) — Phase D fixes `run_mutants.py` process-group cleanup, `axil_xbar` scope, and generates `docs/mutation_report.md` directly from the run log.
- **Synthesis & OpenSTA Timing Tables:** being re-measured (see [`docs/FIX_REPORT_R2.md`](docs/FIX_REPORT_R2.md)) — Phase E restores `synth/synth.ys` and replaces stale hardcoded netlist cells with portable port/hierarchy constraints.
- **Historical Gate Logs (Phases 0–4 Baseline):** Archived under `docs/logs/phase0_gate.log` .. `docs/logs/phase4_gate.log` (superseded by Second Remediation Pass R2).
