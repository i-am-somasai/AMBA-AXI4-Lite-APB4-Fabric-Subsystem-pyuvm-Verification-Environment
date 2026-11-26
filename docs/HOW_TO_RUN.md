# AMBA-Fabric Complete Command & Verification Guide (`docs/HOW_TO_RUN.md`)

Every command in this guide is copied from [`Makefile`](../Makefile), `tb/*/Makefile`, and `scripts/`, and was verified with its recorded exit status in [`docs/logs/how_to_run_verified.log`](logs/how_to_run_verified.log).

---

## 0. Prerequisites and Installation

### Verified Toolchain Versions (`make env-check`)

| Component | Verified Version | Source / Location |
|---|---|---|
| **OSS CAD Suite** | `2026-11-22` | Default `$HOME/oss-cad-suite` (`OSS_CAD_SUITE`) |
| **Icarus Verilog** | `14.0 (devel)` (`s20260301-1260-gfd4a65b20-dirty`) | OSS CAD Suite (`iverilog`) |
| **Verilator** | `5.055 devel` (`v5.054-354-g005ee501b`) | OSS CAD Suite (`verilator`, `verilator_coverage`) |
| **Yosys** | `0.71+77` (`11d972c20`) | OSS CAD Suite (`yosys`) |
| **SymbiYosys / Boolector** | `SBY v0.71-7-gb21f778` / `Boolector 3.2.4` | OSS CAD Suite (`sby`, `boolector`, `abc`) |
| **GTKWave** | `GTKWave Analyzer v4.0.0-prealpha (e40ba79)` | OSS CAD Suite (`gtkwave`) |
| **Python / cocotb / pyuvm** | `Python 3.11.6` (`tabbypy3`), `cocotb 2.1.0`, `pyuvm 5.0.0`, `cocotb-coverage 2.0` | OSS CAD Suite `py3bin` + [`requirements.txt`](../requirements.txt) |
| **OpenSTA** | `2.6.0` | System/Nix (`STA_BIN` in `Makefile` / `scripts/env.sh`) |
| **SKY130 HD PDK** | `sky130_fd_sc_hd__tt_025C_1v80.lib` | Volare PDK (`SKY130_LIB` env override) |

### Installation Steps

1. **Install OSS CAD Suite (`2026-11-22` or matching release)** into `$HOME/oss-cad-suite` (or set `OSS_CAD_SUITE=/path/to/oss-cad-suite`).
2. **Install Python dependencies from [`requirements.txt`](../requirements.txt):**
   OSS CAD Suite already bundles `cocotb==2.1.0` and `find_libpython==0.5.1` inside `py3bin`. To install the remaining verification packages (`pyuvm==5.0.0`, `cocotb-coverage==2.0`, `PyYAML==6.0.4`, etc.) into OSS CAD Suite's `py3bin`—matching [`.github/workflows/ci.yml`](../.github/workflows/ci.yml):
   ```bash
   mkdir -p build/tmp
   grep -vE '^(cocotb|find_libpython)==' requirements.txt > build/tmp/ci-reqs.txt
   ~/oss-cad-suite/py3bin/python3 -m pip install --no-cache-dir --no-deps -r build/tmp/ci-reqs.txt
   ```
   > **Note:** Optional offline PNG waveform plotting ([`scripts/render_waveform.py`](../scripts/render_waveform.py)) requires `matplotlib` and `numpy` from `requirements.txt`; run it with `.venv/bin/python3` (the project venv), since base OSS CAD Suite `tabbypy3` omits `matplotlib`. Simulation, formal verification, mutation testing, synthesis, and STA run without `matplotlib`.
3. **OpenSTA and SKY130 Liberty (needed only for `make synth` and `make sta`):**
   If `sta` is not already in `PATH` or `sky130_fd_sc_hd__tt_025C_1v80.lib` is in a custom location, export `STA_BIN` and `SKY130_LIB` before sourcing `scripts/env.sh`.
4. **Disk-space rule (important):**
   Never compile simulations or mutants in `/tmp` if `/tmp` is a small RAM-backed `tmpfs`. [`scripts/env.sh`](../scripts/env.sh) and [`Makefile`](../Makefile) force both `BUILD_DIR` and `TMPDIR` inside `<repo>/build/`. Keep at least **500 MB–1 GB** free on the workspace volume for multi-seed Verilator builds and coverage `.dat` artifacts.

