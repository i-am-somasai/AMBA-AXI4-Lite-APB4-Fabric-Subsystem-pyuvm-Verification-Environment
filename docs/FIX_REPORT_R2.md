# AMBA-Fabric Second Remediation Report (`docs/FIX_REPORT_R2.md`)

Tracks remediation of the independent adversarial audit on commit `8664339` (`audit_input/AUDIT_REPORT.md`: 33 BLOCKER, 37 MAJOR, 12 MINOR, 5 INFO).

---

## Phase Summary

| Phase | Scope & Audit IDs | Status | Commits |
|---|---|---|---|
| **Phase A** | RTL Rule 6 fix (`axil_csr`), CDC reset fix, models, decisions (`DEC-006..008`), 8 test rewrites (`XB-03/07/12/14/15`, `UA-02`, `BR-05`, `CD-03`), 16 sanity mutants | `DONE` | `fix(R2-A)` (this commit) |
| **Phase B** | Formal (`rr_arbiter_props.v`, bounded fairness, `sync_fifo` data ordering, bridge/xbar over-assumptions, CSR causality/Rule 6, exact wording) | `DONE` | [`docs/logs/phase_b_formal.log`](docs/logs/phase_b_formal.log) |
| **Phase C** | Honest coverage (`CdcMonitor` edge measurement, stimulus for 44 holes, waivers, `make cov-report` fix & full re-measure) | `DONE` | [`docs/logs/func_cov.log`](docs/logs/func_cov.log) |
| **Phase D** | Mutation (`run_mutants.py` process group kill, `axil_xbar` scope fix, CSR/bridge test gaps, 240-mutant run, script-generated report) | `DONE` | [`docs/mutation_report.md`](mutation_report.md) |
| **Phase E** | Synthesis & STA (`synth/synth.ys`, portable reset false-path constraints, dynamic `fmax_sweep.py` parsing, clean measurements) | `TODO` | - |
| **Phase F** | Data-driven docs (`scripts/gen_metrics.py`, `docs/metrics.json`, regenerate docs, `bugs.md` / `decisions.md` / `interfaces.md`, CI check scripts) | `TODO` | - |
| **Phase G** | CI (`ci.yml` artifact/command alignment, fresh checkout check, remote GitHub Actions verification) | `TODO` | - |
| **Final** | Clean-clone full re-measure & `remediation-r2-done` tag | `TODO` | - |

---

## Detailed Remediation Log

### Phase A: RTL Fix and Tests That Can Fail (`AXIL-R6`, `RTL-axil_csr`, `PROBE-02`, `XB-07`, `XB-12`, `XB-14`, `XB-15`, `UA-02`, `XB-03`, `BR-05`, `CD-03`, `SMUT-01..16`)
- **Status:** `DONE`
- **Files Changed:** `rtl/axil/axil_csr.v`, `rtl/cdc/axil_cdc_bridge.v`, `rtl/common/async_fifo.v`, `formal/axil_csr.sby`, `tb/models/{addr_map,reg_model,ram_model,peripheral_model,fabric_ref_model}.py`, `tb/unit/test_axil_csr.py`, `tb/block/{test_axil_xbar,test_apb_uart,test_axil2apb_bridge,test_axil_cdc_bridge,test_amba_fabric_top}.py`, `tb/pyuvm/{agents/axil_master_agent.py,env/fabric_scoreboard.py,sequences/directed_seqs.py,tests/test_directed.py}`, `mutation/sanity/run_sanity.py`, `scripts/run_sanity.sh`, `docs/{bugs.md,decisions.md,audit_r2_tracking.csv,FIX_REPORT_R2.md}`
- **Commands Run:**
  - `make lint` -> CLEAN
  - `(cd formal && sby -f axil_csr.sby)` -> prove/bmc/cover PASS
  - `(cd formal && sby -f axil_cdc_bridge.sby)` -> bmc/cover PASS
  - `make unit SIM=icarus` -> PASS
  - `make -C tb/block all SIM=icarus` -> PASS (including `XB-03`, `XB-07`, `UA-02`, `BR-05`, `CD-03`)
  - `bash scripts/run_sanity.sh` -> **16/16 KILLED, 0 SURVIVED, 0 INVALID**
  - `make -C tb/pyuvm -j4 SIM=icarus SEEDS="$(seq 601 620)" regress` -> PASS (all 20 seeds `601..620` + directed/CDC sweeps)
