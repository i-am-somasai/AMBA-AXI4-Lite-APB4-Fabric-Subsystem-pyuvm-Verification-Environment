# AMBA-Fabric Third Remediation & Release Prep Report (`docs/FIX_REPORT_R3.md`)

Tracks closure of the **16 MAJOR** findings (and targeted fidelity / documentation / build items) identified by the third adversarial audit (`audit_input/AUDIT_REPORT.md` on commit `338fd18`, `remediation-r2`), without modifying RTL files unless an unavoidable bug is confirmed and approved.

---

## Acceptance Checks & Execution Log

### Task R3-1 — `GP-02`, `SMUT-17` Sanity Gate, and Test Fidelity Upgrades (`GP-02`, `SANITY-10`, `UA-01`, `TM-02`, `BR-02`, `XB-02`, `XB-03`)

#### Pre-Task Acceptance Checks (Written Before Execution)
1. **GPIO 2-FF latency (`GP-02`):**
   - Command: `make -C tb/block -f Makefile.single TOPLEVEL=apb_gpio MODULE=test_apb_gpio COCOTB_TEST_FILTER=test_gp02_input_sync_latency SIM=icarus`
   - Expected: `TESTS=1 PASS=1 FAIL=0`; verifies APB `IN` (`0x08`) is unchanged at `+1` cycle and updated at `+2` cycles for `0->1` and `1->0`, and that a 1-cycle `gpio_i` pulse produces unchanged `IN` at `+1`, matches the pulse at `+2`, and returns to `0` at `+3` (with optional read-only synchronizer flop cross-check).
2. **Sanity mutant `SMUT-17` & `metrics.json`-driven count:**
   - Command: `bash scripts/run_sanity.sh | tee docs/logs/sanity.log` (or `make sanity`)
   - Expected: Exit `0`; every sanity mutant compiles cleanly (`0 INVALID`), **`17/17 KILLED, 0 SURVIVED`**; `SMUT-17` (GPIO 2-FF -> 1-FF) killed specifically by an explicit assertion failure in `test_gp02_input_sync_latency` (exact assertion line logged, not timeout/crash/build failure); sanity counts in `docs/metrics.json` and generated docs flow from `docs/logs/sanity.log`.
3. **UART `UA-01` (all 256 byte values), Timer `TM-02` (exact `LOAD+1` period), Bridge `BR-02` (cycle-by-cycle APB signal hold while `PREADY=0`), Crossbar `XB-02`/`XB-03` docstrings + `docs/vplan.md` L2 citations:**
   - Commands: `make unit SIM=icarus`, `make block SIM=icarus`, `python3 scripts/gen_test_map.py`, `python3 scripts/gen_metrics.py`, `python3 scripts/gen_docs.py`, `make lint`
   - Expected: Exit `0`, zero failures across all unit/block tests and consistency gates; `docs/vplan.md` rows `XB-02` and `XB-03` explicitly cite the covering L0/L2 tests.
4. **Full 20-seed regression (after all R3-1 edits):**
   - Command: `make -C tb/pyuvm -j2 SIM=icarus SEEDS="$(seq 721 740)" regress`
   - Expected: `20/20` fresh seeds pass (`0` failures, `0` scoreboard mismatches).

#### Measured Results & Evidence
- **Status:** `DONE`
- **`GP-02` & `SMUT-17`:** Rewrote `test_gp02_input_sync_latency` in `tb/block/test_apb_gpio.py` to repeat isolated APB read `SETUP` capture experiments aligned to `+1`, `+2`, and `+3` cycles for `0->1`, `1->0`, and a `1-cycle` pulse (`0xCAFE`), plus read-only cross-checks of internal `sync_gpio_q2`. Added `SMUT-17` (`sync_gpio_q2 <= gpio_i | ...` 1-FF bypass) to `mutation/sanity/run_sanity.py` and wired `sanity` metrics via `scripts/gen_metrics.py` and `scripts/doc_blocks.py` (`docs/logs/sanity.log` -> `docs/metrics.json`).
  - Gate command: `make sanity` (`python3 mutation/sanity/run_sanity.py | tee docs/logs/sanity.log`) -> **`17/17 KILLED, 0 SURVIVED, 0 INVALID`**, exit `0`.
  - **`SMUT-17` Kill Proof:** Killed by explicit assertion in `test_apb_gpio.test_gp02_input_sync_latency` at `tb/block/test_apb_gpio.py:97` (`GP-02 0->1 (+1 cycle): expected unchanged 0x0000`) with `0` build/lint errors (`docs/logs/sanity.log:18`).
- **Fidelity Upgrades (`UA-01`, `TM-02`, `BR-02`, `XB-02`, `XB-03`):**
  - `UA-01` (`tb/block/test_apb_uart.py:25-63`): loops all `256` byte values (`0..255`).
  - `TM-02` (`tb/block/test_apb_timer.py:67-109`): asserts exact `LOAD + 1 = 9` cycle period across all `4` periodic iterations.
  - `BR-02` (`tb/block/test_axil2apb_bridge.py:160-206`): cycle-by-cycle check in test body asserts `PSEL`, `PENABLE`, `PADDR`, `PWRITE`, `PWDATA`, and `PSTRB` remain held on every `PREADY=0` wait cycle across wait states `1, 2, 4`.
  - `XB-02`, `XB-03` (`tb/block/test_axil_xbar.py:180-217`, `scripts/doc_blocks.py`, `docs/vplan.md`): L1 docstrings and `docs/vplan.md` rows now explicitly cite L0/L2 covering tests (`test_axil_ram_operations`, `test_top01_register_map_connectivity`, `test_cs02_access_types_w1c`, `test_sys_strobe_patterns`). Also fixed `scripts/gen_test_map.py:131` so `parse_results_xmls()` scans only `build/results/` (ignoring `build/sanity/` mutant failure XMLs).