---

## 1. Environment Setup

| Item | Details |
|---|---|
| **Command** | `source scripts/env.sh && make env-check` |
| **What it does** | Activates OSS CAD Suite tools (`PATH`, `py3bin`), adds OpenSTA to `PATH`, links `SKY130_LIB` to `build/sky130_tt.lib` if present, sets `BUILD_DIR` / `TMPDIR` / `PYTHONPATH`, and checks all binaries plus `cocotb`, `pyuvm`, `cocotb_coverage`. |
| **Expected result** | Prints tool paths, `SKY130: FOUND`, and `Python packages: cocotb, pyuvm, cocotb-coverage OK` (exit `0`). |
| **Runtime / Memory** | `~0.5 s` / `< 30 MB` |

To place build artifacts outside the repository tree without using `/tmp`:

```bash
export BUILD_DIR=/path/to/large/disk/amba_build
source scripts/env.sh
make env-check
```

---

## 2. Lint & Static Consistency Checks

| Item | Details |
|---|---|
| **Command** | `make lint` |
| **What it does** | Sequentially runs: (1) `./scripts/check_no_synthetic_cov.sh` (forbids `sample_*()` calls outside `tb/pyuvm/func_cov/` and `tb/pyuvm/monitors/`), (2) `python3 scripts/check_bug_refs.py` (validates `BUG-001`..`BUG-024` sequential IDs and regression test names in `docs/bugs.md`), (3) `python3 scripts/check_docs_consistency.py` (verifies zero diff between `docs/metrics.json`, `rtl/axil/axil_decoder.v`, `README.md`, `docs/results.md`, and `docs/vplan.md`, zero forbidden stale strings, zero broken local links, and zero personal paths), and (4) `verilator --lint-only -Wall -Wno-DECLFILENAME -Wno-MULTITOP` across all 17 RTL files under `rtl/`. |
| **Expected result** | `Lint CLEAN.` (exit `0`). |
| **Runtime / Memory** | `~1.0 s` / `< 80 MB` |

Dry-run or individual gates:

```bash
make -n lint
./scripts/check_no_synthetic_cov.sh
python3 scripts/check_bug_refs.py
python3 scripts/check_docs_consistency.py
```

---

## 3. Level 0: Unit Tests (`tb/unit/`)

| Command | Scope | Expected Result | Typical Runtime | Approx. Memory |
|---|---|---|---|---|
| `make unit SIM=icarus` | Clean + run all 9 L0 modules (`hello_world`, `rst_sync`, `sync_fifo`, `async_fifo`, `rr_arbiter`, `axil_decoder`, `axil_default_slave`, `axil_ram`, `axil_csr`) | `All L0 unit tests executed successfully (SIM=icarus).` (`14/14` cocotb tests PASS) | `~29 s` | `~60 MB` |
| `make -C tb/unit test_axil_csr SIM=icarus` | Single L0 module (`test_axil_csr.py`, 4 tests: `CS-01`..`CS-04`) | `TESTS=4 PASS=4 FAIL=0 SKIP=0` | `~2.7 s` | `~50 MB` |

Available unit targets in [`tb/unit/Makefile`](../tb/unit/Makefile):
`test_hello_world`, `test_rst_sync`, `test_sync_fifo`, `test_async_fifo`, `test_rr_arbiter`, `test_axil_decoder`, `test_axil_default_slave`, `test_axil_ram`, `test_axil_csr`.

---

## 4. Level 1: Block & Top-Smoke Tests (`tb/block/`)

| Command | Scope | Expected Result | Typical Runtime | Approx. Memory |
|---|---|---|---|---|
| `make block SIM=icarus` | Clean + run all 7 L1 suites (`axil2apb_bridge`, `axil_xbar`, `apb_timer`, `apb_gpio`, `apb_uart`, `axil_cdc_bridge`, `amba_fabric_top`) | `All Phase 3 block and top tests executed successfully (SIM=icarus).` (`38/38` cocotb tests PASS) | `~29 s` | `~80 MB` |
| `make -C tb/block test_apb_gpio SIM=icarus` | Single block suite (`GP-01`..`GP-03`, 3 tests) | `TESTS=3 PASS=3 FAIL=0 SKIP=0` | `~2.7 s` | `~60 MB` |
| `make -C tb/block -f Makefile.single TOPLEVEL=apb_gpio MODULE=test_apb_gpio COCOTB_TEST_FILTER=test_gp02_input_sync_latency SIM=icarus` | Single named test via `COCOTB_TEST_FILTER` | `TESTS=1 PASS=1 FAIL=0 SKIP=0` | `~2.5 s` | `~60 MB` |

