# Independent Re-Audit Report (R3) — AMBA-Fabric

> Local file paths were replaced with <WORK_DIR> for publication; findings are unchanged.


## 1. Computed Verdict & Executive Summary

**Computed Verdict:** `READY WITH MINOR ISSUES`

- **Audited Branch / Commit:** `origin/release-prep` (`4bd08534f3a7ebb5f99c3322843b2703eab7ac96`)
- **Clean Clone Scope:** Fresh GitHub clone (`214` tracked files) into `<WORK_DIR>/clone`.
- **Severity Totals (Computed):** `0` BLOCKER, `0` MAJOR, `15` MINOR across `64` audited checks.
- **Summary:** All 16 prior `MAJOR` findings were substantially remediated on `origin/release-prep` (`4bd0853`): `GP-02` / `SMUT-17` now enforce `+1`/`+2`/`+3` cycle 2-FF GPIO latency (`17/17` sanity mutants killed + `5/5` new independent bugs killed), `axil2apb_bridge` was upgraded to unbounded `prove` (`abc pdr`), bounded formal rationales are documented in `docs/limitations.md`, all bounded `EQUIV_BMC10` equivalence claims were eliminated (`0` bounded equivalents; `17` unbounded/dead equivalents in repo, `18` in fresh rerun), `README.md` S0 address range was fixed to `0x4000_0000 - 0x4000_FFFF` (`64 KB`), and GitHub Actions run `45665895644` passed on the exact audited commit SHA `4bd08534f3a7ebb5f99c3322843b2703eab7ac96`.
- **Local Note:** Local `release-prep` in `<WORK_DIR>` holds 2 unpushed commits (`47f25a2` recording run `45665895644` and `3f80da4` adding `docs/FIX_REPORT_R3.md`) ahead of pushed `origin/release-prep` (`4bd0853`).

## 2. Scorecard

| Category | Total | PASS | FAIL | PARTIAL | NOT_FOUND | NOT_RUN | N/A |
|---|---:|---:|---:|---:|---:|---:|---:|
| Prior MAJOR Closure | 16 | 9 | 0 | 7 | 0 | 0 | 0 |
| Clean Clone Build | 9 | 9 | 0 | 0 | 0 | 0 | 0 |
| Sanity & Bug Injection | 6 | 6 | 0 | 0 | 0 | 0 | 0 |
| Mutation & Spot Checks | 7 | 5 | 0 | 2 | 0 | 0 | 0 |
| Formal Verification | 3 | 2 | 0 | 1 | 0 | 0 | 0 |
| Docs vs RTL | 5 | 2 | 0 | 3 | 0 | 0 | 0 |
| Metric Honesty | 12 | 12 | 0 | 0 | 0 | 0 | 0 |
| Regression Checks | 6 | 4 | 0 | 2 | 0 | 0 | 0 |
| **Overall** | **64** | **49** | **0** | **15** | **0** | **0** | **0** |

- **Severity Breakdown:** `BLOCKER=0`, `MAJOR=0`, `MINOR=15`, `NONE=49`.

## 3. Closure Table for the 16 Prior MAJOR Findings

