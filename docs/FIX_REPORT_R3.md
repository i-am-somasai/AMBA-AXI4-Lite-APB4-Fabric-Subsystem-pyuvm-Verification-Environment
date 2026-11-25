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