Available block targets in [`tb/block/Makefile`](../tb/block/Makefile):
`test_axil2apb_bridge`, `test_axil_xbar`, `test_apb_timer`, `test_apb_gpio`, `test_apb_uart`, `test_axil_cdc_bridge`, `test_amba_fabric_top`.

---

## 5. Level 2: Subsystem & `pyuvm` (`tb/pyuvm/`)

### Directed Suite + CDC Clock-Ratio Sweeps

- **Command:** `make -C tb/pyuvm test_directed SIM=icarus`
- **What it does:** Runs all `pyuvm` directed tests in [`tb/pyuvm/tests/test_directed.py`](../tb/pyuvm/tests/test_directed.py) (`XB-11`, `XB-12`, `XB-14`, `XB-15`, `BR-04`–`BR-06`, contention, strobes) plus `TestCoverageClosure` at default `25.0 ns` `clk_slow`, and then re-runs `TestCoverageClosure` at `CLK_SLOW_PERIOD_NS=10.3 CLK_SLOW_PHASE_NS=2.5 SEED=103` and `CLK_SLOW_PERIOD_NS=6.0 CLK_SLOW_PHASE_NS=1.2 SEED=60`.
- **Expected result:** `TESTS=1 PASS=1 FAIL=0` on final sweep, `PASS` across all 3 runs.
- **Runtime / Memory:** `~22 s` / `~120 MB`

### Stress Smoke & Passing `SEED` / `SEEDS`

- **Quick stress smoke (200 txns/master = 400 total):**
  `make -C tb/pyuvm test_stress SIM=icarus SEED=42 NUM_TRANS_PER_MASTER=200` (`~3.7 s`, `~100 MB`).
- **Passing `SEED` (single stress test):** `SEED=<N>` sets `COCOTB_RANDOM_SEED`, `RANDOM_SEED`, and Python `random.seed(N)` in [`test_stress.py`](../tb/pyuvm/tests/test_stress.py). Default `NUM_TRANS_PER_MASTER=5000` (`10,000` concurrent transactions across M0 and M1).
- **Passing `SEEDS` (`make regress`):**
  - **Single integer `SEEDS=20`:** expands via `seq 1 20` inside [`tb/pyuvm/Makefile`](../tb/pyuvm/Makefile) (`1 2 ... 20`).
  - **Custom space-separated list — quoting rule:** enclose the list in double quotes so the outer `Makefile` forwards all tokens intact to `$(MAKE) -C tb/pyuvm ... SEEDS="$(SEEDS)"`:
    ```bash
    make -n regress SIM=icarus SEEDS="601 602 603"
    ```

---

## 6. Full Regression & XML Inspection

| Command | Description | Expected Result | Typical Runtime | Approx. Memory |
|---|---|---|---|---|
| `make regress SIM=icarus SEEDS=1` | Directed + CDC sweeps + 1 full `10,000`-txn stress seed (`SEED=1`) | `All pyuvm directed and stress tests passed successfully.` | `~42 s` | `~150 MB` |
| `make -n regress SIM=icarus SEEDS=20` | Plan/dry-run check for full 20-seed Icarus regression (`200,000` txns, `-j4`) | Expands all `stress_seed_1..20` targets, exit `0` | ~3–5 min when executed (`-j4`) | `~400 MB` (4 workers) |
| `make regress-verilator SEEDS=1` | Compiles Verilator C++ (`-j2` default) and runs directed + 1 stress seed | `All pyuvm directed and stress tests passed successfully.` | `~82 s` | `~600 MB–1 GB` (compile) |

> **Dry-run note on Verilator:** Do not rely on `make -n regress-verilator` on a clean build tree: `cocotb`'s `Makefile.verilator` tries to invoke `make -f Vtop.mk` before `verilator -cc` generates `Vtop.mk` and exits `2`. Run `make regress-verilator SEEDS=1` directly instead.