- **Log Paths:**
  - `docs/logs/phase_a_lint.log`
  - `docs/logs/phase_a_formal_csr.log`
  - `docs/logs/phase_a_formal_cdc.log`
  - `docs/logs/phase_a_unit.log`
  - `docs/logs/phase_a_block.log`
  - `docs/logs/phase_a_sanity.log`
  - `docs/logs/phase_a_regress_20seeds.log`
- **Before / After Numbers:**
  - Before: `0x6000_0001` returns `SLVERR` (`AXIL-R6` FAIL); `XB-07` 0 assertions; `XB-12` idle reset; `XB-14` ignores APB `PPROT`; `XB-15` RAM-only; `UA-02` misses `RX_OVF`; `CD-03` resets both domains & hangs without sys reset; `SMUT-09` & `SMUT-10` escape (8/10 killed).
  - After: `0x6000_0001..3` return `OKAY` + `0xA3BA_0001`; CSR formal `prove`+`bmc`(`CHECK_CAUSALITY=1`)+`cover` PASS; `BUG-023` & `BUG-024` logged; `DEC-006..008` logged; all 8 tests rewritten with direct assertions; **16/16 sanity mutants KILLED**; 20 fresh seeds (`601..620`) PASS.
- **Remaining Issues:** None for Phase A.

---

### Phase B: Formal Verification (`FORMAL-*`, `V-07`)
- **Status:** `DONE`
- **Files Changed:** `formal/rr_arbiter.sby`, `formal/rr_arbiter_props.v`, `rtl/common/sync_fifo.v`, `formal/sync_fifo_props.v`, `formal/axil2apb_bridge_props.v`, `rtl/axil/axil_xbar.v`, `formal/axil_xbar_props.v`, `formal/apb_uart.sby`, `docs/coverage_waivers.md`, `scripts/run_all_formal.sh`, `README.md`, `docs/audit_r2_tracking.csv`, `docs/FIX_REPORT_R2.md`
- **Commands Run:** `make lint`, `bash scripts/run_all_formal.sh`, `make unit SIM=icarus`, `make -C tb/block test_axil_xbar test_axil2apb_bridge SIM=icarus`
- **Log Paths:** [`docs/logs/phase_b_lint.log`](docs/logs/phase_b_lint.log), [`docs/logs/phase_b_formal.log`](docs/logs/phase_b_formal.log), [`docs/logs/formal_suite.log`](docs/logs/formal_suite.log), [`docs/logs/phase_b_unit.log`](docs/logs/phase_b_unit.log)
- **Before / After Numbers:**
  - Before: `rr_arbiter_props.v` orphaned; no bounded fairness; `sync_fifo` lacked data-ordering proof; over-assumptions in `axil2apb_bridge_props.v` and `axil_xbar_props.v`; `coverage_waivers.md:43` claimed "exhaustively proven".
  - After: **10/10** formal suites PASS (`apb_timer` prove d=20 4c, `apb_uart` bmc d=25 9c, `async_fifo` bmc d=25 4c, `axil2apb_bridge` bmc d=25 10c, `axil_cdc_bridge` bmc d=30 5c, `axil_csr` prv+bmc d=20 5c, `axil_ram` bmc d=20 5c, `axil_xbar` bmc d=20 31c, `rr_arbiter` prove d=20 3c, `sync_fifo` prove d=20 8c), **0** undriven-wire warnings, **0** counterexamples from removing over-assumptions (no RTL bugs triggered, no reduced depth/DATA_WIDTH needed); `rr_arbiter` documented as standalone verified block (`DEC-007`).
- **Remaining Issues:** `V-06` stays `OPEN` until Phase C1 fixes `CdcMonitor` period measurement (Phase B formal half closed).

