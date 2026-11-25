# AMBA-Fabric Second Remediation Report (`docs/FIX_REPORT_R2.md`)

Tracks remediation of the independent adversarial audit on commit `8664339` (`audit_input/AUDIT_REPORT.md`: 33 BLOCKER, 37 MAJOR, 12 MINOR, 5 INFO).

---

## Phase Summary

| Phase | Scope & Audit IDs | Status | Commits |
|---|---|---|---|
| **Phase A** | RTL Rule 6 fix (`axil_csr`), CDC reset fix, models, decisions (`DEC-006..008`), 8 test rewrites (`XB-03/07/12/14/15`, `UA-02`, `BR-05`, `CD-03`), 16 sanity mutants | `DONE` | `fix(R2-A)` (this commit) |
| **Phase B** | Formal (`rr_arbiter_props.v`, bounded fairness, `sync_fifo` data ordering, bridge/xbar over-assumptions, CSR causality/Rule 6, exact wording) | `DONE` | [`docs/logs/phase_b_formal.log`](logs/phase_b_formal.log) |
| **Phase C** | Honest coverage (`CdcMonitor` edge measurement, stimulus for 44 holes, waivers, `make cov-report` fix & full re-measure) | `DONE` | [`docs/logs/func_cov.log`](logs/func_cov.log) |
| **Phase D** | Mutation (`run_mutants.py` process group kill, `axil_xbar` scope fix, CSR/bridge test gaps, 240-mutant run, script-generated report) | `DONE` | [`docs/mutation_report.md`](mutation_report.md) |
| **Phase E** | Synthesis & STA (`synth/synth.ys`, portable reset false-path constraints, dynamic `fmax_sweep.py` parsing, clean measurements) | `DONE` | [`docs/logs/phase_e_fmax_sweep.log`](logs/phase_e_fmax_sweep.log) |
| **Phase F** | Data-driven docs (`scripts/gen_metrics.py`, `docs/metrics.json`, regenerate docs, `bugs.md` / `decisions.md` / `interfaces.md`, CI check scripts) | `DONE` | [`docs/metrics.json`](metrics.json) |
| **Phase G** | CI (`ci.yml` artifact/command alignment, fresh checkout check, remote GitHub Actions verification) | `DONE` | [run `45602303543`](https://github.com/i-am-somasai/AMBA-AXI4-Lite-APB4-Fabric-Subsystem-pyuvm-Verification-Environment/actions/runs/45602303543) |
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
- **Log Paths:** [`docs/logs/phase_b_lint.log`](logs/phase_b_lint.log), [`docs/logs/phase_b_formal.log`](logs/phase_b_formal.log), [`docs/logs/formal_suite.log`](logs/formal_suite.log), [`docs/logs/phase_b_unit.log`](logs/phase_b_unit.log)
- **Before / After Numbers:**
  - Before: `rr_arbiter_props.v` orphaned; no bounded fairness; `sync_fifo` lacked data-ordering proof; over-assumptions in `axil2apb_bridge_props.v` and `axil_xbar_props.v`; `coverage_waivers.md:43` claimed "exhaustively proven".
  - After: **10/10** formal suites PASS (`apb_timer` prove d=20 4c, `apb_uart` bmc d=25 9c, `async_fifo` bmc d=25 4c, `axil2apb_bridge` bmc d=25 10c, `axil_cdc_bridge` bmc d=30 5c, `axil_csr` prv+bmc d=20 5c, `axil_ram` bmc d=20 5c, `axil_xbar` bmc d=20 31c, `rr_arbiter` prove d=20 3c, `sync_fifo` prove d=20 8c), **0** undriven-wire warnings, **0** counterexamples from removing over-assumptions (no RTL bugs triggered, no reduced depth/DATA_WIDTH needed); `rr_arbiter` documented as standalone verified block (`DEC-007`).
- **Remaining Issues:** `V-06` stays `OPEN` until Phase C1 fixes `CdcMonitor` period measurement (Phase B formal half closed).

---

### Phase C: Honest Functional & Code Coverage (`V-04`, `V-05`, `COV-*`)
- **Status:** `DONE`
- **Files Changed:** `tb/pyuvm/func_cov/fabric_cov.py`, `tb/pyuvm/monitors/fabric_monitors.py`, `tb/models/axil_driver.py`, `tb/pyuvm/sequences/{axil_seq_item.py,axil_base_seq.py,coverage_closure_seq.py}`, `tb/pyuvm/agents/axil_master_agent.py`, `tb/pyuvm/tests/test_directed.py`, `tb/pyuvm/Makefile`, `tb/block/{Makefile.single,test_axil2apb_bridge.py}`, `scripts/{merge_cov.py,run_regression.sh}`, `docs/{coverage_waivers.md,decisions.md,audit_r2_tracking.csv,FIX_REPORT_R2.md}`
- **Commands Run:** `./scripts/check_no_synthetic_cov.sh`, `make cov-report`, `python3 scripts/merge_cov.py docs/logs`
- **Log Paths:** [`docs/logs/phase_c_cov_report.log`](logs/phase_c_cov_report.log), [`docs/logs/func_cov.log`](logs/func_cov.log), [`docs/logs/code_cov_summary.txt`](logs/code_cov_summary.txt)
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
- **Status:** `DONE`
- **Files Changed:** `synth/synth.ys`, `Makefile`, `scripts/env.sh`, `synth/sta.tcl`, `synth/fmax_sweep.py`, `docs/{decisions.md,audit_r2_tracking.csv,FIX_REPORT_R2.md}`
- **Commands Run:** `rm -rf synth/results && make clean && make synth && make sta` (executed twice from clean to verify determinism), negative empty-query `sta.tcl` check, `grep` hardcoded/`/home/` check
- **Log Paths:** [`docs/logs/phase_e_synth.log`](logs/phase_e_synth.log), [`docs/logs/phase_e_sta.log`](logs/phase_e_sta.log), [`docs/logs/phase_e_fmax_sweep.log`](logs/phase_e_fmax_sweep.log)
- **Before / After Numbers:**
  - Before: `synth/synth.ys` missing from git; `sta.tcl` & `fmax_sweep.py` hardcoded stale cell IDs (`_14798_`, `_14800_`); `fmax_sweep.py` printed hardcoded `81.63 MHz` & `_12691_/DE` critical path text; fresh STA yielded `-19.33 ns`.
  - After: `synth/synth.ys` committed & invoked via `Makefile` (`RAM_DEPTH=64` confirmed via `2,048` `u_ram.mem[0..63]` flops); **9,237 cells**, **3,630 sequential flops** (`1,140` `dfrtp_1` + `10` `dfstp_1` + `2,480` `edfxtp_1`), **138,086.19 um2** chip area (`74.78%` sequential). Constraint validation fails `sta.tcl` on any empty query (verified exit `1`); `rst_n` false-path targets only the 4 `rst_sync` cells while `rst_sys_n`/`rst_slow_n` recovery/removal remain TIMED (`DEC-011`). Full pre-layout netlist at `clk_sys=10.0 ns`: **WNS = -18.60 ns**, **TNS = -54046.39 ns** (`asynchronous` reset recovery on unbuffered fanout-958 `rst_sys_n`, slew `29.27 ns`, **Fmax = 34.97 MHz @ 28.60 ns**), `clk_sys` setup `-15.48 ns`, `clk_slow` setup `+16.64 ns` (`MET`), hold `+0.23 ns` (`MET`), `check_setup` `5` constant-`1'b1` unconstrained endpoints. Reference core datapath+IO (`rst_sync` Q isolated in STA only): **WNS = -5.89 ns**, **TNS = -16999.71 ns**, **Fmax = 62.89 MHz @ 15.90 ns** (`s1_axil_awaddr[15] -> _12228_/DE`, pure reg-to-reg `-4.15 ns`). Two clean builds produced byte-identical `sta.log`/`fmax_sweep.log` and identical `synth` stats; zero hardcoded cell/Fmax strings or `/home/` paths remain.
- **Remaining Issues:** Target `100 MHz` is **VIOLATED** (`-18.60 ns` full netlist / `-5.89 ns` datapath+IO); unbuffered 958-load `rst_sys_n` recovery is a pre-layout limitation documented in `DEC-011` pending physical reset-tree buffering (OpenLane CTS/resizer, `S-03` out of scope).

---

### Phase F: Data-Driven Documentation (`METRIC-*`, `VPLAN-AUDIT`, `BUGS-AUDIT`, `DECISIONS-AUDIT`, `DOD-08/09`)
- **Status:** `DONE`
- **Files Changed:** `scripts/{gen_metrics.py,doc_blocks.py,gen_docs.py,check_docs_consistency.py,check_bug_refs.py,gen_test_map.py}`, `Makefile`, `README.md`, `docs/{metrics.json,results.md,vplan.md,test_map.csv,bugs.md,interfaces.md,decisions.md,FIX_REPORT_R2.md,audit_r2_tracking.csv}`, `docs/logs/{synth.log,sta.log,fmax_sweep.log,regression_20seeds.log,phase_f_*}`
- **Commands Run:** `make unit SIM=icarus && make block SIM=icarus && make -C tb/pyuvm test_directed SIM=icarus && make -C tb/pyuvm test_stress SIM=icarus SEED=42`, `python3 scripts/gen_test_map.py`, `python3 scripts/gen_metrics.py`, `python3 scripts/gen_docs.py`, `make lint` (running `check_no_synthetic_cov.sh` + `check_bug_refs.py` + `check_docs_consistency.py` + Verilator lint)
- **Log Paths:** [`docs/logs/phase_f_lint.log`](logs/phase_f_lint.log), [`docs/logs/phase_f_unit.log`](logs/phase_f_unit.log), [`docs/logs/phase_f_block.log`](logs/phase_f_block.log), [`docs/logs/phase_f_pyuvm_directed.log`](logs/phase_f_pyuvm_directed.log), [`docs/logs/phase_f_stress_seed42.log`](logs/phase_f_stress_seed42.log)
- **Before / After Numbers:**
  - Before: Contradictory hand-typed metrics across `README.md`, `docs/results.md`, `docs/vplan.md` (`3,238` vs `3,759` lines, `21` vs `22` bugs, `83.88%` vs `100%` coverage, `8/8` vs `10/10` formal); broken links (`BUG-022` non-existent test file, `BUG-012` missing class, stale canonical STA logs); unlogged `axil_decoder` / `synth.ys` deviations.
  - After: Single authoritative [`docs/metrics.json`](metrics.json) (`17` modules, `3,200` non-blank/non-comment RTL lines, `61` test defs, `77` XML runs, `40/40` Spec 9.1 PASS, `267/267` `100.00%` coverage, `92.0%` Verilator line cov, `10/10` formal, `205/240` raw / `93.61%` adj mutation, `24` bugs `BUG-001..BUG-024`, `9,237` cells / `3,630` flops / `138,086.19 um2`, `-18.60 ns` full WNS / `34.97 MHz` pre-layout reset limit vs `62.89 MHz` datapath+IO ref, CI `NOT VERIFIED`). All 21 generated `<!-- BEGIN:metrics:* -->` blocks across `README.md`, `docs/results.md`, and `docs/vplan.md` pass `check_docs_consistency.py` with `0` diffs, `0` stale strings, and `0` broken links; `check_bug_refs.py` passes on all 24 bugs; `make lint` exits `0`.
- **Remaining Issues:** None for Phase F (`CI Status` remains `NOT VERIFIED` until Phase G pushes and confirms a remote GitHub Actions run).

---

### Phase G: CI & Final Clean-Clone Re-Measure (`CI-WORKFLOW`, `CI-REMOTE`, `V-10`)
- **Status:** `DONE`
- **Files Changed:** `.github/workflows/ci.yml`, `Makefile`, `tb/{unit,block}/Makefile.single`, `mutation/run_mutants.py`, `requirements.txt`, `scripts/{gen_metrics.py,doc_blocks.py}`, `README.md`, `docs/{metrics.json,results.md,vplan.md,audit_r2_tracking.csv,FIX_REPORT_R2.md,logs/ci_remote_verified.json,logs/phase_g_ci_local_check.log}`
- **Commands Run:** Fresh clean-clone CI run (`build/clean_clone_ci`, without `scripts/env.sh`), `git push -u origin remediation-r2`, remote GitHub Actions run `45602303543` (`c46cc77`), `python3 scripts/gen_metrics.py`, `python3 scripts/gen_docs.py`, `make lint`
- **Log Paths:** [`docs/logs/phase_g_ci_local_check.log`](logs/phase_g_ci_local_check.log), [`docs/logs/ci_remote_verified.json`](logs/ci_remote_verified.json), [GitHub Actions Run `45602303543`](https://github.com/i-am-somasai/AMBA-AXI4-Lite-APB4-Fabric-Subsystem-pyuvm-Verification-Environment/actions/runs/45602303543)
- **Before / After Numbers:**
  - Before: `CI Status: PASS` unverified on GitHub; `.github/workflows/ci.yml` did not trigger on `remediation-*`, used conflicting `setup-python` against `oss-cad-suite` `vvp` `PYTHONHOME`, and uploaded unbuilt `docs/logs/` & `synth/results/`.
  - After: `.github/workflows/ci.yml` triggers on `[main, 'phase-*', 'remediation-*']`, pins `YosysHQ/setup-oss-cad-suite@v3` (`2026-11-22`), uses `oss-cad-suite` bundled Python 3.11 (`tabbypy3`, `DEC-002`) with pinned `requirements.txt`, enforces `check_no_synthetic_cov.sh`, `check_bug_refs.py`, `check_docs_consistency.py`, `make lint`, `make unit`, `make block`, `make regress SEEDS=3`, `run_sanity.py` (16/16), `make formal` (10/10), `make mutation-sample`, and uploads only `build/results/` & `docs/logs/formal_suite.log` (`27,329` bytes). Remote run `45602303543` completed `success` across all steps; `docs/metrics.json`, `README.md`, and `docs/results.md` updated via `ci_remote_verified.json`.
- **Remaining Issues:** Ready for Final clean-clone re-measure and `remediation-r2-done` tag.

---

## Commit & Tag Log

| Commit SHA | Phase | Message | Gate Evidence |
|---|---|---|---|
| `4df91d4` | R2-00 | Initialize R2 tracking, isolate `BUILD_DIR`, untrack XMLs | `docs/audit_r2_tracking.csv` |
| `98f336d` | Phase A | CSR Rule 6, CDC independent reset, 8 weak tests, 16 sanity mutants | `docs/logs/phase_a_*.log` (`16/16 KILLED`) |
| `8d88475` | Phase B | Bind `rr_arbiter_props`, `sync_fifo` data order, remove over-assumptions | `docs/logs/phase_b_formal.log` (`10/10 PASS`) |
| `570b96d` | Phase C | Honest `CdcMonitor` timing, close 44 holes (`267/267`), fix `cov-report` | `docs/logs/func_cov.log`, `docs/logs/code_cov_summary.txt` |
| `99e5a4d`, `52bf157` | Phase D | Runner scope/pgid, frozen 240-mutant run (`205/240` raw, `93.61%` adj) | `docs/mutation_report.md`, `docs/logs/mutation*.log` |
| `d2291b4` | Phase E | `synth/synth.ys`, portable reset constraints, dynamic `fmax_sweep.py` | `docs/logs/phase_e_{synth,sta,fmax_sweep}.log` |
| `4fed12c` | Phase F | `gen_metrics.py`, `metrics.json`, `doc_blocks`, bug/doc checks | `docs/logs/phase_f_lint.log` |
| `4896e57`..`c46cc77`+ | Phase G | Aligned `ci.yml`, `oss-cad-suite` Python 3.11, green remote CI run | Run `45602303543`, `docs/logs/phase_g_ci_local_check.log` |

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
- `V-10` (MAJOR): CLOSED (green remote GitHub Actions run `45602303543` on `c46cc77` with built-only artifacts `27,329` bytes)
- `S-01` (BLOCKER): CLOSED (`synth/synth.ys` committed, `9237` cells / `3630` flops / `138086.19 um2`, dynamic OpenSTA `-18.60 ns` recovery WNS / `34.97 MHz` full netlist & `-5.89 ns` / `62.89 MHz` datapath+IO ref)
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
- `SYNTH-YS` (BLOCKER): CLOSED (`synth/synth.ys` committed and invoked by `Makefile` `synth` target in `docs/logs/phase_e_synth.log`)
- `SYNTH-STA` (BLOCKER): CLOSED (`sta.tcl` enforces non-empty queries, keeps `rst_sys_n`/`rst_slow_n` timed per E2, runs `check_setup`, dynamic `fmax_sweep.py` parsing in `docs/logs/phase_e_sta.log`)
- `SYNTH-REPORT` (BLOCKER): CLOSED (dynamically parsed synthesis & STA metrics in `docs/logs/phase_e_{synth,sta,fmax_sweep}.log`; `100 MHz` violation stated honestly)
- `CI-REMOTE` (MAJOR): CLOSED (pushed `remediation-r2` to `origin`; GitHub Actions run `45602303543` `completed/success`)
- `LAYOUT-SYNTH_YS` (BLOCKER): CLOSED (`synth/synth.ys` committed at Spec Sec 15 path)
- `METRIC-01` (BLOCKER): CLOSED (`scripts/gen_metrics.py` measures `17` modules / `3,200` non-blank non-comment lines across `rtl/**/*.v`)
- `METRIC-02` (BLOCKER): CLOSED (`61` Python defs / `77` XML testcases PASS / `40/40` Spec 9.1 PASS in `docs/test_map.csv` & `docs/metrics.json`)
- `METRIC-05` (BLOCKER): CLOSED (`267/267` `100.00%` across 24 merged YAMLs populated via `doc_blocks.py`)
- `METRIC-06` (MAJOR): CLOSED (`Line 92.0% | Branch 91.2% | Expr 93.8% | Toggle 74.8% | FSM State 100.0%` populated from `docs/metrics.json`)
- `METRIC-07` (MAJOR): CLOSED (`10/10` formal suites + `84` covers regenerated across `README.md`/`results.md`/`vplan.md` from `docs/metrics.json`)
- `METRIC-09` (BLOCKER): CLOSED (`165/240` -> `205/240` `85.42%` raw / `93.61%` adj populated from `docs/metrics.json`)
- `METRIC-10` (MAJOR): CLOSED (`24` sequential bugs `BUG-001..BUG-024` verified by `scripts/check_bug_refs.py` & `docs/metrics.json`)
- `METRIC-12` (BLOCKER): CLOSED (`9,237` cells / `3,630` flops (`2,048` RAM) / `138,086.19 um2` populated from `docs/metrics.json`)
- `METRIC-13` (BLOCKER): CLOSED (`WNS -18.60 ns / TNS -54046.39 ns / 34.97 MHz` & `62.89 MHz` datapath+IO ref populated from `docs/metrics.json`)
- `METRIC-14` (MAJOR): CLOSED (`CI Status: PASS` + run `45602303543` URL recorded via `ci_remote_verified.json` -> `metrics.json` -> `README.md`/`results.md`)
- `DOD-01` (BLOCKER): CLOSED (Phase A gate verified: 16/16 sanity mutants KILLED, Rule 6 fixed, 8 tests rewritten, 20 fresh seeds PASS)
- `DOD-02` (MAJOR): CLOSED (20 Icarus seeds `601..620` in Phase A + 20 Verilator coverage seeds `1..20` in Phase C PASS)
- `DOD-03` (BLOCKER): CLOSED (`make cov-report` exits 0; 267/267 100.00% real coverage + `DEC-009`/`DEC-010` waivers)
- `DOD-04` (MAJOR): CLOSED (10/10 formal suites PASS in `docs/logs/phase_b_formal.log` with 0 undriven-wire warnings & no weakening assumptions)
- `DOD-05` (BLOCKER): CLOSED (frozen `mutation/mutant_list_240.json` D3 baseline 165/240 -> D5 final 205/240 raw 85.42% / 93.61% adj via `docs/mutation_report.md`)
- `DOD-06` (BLOCKER): CLOSED (two clean `make synth && make sta` runs yielded byte-identical `sta.log`/`fmax_sweep.log` & identical `synth` stats)
- `DOD-07` (MAJOR): CLOSED (verified green CI run `45602303543` and updated CI badge/table links in `README.md` & `docs/results.md`)
- `DOD-08` (BLOCKER): CLOSED (`README.md`, `results.md`, `vplan.md` generated via `BEGIN:metrics` blocks; `make lint` enforces `check_bug_refs.py` & `check_docs_consistency.py`)
- `DOD-09` (BLOCKER): CLOSED (`README.md` Section 9 resume bullets generated solely inside `BEGIN:metrics:readme_resume_bullets` from `docs/metrics.json`)
- `VPLAN-AUDIT` (BLOCKER): CLOSED (`docs/vplan.md` Sections 1..6 regenerated cleanly from `docs/metrics.json` & `docs/test_map.csv`)
- `BUGS-AUDIT` (MAJOR): CLOSED (`BUG-012/014/016/017/019/022` refs fixed; `scripts/check_bug_refs.py` verifies all 24 bugs PASS)
- `DECISIONS-AUDIT` (MAJOR): CLOSED (`docs/interfaces.md` updated for `axil_decoder` `[3:0]` `slave_sel`; `DEC-006..DEC-013` recorded in `docs/decisions.md`)
