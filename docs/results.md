# Verification & Implementation Results

This document records **real, measured results** from actual tool execution.
**Non-negotiable rule:** No fabricated numbers. If a metric has not been measured yet, it is marked as "Not measured". Raw logs are archived in `docs/logs/`.

---

## 1. Overall Metrics Summary

| Metric | Measured Value | Spec Reference | Log Reference / Command |
|---|---|---|---|
| RTL Modules / Total Lines | Not measured (Phase 1-3) | Section 17 | `wc -l rtl/**/*.v` |
| Total Tests (Directed / Random) | 1 (Phase 0 smoke test) | Section 9 | `tb/unit/test_hello_world.py` |
| Random Transactions Executed | Not measured (Phase 4) | Section 9.1 (XB-13) | `docs/logs/xb13_stress.log` |
| Multi-seed Regression Seeds Passed | Not measured (Phase 5) | Section 9.2 (≥20 seeds) | `docs/logs/regression.log` |
| Functional Coverage (Bins Hit / Total) | Not measured (Phase 5) | Section 10 (100% goal) | `docs/logs/func_cov.log` |
| Code Coverage (Verilator Line / Toggle) | Not measured (Phase 5) | Section 10 | `docs/logs/code_cov/` |
| Formal Properties Proven / BMC Depth | Not measured (Phase 1, 2, 5) | Section 11 | `docs/logs/formal_summary.log` |
| CDC Clock Ratios & Phases Swept | Not measured (Phase 3-4) | Section 9.1 (CD-01) | `docs/logs/cdc_sweep.log` |
| Mutants Generated / Killed / Score | Not measured (Phase 6) | Section 12 | `docs/logs/mutation_summary.log` |
| Crossbar Added Latency (Cycles) | Not measured (Phase 2) | Section 7.2 (≤1 cycle) | Waveform measurement |
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