| Prior ID | Closure | Status | Severity | Evidence & Observed Verification |
|---|---|---|---|---|
| **GP-02** | **CLOSED** | PASS | NONE | `tb/block/test_apb_gpio.py:51-150; 03_block.log` — test_gp02_input_sync_latency now verifies IN==0x0000 at +1 cycle on 0->1 step, unchanged 0xBEEF at +1 on 1->0 step, 1-cycle pulse (+1/+2/+3), and sync_gpio_q2 timing. |
| **SANITY-10** | **CLOSED** | PASS | NONE | `mutation/sanity/run_sanity.py:240-250; 07_sanity.log` — SMUT-17 (reducing apb_gpio 2-FF sync to 1-FF) added to committed sanity suite and KILLED by test_apb_gpio.test_gp02_input_sync_latency at line 97. |
| **FORMAL-BRIDGE** | **CLOSED** | PASS | NONE | `formal/axil2apb_bridge.sby:1-14; formal/axil2apb_bridge_props.v:336-345` — Upgraded from bmc to mode prove (abc pdr); passes in 2s with 10 covers reached. 1-bit single-outstanding causality matches axil_props contract without hiding behavior. |
| **FORMAL-XBAR** | **PARTIAL** | PARTIAL | MINOR | `formal/axil_xbar.sby:1-12; docs/limitations.md:15; 04_formal.log` — Passes BMC depth 20 in 41s with 31 covers (>18-cycle liveness bound); still bounded BMC (abc pdr timed out >5m, smtbmc k-induction blocked by hierarchical refs on frozen RTL), honestly disclosed in docs/limitations.md:15. |
| **FORMAL-CDC** | **PARTIAL** | PARTIAL | MINOR | `formal/axil_cdc_bridge.sby:1-23; docs/limitations.md:13; rtl/cdc/axil_cdc_bridge.v:383-388` — Passes multiclock BMC depth 30 in 78s with 5 covers; remains bounded due to SymbiYosys async2sync multiclock unrolling (documented in docs/limitations.md:13). Note existing assume(rst_sys_n/rst_slow_n) after cycle 0 excludes mid-flight formal reset (covered by CD-03 sim). |
| **V-07** | **PARTIAL** | PARTIAL | MINOR | `scripts/run_all_formal.sh; README.md:164-169; docs/limitations.md:9-20` — All 10/10 SBY suites PASS (84 covers, 149s fresh): 4 unbounded prove (incl. axil2apb_bridge abc pdr), 1 hybrid prv+bmc (axil_csr), 5 bounded BMC d=20..30 with honest modes and technical rationales in docs/limitations.md. |
| **DOD-04** | **PARTIAL** | PARTIAL | MINOR | `docs/spec.md:837; formal/*.sby; docs/limitations.md:9-20` — All 10 formal suites pass with 84/84 cover traces reached; axil2apb_bridge closed to unbounded prove while 5 suites remain bounded BMC with documented rationales. |
| **FORMAL-WORDING** | **CLOSED** | PASS | NONE | `README.md:177; docs/mutation_report.md:24-28; grep 'proven equivalent'` — README.md:177 and docs/mutation_report.md:24-28 strictly distinguish 17 unbounded-proven/dead-signal equivalents from 0 bounded-equivalent (depth 10); historical FIX_REPORT.md:144 refers only to R1. |
| **MUT-EQUIV-CLAIM** | **CLOSED** | PASS | NONE | `mutation/check_equiv.py:6-13; docs/logs/mutation_equiv.log:1-21; 12_mutation_equiv.log` — Every formal equivalence proof in check_equiv.py uses Yosys equiv_induct (3) or SBY mode prove abc pdr (11 in repo log, 12 in fresh rerun incl. axil2apb_bridge #3) plus 3 dead-signal proofs; 0 bounded BMC10 claims. |
| **METRIC-09** | **PARTIAL** | PARTIAL | MINOR | `docs/results.md:22,125; docs/mutation_report.md:21-28; 11_mutation_frozen.log; 12_mutation_equiv.log` — Wording defect is fixed (0 bounded d=10). Fresh frozen rerun killed 218/240 (90.83% raw, 18 unbounded/dead equiv, 98.20% adj) vs repo 219/240 (91.25% raw, 17 equiv, 98.21% adj) because axil2apb_bridge #3 (s_axil_bresp[0]=0, EQUIV_PROVE) survived our rerun. |
| **DOC-README-ADDR** | **CLOSED** | PASS | NONE | `README.md:109; rtl/axil/axil_decoder.v:6-7; scripts/check_docs_consistency.py:37-51` — README.md:109 now reports S0 as 0x4000_0000 - 0x4000_FFFF (64 KB) matching S0_MASK=32'hFFFF_0000 and enforced by check_docs_consistency.py. |
| **DOD-08** | **CLOSED** | PASS | NONE | `README.md:109,217,314; docs/decisions.md:24-25; docs/coverage_waivers.md:12-23` — README S0 range fixed, README:314 tree updated to axil_master_agent.py, DEC-014/DEC-015 logged, coverage_waivers.md updated to 303/36/267 leaf-bin accounting, contention.png present. |
| **V-10** | **CLOSED** | PASS | NONE | `.github/workflows/ci.yml:1-71; user CI run 45665895644 on 4bd08534f3a7ebb5f99c3322843b2703eab7ac96` — All ci.yml steps pass locally on clean clone. User supplied GitHub Actions run 45665895644 (https://github.com/i-am-somasai/AMBA-AXI4-Lite-APB4-Fabric-Subsystem-pyuvm-Verification-Environment/actions/runs/45665895644) completed/success with head_sha=4bd08534f3a7ebb5f99c3322843b2703eab7ac96 matching origin/release-prep exactly (gh CLI absent locally). |
| **CI-REMOTE** | **CLOSED** | PARTIAL | MINOR | `docs/logs/ci_remote_verified.json; README.md:5,143; user CI run 45665895644` — Audited commit 4bd0853 honestly states PENDING (no false green SHA mismatch); user-verified run 45665895644 matches 4bd0853 100% (success), leaving only a minor unpushed doc update (47f25a2) to replace PENDING. |
| **METRIC-14** | **CLOSED** | PASS | NONE | `README.md:143; docs/results.md:26; docs/logs/ci_remote_verified.json; run 45665895644` — Audited commit 4bd0853 reports PENDING rather than an older stale run, and external user-supplied run 45665895644 confirms green CI on exact SHA 4bd0853. |
| **DOD-07** | **CLOSED** | PARTIAL | MINOR | `README.md:4-5; .github/workflows/ci.yml; user CI run 45665895644` — Remote CI run 45665895644 succeeded on exact audited SHA 4bd0853 and live workflow badge targets branch release-prep; static shields.io badge in README.md:5 still reads PENDING on 4bd0853 until 47f25a2 is pushed. |

## 4. Clean-Clone Build, Simulation, Formal, Synthesis & STA

- `make env-check`: **PASS** (`iverilog 14.0`, `verilator 5.055`, `yosys 0.71+77`, `sby`, `OpenSTA 2.6.0`, `SKY130`, Python `cocotb`/`pyuvm`/`cocotb-coverage`).
- `make lint`: **PASS** (`<WORK_DIR>/logs/01_lint.log`).
- `make unit SIM=icarus`: **PASS** (`14/14` across 9 XMLs, `<WORK_DIR>/logs/02_unit.log`).
- `make block SIM=icarus`: **PASS** (`38/38` across 7 XMLs, `<WORK_DIR>/logs/03_block.log`).
- `make regress SIM=icarus SEEDS="801..820"`: **PASS** (`20/20` fresh seeds, `200,000` txns, `0` mismatches, `<WORK_DIR>/logs/05_regress_20icarus.log`).
- `make cov-report`: **PASS** (`20/20` Verilator seeds `1..20` = `200,000` txns; `267/267 = 100.00%` func cov across 24 YAMLs; Verilator Line `92.4%` `496/537`, Branch `91.6%` `501/547`, Expr `93.8%` `1036/1105`, Toggle `76.2%` `10821/14202`, `<WORK_DIR>/logs/06_cov_report.log`).
- `make formal`: **PASS** (`10/10` SBY tasks, `84` covers in `149s`, `<WORK_DIR>/logs/04_formal.log`).
- `make synth` & `make sta`: **PASS** (`9,237` cells, `3,630` flops, `138,086.19 um^2`, `74.78%` seq; Full WNS `-18.60 ns` / `34.97 MHz`, Core+IO ref WNS `-5.89 ns` / `62.89 MHz`, `clk_slow +16.64 ns` MET, hold `+0.23 ns` MET; `<WORK_DIR>/logs/08_synth.log`, `<WORK_DIR>/logs/09_sta.log`).

## 5. GP-02, Committed Sanity Gate & 5 Independent Injected Bugs

- **Committed Sanity Gate (`make sanity`):** **17/17 KILLED** (`0` survived, `0` invalid, `<WORK_DIR>/logs/07_sanity.log`), including `SMUT-17` (GPIO 1-FF bypass) killed at `tb/block/test_apb_gpio.py:97`.
- **5 Independent Injected Bugs (`inject_5_bugs.py`, `<WORK_DIR>/logs/10_inject_5_bugs.log`):** **5/5 KILLED** after passing both `iverilog -g2012` and `verilator --lint-only -Wall`:

| Bug ID | Injected Defect | Catching Tests |
|---|---|---|
| **ABUG-01** | Independent bug 1: UART baud-divisor off-by-one (baud_cnt >= reg_bauddiv + 1) (`rtl/apb/apb_uart.v:120`) | KILLED cleanly after passing iverilog+Verilator lint; caught by test_apb_uart.test_ua03_bauddiv_sweep and test_apb_uart.test_ua04_framing_error. |
| **ABUG-02** | Independent bug 2: Timer W1C clears on pwdata[1] instead of pwdata[0] (`rtl/apb/apb_timer.v:83`) | KILLED cleanly after passing iverilog+Verilator lint; caught by test_apb_timer.test_tm02_periodic_countdown and test_apb_timer.test_tm03_w1c_timeout_and_irq_clear. |
| **ABUG-03** | Independent bug 3: CSR IRQ_MASK[0] ignored in reg_irq_status (`rtl/axil/axil_csr.v:57`) | KILLED cleanly after passing iverilog+Verilator lint; caught by test_axil_csr.test_cs03_irq_aggregation and test_axil_csr.test_cs04_ooo_w1c32_ro_wo_and_backpressure. |
| **ABUG-04** | Independent bug 4: slow_regs SLOW_SCRATCH WSTRB[2] lane dropped (`rtl/cdc/slow_regs.v:82`) | KILLED cleanly after passing iverilog+Verilator lint; caught by test_axil_cdc_bridge.test_cd01_ratio_phase_sweep and test_axil_cdc_bridge.test_cd03_reset_recovery. |
| **ABUG-05** | Independent bug 5: Bridge m_apb_pstrb forced to 4'b1111 on reads (`rtl/apb/axil2apb_bridge.v:155`) | KILLED by test_axil2apb_bridge.test_br07_apb_wait_err_cov and test_br08_addr_walk_and_ooo_backpressure (note: test_br04_pstrb_patterns only checks writes). |

## 6. Frozen Mutation Rerun, Equivalence Wording & Survivor Spot-Check

- **Frozen 240-Mutant Rerun (`mutation/mutant_list_240.json`):** **`218/240` KILLED (`90.83%` raw)**, `22` survived, `0` timeouts, `0` build errors in `290.89s` (`<WORK_DIR>/logs/11_mutation_frozen.log`).
- **Equivalence Analysis (`mutation/check_equiv.py`, `<WORK_DIR>/logs/12_mutation_equiv.log`):** Of the `22` fresh survivors, **`18` are unbounded-proven or structurally dead** (`12` SBY `mode prove` `abc pdr` + `3` Yosys `equiv_induct` + `3` `u_default_slave._unused_inputs` dead-wire proofs), `0` are `bounded-equivalent (depth 10)`, and **`4` are residual** (`axil_xbar #0, #9, #13, #16`). Fresh conservative adjusted score: **`98.20%` (`218/222`)**.
- **1-Mutant Delta vs Repo (`219/240` in `docs/mutation_report.md`):** `axil2apb_bridge #3` (`const0` on `$procdff$314` `s_axil_bresp[0]`) survived `test_axil2apb_bridge` (`8/8 PASS`) in our fresh run and was proved `EQUIV_PROVE (sby abc pdr)` because `s_axil_bresp[0]` is identically `0` in `axil2apb_bridge.v:169`.
- **Wording Verification:** `grep -rn 'proven equivalent' README.md docs/` confirms `README.md:177` and `docs/mutation_report.md:24-28` reserve unbounded-proven wording strictly for unbounded `equiv_induct` / SBY `prove` (`abc pdr`) / dead-signal proofs (`0` bounded depth-10 claims).
- **Spot-Check of 6 Survivors (`MUT-SPOT-1..6`):** Verified `axil2apb_bridge #3` (`EQUIV_PROVE`), `axil2apb_bridge #23` (`EQUIV_PROVE` on constant `4'b0000` bit 2), `axil_csr #18` (`EQUIV_PROVE` on `read_word[5]==1` compare), `axil_decoder #1` (`EQUIV_YOSYS` redundant mask bit), `axil_xbar #5` (`SIGNAL_PROOF` dead `def_araddr[2]`), and `axil_xbar #0` (`SIGNAL_TRIAGE` residual gap on `wr_prio[gt]==0`).

## 7. Formal Verification, Modes, `docs/limitations.md` & Assumptions

- **Mode Parity:** Every `.sby` task mode (`3` `k-induction prove`, `1` `PDR prove` on `axil2apb_bridge`, `1` `prv+bmc` on `axil_csr`, `5` `bmc d=20..30`) matches `README.md:164-168` and `docs/results.md:63-73`. Only `docs/vplan.md:55` (outside managed blocks) still reads `BMC depth 25` for `F-06`/`axil2apb_bridge.sby` (`MINOR`).
- **`docs/limitations.md` Review:** Accurately explains why `axil_cdc_bridge` (`multiclock` + `async2sync` d=30), `async_fifo` (`multiclock` + `async2sync` d=25), `axil_xbar` (`abc pdr` >5m timeouts & hierarchical refs on frozen RTL, d=20 > 18-cycle liveness), `axil_ram` (d=20 array state), and `apb_uart` (d=25 serial frame depth) remain bounded.
- **New & Existing Assumptions:** New R3 assumption in `formal/axil2apb_bridge_props.v:338-340` (`f_aw_seen`/`f_w_seen`/`f_rd_live_active` 1-bit causality) replaces 8-bit wrapping counters without hiding any valid single-outstanding bridge behavior. Existing post-reset `assume(rst_n)` in `axil_xbar_props.v:219` and `axil_cdc_bridge.v:385,387` keeps formal reset asserted after cycle 0 (mid-flight reset verified in simulation via `XB-12` and `CD-03`).

## 8. Docs vs RTL & CI Verification

- **Address Map Regeneration:** Regenerated S0–S3 from `rtl/axil/axil_decoder.v` via `gen_metrics.parse_memory_map()` — matches `README.md:109-115` identically (`S0: 0x4000_0000 - 0x4000_FFFF`, `64 KB`).
- **Coverage Waivers (`docs/coverage_waivers.md`):** Total `303` defined / `36` waived / `267` reachable (`100.00%`) aligns with `docs/results.md` (`MINOR`: `fabric_cov.py:111` omits `'full'` from `cg_cdc.occupancy` bins, so `cocotb-coverage` reports `19` `cg_cdc` bins while `coverage_waivers.md` adds the `6` excluded `'full'` bins = `25`).
- **Docs Consistency:** `scripts/check_docs_consistency.py` and `scripts/check_bug_refs.py` both exited `0` (`0` diffs, `0` stale patterns, `0` broken links, `24/24` bug refs valid).
- **CI Verification:** `gh` CLI unavailable; user provided GitHub Actions run `45665895644` (https://github.com/i-am-somasai/AMBA-AXI4-Lite-APB4-Fabric-Subsystem-pyuvm-Verification-Environment/actions/runs/45665895644), status `completed / success`, `head_sha = 4bd08534f3a7ebb5f99c3322843b2703eab7ac96` matching `origin/release-prep` (`4bd0853`) identically. On `4bd0853`, `README.md:5,143` and `docs/logs/ci_remote_verified.json` honestly state `PENDING` (local commit `47f25a2` recording `45665895644` has not been pushed yet).

## 9. Metric Honesty Table (`README.md` & `docs/results.md`)

| Metric ID | Metric | Claimed (`README` / `docs/results.md`) | Fresh Measured | Match? |
|---|---|---|---|---|
| **METRIC-01** | RTL modules (17) and non-blank non-comment lines (3,200) | `docs/results.md:15,34-53` | Fresh measurement on clean clone: 17 modules, 3,200 non-blank non-comment lines across rtl/**/*.v (exact match). | **PASS** |
| **METRIC-02** | Test defs (61), XML runs (96), Spec map (40/40) | `docs/results.md:16` | Fresh AST count = 61 unique decorated tests (14 unit, 38 block, 8 pyuvm_directed, 1 stress); 40/40 Spec IDs PASS. Note fresh local run leaves 66 XMLs because cov-report cleans block before re-running bridge+pyuvm. | **PASS** |
| **METRIC-03** | Random transactions (200k Verilator + 200k Icarus, 0 mismatches) | `05_regress_20icarus.log` | Fresh measured: 200,000 Icarus txns (fresh seeds 801..820, 0 mismatches) + 200,000 Verilator txns (seeds 1..20, 0 mismatches) = 400,000 txns. | **PASS** |
| **METRIC-04** | 20 Verilator + 20 Icarus seeds passed | `05_regress_20icarus.log` | Fresh measured: 20/20 fresh Icarus seeds (801..820) and 20/20 Verilator seeds (1..20) passed cleanly. | **PASS** |
| **METRIC-05** | Functional coverage 100.00% (267/267 reachable, 24 YAMLs, 36 waived) | `docs/logs/func_cov.log` | Fresh cov-report merged 24 YAML files and achieved 267/267 (100.00%) reachable bins with zero holes. | **PASS** |
| **METRIC-06** | Verilator code coverage (Line 92.4%, Branch 91.6%, Expr 93.8%, Toggle 76.2%) | `docs/logs/code_cov_summary.txt` | Fresh cov-report reproduced exact deterministic points: Line 92.4% (496/537), Branch 91.6% (501/547), Expr 93.8% (1036/1105), Toggle 76.2% (10821/14202), FSM State 100.0% (5/5), FSM Arc 25.0% (1/4). | **PASS** |
| **METRIC-07** | Formal verification (10/10 PASS, 84 covers, 152s claimed) | `04_formal.log` | Fresh measured: 10/10 suites PASS, 84 covers reached, 149s total runtime (vs 152s in archived log, normal wall-clock variance) with exact mode match. | **PASS** |
| **METRIC-08** | CDC ratios & phases (3 slow periods x 3 phases, formal depth 25/30) | `03_block.log` | Verified 25.0 ns, 10.3 ns, 6.0 ns slow clock periods x phases in CD-01 and TestCoverageClosure plus formal async_fifo d=25 and axil_cdc_bridge d=30. | **PASS** |
| **METRIC-10** | Bugs found & resolved (24 bugs: 15 RTL + 9 TB/formal/tooling) | `docs/bugs.md` | Verified 24 sequential bug entries (BUG-001..BUG-024) and all regression test references valid via check_bug_refs.py. | **PASS** |
| **METRIC-11** | Crossbar added latency (0 cycles) | `tb/block/test_axil_xbar.py (test_xb06_parallel_different_slaves)` | XB-06 parallel M0->S0 and M1->S1 transfer test passed cleanly in 03_block.log confirming 0 added serialization cycles. | **PASS** |
| **METRIC-12** | Synthesis SKY130 HD (9,237 cells / 3,630 flops / 138,086.19 um^2) | `08_synth.log` | Fresh Yosys synthesis reproduced identical 9,237 cells, 3,630 flops (1,140 dfrtp_1 + 10 dfstp_1 + 2,480 edfxtp_1), 138,086.19 um^2 area, and 74.78% sequential. | **PASS** |
| **METRIC-13** | STA 100 MHz WNS -18.60 ns / TNS -54046.39 ns / 34.97 MHz (62.89 MHz ref) | `09_sta.log` | Fresh OpenSTA sweep reproduced identical numbers: full WNS -18.60 ns, TNS -54046.39 ns, 34.97 MHz (28.60 ns), clk_slow +16.64 ns, hold +0.23 ns, core+IO ref -5.89 ns (62.89 MHz). | **PASS** |
| **METRIC-09** | Mutation score metric honesty (raw, unbounded equiv, adjusted) | `docs/results.md:22,125` | Wording defect is fixed (0 bounded d=10). Fresh frozen rerun killed 218/240 (90.83% raw, 18 unbounded/dead equiv, 98.20% adj) vs repo 219/240 (91.25% raw, 17 equiv, 98.21% adj) because axil2apb_bridge #3 (s_axil_bresp[0]=0, EQUIV_PROVE) survived our rerun. | **PARTIAL** |
| **METRIC-14** | Published CI status metric matches verified state | `README.md:143` | Audited commit 4bd0853 reports PENDING rather than an older stale run, and external user-supplied run 45665895644 confirms green CI on exact SHA 4bd0853. | **PASS** |

## 10. Regression Results & New Defects

| Check ID | Requirement | Status | Severity | Details |
|---|---|---|---|---|
| **REG-NO-SYNTH-COV** | No sample_* calls outside monitors/func_cov | PASS | NONE | Both check_no_synthetic_cov.sh and independent grep across tb/ confirmed zero sample_* calls outside fabric_cov.py and fabric_monitors.py. |
| **REG-0X60000001-ALIGNED** | 0x6000_0001 behaves as word-aligned 0x6000_0000 (Rule 6) | PASS | NONE | axil_csr decodes [7:2] ignoring [1:0]; test_cs01 (+1/+2/+3 on 0x6000_0000) and test_xb15_unaligned_address both passed in fresh runs (and SMUT-11 killed). |
| **REG-NO-HOME-PATHS** | No hardcoded <WORK_DIR>/ paths in git-tracked files | PASS | NONE | git grep '<WORK_DIR>/' matched only regex/sed sanitizers and generic prose explanations in docs/FIX_REPORT*.md and docs/decisions.md; zero hardcoded personal paths. |
| **REG-NO-GEN-TRACKED** | No build/sim/mutation/formal generated artifacts tracked in git | PASS | NONE | Zero sim_build/, obj_dir/, *.vcd, *.fst, *.xml, *.dat, or build/ files tracked; only intentional frozen mutation/mutant_list_240.json and archived docs/logs/ exist. |
| **REG-LINT-ICARUS** | Icarus @* array-sensitivity warnings in axil_xbar.v documented | PARTIAL | MINOR | Non-fatal iverilog @* unpacked-array warnings remain on axil_xbar.v (Verilator lint clean); intentionally preserved to keep mutant hashes stable and documented in docs/limitations.md:25-34. |
| **REG-MAKEFILE-NEWLINE** | Top-level Makefile SEEDS parameter handling for multi-seed lists | PARTIAL | MINOR | Space-separated SEEDS="801 802 ... 820" now works cleanly via Makefile:78 quotes, though newline-separated SEEDS="$(seq 801 820)" breaks bash echo quoting on Makefile:76. |

- **New Minor Defects Observed:**
  1. `DOC-VPLAN-F06`: `docs/vplan.md:55` still cites `formal/axil2apb_bridge.sby (BMC depth 25)` instead of `PDR (prove)`.
  2. `DOC-BR04-SCOPE`: `tb/block/test_axil2apb_bridge.py:251-294` (`test_br04_pstrb_patterns`) only tests write `PSTRB` values; read `PSTRB==0` is covered by `test_br07` and `test_br08` rather than `BR-04`.
  3. `METRIC-09` (`218` vs `219`): `axil2apb_bridge #3` (`s_axil_bresp[0] = 0`, `EQUIV_PROVE`) survived fresh rerun (`218/240`) vs `docs/logs/mutation.log` (`219/240`).
  4. `CI-REMOTE` / `DOD-07` (`PENDING` on pushed SHA): Commit `47f25a2` recording green CI run `45665895644` and `3f80da4` (`FIX_REPORT_R3.md`) remain local/unpushed ahead of `origin/release-prep` (`4bd0853`).

## 11. Prioritized Remediation List

- **BLOCKER (0):** None.
- **MAJOR (0):** None.
- **MINOR (15):**
  - **FORMAL-XBAR** (`formal/axil_xbar.sby:1-12; docs/limitations.md:15; 04_formal.log`): Passes BMC depth 20 in 41s with 31 covers (>18-cycle liveness bound); still bounded BMC (abc pdr timed out >5m, smtbmc k-induction blocked by hierarchical refs on frozen RTL), honestly disclosed in docs/limitations.md:15.
  - **FORMAL-CDC** (`formal/axil_cdc_bridge.sby:1-23; docs/limitations.md:13; rtl/cdc/axil_cdc_bridge.v:383-388`): Passes multiclock BMC depth 30 in 78s with 5 covers; remains bounded due to SymbiYosys async2sync multiclock unrolling (documented in docs/limitations.md:13). Note existing assume(rst_sys_n/rst_slow_n) after cycle 0 excludes mid-flight formal reset (covered by CD-03 sim).
  - **V-07** (`scripts/run_all_formal.sh; README.md:164-169; docs/limitations.md:9-20`): All 10/10 SBY suites PASS (84 covers, 149s fresh): 4 unbounded prove (incl. axil2apb_bridge abc pdr), 1 hybrid prv+bmc (axil_csr), 5 bounded BMC d=20..30 with honest modes and technical rationales in docs/limitations.md.
  - **DOD-04** (`docs/spec.md:837; formal/*.sby; docs/limitations.md:9-20`): All 10 formal suites pass with 84/84 cover traces reached; axil2apb_bridge closed to unbounded prove while 5 suites remain bounded BMC with documented rationales.
  - **METRIC-09** (`docs/results.md:22,125; docs/mutation_report.md:21-28; 11_mutation_frozen.log; 12_mutation_equiv.log`): Wording defect is fixed (0 bounded d=10). Fresh frozen rerun killed 218/240 (90.83% raw, 18 unbounded/dead equiv, 98.20% adj) vs repo 219/240 (91.25% raw, 17 equiv, 98.21% adj) because axil2apb_bridge #3 (s_axil_bresp[0]=0, EQUIV_PROVE) survived our rerun.
  - **CI-REMOTE** (`docs/logs/ci_remote_verified.json; README.md:5,143; user CI run 45665895644`): Audited commit 4bd0853 honestly states PENDING (no false green SHA mismatch); user-verified run 45665895644 matches 4bd0853 100% (success), leaving only a minor unpushed doc update (47f25a2) to replace PENDING.
  - **DOD-07** (`README.md:4-5; .github/workflows/ci.yml; user CI run 45665895644`): Remote CI run 45665895644 succeeded on exact audited SHA 4bd0853 and live workflow badge targets branch release-prep; static shields.io badge in README.md:5 still reads PENDING on 4bd0853 until 47f25a2 is pushed.
  - **MUT-FROZEN-240** (`mutation/run_mutants.py --mutant-list mutation/mutant_list_240.json; 11_mutation_frozen.log`): Fresh run scored 218/240 raw (90.83%, 22 survivors, 0 tmo, 0 bld_err, 290.89s) vs repo docs/logs/mutation.log 219/240 (91.25%); delta is 1 mutant (axil2apb_bridge #3), proved unbounded-equivalent by SBY abc pdr.
  - **MUT-SPOT-6** (`rtl/axil/axil_xbar.v:299; docs/mutation_report.md:82; 12_mutation_equiv.log:9`): Residual non-equivalent survivor (SIGNAL_TRIAGE): forces wr_prio[gt]==1'b0 comparison to 1 on one generated target instance; reflects genuine minor L1 contention coverage gap on non-S1 targets.
  - **FORMAL-ASSUMPTIONS** (`formal/axil2apb_bridge_props.v:336-345; formal/axil_xbar_props.v:215-220; rtl/cdc/axil_cdc_bridge.v:383-388`): New R3 assumption in axil2apb_bridge_props.v:338-340 (1-bit f_aw_seen/f_w_seen/f_rd_live_active) enforces SINGLE_OUTSTANDING=1 without hiding bridge FSM states. Pre-existing post-reset assume(rst_n) in axil_xbar_props.v:219 and axil_cdc_bridge.v:385,387 excludes mid-flight reset in formal (covered in sim by XB-12/CD-03).
  - **DOC-WAIVERS-CHECK** (`docs/coverage_waivers.md:12-23; tb/pyuvm/func_cov/fabric_cov.py:105-113; docs/logs/func_cov.log`): Leaf-bin accounting totals 303 defined / 36 waived / 267 reachable (100.00%). Minor note: fabric_cov.py:111 omits 'full' from cg_cdc.occupancy bins=['empty','partial'], so cocotb-coverage sees 19 cg_cdc bins while waivers add 6 conceptual 'full' bins (25).
  - **DOC-VPLAN-F06** (`docs/vplan.md:55; formal/axil2apb_bridge.sby:6-12`): New minor doc defect: docs/vplan.md:55 (outside managed metrics blocks) still says 'formal/axil2apb_bridge.sby (BMC depth 25)' instead of 'PDR (prove)'.
  - **DOC-BR04-SCOPE** (`docs/vplan.md:96; tb/block/test_axil2apb_bridge.py:251-294; 10_inject_5_bugs.log`): New minor finding: test_br04_pstrb_patterns only exercises writes (pwrite==1), while PSTRB==0 on reads is checked by test_br07 and test_br08 (exposed by ABUG-05).
  - **REG-LINT-ICARUS** (`rtl/axil/axil_xbar.v:203-213,370-513; docs/limitations.md:25-34; 03_block.log`): Non-fatal iverilog @* unpacked-array warnings remain on axil_xbar.v (Verilator lint clean); intentionally preserved to keep mutant hashes stable and documented in docs/limitations.md:25-34.
  - **REG-MAKEFILE-NEWLINE** (`Makefile:76-78; 05_regress_20icarus.log`): Space-separated SEEDS="801 802 ... 820" now works cleanly via Makefile:78 quotes, though newline-separated SEEDS="$(seq 801 820)" breaks bash echo quoting on Makefile:76.
