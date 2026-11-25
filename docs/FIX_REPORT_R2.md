# AMBA-Fabric Second Remediation Report (`docs/FIX_REPORT_R2.md`)

Tracks remediation of the independent adversarial audit on commit `8664339` (`audit_input/AUDIT_REPORT.md`: 33 BLOCKER, 37 MAJOR, 12 MINOR, 5 INFO).

---

## Phase Summary

| Phase | Scope & Audit IDs | Status | Commits |
|---|---|---|---|
| **Phase A** | RTL Rule 6 fix (`axil_csr`), models, crossbar decision, 8 test rewrites (`XB-07/12/14/15`, `UA-02`, `XB-03`, `BR-05`, `CD-03`), 10 sanity mutants | `TODO` | - |
| **Phase B** | Formal (`rr_arbiter_props.v`, bounded fairness, `sync_fifo` data ordering, bridge/xbar over-assumptions, CSR causality/Rule 6, exact wording) | `TODO` | - |
| **Phase C** | Honest coverage (`CdcMonitor` edge measurement, stimulus for 44 holes, waivers, `make cov-report` fix & full re-measure) | `TODO` | - |
| **Phase D** | Mutation (`run_mutants.py` process group kill, `axil_xbar` scope fix, CSR/bridge test gaps, 240-mutant run, script-generated report) | `TODO` | - |
| **Phase E** | Synthesis & STA (`synth/synth.ys`, portable reset false-path constraints, dynamic `fmax_sweep.py` parsing, clean measurements) | `TODO` | - |
| **Phase F** | Data-driven docs (`scripts/gen_metrics.py`, `docs/metrics.json`, regenerate docs, `bugs.md` / `decisions.md` / `interfaces.md`, CI check scripts) | `TODO` | - |
| **Phase G** | CI (`ci.yml` artifact/command alignment, fresh checkout check, remote GitHub Actions verification) | `TODO` | - |
| **Final** | Clean-clone full re-measure & `remediation-r2-done` tag | `TODO` | - |

---

## Detailed Remediation Log

### Phase A: RTL Fix and Tests That Can Fail (`AXIL-R6`, `RTL-axil_csr`, `PROBE-02`, `XB-07`, `XB-12`, `XB-14`, `XB-15`, `UA-02`, `XB-03`, `BR-05`, `CD-03`, `SMUT-01..10`)
- **Status:** `TODO`
- **Files Changed:** Pending
- **Commands Run:** Pending
- **Log Paths:** Pending
- **Before / After Numbers:**
  - Before: `0x6000_0001` returns `SLVERR` (`AXIL-R6` FAIL); `XB-07` 0 assertions; `XB-12` idle reset; `XB-14` ignores APB `PPROT`; `XB-15` RAM-only; `UA-02` misses `RX_OVF`; `SMUT-09` & `SMUT-10` escape (8/10 killed).
  - After: Pending Phase A execution.
- **Remaining Issues:** None yet.

---

### Phase B: Formal Verification (`FORMAL-*`, `V-07`)
- **Status:** `TODO`
- **Files Changed:** Pending
- **Commands Run:** Pending
- **Log Paths:** Pending
- **Before / After Numbers:**
  - Before: `rr_arbiter_props.v` orphaned; no bounded fairness; `sync_fifo` lacks data-ordering proof; over-assumptions in `axil2apb_bridge_props.v` and `axil_xbar_props.v`; `CHECK_CAUSALITY(0)` in `axil_csr.v`; `coverage_waivers.md:43` claims "exhaustively proven".
  - After: Pending Phase B execution.
- **Remaining Issues:** None yet.

---

### Phase C: Honest Functional & Code Coverage (`V-04`, `V-05`, `COV-*`)
- **Status:** `TODO`
- **Files Changed:** Pending
- **Commands Run:** Pending
- **Log Paths:** Pending
- **Before / After Numbers:**
  - Before: Functional coverage 83.88% (229/273) with 44 uncovered bins; `CdcMonitor` reads `CLK_SLOW_PERIOD_NS` env var; `make cov-report` exits non-zero / fails on small `/tmp`; `vplan.md` & `results.md` claim 280/280 (100%).
  - After: Pending Phase C execution.
- **Remaining Issues:** None yet.

---