- **Unit, Block, Lint & 20-Seed Regression:**
  - `make unit SIM=icarus && make block SIM=icarus && make lint`: all PASS (`EXIT=0`), `40/40` spec tests PASS in `docs/test_map.csv`.
  - `make -C tb/pyuvm -j4 SIM=icarus SEEDS="$(seq 721 740)" regress | tee docs/logs/r3_1_regress_20seeds.log`: `20/20` fresh seeds (`721..740`) PASS, `10,000` txns/seed (`200,000` total), `0` mismatches (`docs/logs/r3_1_regress_20seeds.log`).

---

### Task R3-2 — Honest "Equivalent" Mutant Wording & Real Gap Tests (`MUT-EQUIV-CLAIM`, `FORMAL-WORDING`, `METRIC-09`)

#### Pre-Task Acceptance Checks (Written Before Execution)
1. **Formal equivalence upgrade on the 15 `EQUIV_BMC10` survivors:**
   - Command: `python3 mutation/check_equiv.py | tee docs/logs/mutation_equiv.log` (runs Yosys `equiv_induct` / SBY `prove` miter first, falling back to `BOUNDED_EQUIV_BMC10` (`bounded-equivalent (depth 10)`) only when unbounded proof fails/times out).
   - Expected: Reproducible deterministic log `docs/logs/mutation_equiv.log` distinguishing unbounded `EQUIV_YOSYS` / `EQUIV_PROVE` / `SIGNAL_PROOF` from `BOUNDED_EQUIV_BMC10` (`bounded-equivalent (depth 10)`). Never uses `"proven"` for bounded miters.
2. **Real test gaps (`axil2apb_bridge #13`, `axil_csr #19`, `rr_arbiter #22`, `axil_ram #0`):**
   - Inspect each survivor; construct a formal CEX / unit or block test where a counterexample is reachable (`tb/block/test_axil2apb_bridge.py`, `tb/unit/test_axil_csr.py`, `tb/unit/test_rr_arbiter.py`, `tb/unit/test_axil_ram.py`).
   - Run affected tests: `make unit SIM=icarus`, `make block SIM=icarus`, `make sanity`.
   - Rerun the **frozen 240-mutant list** (`python3 mutation/run_mutants.py --mutant-list mutation/mutant_list_240.json --seed 42 -j4 --output docs/logs/mutation.log`) and record before (`165/240 = 68.75%` D3 baseline, `205/240 = 85.42%` R2) and after kill counts.
3. **Report regeneration & wording check:**
   - Commands: `python3 mutation/gen_mutation_report.py`, `python3 scripts/gen_metrics.py`, `python3 scripts/gen_docs.py`, `make lint`
   - Expected: `docs/mutation_report.md`, `docs/results.md`, and `README.md` (Section 5.3 & Resume Bullets) report: (a) raw score first (`baseline -> final`), (b) conservative adjusted score (unbounded-proven + structurally dead survivors only), and (c) separate bounded-adjusted score labeled `"bounded-equivalent (depth 10)"`.
   - Command: `grep -rn "proven equivalent" README.md docs/`
   - Expected: Matches **only** unbounded-proven cases (zero hits describing depth-10 bounded miters as `"proven"`).

#### Measured Results & Evidence
- **Status:** `DONE`
- **Equivalence Upgrades (`mutation/check_equiv.py` -> `docs/logs/mutation_equiv.log`):**
  - Replaced unscripted bounded `EQUIV_BMC10` calls with reproducible [`mutation/check_equiv.py`](../mutation/check_equiv.py), attempting Yosys `equiv_induct` and SymbiYosys `mode prove` (`abc pdr`) on sequential miters before falling back to `BOUNDED_EQUIV_BMC10` (`bounded-equivalent (depth 10)`).
  - Auditing the `15` formerly `EQUIV_BMC10` survivors exposed `3` that actually had reachable counterexamples (`axil_csr #04` step 6, `axil_csr #25` step 6, `sync_fifo #28` step 10), while `12` (`rr_arbiter #01/#05/#08/#16/#24/#28`, `sync_fifo #24`, `axil_csr #18/#24`, `axil2apb_bridge #03/#23/#29`) closed unboundedly via SymbiYosys `prove` (`abc pdr`).
- **Gap Tests Added & Frozen 240-Mutant Re-Run (`docs/logs/mutation.log`):**
  - `axil2apb_bridge #13`: Updated `test_br08_addr_walk_and_ooo_backpressure` (`tb/block/test_axil2apb_bridge.py:515-589`) to walk all `32` address bits on both `w_first` and `aw_first`, set bit 27 (`0x4800_0100`) in manual `w_first`, and assert APB pin stability during `ST_ACCESS`.
  - `axil_csr #19`, `#04`, `#25`: Added explicit `BVALID` hold (`BREADY=0`) and clear checks, multi-bit `W1C_TEST` isolation across unrelated writes, and odd 1-cycle `w_first` stagger checks in `tb/unit/test_axil_csr.py:270-346`.
  - `rr_arbiter #22`, `#23`: Added single-requester repeat checks with `lock=0` in `tb/unit/test_rr_arbiter.py:157-174`.
  - `axil_ram #0`, `#02`, `#08`, `#18`, `#22`, `#23`: Added immediate per-word readback + `WSTRB=0` retention checks across all `256` words in `tb/unit/test_axil_ram.py:67-113` (`30/30` = `100.00%` on `axil_ram`).
  - `sync_fifo #28`: Added `0x08|i` bit-pair independence sweeps with `0`-cycle and `1`-cycle idle holds in `tb/unit/test_sync_fifo.py:102-119`.
  - **Before / After on Frozen `mutation/mutant_list_240.json`:** D3 baseline `165/240 (68.75%)` -> R2 `205/240 (85.42%)` -> **R3-2 Final `219/240 KILLED (91.25% raw)`**, `0` timeouts, `0` build errors, `21` total survivors (`14` unbounded-proven `equiv_induct`/SBY `prove` `abc pdr` + `3` structurally dead `SIGNAL_PROOF` on `axil_default_slave._unused_inputs` = **`17` unbounded/dead equivalent**, **`0` `bounded-equivalent (depth 10)`**, `4` residual `SIGNAL_TRIAGE` on `axil_xbar`).
  - **Adjusted Scores:** Conservative adjusted score (unbounded-proven + structurally dead only) = **`98.21% (219/223)`**; adjusted score including bounded-equivalent (depth 10) = **`98.21% (219/223)`**.