### Reading Results XML & Updating `docs/test_map.csv`

- Cocotb writes JUnit XML files to:
  - `build/results/unit/results_<module>.xml`
  - `build/results/block/results_<module>.xml`
  - `build/results/pyuvm/results_test_directed.xml`, `results_test_cdc_10_3.xml`, `results_test_cdc_6_0.xml`, `results_test_stress_<seed>.xml`
- Check quickly for failures across all XMLs:
  ```bash
  grep -rn "failure" build/results/ || echo "ZERO FAILURES"
  ```
- Regenerate [`docs/test_map.csv`](test_map.csv) and `docs/vplan.md` spec tables after running `unit`, `block`, `test_directed`, and at least `SEED=42` (`NUM_TRANS_PER_MASTER` full regression) so every test XML exists under `build/results/`:
  ```bash
  python3 scripts/gen_test_map.py
  ```

---

## 7. Coverage Collection & Reporting

| Item | Details |
|---|---|
| **Full command** | `make cov-report` (calls [`scripts/run_regression.sh`](../scripts/run_regression.sh); inspected via `make -n cov-report`) |
| **What it does** | Cleans `tb/pyuvm` & `tb/block`; compiles & runs `test_directed`, `test_axil2apb_bridge`, and 20 stress seeds (`1..20`, `5,000`/master = `200,000` txns) under Verilator with `VERILATOR_COVERAGE=1`; merges `build/coverage/*.dat` via `verilator_coverage -write`; writes `docs/logs/code_cov_summary.txt` and annotated Verilog under `docs/logs/code_cov/`; runs `scripts/merge_cov.py` to write `docs/logs/func_cov.log`. |
| **Merge-only command** | `python3 scripts/merge_cov.py docs/logs` |
| **Expected result** | `merge_cov.py` prints `OVERALL AGGREGATE COVERAGE \| 267 \| 267 \| 100.00%` across 24 archived YAMLs (`20` stress + `3` directed/CDC + `1` block `cg_apb`) and saves `docs/logs/func_cov.log` (`< 0.2 s`). |
| **Runtime / Memory** | Full `make cov-report`: ~8–15 min (depends on core count) / `~1 GB` peak during Verilator `--coverage` build. |

**Output locations:**
- Functional coverage report: [`docs/logs/func_cov.log`](logs/func_cov.log)
- Code coverage summary: [`docs/logs/code_cov_summary.txt`](logs/code_cov_summary.txt)
- Per-file annotated RTL source: `docs/logs/code_cov/*.v`

---

## 8. Formal Verification (`formal/`)

### Run All 10 Suites

- **Command:** `make formal` (calls [`scripts/run_all_formal.sh`](../scripts/run_all_formal.sh))
- **Expected result:** `Formal suite PASSED (10/10 modules clean).` with `84` covers reached (`~126 s` locally); writes table to [`docs/logs/formal_suite.log`](logs/formal_suite.log).
- **Approx. Memory:** `< 300 MB` (sequentially invokes `sby -f <suite>.sby`).

### Run a Single Suite & Understand Modes

```bash
(cd formal && sby -f apb_timer.sby)
```

| `.sby` File | Method / Mode | Depth | Engine | Covers Reached | Verified Runtime |
|---|---|---:|---|---:|---:|
| [`apb_timer.sby`](../formal/apb_timer.sby) | `prove` (k-induction) | 20 | `smtbmc boolector` | 4 | `~1 s` |
| [`rr_arbiter.sby`](../formal/rr_arbiter.sby) | `prove` (k-induction) | 20 | `smtbmc boolector` | 3 | `~1 s` |
| [`sync_fifo.sby`](../formal/sync_fifo.sby) | `prove` (k-induction) | 20 | `smtbmc boolector` | 8 | `~3 s` |
| [`axil2apb_bridge.sby`](../formal/axil2apb_bridge.sby) | `prove` (unbounded PDR) | 25 | `abc pdr` (`boolector` cover) | 10 | `~3 s` |
| [`axil_csr.sby`](../formal/axil_csr.sby) | `prv+bmc` (k-induction + causality BMC) | 20 | `smtbmc boolector` | 5 | `~3 s` |
| [`axil_ram.sby`](../formal/axil_ram.sby) | `bmc` (bounded) | 20 | `smtbmc boolector` | 5 | `~3 s` |
| [`axil_xbar.sby`](../formal/axil_xbar.sby) | `bmc` (bounded) | 20 | `smtbmc boolector` | 31 | `~43 s` |
| [`apb_uart.sby`](../formal/apb_uart.sby) | `bmc` (bounded) | 25 | `smtbmc boolector` | 9 | `~5 s` |
| [`async_fifo.sby`](../formal/async_fifo.sby) | `bmc` (`multiclock on`, `async2sync`) | 25 | `smtbmc boolector` | 4 | `~8 s` |
| [`axil_cdc_bridge.sby`](../formal/axil_cdc_bridge.sby) | `bmc` (`multiclock on`, `async2sync`) | 30 | `smtbmc boolector` | 5 | `~82 s` |