### Phase D: Mutation Testing (`V-09`, `MUT-*`)
- **Status:** `TODO`
- **Files Changed:** Pending
- **Commands Run:** Pending
- **Log Paths:** Pending
- **Before / After Numbers:**
  - Before: Fresh run 183/240 (76.25%); `run_mutants.py` leaks timed-out `vvp` processes; `axil_xbar` mutates TB/wrapper; `docs/mutation_report.md` has 30/29 math (103.4%), phantom survivor `#29`, duplicate `mutation_triage.md`, and misclassified test gaps.
  - After: Pending Phase D execution.
- **Remaining Issues:** None yet.

---

### Phase E: Synthesis and STA (`S-01`, `SYNTH-*`)
- **Status:** `TODO`
- **Files Changed:** Pending
- **Commands Run:** Pending
- **Log Paths:** Pending
- **Before / After Numbers:**
  - Before: `synth/synth.ys` missing; `sta.tcl` & `fmax_sweep.py` hardcode stale cells (`_14798_`, `_14800_`); `fmax_sweep.py` prints hardcoded `81.63 MHz`; fresh OpenSTA yields WNS `-19.33 ns` (<62.5 MHz).
  - After: Pending Phase E execution.
- **Remaining Issues:** None yet.

---

### Phase F: Data-Driven Documentation (`METRIC-*`, `VPLAN-AUDIT`, `BUGS-AUDIT`, `DECISIONS-AUDIT`, `DOD-08/09`)
- **Status:** `TODO`
- **Files Changed:** Pending
- **Commands Run:** Pending
- **Log Paths:** Pending
- **Before / After Numbers:**
  - Before: Contradictory hand-typed metrics across `README.md`, `docs/results.md`, `docs/vplan.md` (lines 3238 vs 3759, bugs 21 vs 22, coverage 83.88% vs 100%, formal 8/8 vs 10/10); broken links (`contention.vcd`, `synth.ys`, `BUG-022` ref); 4 unlogged deviations in `docs/decisions.md`.
  - After: Pending Phase F execution.
- **Remaining Issues:** None yet.

---

### Phase G: CI & Final Clean-Clone Re-Measure (`CI-WORKFLOW`, `CI-REMOTE`, `V-10`)
- **Status:** `TODO`
- **Files Changed:** Pending
- **Commands Run:** Pending
- **Log Paths:** Pending
- **Before / After Numbers:**
  - Before: `CI Status: PASS` unverified on GitHub; CI uploads unbuilt `docs/logs/` & `synth/results/`.
  - After: Pending Phase G execution.
- **Remaining Issues:** None yet.

---

## Commit & Tag Log

| Commit SHA | Tag | Message | Gate Evidence |
|---|---|---|---|
| *Pending* | - | - | - |

## Audit Row Closure Register (70 BLOCKER & MAJOR Rows)