---

### Phase C: Honest Functional & Code Coverage (`V-04`, `V-05`, `COV-*`)
- **Status:** `DONE`
- **Files Changed:** `tb/pyuvm/func_cov/fabric_cov.py`, `tb/pyuvm/monitors/fabric_monitors.py`, `tb/models/axil_driver.py`, `tb/pyuvm/sequences/{axil_seq_item.py,axil_base_seq.py,coverage_closure_seq.py}`, `tb/pyuvm/agents/axil_master_agent.py`, `tb/pyuvm/tests/test_directed.py`, `tb/pyuvm/Makefile`, `tb/block/{Makefile.single,test_axil2apb_bridge.py}`, `scripts/{merge_cov.py,run_regression.sh}`, `docs/{coverage_waivers.md,decisions.md,audit_r2_tracking.csv,FIX_REPORT_R2.md}`
- **Commands Run:** `./scripts/check_no_synthetic_cov.sh`, `make cov-report`, `python3 scripts/merge_cov.py docs/logs`
- **Log Paths:** [`docs/logs/phase_c_cov_report.log`](docs/logs/phase_c_cov_report.log), [`docs/logs/func_cov.log`](docs/logs/func_cov.log), [`docs/logs/code_cov_summary.txt`](docs/logs/code_cov_summary.txt)
- **Before / After Numbers:**
  - Before: Functional coverage 83.88% (229/273) with 44 uncovered bins; `CdcMonitor` read `CLK_SLOW_PERIOD_NS` env var; `make cov-report` failed on `/tmp` space & exited 1; Verilator line 90.0%, branch 89.2%, expr 92.7%, toggle 75.2%.
  - After: Functional coverage **100.00% (267/267 reachable bins)** across 24 merged YAMLs (20 Verilator seeds `1..20`, directed tests, CDC `10.3ns`/`6.0ns` sweeps, block `cg_apb` tagged `source=block`), 36 documented waivers (`cg_txn` 24 + `cg_cdc` 6 + `cg_contention` 3 per `DEC-009` + `cg_apb.strb_cross` 3 per `DEC-010`, net 267 legal reachable bins vs 273 pre-R2); Verilator code coverage **line 92.0% (494/537)**, **branch 91.2% (499/547)**, **expr 93.8% (1036/1105)**, **toggle 74.8% (10616/14202)**, **fsm_state 100.0% (5/5)**; `make cov-report` exits `0` cleanly using `BUILD_DIR`.
- **Remaining Issues:** None for Phase C (`check_no_synthetic_cov.sh` PASS).

---

### Phase D: Mutation Testing (`V-09`, `MUT-*`)
- **Status:** `DONE`
- **Files Changed:** `mutation/{run_mutants.py,mutant_list_240.json,gen_mutation_report.py}`, `tb/unit/{test_async_fifo,test_rr_arbiter,test_sync_fifo,test_axil_decoder,test_axil_ram,test_axil_csr}.py`, `tb/block/{test_axil2apb_bridge,test_axil_xbar}.py`, `docs/{mutation_report.md,audit_r2_tracking.csv,FIX_REPORT_R2.md}` (deleted duplicate `docs/mutation_triage.md`)
- **Commands Run:** `python3 mutation/run_mutants.py --generate-list mutation/mutant_list_240.json --seed 42 --max-mutants 240`, `python3 mutation/run_mutants.py --mutant-list mutation/mutant_list_240.json --seed 42 -j4 --output docs/logs/mutation_baseline.log`, `make unit SIM=icarus && make block SIM=icarus`, `python3 mutation/run_mutants.py --mutant-list mutation/mutant_list_240.json --seed 42 -j4 --output docs/logs/mutation.log`, Yosys `equiv_induct` + Boolector `d=10` miter checks (`docs/logs/mutation_equiv.log`), `python3 mutation/gen_mutation_report.py`
- **Log Paths:** [`docs/logs/mutation_baseline.log`](logs/mutation_baseline.log), [`docs/logs/mutation.log`](logs/mutation.log), [`docs/logs/mutation_equiv.log`](logs/mutation_equiv.log), [`docs/logs/phase_d_golden_unit_block.log`](logs/phase_d_golden_unit_block.log)
- **Before / After Numbers:**
  - Before (D3 baseline on frozen 240-mutant list): **165/240 killed (68.75% raw)**, 64 survived, 11 timeouts (`async_fifo`), 0 build errors. Previously `run_mutants.py` leaked `vvp` processes, mutated `tb_axil_xbar`/submodules, and `docs/mutation_report.md` had 30/29 math & duplicate `docs/mutation_triage.md`.
  - After (D5 final on identical 240-mutant list): **205/240 killed (85.42% raw, +40 kills / +16.67%)**, 35 survived, **0 timeouts**, **0 build errors**; 21 equivalent (18 Yosys `equiv_induct` / Boolector `d=10` miter + 3 `axil_default_slave._unused_inputs` signal proof), 14 residual non-equivalent survivors, **93.61% adjusted (205/219)**; 0 leaked `vvp` processes.