Each `.sby` produces `<module>_prove/`, `<module>_bmc/`, and `<module>_cover/` work directories inside `formal/` (gitignored; safe to remove with `rm -rf formal/*/`). See [`docs/limitations.md`](limitations.md) for why the 5 bounded `bmc` suites remain bounded.

---

## 9. Mutation Testing & Equivalence Check (`mutation/`)

| Command | What it does | Expected Result | Typical Runtime / Memory |
|---|---|---|---|
| `make mutation-sample` | CI 24-mutant sample (3 per module across 8 DUTs) | Writes `build/results/mutation_sample.log` | `~39 s` / `~400 MB` |
| `make -n mutation` / `make mutation` | Evaluates 240 mutants (`python3 mutation/run_mutants.py --max-mutants 240`); add `--mutant-list mutation/mutant_list_240.json` to run the exact frozen baseline list | Writes `docs/logs/mutation.log` & copies survivors to `mutation/results/survivors/` | ~5–8 min (`-j4`) / `~800 MB` |
| `python3 mutation/check_equiv.py --output build/results/mutation_equiv_check.log` | Runs Yosys `equiv_induct`, SBY `mode prove` (`abc pdr`), and structural dead-wire checks across survivors (21 in `docs/logs/mutation.log`) | Classifies `EQUIV_YOSYS`, `EQUIV_PROVE`, `SIGNAL_PROOF`, or `NOT_EQUIV` | `~40 s` / `~300 MB` |
| `python3 mutation/run_mutants.py --help` | Prints full CLI flags (`--seed`, `--jobs`, `--mutant-list`, `--output`) | Exit `0` | `< 0.1 s` |

- **How to read [`docs/mutation_report.md`](mutation_report.md):** Generated strictly from logs via `python3 mutation/gen_mutation_report.py`. Reports raw kill rate (`Kill / Valid`, counting timeouts & build errors separately as non-kills), unbounded-proven/dead-signal equivalents vs bounded-equivalent (`0` remaining), and conservative adjusted kill score (`Kill / (Valid - Unbounded_Dead_Equiv)`).

---

## 10. Sanity Mutants Gate (`make sanity`)

| Item | Details |
|---|---|
| **Command** | `make sanity` (runs `python3 mutation/sanity/run_sanity.py \| tee docs/logs/sanity.log`) |
| **What it does** | Injects 17 permanent targeted RTL defects (`SMUT-01`–`SMUT-17`), verifies each mutant passes both `iverilog -g2012` and `verilator --lint-only` (otherwise flagged `INVALID`), and runs its assigned cocotb/pyuvm test expecting failure. |
| **Expected result** | `Sanity Summary: 17/17 KILLED, 0 SURVIVED, 0 INVALID` (all temporary builds stay inside `build/sanity/`). |
| **What `17/17 KILLED` proves** | Every sanity defect compiles as valid Verilog and causes an active regression assertion failure—none silently passes due to missing checks or uncompiled mutations. |
| **Runtime / Memory** | `~49 s` / `~150 MB` |

---

## 11. Synthesis and Static Timing Analysis (`make synth`, `make sta`)

### Run Commands