- **Regenerated Reports & Gates:**
  - `python3 mutation/gen_mutation_report.py && python3 scripts/gen_metrics.py && python3 scripts/gen_docs.py && make lint`: EXIT `0`; `grep -rn -i "proven equivalent" README.md docs/` matches `README.md:173` (unbounded-proven/structurally dead only, `0` bounded) and historical `docs/FIX_REPORT.md:144`.
  - `make unit SIM=icarus && make block SIM=icarus && make -C tb/pyuvm -j2 SIM=icarus SEEDS=1 regress && make sanity`: all PASS (`EXIT=0`, `40/40` spec tests PASS, `17/17` sanity mutants KILLED).

---

### Task R3-3 — Formal `prove` Attempts on Bridge & Crossbar, and Honest Mode Reporting (`V-07`, `FORMAL-XBAR`, `FORMAL-BRIDGE`, `FORMAL-CDC`, `DOD-04`, `FORMAL-WORDING`)

#### Pre-Task Acceptance Checks (Written Before Execution)
1. **`k-induction (prove)` attempt on `axil2apb_bridge` then `axil_xbar`:**
   - Place any inductive strengthening invariants strictly in `formal/axil2apb_bridge_props.v` and `formal/axil_xbar_props.v` (zero RTL edits); never add behaviour-hiding assumptions (document any assumption with reason).
   - Run `(cd formal && sby -f axil2apb_bridge.sby)` and `(cd formal && sby -f axil_xbar.sby)` (time-boxed <= 30 min each). If induction closes (`DONE (PASS)`), retain `prove`; otherwise retain bounded `bmc` and document why in `docs/limitations.md`. `axil_cdc_bridge` (multiclock) stays `bmc`.
2. **Formal suite regression & honest mode table:**
   - Commands: `make formal | tee docs/logs/formal_suite.log`, `python3 scripts/gen_metrics.py`, `python3 scripts/gen_docs.py`, `make lint`
   - Expected: `10/10` formal suites PASS (`EXIT=0`), `docs/limitations.md` exists documenting all remaining bounded suites (reason + depth), and `README.md` + `docs/results.md` + `docs/vplan.md` state for every suite exact `k-induction (prove)` or `BMC depth N` directly from the run log.
3. **Full verification check:**
   - Commands: `make unit SIM=icarus`, `make block SIM=icarus`, `make sanity`, `make lint`
   - Expected: Zero regressions (`EXIT=0`).

#### Measured Results & Evidence
- **Status:** `DONE`
- **No RTL Edits:** Zero files under `rtl/` were modified (`git diff --name-only rtl/` empty).
- **`axil2apb_bridge` Upgraded to Unbounded `PDR (prove)` (`abc pdr`):**
  - Updated [`formal/axil2apb_bridge_props.v`](../formal/axil2apb_bridge_props.v) (`CHECK_CAUSALITY(0)` on `u_axil_props` plus 1-bit single-outstanding request/response causality via `f_aw_seen`, `f_w_seen`, and `f_rd_live_active`, eliminating `8`-bit wrapping-counter wraparound in unbounded proof) and [`formal/axil2apb_bridge.sby`](../formal/axil2apb_bridge.sby) (`prove: abc pdr`, `cover: smtbmc boolector`).
  - Result: `axil2apb_bridge` **DONE (`PASS`, `3s`, `10` cover traces)** via unbounded `PDR (prove)`.
- **`axil_xbar` Bounded Rationale (`BMC depth 20`):**
  - Tested both `abc pdr` (timed out on repeated anytime passes after > 300s at `PRV=135` across 2-master × 5-target state + 5-bit liveness timers) and `smtbmc boolector` k-induction (basecase depth 20 passed, induction step 0 failed on slave write stability without hierarchical access to frozen RTL internals `dut.aw_done`/`dut.w_done`/`dut.ar_done`). Retained [`formal/axil_xbar.sby`](../formal/axil_xbar.sby) at `BMC depth 20` and documented every bounded suite in [`docs/limitations.md`](limitations.md).
- **Honest Formal Reporting (`docs/logs/formal_suite.log` -> `docs/metrics.json` -> `README.md`, `docs/results.md`, `docs/vplan.md`):**
  - Updated [`scripts/gen_metrics.py`](../scripts/gen_metrics.py) (`_formal_sby_info` / `method_label`) and [`scripts/doc_blocks.py`](../scripts/doc_blocks.py) so every suite reports exact `k-induction (prove)`, `PDR (prove, abc pdr)`, `k-induction (prove) + BMC depth 20`, or `BMC depth N` (`10/10 PASS`: `apb_timer` `k-induction (prove)`, `rr_arbiter` `k-induction (prove)`, `sync_fifo` `k-induction (prove)`, `axil2apb_bridge` `PDR (prove, abc pdr)`, `axil_csr` `k-induction (prove) + BMC depth 20`, `apb_uart` `BMC depth 25`, `async_fifo` `BMC depth 25, multiclock`, `axil_cdc_bridge` `BMC depth 30, multiclock`, `axil_ram` `BMC depth 20`, `axil_xbar` `BMC depth 20`; `84` covers in `152s`).