- `F-02` (BLOCKER): OPEN (assigned to Phase A A2/A3)
- `F-05` (BLOCKER): OPEN (assigned to Phase A A1)
- `F-06` (MAJOR): OPEN (assigned to Phase A A3)
- `F-08` (MAJOR): OPEN (assigned to Phase A A3)
- `V-02` (MAJOR): OPEN (assigned to Phase A A1/A3)
- `V-04` (BLOCKER): OPEN (assigned to Phase C C2/C4)
- `V-05` (MAJOR): OPEN (assigned to Phase C C3)
- `V-06` (MAJOR): OPEN (assigned to Phase B B/C1)
- `V-07` (MAJOR): OPEN (assigned to Phase B B)
- `V-09` (BLOCKER): OPEN (assigned to Phase D D1-D5)
- `V-10` (MAJOR): OPEN (assigned to Phase G G)
- `S-01` (BLOCKER): OPEN (assigned to Phase E E1-E4)
- `REG-UART-08` (MAJOR): OPEN (assigned to Phase A A3)
- `AXIL-R6` (BLOCKER): OPEN (assigned to Phase A A1)
- `RTL-axil_xbar` (MAJOR): OPEN (assigned to Phase A A2)
- `RTL-axil_csr` (BLOCKER): OPEN (assigned to Phase A A1)
- `XB-07` (BLOCKER): OPEN (assigned to Phase A A3)
- `XB-12` (BLOCKER): OPEN (assigned to Phase A A3)
- `XB-14` (BLOCKER): OPEN (assigned to Phase A A3)
- `XB-15` (BLOCKER): OPEN (assigned to Phase A A3)
- `UA-02` (MAJOR): OPEN (assigned to Phase A A3)
- `COV-cg_order` (MAJOR): OPEN (assigned to Phase C C2)
- `COV-cg_backpressure` (MAJOR): OPEN (assigned to Phase C C2)
- `COV-cg_apb` (MAJOR): OPEN (assigned to Phase C C2)
- `COV-cg_cdc` (MAJOR): OPEN (assigned to Phase C C1/C4)
- `COV-cg_uart` (MAJOR): OPEN (assigned to Phase C C2)
- `COV-cg_reset` (MAJOR): OPEN (assigned to Phase C C2)
- `COV-HONESTY` (MAJOR): OPEN (assigned to Phase C C1)
- `COV-FUNC-MERGE` (BLOCKER): OPEN (assigned to Phase C C3/C4)
- `COV-CODE-VERILATOR` (MAJOR): OPEN (assigned to Phase C C3/C4)
- `FORMAL-async_fifo` (MAJOR): OPEN (assigned to Phase B B)
- `FORMAL-axil2apb_bridge` (MAJOR): OPEN (assigned to Phase B B)
- `FORMAL-axil_xbar` (MAJOR): OPEN (assigned to Phase B B)
- `FORMAL-rr_arbiter` (MAJOR): OPEN (assigned to Phase B B)
- `FORMAL-sync_fifo` (MAJOR): OPEN (assigned to Phase B B)
- `FORMAL-rr_arbiter_props` (MAJOR): OPEN (assigned to Phase B B)
- `FORMAL-WORDING` (MAJOR): OPEN (assigned to Phase B B)
- `MUT-SCRIPT` (MAJOR): OPEN (assigned to Phase D D1)
- `MUT-TRIAGE` (BLOCKER): OPEN (assigned to Phase D D4)
- `MUT-SPOT5` (MAJOR): OPEN (assigned to Phase D D3/D4)
- `PROBE-02` (BLOCKER): OPEN (assigned to Phase A A1)
- `SMUT-09` (BLOCKER): OPEN (assigned to Phase A A4)
- `SMUT-10` (BLOCKER): OPEN (assigned to Phase A A4)
- `SYNTH-YS` (BLOCKER): OPEN (assigned to Phase E E1)
- `SYNTH-STA` (BLOCKER): OPEN (assigned to Phase E E2/E3)
- `SYNTH-REPORT` (BLOCKER): OPEN (assigned to Phase E E4)
- `CI-REMOTE` (MAJOR): OPEN (assigned to Phase G G)
- `LAYOUT-SYNTH_YS` (BLOCKER): OPEN (assigned to Phase E E1)
- `METRIC-01` (BLOCKER): OPEN (assigned to Phase F F1/F2)
- `METRIC-02` (BLOCKER): OPEN (assigned to Phase F F1/F2)
- `METRIC-05` (BLOCKER): OPEN (assigned to Phase F F1/F2)
- `METRIC-06` (MAJOR): OPEN (assigned to Phase F F1/F2)
- `METRIC-07` (MAJOR): OPEN (assigned to Phase F F1/F2)
- `METRIC-09` (BLOCKER): OPEN (assigned to Phase F F1/F2)
- `METRIC-10` (MAJOR): OPEN (assigned to Phase F F1/F3)
- `METRIC-12` (BLOCKER): OPEN (assigned to Phase F F1/F2)
- `METRIC-13` (BLOCKER): OPEN (assigned to Phase F F1/F2)
- `METRIC-14` (MAJOR): OPEN (assigned to Phase G G)
- `DOD-01` (BLOCKER): OPEN (assigned to Phase A A1-A4)
- `DOD-02` (MAJOR): OPEN (assigned to Phase C C4/Final)
- `DOD-03` (BLOCKER): OPEN (assigned to Phase C C2-C4)
- `DOD-04` (MAJOR): OPEN (assigned to Phase B B)
- `DOD-05` (BLOCKER): OPEN (assigned to Phase D D1-D5)
- `DOD-06` (BLOCKER): OPEN (assigned to Phase E E1-E4)
- `DOD-07` (MAJOR): OPEN (assigned to Phase G G)
- `DOD-08` (BLOCKER): OPEN (assigned to Phase F F2/F3/F5)
- `DOD-09` (BLOCKER): OPEN (assigned to Phase F F6)
- `VPLAN-AUDIT` (BLOCKER): OPEN (assigned to Phase F F2)
- `BUGS-AUDIT` (MAJOR): OPEN (assigned to Phase F F3)
- `DECISIONS-AUDIT` (MAJOR): OPEN (assigned to Phase F F4)