| Command | Tool & Inputs | Output Files | Typical Runtime / Memory |
|---|---|---|---|
| `make synth` | Yosys (`synth/synth.ys`, `RAM_DEPTH=64`, mapped to `build/sky130_tt.lib`) | `synth/results/synth.log`, `synth/results/amba_fabric_netlist.v` | `~6.3 s` / `72.9 MB` peak |
| `make sta` | OpenSTA (`sta -exit synth/sta.tcl` + `python3 synth/fmax_sweep.py`) | `synth/results/sta.log`, `synth/results/fmax_sweep.log` | `~19.2 s` / `~150 MB` |

### Reading `synth/results/fmax_sweep.log` (WNS / TNS)

- `make sta` requires `synth/results/amba_fabric_netlist.v` from `make synth` first.
- **`clk_sys` target (`10.00 ns` = `100 MHz`):** Look at `Overall WNS` / `Overall TNS` (`-18.60 ns` / `-54046.39 ns` -> `VIOLATED`). As `Section 4` of `fmax_sweep.log` shows, this pre-layout violation is dominated by unbuffered `rst_sys_n` reset recovery (`fanout=958`, `cap=3.46 pF`, `slew=29.27 ns`) rather than datapath logic; Section 3 reports the core+I/O reference (`-5.89 ns`, `62.89 MHz`) with `rst_sync` Q isolated in STA only.
- **`clk_slow` target (`24.00 ns` = `41.67 MHz`) and Hold:** Both meet constraints (`+16.64 ns` setup slack, `+0.23 ns` hold slack).
- **Dynamic query failure:** `sta.tcl` aborts (`exit 1`) if `rst_sync` nets or clocks cannot be matched—ensuring timing numbers are never silently printed on empty constraints.

---

## 12. Docs and Metrics Regeneration

- **Render markdown metric blocks only (reads existing [`docs/metrics.json`](metrics.json)):**
  ```bash
  python3 scripts/gen_docs.py
  python3 scripts/check_docs_consistency.py
  python3 scripts/check_bug_refs.py
  ```
  (`gen_docs.py` runs in `~0.06 s` and updates `README.md`, `docs/results.md`, and `docs/vplan.md` identically.)
- **Regenerate `docs/metrics.json` from scratch (requires a populated `build/results/` tree):**
  Run `make unit SIM=icarus`, `make block SIM=icarus`, `make -C tb/pyuvm test_directed SIM=icarus`, and stress regression XMLs first (since `scripts/gen_metrics.py` fails intentionally if `build/results/**/results*.xml` is empty), then run:
  ```bash
  python3 scripts/gen_metrics.py
  python3 scripts/gen_test_map.py
  python3 scripts/gen_docs.py
  python3 scripts/check_docs_consistency.py
  ```

---

## 13. Waveforms and VCD Inspection

1. **Generate a VCD from a block simulation** (`tb/block/tb_axil_xbar.v` dumps `tb/block/dump.vcd` automatically when compiled with `COCOTB_SIM`):
   ```bash
   make -C tb/block test_axil_xbar COCOTB_TEST_FILTER=test_xb05_contention_same_slave SIM=icarus
   ```
   Produces `tb/block/dump.vcd` (`~2.7 s`).
2. **Open in GTKWave (requires X11/Wayland display):**
   ```bash
   gtkwave tb/block/dump.vcd &
   ```
   *(In headless environments, `gtkwave --version` verifies the binary.)*
3. **Static PNG render (via project `.venv` with `matplotlib` + `numpy` from [`requirements.txt`](../requirements.txt), used to produce [`docs/img/contention.png`](img/contention.png)):**
   ```bash
   .venv/bin/python3 scripts/render_waveform.py tb/block/dump.vcd build/results/contention_preview.png
   ```
   Saves the rendered timing diagram to `build/results/contention_preview.png` (`~2.7 s`).

---

## 14. Continuous Integration (`.github/workflows/ci.yml`)

- **Triggers:** Pushes to `main`, `phase-*`, `remediation-*`, `release-*`; PRs to `main`; manual `workflow_dispatch`.
- **Job `lint-and-verify` steps (`ubuntu-latest`, OSS CAD Suite `2026-11-22`):**
  1. Environment check + `check_no_synthetic_cov.sh` + `check_bug_refs.py` + `check_docs_consistency.py`
  2. `make lint`, `make unit SIM=icarus`, `make block SIM=icarus`
  3. `make regress SIM=icarus SEEDS=3`
  4. `python3 mutation/sanity/run_sanity.py` (`17/17`)
  5. `make formal` (`10/10`)
  6. `make mutation-sample` (`24`-mutant smoke)
  7. Uploads `build/results/` and `docs/logs/formal_suite.log` as artifact `verification-logs-and-reports` (`always()`).