- **Verification Gates (`EXIT 0`):**
  - `make formal` -> `Formal suite PASSED (10/10 modules clean)` (`docs/logs/formal_suite.log`).
  - `python3 scripts/gen_metrics.py && python3 scripts/gen_docs.py && make lint` -> `0` diffs, `0` stale strings, `0` broken links, Verilator lint clean.
  - `make unit SIM=icarus && make block SIM=icarus && make sanity && make lint` -> all unit/block tests PASS, `17/17 KILLED` sanity gate (`docs/logs/sanity.log`), lint clean.

---

### Task R3-4 — Decoder-Driven README Memory Map, Coverage Waivers Alignment, Decisions, Limitations & Deterministic Coverage (`DOC-README-ADDR`, `COV-WAIVERS-DOC`, `LINT-ICARUS`, `DOC-README-TREE`, `DOC-DECISIONS`, `CLONE-REGRESS`, `COV-CODE`, `DOD-08`)

#### Pre-Task Acceptance Checks (Written Before Execution)
1. **Decoder-driven `README.md` Memory Map (`DOC-README-ADDR`):**
   - Generate `<!-- BEGIN:metrics:readme_memory_map -->` in `README.md` Section 3 from `rtl/axil/axil_decoder.v` (`S0` = `0x4000_0000 - 0x4000_FFFF`, `64 KB`; `S1` = `0x5000_0000 - 0x5000_0FFF`, `4 KB` slot / `1 KB` RAM; `S2` = `0x6000_0000 - 0x6000_00FF`, `256 B`; `S3` = `0x7000_0000 - 0x7000_00FF`, `256 B`) via `scripts/gen_metrics.py` + `scripts/doc_blocks.py`.
   - Update `scripts/check_docs_consistency.py` to parse `rtl/axil/axil_decoder.v` directly and fail with non-zero exit if `README.md` disagrees with `axil_decoder.v`.
   - Verification check: `python3 scripts/check_docs_consistency.py` exits `0`, and mutating a temporary copy / assertion check proves mismatch fails.
2. **Repository tree, waivers table, `decisions.md`, and Icarus warnings (`DOC-README-TREE`, `COV-WAIVERS-DOC`, `DOC-DECISIONS`, `LINT-ICARUS`):**
   - Update `README.md` Section 10 `tb/pyuvm/agents/` to list only `axil_master_agent.py` (matching disk).
   - Update `docs/coverage_waivers.md` summary table to leaf-bin counts matching `docs/results.md` / `docs/vplan.md` (`303` defined pre-waiver, `36` waived, `267` reachable target).
   - Append `DEC-014` (`axil_default_slave` & `axil_decoder` inside `axil_xbar` vs Spec Sec 7.6) and `DEC-015` (fixed top-level `NUM_MASTERS=2` and internal CDC `async_fifo` `DEPTH=4`) to `docs/decisions.md`.
   - Leave `rtl/axil/axil_xbar.v` untouched (`git diff --name-only rtl/` empty) and document Icarus `iverilog -Wall` `@*` array-sensitivity warnings in `docs/limitations.md`.
3. **Multi-seed `Makefile` quoting & deterministic `make cov-report` (`CLONE-REGRESS`, `COV-CODE`, `DOD-08`):**
   - Quote `"$(SEEDS)"` in `Makefile` (`regress` and `regress-verilator`); fix deterministic `SEED`s for `test_directed` and `test_axil2apb_bridge` in `scripts/run_regression.sh`.
   - Commands & Expected:
     - `make regress SIM=icarus SEEDS="741 742"` -> `EXIT 0` (2 seeds complete cleanly; temp seed YAMLs cleaned so tracked `docs/logs/cov_*.yaml` stay exact).
     - Run `make cov-report` **twice from clean** (`docs/logs/code_cov_summary.txt` diffed between Run 1 and Run 2 -> **byte-identical, 0 diff**), then run `python3 scripts/gen_metrics.py && python3 scripts/gen_docs.py && make lint` (`EXIT 0`).
     - Verify `0` uncommitted RTL changes (`git diff --name-only rtl/` empty) and clean `git status` before committing `fix(R3-04): ...`.

#### Measured Results & Evidence
- **Status:** `DONE`
- **No RTL Edits:** Zero files under `rtl/` were modified (`git diff --name-only rtl/` empty).
- **Decoder-Driven `README.md` Memory Map (`DOC-README-ADDR`):**
  - Added `parse_memory_map()` in [`scripts/gen_metrics.py`](../scripts/gen_metrics.py) parsing `S0_BASE`/`S0_MASK`..`S3_BASE`/`S3_MASK` directly from [`rtl/axil/axil_decoder.v`](../rtl/axil/axil_decoder.v) (`S0`: `0x4000_0000 - 0x4000_FFFF`, `64 KB`; `S1`: `0x5000_0000 - 0x5000_0FFF`, `4 KB` slot / `1 KB` RAM; `S2`: `0x6000_0000 - 0x6000_00FF`, `256 B`; `S3`: `0x7000_0000 - 0x7000_00FF`, `256 B`), rendered into `README.md` via [`scripts/doc_blocks.py`](../scripts/doc_blocks.py) (`<!-- BEGIN:metrics:readme_memory_map -->`).
  - Added `verify_readme_matches_decoder()` and `0x4FFF_FFFF` forbidden-pattern check in [`scripts/check_docs_consistency.py`](../scripts/check_docs_consistency.py); negative test with `0x4FFF_FFFF` failed as expected (`NEGATIVE CHECK PASS`).