- **Remaining Issues:** None for Phase D (`V-09`, `MUT-SCRIPT`, `MUT-TRIAGE`, `MUT-SPOT5`, `DOD-05` closed).

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

- `F-02` (BLOCKER): CLOSED (`DEC-007` logged; `test_xb07_arbitration_fairness` WR+RD assertions; `SMUT-10` KILLED in `docs/logs/phase_a_sanity.log`)
- `F-05` (BLOCKER): CLOSED (`rtl/axil/axil_csr.v` decodes `[7:2]`; `BUG-023` logged; `0x6000_0001..3` verified in `docs/logs/phase_a_unit.log`)
- `F-06` (MAJOR): CLOSED (`test_xb14_prot_passthrough` & `test_br01` assert `PPROT`; `test_br05_dual_master_apb_mixed_rw` added; `SMUT-09`/`SMUT-16` KILLED)
- `F-08` (MAJOR): CLOSED (`test_ua02_fifo_full_and_overflow_flags` verifies `RX_OVF` & W1C; `SMUT-12` KILLED)
- `V-02` (MAJOR): CLOSED (`tb/models/` aligned to `[1:0]` ignore Rule 6; APB `PPROT` checked in `XB-14` & `BR-01`)
- `V-04` (BLOCKER): CLOSED (`267/267 (100.00%)` reachable bins across 24 merged YAMLs in `docs/logs/func_cov.log`; `DEC-009`/`DEC-010` waivers documented)
- `V-05` (MAJOR): CLOSED (`scripts/run_regression.sh` builds in `BUILD_DIR`, cleans intermediate `sim_build`, and `make cov-report` exits 0)
- `V-06` (MAJOR): CLOSED (Phase B bound `rr_arbiter_props.v`; Phase C replaced `CLK_SLOW_PERIOD_NS` read in `CdcMonitor` with `RisingEdge` pin timing)
- `V-07` (MAJOR): CLOSED (`rr_arbiter_props` bound, `sync_fifo` magic data-order `prove` PASS, bridge/xbar over-assumptions removed, `axil_csr` `prv+bmc` PASS in `docs/logs/phase_b_formal.log`)
- `V-09` (BLOCKER): CLOSED (`mutation/run_mutants.py` process-group kill & strict `axil_xbar` scope; 205/240 raw 85.42%, 205/219 adj 93.61% in `docs/mutation_report.md`)
- `V-10` (MAJOR): OPEN (assigned to Phase G G)
- `S-01` (BLOCKER): OPEN (assigned to Phase E E1-E4)
- `REG-UART-08` (MAJOR): CLOSED (`test_ua02_fifo_full_and_overflow_flags` asserts `STATUS[5]==1` & W1C in `docs/logs/phase_a_block.log`)
- `AXIL-R6` (BLOCKER): CLOSED (`rtl/axil/axil_csr.v` decodes `[7:2]`, `axil_csr.sby` prove+bmc+cover PASS in `docs/logs/phase_a_formal_csr.log`)
- `RTL-axil_xbar` (MAJOR): CLOSED (`DEC-007` logged in `docs/decisions.md` without modifying `docs/spec.md`)
- `RTL-axil_csr` (BLOCKER): CLOSED (`rtl/axil/axil_csr.v` Rule 6 fixed; `DEC-006` documents `bmc` `CHECK_CAUSALITY=1` / `prove` `0`)
- `XB-07` (BLOCKER): CLOSED (`tb/block/test_axil_xbar.py` continuous AW/AR WR+RD diff<=1 assertions; `SMUT-10` KILLED)
- `XB-12` (BLOCKER): CLOSED (`tb/pyuvm/tests/test_directed.py` resets mid-AW/W/B/AR/R, flushes SB/agents UNKNOWN; `SMUT-14` KILLED)
- `XB-14` (BLOCKER): CLOSED (`ProtPassThroughSeq` & `test_br01` assert physical `apb_pprot`/`m_apb_pprot` 0..7; `SMUT-09` KILLED)
- `XB-15` (BLOCKER): CLOSED (`UnalignedAddressSeq` checks `+1/+2/+3` across RAM/CSR/APB/CDC; `SMUT-11` KILLED)
- `UA-02` (MAJOR): CLOSED (`test_ua02_fifo_full_and_overflow_flags` verifies `RX_OVF` & W1C; `SMUT-12` KILLED)
- `COV-cg_order` (MAJOR): CLOSED (`AxilBusMonitor` tracks `t_w_valid` vs `t_aw_valid`; `cg_order.cross` 12/12 100.00%)
- `COV-cg_backpressure` (MAJOR): CLOSED (`AxilSeqItem` + `AxilDriver` + `CoverageClosureSeq` cover `0/1/2-4/5-16` `BREADY`/`RREADY`; `cg_backpressure.cross` 20/20 100.00%)
- `COV-cg_apb` (MAJOR): CLOSED (`test_br07_apb_wait_err_cov` with `ApbBusMonitor` `source=block`; `DEC-010` waives RD strobes; `wait_cross` 16/16 & `strb_cross` 5/5)
- `COV-cg_cdc` (MAJOR): CLOSED (`CdcMonitor` measures physical clock periods & observes `ST_WAIT_RESP` partial occupancy; `cg_cdc.cross` 12/12 100.00%)
- `COV-cg_uart` (MAJOR): CLOSED (`CoverageClosureSeq` fills TX FIFO at `BAUDDIV` 0/1/4 & drives external `uart_rx` bad stop bit; `cg_uart.cross` 9/9 & `err` 3/3)
- `COV-cg_reset` (MAJOR): CLOSED (`test_xb12_reset_recovery` drops `rst_n` mid-AW/W/B/AR/R before driver cleanup; `cg_reset.phase` 5/5 100.00%)
- `COV-HONESTY` (MAJOR): CLOSED (`CdcMonitor` free of `CLK_SLOW_PERIOD_NS` env read; `check_no_synthetic_cov.sh` PASS)
- `COV-FUNC-MERGE` (BLOCKER): CLOSED (`merge_cov.py` merges 20 Verilator seeds `1..20` + directed + CDC + block `cg_apb` = 267/267 in `docs/logs/func_cov.log`)
- `COV-CODE-VERILATOR` (MAJOR): CLOSED (`code_cov_summary.txt`: line 92.0% 494/537, branch 91.2% 499/547, expr 93.8% 1036/1105, toggle 74.8%)
- `FORMAL-async_fifo` (MAJOR): CLOSED (`docs/coverage_waivers.md:43` updated to `bounded model checking (multiclock BMC depth 25)`)
- `FORMAL-axil2apb_bridge` (MAJOR): CLOSED (`!s_axil_arvalid` over-assumption removed in `formal/axil2apb_bridge_props.v`; concurrent WR+RD covers verified, `bmc d=25` PASS 10 covers)
- `FORMAL-axil_xbar` (MAJOR): CLOSED (`f_s_bresp_wait` fixed to require committed `AW+W` handshake; `wr_prio`/`rd_prio` bounded fairness & contention covers added, `bmc d=20` PASS 31 covers)
- `FORMAL-rr_arbiter` (MAJOR): CLOSED (`formal/rr_arbiter_props.v` bound in `rr_arbiter.sby` & `f_wait_cnt < NUM_REQS` bounded fairness proved, `prove d=20` PASS 3 covers)
- `FORMAL-sync_fifo` (MAJOR): CLOSED (inductive `(* anyconst *)` magic-value data-ordering & integrity proof added in `rtl/common/sync_fifo.v`, `prove d=20` PASS 8 covers)
- `FORMAL-rr_arbiter_props` (MAJOR): CLOSED (`formal/rr_arbiter.sby` runs `prep -top rr_arbiter_props` with 0 undriven-wire warnings)
- `FORMAL-WORDING` (MAJOR): CLOSED (`coverage_waivers.md:43` 'exhaustively proven' removed; `README.md` documents formal depths & standalone `rr_arbiter`)
- `MUT-SCRIPT` (MAJOR): CLOSED (`mutation/run_mutants.py` uses `start_new_session=True` + `os.killpg(SIGKILL)`, separates `TIMEOUT`/`BUILD_ERROR`, scopes `axil_xbar` to `$paramod*axil_xbar`)
- `MUT-TRIAGE` (BLOCKER): CLOSED (deleted duplicate `docs/mutation_triage.md`; `mutation/gen_mutation_report.py` parses logs & `mutation_equiv.log` deterministically)
- `MUT-SPOT5` (MAJOR): CLOSED (added `test_cs04` CSR OOO/RO/WO/32b-W1C & `test_br08` 32b PADDR/`w_first`/`PSTRB=0` + unit/block tests; +40 kills)
- `PROBE-02` (BLOCKER): CLOSED (`0x6000_0001..3` return `OKAY` + `0xA3BA0001` in `test_cs01_reset_values` & `test_xb15_unaligned_address`)
- `SMUT-09` (BLOCKER): CLOSED (`mutation/sanity/run_sanity.py` kills `SMUT-09` at `tb/pyuvm/sequences/directed_seqs.py:54`)
- `SMUT-10` (BLOCKER): CLOSED (`mutation/sanity/run_sanity.py` kills `SMUT-10` at `tb/block/test_axil_xbar.py:405`)
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
- `DOD-01` (BLOCKER): CLOSED (Phase A gate verified: 16/16 sanity mutants KILLED, Rule 6 fixed, 8 tests rewritten, 20 fresh seeds PASS)
- `DOD-02` (MAJOR): CLOSED (20 Icarus seeds `601..620` in Phase A + 20 Verilator coverage seeds `1..20` in Phase C PASS)
- `DOD-03` (BLOCKER): CLOSED (`make cov-report` exits 0; 267/267 100.00% real coverage + `DEC-009`/`DEC-010` waivers)
- `DOD-04` (MAJOR): CLOSED (10/10 formal suites PASS in `docs/logs/phase_b_formal.log` with 0 undriven-wire warnings & no weakening assumptions)
- `DOD-05` (BLOCKER): CLOSED (frozen `mutation/mutant_list_240.json` D3 baseline 165/240 -> D5 final 205/240 raw 85.42% / 93.61% adj via `docs/mutation_report.md`)
- `DOD-06` (BLOCKER): OPEN (assigned to Phase E E1-E4)
- `DOD-07` (MAJOR): OPEN (assigned to Phase G G)
- `DOD-08` (BLOCKER): OPEN (assigned to Phase F F2/F3/F5)
- `DOD-09` (BLOCKER): OPEN (assigned to Phase F F6)
- `VPLAN-AUDIT` (BLOCKER): OPEN (assigned to Phase F F2)
- `BUGS-AUDIT` (MAJOR): OPEN (assigned to Phase F F3)
- `DECISIONS-AUDIT` (MAJOR): OPEN (assigned to Phase F F4)