- **Local-only steps not run in CI:** `make cov-report` (20 Verilator seeds), full `make mutation` (240 mutants), `make synth`, and `make sta`.
- **Inspecting CI:** Open the Actions tab on GitHub for the run URL recorded in [`README.md`](../README.md) Section 6 / [`docs/logs/ci_remote_verified.json`](logs/ci_remote_verified.json), verify `head_sha` matches the code commit, and download `verification-logs-and-reports` from the Artifacts panel.

---

## 15. Cleaning Build Artifacts

| Command | Removes |
|---|---|
| `make clean` | Top `build/` (`tmp/`, `sim_build/`, `results/`, `coverage/`, `sanity/`, `sky130_tt.lib`), plus `tb/{unit,block,pyuvm}` `sim_build*`, `__pycache__`, `results*.xml`, `*.vcd`, and root `*.log` |
| `make -C tb/unit clean` | `tb/unit/sim_build*`, `build/sim_build/unit_*`, `build/results/unit`, `*.xml`, `*.vcd` |
| `make -C tb/block clean` | `tb/block/sim_build*`, `build/sim_build/block_*`, `build/results/block`, `*.xml`, `*.vcd` |
| `make -C tb/pyuvm clean` | `tb/pyuvm/sim_build*`, `build/sim_build/pyuvm_*`, `build/results/pyuvm`, `*.xml`, `*.vcd` |
| `rm -rf formal/*/` | Generated SymbiYosys task directories (`<suite>_prove/`, `<suite>_bmc/`, `<suite>_cover/`) |

*(Tracked golden logs under `docs/logs/` are unaffected by `make clean`.)*

---

## 16. Troubleshooting

1. **Disk space / `/tmp` full errors:** Ensure `source scripts/env.sh` is run so `TMPDIR` and `BUILD_DIR` point inside `<repo>/build/` (not small RAM-backed `/tmp`).
2. **Memory pressure during Verilator compile or mutation runs:**
   - Top-level `Makefile` caps parallel builds via `MAX_JOBS=2` for `SIM=verilator` (`4` for `SIM=icarus`), and `mutation/run_mutants.py` caps `--jobs` at `4`. Lower `--jobs 2` on machines with `< 4 GB` RAM.
3. **Verilator / `cocotb` version notes:**
   - `make -n regress-verilator` exits `2` on clean trees because `cocotb`'s `Makefile.verilator` invokes `Vtop.mk` before Verilator generates it; invoke `make regress-verilator SEEDS=1` (real execution) instead.
   - `cocotb 2.1.0` prints a harmless deprecation notice (`Using MODULE is deprecated, please use COCOTB_TEST_MODULES instead`) when invoking `Makefile.single` with `MODULE=`.
   - `iverilog -g2012 -Wall` prints benign unpacked-array `@*` sensitivity warnings on `rtl/axil/axil_xbar.v`; Verilator lint (`make lint`) is zero-warning clean.
   - `render_waveform.py` fails with `ModuleNotFoundError: No module named 'matplotlib'` if invoked with base OSS CAD Suite `tabbypy3`; invoke `.venv/bin/python3 scripts/render_waveform.py ...` (where `requirements.txt` installs `matplotlib` and `numpy`).
4. **`SEEDS` quoting:** Pass single integer counts bare (`SEEDS=20`), but **always quote** explicit multi-seed lists (`SEEDS="601 602 603"`). Unquoted spaces cause GNU Make to interpret `602` and `603` as Make targets.
5. **Finding a failing seed in a regression:**
   ```bash
   grep -rn "failure" build/results/pyuvm/results_test_stress_*.xml
   ```
   Or inspect stdout/console output for `FAIL=1` next to `SEED=<N>`.
6. **Reproducing a failing seed identically:**
   ```bash
   make -C tb/pyuvm test_stress SIM=icarus SEED=<N> NUM_TRANS_PER_MASTER=5000
   ```
   (Use the exact same `SIM`, `SEED`, `NUM_TRANS_PER_MASTER`, and—for CDC runs—`CLK_SLOW_PERIOD_NS` and `CLK_SLOW_PHASE_NS`.)