- **Repository Tree, Coverage Waivers, Decisions & Icarus Warnings (`DOC-README-TREE`, `COV-WAIVERS-DOC`, `DOC-DECISIONS`, `LINT-ICARUS`):**
  - Updated `README.md` Section 10 `tb/pyuvm/` tree so `agents/` lists only [`tb/pyuvm/agents/axil_master_agent.py`](../tb/pyuvm/agents/axil_master_agent.py) alongside actual `env/`, `monitors/`, `func_cov/`, `sequences/`, and `tests/` files.
  - Updated [`docs/coverage_waivers.md`](coverage_waivers.md) summary table to leaf-bin accounting matching `docs/results.md` and `docs/vplan.md` (**303** defined pre-waiver, **36** waived, **267** reachable target across 32 leaf sub-metrics).
  - Appended `DEC-014` (encapsulation of `axil_decoder` and `axil_default_slave` inside `axil_xbar` vs Spec Sec 7.6) and `DEC-015` (fixed `NUM_MASTERS=2`, `NUM_SLAVES=4`, `FIFO_DEPTH=4` on `amba_fabric_top` sub-instances) to [`docs/decisions.md`](decisions.md).
  - Left [`rtl/axil/axil_xbar.v`](../rtl/axil/axil_xbar.v) untouched and documented `iverilog -g2012 -Wall` `@*` array-sensitivity warnings in [`docs/limitations.md`](limitations.md).
- **Multi-Seed `Makefile` Quoting & Deterministic `make cov-report` (`CLONE-REGRESS`, `COV-CODE`, `DOD-08`):**
  - Quoted `"$(SEEDS)"` in [`Makefile`](../Makefile) lines `78` and `85`; verified `make regress SIM=icarus SEEDS="741 742"` passes both seeds with zero scoreboard mismatches (temp seed YAMLs cleaned afterwards).
  - Pinned `SEED`, `COCOTB_RANDOM_SEED`, and `RANDOM_SEED` propagation in [`tb/pyuvm/Makefile.single`](../tb/pyuvm/Makefile.single), [`tb/block/Makefile.single`](../tb/block/Makefile.single), and [`scripts/run_regression.sh`](../scripts/run_regression.sh) (`42` for `test_directed` & `test_axil2apb_bridge`, `${s}` for seeds `1..20`).
  - Executed `make cov-report` **twice from clean** (`build/r3_4_cov/run1.log`, `build/r3_4_cov/run2.log`): `diff -u` on `code_cov_summary.txt` and `func_cov.log` reported **zero differences** (`CODE_COV_IDENTICAL=YES`, `FUNC_COV_IDENTICAL=YES`): Line **92.4% (496/537)**, Branch **91.6% (501/547)**, Expression **93.8% (1036/1105)**, Toggle **76.2% (10821/14202)**, FSM State **100.0% (5/5)**, FSM Arc **25.0% (1/4)**, Functional **100.00% (267/267)** across 24 merged YAMLs (`docs/logs/phase_c_cov_report.log`, `docs/logs/code_cov_summary.txt`, `docs/logs/func_cov.log`).
- **Final Verification Gates (`EXIT 0`):**
  - Stripped `/home/<user>/` paths from `docs/logs/r3_1_regress_20seeds.log` and `docs/logs/phase_c_cov_report.log`.
  - `make unit SIM=icarus && make block SIM=icarus && make sanity && make lint`: all unit/block XMLs PASS, `17/17 KILLED` sanity gate (`docs/logs/sanity.log`), `README.md`/`docs/results.md`/`docs/vplan.md` regenerated cleanly from `docs/metrics.json` with zero consistency errors and clean Verilator lint.

---

### Task R3-5 — CI Alignment, Clean-Clone Verification & Remote Actions Check (`V-10`, `CI-REMOTE`, `METRIC-14`, `DOD-07`)

#### Pre-Task Acceptance Checks (Written Before Execution)
1. **CI Workflow & Honest Pre-Push CI Status:**
   - Update `.github/workflows/ci.yml` `on.push.branches` to include `'release-*'` so pushing `release-prep` triggers GitHub Actions.
   - Update `docs/logs/ci_remote_verified.json` to `PENDING` (no stale `c46cc77` PASS claim for `release-prep`) and `scripts/doc_blocks.py` (`?branch=release-prep`, valid relative link in `docs/results.md`), then run `python3 scripts/gen_metrics.py && python3 scripts/gen_docs.py && make lint` -> `EXIT 0`.
2. **Clean-Clone Reproduction (`build/r3_5_clean_clone`):**
   - Clone tracked files (`git clone --local . build/r3_5_clean_clone`), source `scripts/env.sh`, and run the exact CI & README quick-start commands:
     `make lint && make unit SIM=icarus && make block SIM=icarus && make regress SIM=icarus SEEDS=1 && make sanity && make formal && make mutation-sample`
   - Plus `grep -rn "/home/" .` inside the clean clone (excluding generated/symlinked `.venv` or `build/`) -> **0 matches** in tracked files, and every CI step **PASS (`EXIT 0`)**.
3. **Branch Push & Remote Actions Confirmation:**
   - Commit `fix(R3-05): ...` cleanly, push `release-prep` to `origin` (or pause for user push if credentials are not configured in this sandbox), and confirm the Actions run is green with commit SHA matching `git rev-parse HEAD`.

#### Measured Results & Evidence
- **Status:** `DONE`
- **CI Workflow & Non-Blocking Annotation:**
  - Updated [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) `on.push.branches` to `[ main, 'phase-*', 'remediation-*', 'release-*' ]`. Left workflow steps unchanged after green run; documented the non-blocking Node.js 20 deprecation annotation (`actions/checkout@v4`, `actions/upload-artifact@v4`, `YosysHQ/setup-oss-cad-suite@v3`) in [`docs/limitations.md`](limitations.md).
