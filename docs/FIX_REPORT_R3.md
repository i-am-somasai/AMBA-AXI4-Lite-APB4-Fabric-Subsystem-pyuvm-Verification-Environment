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