---

## 17. One-Page Cheat Sheet

| Goal | Exact Command | Typical Runtime | Approx. Memory |
|---|---|---:|---:|
| Setup env & check tools | `source scripts/env.sh && make env-check` | `~0.5 s` | `< 30 MB` |
| Static checks & RTL lint | `make lint` | `~1.0 s` | `< 80 MB` |
| Synthetic cov gate only | `./scripts/check_no_synthetic_cov.sh` | `~0.1 s` | `< 20 MB` |
| Bug log cross-check | `python3 scripts/check_bug_refs.py` | `~0.2 s` | `< 30 MB` |
| Docs vs `metrics.json` check | `python3 scripts/check_docs_consistency.py` | `~0.2 s` | `< 30 MB` |
| Re-render managed doc blocks | `python3 scripts/gen_docs.py` | `~0.1 s` | `< 30 MB` |
| All L0 unit tests (Icarus) | `make unit SIM=icarus` | `~29 s` | `~60 MB` |
| Single L0 unit module | `make -C tb/unit test_axil_csr SIM=icarus` | `~2.7 s` | `~50 MB` |
| All L1 block tests (Icarus) | `make block SIM=icarus` | `~29 s` | `~80 MB` |
| Single L1 block test (filtered) | `make -C tb/block -f Makefile.single TOPLEVEL=apb_gpio MODULE=test_apb_gpio COCOTB_TEST_FILTER=test_gp02_input_sync_latency SIM=icarus` | `~2.5 s` | `~60 MB` |
| L2 pyuvm directed + CDC sweeps | `make -C tb/pyuvm test_directed SIM=icarus` | `~22 s` | `~120 MB` |
| L2 pyuvm stress smoke (400 txns) | `make -C tb/pyuvm test_stress SIM=icarus SEED=42 NUM_TRANS_PER_MASTER=200` | `~3.7 s` | `~100 MB` |
| L2 regress (Icarus, 1 seed) | `make regress SIM=icarus SEEDS=1` | `~42 s` | `~150 MB` |
| L2 regress (Icarus, 20 seeds) | `make -n regress SIM=icarus SEEDS=20` (run without `-n` for full `200,000` txns) | ~3–5 min | `~400 MB` |
| L2 regress (Verilator, 1 seed) | `make regress-verilator SEEDS=1` | `~82 s` | `~800 MB` |
| Merge coverage YAMLs only | `python3 scripts/merge_cov.py docs/logs` | `< 0.2 s` | `< 40 MB` |
| Full coverage + 20-seed Verilator | `make -n cov-report` (run without `-n` for full 20-seed coverage) | ~8–15 min | `~1 GB` |
| Single formal suite | `(cd formal && sby -f apb_timer.sby)` | `~1.4 s` | `< 100 MB` |
| All 10 formal suites | `make formal` | `~126 s` | `< 300 MB` |
| Sanity-mutant gate (17 bugs) | `make sanity` | `~49 s` | `~150 MB` |
| Sampled mutation smoke (24) | `make mutation-sample` | `~39 s` | `~400 MB` |
| Full mutation run (240) | `make -n mutation` (run without `-n` for full 240-mutant sweep) | ~5–8 min | `~800 MB` |
| Mutant equivalence prover | `python3 mutation/check_equiv.py --output build/results/mutation_equiv_check.log` | `~40 s` | `~300 MB` |
| SKY130 synthesis (Yosys) | `make synth` | `~6.3 s` | `~75 MB` |
| OpenSTA + Fmax sweep | `make sta` | `~19 s` | `~150 MB` |
| Generate VCD waveform | `make -C tb/block test_axil_xbar COCOTB_TEST_FILTER=test_xb05_contention_same_slave SIM=icarus` | `~2.7 s` | `~80 MB` |
| Open VCD in GTKWave | `gtkwave tb/block/dump.vcd &` | interactive | `~80 MB` |
| Render VCD waveform PNG (`.venv`) | `.venv/bin/python3 scripts/render_waveform.py tb/block/dump.vcd build/results/contention_preview.png` | `~2.7 s` | `~120 MB` |
| Clean all builds & XMLs | `make clean` | `< 0.2 s` | `< 20 MB` |