- **Verified Remote GitHub Actions Run ([`docs/logs/ci_remote_verified.json`](logs/ci_remote_verified.json)):**
  - **Run URL:** `https://github.com/i-am-somasai/AMBA-AXI4-Lite-APB4-Fabric-Subsystem-pyuvm-Verification-Environment/actions/runs/45665895644`
  - **Status / Event / Branch / Job / Duration:** `Success` (`push` on `release-prep`, workflow `ci.yml`, job `"Lint, Unit, Regression, Formal & Mutation"`, `4m 37s`, artifact `verification-logs-and-reports` `29,664` bytes).
  - **Verified Commit SHA:** `4bd08534f3a7ebb5f99c3322843b2703eab7ac96` (matched `git rev-parse HEAD` when pushed).
  - **Scope Disclosed in `README.md` & `docs/results.md`:** Covers synthetic-cov/bug-ref/doc checks, Verilator lint, L0 unit, L1 block, 3-seed Icarus regression, `17` sanity mutants, `10/10` formal, and `24`-mutant sampled mutation smoke; SKY130 synthesis/STA, full 20-seed Verilator coverage, and the full 240-mutant run remain local-only.
- **Clean-Clone Full CI Reproduction ([`docs/logs/clean_clone_r3.log`](logs/clean_clone_r3.log)):**
  - Cloned committed tree (`git clone --local . build/r3_5_clean_clone`) and ran the entire `.github/workflows/ci.yml` sequence:
    `./scripts/check_no_synthetic_cov.sh && python3 scripts/check_bug_refs.py && python3 scripts/check_docs_consistency.py && make lint && make unit SIM=icarus && make block SIM=icarus && make regress SIM=icarus SEEDS=1 && python3 mutation/sanity/run_sanity.py && make formal && make mutation-sample`
  - Every step exited `0` (`CLEAN_CLONE_CI_PASS=YES`; `17/17` sanity killed; `10/10` formal PASS; `21/24 = 87.50%` sampled mutation, `0` timeouts, `0` build errors; zero personal `/home/<user>/` paths in tracked files).

---

### Task R3-6 — Hostile Self-Audit, Regression Verification & Verdict (`ALL R3-1..R3-5 GATES`)

#### Pre-Task Acceptance Checks (Written Before Execution)
1. **Regression & Hygiene Checks on Current `HEAD`:**
   - `./scripts/check_no_synthetic_cov.sh` -> zero `sample_*` calls outside monitors/collectors (`EXIT 0`).
   - `SEED=42 make -C tb/pyuvm -j2 SIM=icarus test_directed` -> `test_xb15_unaligned_address` verifies `0x6000_0001` behaves as word-aligned per AXI4-Lite Rule 6 (`EXIT 0`).
   - `make unit SIM=icarus && make block SIM=icarus && make sanity && make lint` -> all unit/block XMLs PASS, `17/17` sanity killed (`SMUT-17` at assertion line), zero doc diffs/stale strings/broken links, Verilator lint clean (`EXIT 0`).
   - `git grep -n "/home/<user>/"` (checking `git grep` for actual local usernames) -> `0` matches; `git ls-files` -> `0` generated build/XML/VCD/VVP/`.dat` files; `git diff --stat remediation-r2 -- rtl/` -> empty (`0` RTL edits).
2. **Hostile Self-Audit & Computed Verdict:**
   - Re-verify every one of the 16 `MAJOR` IDs and remaining `MINOR` rows from `audit_input/audit_results.csv` with file path, line numbers, command, and log evidence.
   - List every row that is still not `PASS` honestly, compute the verdict by rule (`any BLOCKER or MAJOR -> NOT READY; only MINOR -> READY WITH MINOR ISSUES; none -> READY`), record out-of-scope observations under **Observations**, and commit `fix(R3-06): ...` with final `make lint` passing.

#### Measured Results & Evidence
- **Status:** `DONE`

#### Hostile Self-Audit of All 16 Audit-3 `MAJOR` IDs & Regression Checks

| Audit ID / Check | Prior Status | Re-Audit Status | Evidence (`file:line`), Command & Verified Observation |
|---|---|---|---|
| **GP-02** | `PARTIAL (MAJOR)` | **PASS** | `tb/block/test_apb_gpio.py:50-152`, `make -C tb/block test_apb_gpio SIM=icarus`: checks `+1`/`+2` on `0->1` (`0xBEEF`), `1->0` (`0x0000`), and `+1`/`+2`/`+3` (`0`/`0xCAFE`/`0`) on 1-cycle pulse + `sync_gpio_q2` flop timing (`3/3 PASS`). |
| **SANITY-10** | `FAIL (MAJOR)` | **PASS** | `mutation/sanity/run_sanity.py` (`SMUT-17`), `make sanity` (`docs/logs/sanity.log`): `17/17 KILLED, 0 SURVIVED, 0 INVALID`; `SMUT-17` killed at `tb/block/test_apb_gpio.py:97` (`assertion failed`). |
| **FORMAL-BRIDGE** | `PARTIAL (MAJOR)` | **PASS** | `formal/axil2apb_bridge.sby:1-14`, `formal/axil2apb_bridge_props.v:89-97,331-343`, `make formal` (`docs/logs/formal_suite.log`): closed unbounded via `PDR (prove, abc pdr)` in `3s` with `10` covers (`0` RTL edits). |
| **FORMAL-WORDING** | `FAIL (MAJOR)` | **PASS** | `README.md:133,160-177`, `docs/results.md:60-74`, `docs/vplan.md:155-171`, `docs/mutation_report.md:24-28`, `docs/limitations.md:1-20`: exact `k-induction (prove)`, `PDR (prove, abc pdr)`, `BMC depth N`, `bounded-equivalent (depth 10)` (`0` bounded cases labeled proven). |
| **MUT-EQUIV-CLAIM** | `PARTIAL (MAJOR)` | **PASS** | `mutation/check_equiv.py`, `docs/logs/mutation_equiv.log`, `docs/mutation_report.md:48-69`: `14` unbounded `equiv_induct` / SBY `prove` + `3` dead-signal `SIGNAL_PROOF` (`axil_default_slave._unused_inputs`), **`0` bounded depth-10**, `4` residual. |
| **METRIC-09** | `PARTIAL (MAJOR)` | **PASS** | `docs/metrics.json`, `docs/results.md:22,115-126`, `docs/logs/mutation.log`: Baseline `165/240 (68.75%)` -> Final `219/240 (91.25% raw)`, `0` tmo/bld_err, Conservative Adj `98.21% (219/223)`, Incl Bounded `98.21% (219/223)`. |
| **DOC-README-ADDR** | `FAIL (MAJOR)` | **PASS** | `README.md:104-119`, `rtl/axil/axil_decoder.v:6-13`, `scripts/check_docs_consistency.py:39-54`: `S0` rendered as `0x4000_0000 - 0x4000_FFFF (64 KB)` directly from `axil_decoder.v`; consistency check fails on mismatch (`EXIT 0`). |
| **DOD-08** | `PARTIAL (MAJOR)` | **PASS** | `README.md`, `docs/results.md`, `docs/vplan.md`, `docs/bugs.md`, `docs/img/*.png`: `python3 scripts/check_docs_consistency.py` -> `0 diffs, 0 stale strings, 0 broken links` (`EXIT 0`). |
| **V-07** | `PARTIAL (MAJOR)` | **PARTIAL (`MAJOR`*)** | `docs/logs/formal_suite.log`, `docs/limitations.md:9-20`: `10/10` PASS (`84` covers, `152s`), `axil2apb_bridge` upgraded to `PDR (prove)`, while `axil_xbar`, `axil_cdc_bridge`, `async_fifo`, `axil_ram`, `apb_uart` remain bounded `BMC depth 20..30`. |
| **FORMAL-XBAR** | `PARTIAL (MAJOR)` | **PARTIAL (`MAJOR`*)** | `formal/axil_xbar.sby:1`, `docs/limitations.md:15`: `abc pdr` timed out >300s (`PRV=135`) and `smtbmc` failed induction step 0 without hierarchical access to frozen RTL internals; retained `BMC depth 20` (`31` covers, `43s`). |
| **FORMAL-CDC** | `PARTIAL (MAJOR)` | **PARTIAL (`MAJOR`*)** | `formal/axil_cdc_bridge.sby:1`, `docs/limitations.md:13`: `multiclock on` (`async2sync`) verified via bounded **`BMC depth 30`** (`5` covers, `82s`), not unbounded `prove`. |
| **DOD-04** | `PARTIAL (MAJOR)` | **PARTIAL (`MAJOR`*)** | `docs/spec.md:834-842`, `docs/logs/formal_suite.log`, `docs/limitations.md`: all 10 `.sby` suites pass (`84` covers), but 5 suites remain bounded `BMC depth 20..30`. |
| **V-10 / CI-REMOTE / METRIC-14 / DOD-07** | `NOT_RUN (MAJOR)` | **PARTIAL (`MINOR`)** | `docs/logs/ci_remote_verified.json`, `docs/logs/clean_clone_r3.log`: GitHub Actions run `45665895644` (`Success`, `4m 37s`, artifact `29,664` bytes) verified green on pushed `release-prep` commit `4bd08534f3a7ebb5f99c3322843b2703eab7ac96`; subsequent doc-only commits (`47f25a2` and R3-6) remain local `[ahead]` of `origin/release-prep`. |
| **Reg: `sample_*`** | - | **PASS** | `./scripts/check_no_synthetic_cov.sh` (`EXIT 0`): `Zero synthetic coverage sampling calls found outside monitor/collector files.` |
| **Reg: `0x6000_0001` Rule 6** | - | **PASS** | `SEED=42 make -C tb/pyuvm -j2 SIM=icarus test_directed` (`test_xb15_unaligned_address PASS`) + `make sanity` `[SMUT-11]` KILLED at `tb/pyuvm/sequences/directed_seqs.py:89`. |
| **Reg: No personal paths / tracked gen / RTL freeze** | - | **PASS** | `git grep -n "/home/<user>/"` (`0` hits for local username), `git ls-files` (`0` tracked build/XML/VCD/VVP/`.dat` files), `git diff --stat remediation-r2 -- rtl/` (`0` files changed in R3). |

*\*Note on severity classification:* Under Audit-3's strict spec checklist (`V-07`, `FORMAL-XBAR`, `FORMAL-CDC`, `DOD-04` graded `MAJOR` whenever core `P0` blocks run `BMC depth N` instead of unbounded `prove`), those 4 rows remain `PARTIAL (MAJOR)`. If documented bounded-BMC limits in [`docs/limitations.md`](limitations.md) are accepted as `MINOR` architectural scope rather than `MAJOR` gaps, then 0 `MAJOR` remain.

#### Complete List of Remaining Non-`PASS` Rows (Honest Accounting)
- **`PARTIAL` (`MAJOR` under Audit-3 unbounded-prove rule):** `V-07`, `FORMAL-XBAR`, `FORMAL-CDC`, `DOD-04`.
- **`PARTIAL` / `NOT_FOUND` (`MINOR`):** `V-10`, `CI-REMOTE`, `METRIC-14`, `DOD-07` (doc-only commits ahead of `4bd0853` green run), `F-02` (`DEC-007` inline arbiter in `axil_xbar`), `V-01` (`DEC-005` cocotb responders in `tb/models/`), `LAYOUT-PORTS` (`DEC-014`/`DEC-015`), `BR-05` (`docs/vplan.md` cites L1 single-master test; L2 dual-master at `test_top02_dual_master_apb_rw`), `DOD-01` (due to `BR-05` ref note), `FORMAL-ASYNC-FIFO` (`BMC depth 25`), `FORMAL-CSR` (`prv+bmc` `DEC-006`), `FORMAL-RAM` (`BMC depth 20`), `FORMAL-UART` (`BMC depth 25`), `LINT-ICARUS` (`axil_xbar.v` `@*` warnings in `docs/limitations.md`), `DOC-MUT-TRIAGE` (consolidated into `docs/mutation_report.md` in `52bf157`).

#### Computed Verdict
- **Computed Verdict (Strict Rule: any `BLOCKER` or `MAJOR` -> `NOT READY`; only `MINOR` -> `READY WITH MINOR ISSUES`; none -> `READY`):**
  - `BLOCKER`: **0**
  - `MAJOR` (under strict Audit-3 unbounded-prove rule on `V-07`, `FORMAL-XBAR`, `FORMAL-CDC`, `DOD-04`): **4** -> **`NOT READY`**
  - *(Conditional note: If documented `BMC depth N` architectural bounds in [`docs/limitations.md`](limitations.md) are accepted as `MINOR` scope rather than `MAJOR`, remaining count is `0 BLOCKER`, `0 MAJOR`, `19 MINOR` -> `READY WITH MINOR ISSUES`.)*

---

### Observations (Out of Scope per Precision Protocol Scope Lock)
1. Legacy R1 archive line [`docs/FIX_REPORT.md:144`](FIX_REPORT.md#L144) retains the historical phrase `"28 proven equivalent"`; all R2/R3 reports, `README.md`, `docs/mutation_report.md`, `docs/results.md`, and `docs/vplan.md` use exact unbounded vs bounded wording.
2. `BR-05` in [`docs/vplan.md`](vplan.md) links only L1 single-master `test_br05_back_to_back_mixed_rw`, while dual-master APB mixed R/W runs in `tb/block/test_amba_fabric_top.py` (`test_top02_dual_master_apb_rw`).
3. Recording green run `45665895644` (`4bd0853`) in `docs/logs/ci_remote_verified.json` (`47f25a2`) and committing this R3-6 self-audit leave local `release-prep` 2 doc-only commits ahead of `origin/release-prep`; pushing `release-prep` aligns remote CI SHA with final `HEAD` if desired.
4. `git diff --stat main -- rtl/` shows 5 RTL files modified in prior R1/R2 remediation commits on `remediation-r2`, whereas `git diff --stat remediation-r2 -- rtl/` confirms `0` RTL edits across `R3-1`..`R3-6`.

---

### Final Summary Table (`R3-1` .. `R3-6`)

| Task | Gate | Evidence File Path | Status |
|---|---|---|---|
| **R3-1** | `17/17` sanity mutants killed (`SMUT-17` assertion at `test_apb_gpio.py:97`); `GP-02` (`+1/+2/+3` incl. pulse return to 0), `UA-01`, `TM-02`, `BR-02`, `XB-02/03` + 20 fresh Icarus seeds `721..740` PASS | [`docs/logs/sanity.log`](logs/sanity.log), [`docs/logs/r3_1_regress_20seeds.log`](logs/r3_1_regress_20seeds.log), [`docs/FIX_REPORT_R3.md`](FIX_REPORT_R3.md) | **DONE** |
| **R3-2** | Frozen 240-mutant suite `219/240 (91.25% raw)`, `0` tmo/bld_err, `17` unbounded/dead (`0` bounded d=10), `98.21% (219/223)` conservative & bounded-incl adj | [`docs/logs/mutation.log`](logs/mutation.log), [`docs/logs/mutation_equiv.log`](logs/mutation_equiv.log), [`docs/mutation_report.md`](mutation_report.md) | **DONE** |
| **R3-3** | `axil2apb_bridge` closed via `PDR (prove, abc pdr)`; `axil_xbar`/`axil_cdc_bridge`/etc. bounds & exact wording across `README`/`results`/`vplan`/`limitations.md` | [`docs/logs/formal_suite.log`](logs/formal_suite.log), [`docs/limitations.md`](limitations.md), [`docs/results.md`](results.md) | **DONE** |
| **R3-4** | `README` map synced/enforced vs `axil_decoder.v`; leaf-bin waivers `303/36/267`; `DEC-014`/`DEC-015`; `SEEDS` quoting + 2x clean `make cov-report` byte-identical (`92.4%` line, `267/267` func) | [`docs/metrics.json`](metrics.json), [`docs/logs/code_cov_summary.txt`](logs/code_cov_summary.txt), [`docs/coverage_waivers.md`](coverage_waivers.md), [`docs/decisions.md`](decisions.md) | **DONE** |
| **R3-5** | Clean-clone full CI reproduction (`CLEAN_CLONE_CI_PASS=YES`), pushed `release-prep` (`4bd08534f3a7ebb5f99c3322843b2703eab7ac96`) green Actions run `45665895644` (`4m 37s`), Node.js 20 warning noted | [`docs/logs/clean_clone_r3.log`](logs/clean_clone_r3.log), [`docs/logs/ci_remote_verified.json`](logs/ci_remote_verified.json), [`docs/limitations.md`](limitations.md) | **DONE** |
| **R3-6** | Final unit/block/`test_directed`/sanity (`17/17`)/`make lint` verified on `HEAD`, all 16 MAJORs + regression checks self-audited honestly, verdict computed (`NOT READY` under strict unbounded-prove rule) | [`docs/FIX_REPORT_R3.md`](FIX_REPORT_R3.md), [`docs/logs/sanity.log`](logs/sanity.log) | **DONE** |

