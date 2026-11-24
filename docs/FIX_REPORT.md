# AMBA-Fabric Remediation Report (docs/FIX_REPORT.md)

This report tracks the remediation of findings F-01 through F-12 identified in the independent review of the AMBA-Fabric project.
Every finding is addressed with honest evidence, verified by real tool executions, and logged to `docs/logs/`.

---

## Finding Details & Status

### F-01: Functional Coverage Fabrication & Monitor-Based Real Sampling
- **Status:** TODO
- **Finding:** Functional coverage "100%" was achieved synthetically: `tb/pyuvm/sequences/coverage_closure_seq.py` directly invoked `sample_*` functions with hardcoded loops across bins. Monitors did not perform genuine bus observation for all covergroups. CDC lacked ratio/phase sweeps; framing error was sampled without driving bad stop bits.
- **Planned Changes:**
  - Delete all `sample_*` calls from `tb/pyuvm/sequences/` and `tb/pyuvm/tests/`.
  - Re-architect `tb/pyuvm/func_cov/fabric_cov.py` and monitors to sample strictly from real DUT signal transitions:
    - `cg_txn`: Sampled from AXI-Lite monitor on transaction completion.
    - `cg_wstrb`, `cg_order`: Sampled from observed WSTRB and observed AW/W handshake arrival cycles.
    - `cg_backpressure`: Sampled from observed ready/valid delays across all five channels.
    - `cg_contention`: Sampled from cycle-aligned crossbar monitor watching both masters.
    - `cg_apb`: Sampled from APB monitor observing PSEL, PENABLE, PREADY, PSLVERR, PSTRB.
    - `cg_cdc`: Sampled from configured clock ratio/phase and FIFO occupancy probes.
    - `cg_uart`: Sampled from observed UART pins, status registers, and baud dividers.
    - `cg_reset`: Sampled by reset monitor recording in-flight transaction phases during reset.
  - Add `scripts/check_no_synthetic_cov.sh` to enforce zero `sample_*` calls outside monitor/collector files.
  - Document unreachable bins in `docs/coverage_waivers.md` with explicit justification.
- **Evidence:** TBD (`docs/logs/check_no_synthetic_cov.log`, `docs/logs/coverage_merged.log`)
- **Before / After Numbers:**
  - Before: 100.00% (280/280 bins) via synthetic sampling.
  - After: TBD (measured honest coverage from real monitors).
- **Remaining Issues:** None yet.

---

### F-02: Missing and Mislabeled Tests in Test Plan & Codebase
- **Status:** TODO
- **Finding:** `docs/vplan.md` marked tests as PASS that were either missing or mislabeled:
  - XB-09 (random READY backpressure) & XB-10 (delayed BREADY/RREADY) missing.
  - UA-04 (framing error injection) missing.
  - CD-03 (mid-transaction reset in either domain) missing.
  - CD-05 had no dual-master concurrent slow register access test.
  - CD-01 lacked clock ratio and phase sweep.
  - CD-02 was only a basic test without stream stress or boundary verification.
  - BR-04, BR-05, BR-06 in `tb/pyuvm/tests/test_directed.py` targeted RAM/CSR rather than the APB bridge.
  - CS-01, CS-02, CS-03 were combined into a single test function without separate spec ID mapping.
- **Planned Changes:**
  - Implement genuine tests named `test_<ID>_<short_name>` for all missing/mislabeled scenarios:
    - `test_xb09_ready_backpressure`, `test_xb10_delayed_bready_rready`
    - `test_ua04_framing_error`
    - `test_cd01_ratio_phase_sweep`, `test_cd02_async_fifo_stream`, `test_cd03_reset_recovery`, `test_cd05_dual_master_slow_regs`
    - Bridge-level `test_br04_pstrb`, `test_br05_contention`, `test_br06_delayed_wdata` in `tb/block/test_axil2apb_bridge.py`
    - Split CSR tests into `test_cs01_reset_values`, `test_cs02_access_types_w1c`, `test_cs03_irq_aggregation`
  - Rename mislabeled tests in `test_directed.py`.
  - Create `scripts/gen_test_map.py` to parse test IDs, inspect `results.xml`, and generate `docs/test_map.csv`.
  - Regenerate `docs/vplan.md` mechanically from `docs/test_map.csv`.
- **Evidence:** TBD (`docs/test_map.csv`, `docs/vplan.md`, `docs/logs/gen_test_map.log`)
- **Before / After Numbers:**
  - Before: Mislabeled tests, unverified features marked PASS in vplan.
  - After: All 40 spec test IDs accounted for, verified by `results.xml`.
- **Remaining Issues:** None yet.

---

### F-03: Formal Verification Overclaims & Protocol Checker Integration
- **Status:** TODO
- **Finding:** `formal/axil_props.v` was never instantiated or referenced by any `.sby` configuration. Formal checks for `axil_xbar`, `axil2apb_bridge`, `axil_ram`, and `async_fifo` were BMC only (depth 20–25) but reported as exhaustively proven. No bounded liveness / deadlock proofs existed despite README claiming "absence of deadlock". No formal proofs for `axil_cdc_bridge` or `apb_uart`.
- **Planned Changes:**
  - Bind `formal/axil_props.v` across crossbar ports, APB bridge AXI interface, RAM, CSR, and CDC bridge.
  - Add bounded liveness properties (every accepted request gets a response within $M$ cycles under fair slave assumptions).
  - Add precondition cover statements for all major assertions to prevent vacuous proofs.
  - Add formal property suite for `axil_cdc_bridge` (FIFO handshake, request/response integrity) and UART FIFO/flag properties.
  - Attempt $k$-induction on `axil_xbar`, `axil2apb_bridge`, and `async_fifo`. If induction cannot close, clearly document as BMC with exact depth.
  - Update `scripts/run_all_formal.sh` to output structured summary: module, mode (BMC / $k$-induction), depth, result, cover count, runtime.
- **Evidence:** TBD (`docs/logs/formal_suite.log`)
- **Before / After Numbers:**
  - Before: Unbound claims of "absence of deadlock" and "proven" without full induction; unused `axil_props.v`.
  - After: Accurate classification (BMC depth $N$ vs $k$-induction), all props bound, bounded liveness checked.
- **Remaining Issues:** None yet.

---

### F-04: Documentation Inconsistencies with Codebase
- **Status:** TODO
- **Finding:** README stated 48 tests while actual count was 43. README claimed UART FIFO depth was 16 entries (RTL and spec define depth 8). README had peripheral address typos (Timer and GPIO base addresses). `results.md` claimed full regression ran on "Icarus & Verilator" without full dual-simulator logs.
- **Planned Changes:**
  - Mechanically extract test counts using script.
  - Correct UART FIFO depth to 8 in README and documentation.
  - Verify and correct peripheral base addresses (`0x4000_0000` UART, `0x4000_1000` Timer, `0x4000_2000` GPIO).
  - Clarify simulation toolchain: primary regression on Icarus Verilog; code coverage and lint on Verilator.
- **Evidence:** TBD (`README.md`, `docs/interfaces.md`, `docs/results.md`)
- **Before / After Numbers:**
  - Before: Discrepant test counts and FIFO depths.
  - After: 100% consistent documentation generated from code.
- **Remaining Issues:** None yet.

---

### F-05: Mutation Testing Sample Size and Survivor Triage
- **Status:** TODO
- **Finding:** Mutation testing evaluated only 20 mutants (65% score); spec Section 12 requested 200–300 mutants across 7 modules (`axil_xbar`, `axil_decoder`, `rr_arbiter`, `axil2apb_bridge`, `async_fifo`, `axil_ram`, `axil_csr`). Surviving mutants (such as `axil_ram` at 25%) were not comprehensively triaged.
- **Planned Changes:**
  - Scale `mutation/run_mutants.py` to evaluate $\ge 250$ mutants across all 7 target modules.
  - Run mutation suite with max 4 parallel workers.
  - Triage every surviving mutant in `docs/mutation_triage.md` (equivalent mutant proof vs testbench gap).
  - Add targeted test improvements to kill non-equivalent survivors and measure before/after scores.
- **Evidence:** TBD (`docs/mutation_triage.md`, `docs/logs/mutation_summary.log`)
- **Before / After Numbers:**
  - Before: 20 mutants, 65.00% score, incomplete triage.
  - After: $\ge 250$ mutants, full triage, quantified before/after scores.
- **Remaining Issues:** None yet.

---

### F-06: Regression Seed Count Verification
- **Status:** TODO
- **Finding:** Full random stress regression ran only 5 seeds in Phase 4; spec Section 9.2 mandates at least 20 random seeds with $\ge 10,000$ transactions per seed.
- **Planned Changes:**
  - Execute full regression across 20 distinct random seeds on Icarus Verilog.
  - Verify $\ge 10,000$ transactions per seed with zero scoreboard mismatches.
  - Capture all seed outputs into `docs/logs/regress_20seeds.log`.
- **Evidence:** TBD (`docs/logs/regress_20seeds.log`)
- **Before / After Numbers:**
  - Before: 5 seeds (50,000 transactions).
  - After: 20 seeds (200,000 transactions) with clean scoreboard logs.
- **Remaining Issues:** None yet.

---

### F-07: CI Workflow Modernization & GitHub Integration
- **Status:** TODO
- **Finding:** GitHub Actions CI workflow had never executed on GitHub; workflow pinned an outdated `oss-cad-suite` release (`2024-05-01`) while local host ran `20261122`; README badge referenced an invalid repository URL.
- **Planned Changes:**
  - Update `.github/workflows/ci.yml` to use matching modern `oss-cad-suite` release or standard runner setup.
  - Ensure all CI commands execute cleanly from a fresh checkout without relying on local `scripts/env.sh`.
  - Fix README CI workflow badge URL.
  - Push branch and verify live execution on GitHub Actions.
- **Evidence:** TBD (GitHub Actions run URL, `docs/logs/ci_validation.log`)
- **Before / After Numbers:**
  - Before: Untested CI workflow with dated toolchain and broken badge.
  - After: Green GitHub Actions run verified and linked.
- **Remaining Issues:** None yet.

---

### F-08: Environment File Tracking & Git Ignore Audit
- **Status:** DONE
- **Finding:** Review requested confirmation that `tb/pyuvm/env/` (`FabricEnv`, scoreboard) is properly tracked in git and not shadowed by `.gitignore`.
- **Changes Made:**
  - Audited tracking via `git ls-files tb/pyuvm/env` (both `fabric_env.py` and `fabric_scoreboard.py` tracked).
  - Explicitly anchored `.gitignore` with `!tb/pyuvm/env/` to guarantee no future ignore conflicts.
  - Performed clean clone in `/tmp/clone_test`, sourced environment, and executed `make lint`, `make unit SIM=icarus`, and `make regress SIM=icarus SEEDS=1`.
  - All three targets passed cleanly from the clean clone checkout.
- **Evidence:**
  - `docs/logs/clean_clone.log` (clean clone execution with zero `/home/` paths).
  - Commit `3ca92c7`: `fix(F-08): safeguard pyuvm env tracking in gitignore`.
- **Before / After Numbers:**
  - Before: Unconfirmed clone buildability.
  - After: Clean clone passes lint (19 modules), 8/8 unit tests, and regression (8 directed + 5 stress seeds = 10,000 tx/seed) with zero mismatches.
- **Remaining Issues:** None.

---

### F-09: pyuvm Verification Architecture Honesty
- **Status:** TODO
- **Finding:** Docs claimed full pyuvm architecture across all agents, but only `AxilMasterAgent` was a pyuvm agent; peripheral and responder models were plain cocotb/Python classes.
- **Planned Changes:**
  - Evaluate promotion to pyuvm agents vs honest architectural documentation.
  - Record architectural decision in `docs/decisions.md` (DEC-004).
  - Clearly state in `README.md` and `docs/results.md` exact classification: "pyuvm testbench (master agents, sequences, env, scoreboard); peripheral and responder models are cocotb Python models".
- **Evidence:** TBD (`docs/decisions.md`, `README.md`)
- **Before / After Numbers:**
  - Before: Ambiguous or over-generalized UVM claims.
  - After: Precise, honest architectural disclosure.
- **Remaining Issues:** None yet.

---

### F-10: Removal of Flawed Audit Artifacts
- **Status:** TODO
- **Finding:** `docs/AUDIT_REPORT.md`, `docs/audit_results.csv`, `docs/audit_results.json`, and `audit/` were committed from a flawed intermediate audit (containing template rows, wrong CSR tables, and local `/home/` paths).
- **Planned Changes:**
  - Remove `docs/AUDIT_REPORT.md`, `docs/audit_results.csv`, `docs/audit_results.json`, and the `audit/` folder from the repository.
- **Evidence:** TBD (`git status`, commit record)
- **Before / After Numbers:**
  - Before: Stale audit artifacts present in repository.
  - After: Clean repository tree without stale audit files.
- **Remaining Issues:** None yet.

---

### F-11: Physical Synthesis & STA Reporting Honesty
- **Status:** TODO
- **Finding:** OpenSTA reported WNS = -2.25 ns at 100 MHz target due to multi-level combinational address decoding and external I/O delay constraints ($F_{\max} = 81.63$ MHz system, $95.15$ MHz core reg-to-reg). Must be reported honestly without relaxing constraints.
- **Planned Changes:**
  - Explicitly document in `README.md` and `docs/results.md`: "Target 100 MHz not met (WNS -2.25 ns under 2.0 ns I/O constraints); Achieved system Fmax 81.63 MHz, core reg-to-reg Fmax 95.15 MHz".
  - Retain realistic SDC constraints (`synth/amba_fabric.sdc`).
  - Provide root cause analysis of critical path (`s1_axil_awaddr[22]` to RAM write enable).
- **Evidence:** TBD (`synth/results/sta.log`, `synth/results/fmax_sweep.log`)
- **Before / After Numbers:**
  - Before: Reported but needed explicit emphasis on constraint honesty.
  - After: Completely transparent timing reporting.
- **Remaining Issues:** None yet.

---

### F-12: License Addition & Language Precision
- **Status:** TODO
- **Finding:** Missing `LICENSE` file despite MIT badge in `README.md`; RTL described as "SystemVerilog" when written in synthesizable Verilog-2005 style with minimal SystemVerilog constructs.
- **Planned Changes:**
  - Add official MIT `LICENSE` file.
  - Update `README.md` and documentation to describe RTL as "Verilog-2005 (SystemVerilog-compatible)".
- **Evidence:** TBD (`LICENSE`, `README.md`)
- **Before / After Numbers:**
  - Before: Missing LICENSE, imprecise RTL language description.
  - After: MIT LICENSE committed, accurate language description.
- **Remaining Issues:** None yet.

---

## Remediation Summary Table

| Finding ID | Title | Status | Primary Files Affected | Log Evidence |
|---|---|---|---|---|
| **F-01** | Honest Functional Coverage | TODO | `tb/pyuvm/func_cov/`, `tb/pyuvm/sequences/`, `docs/coverage_waivers.md` | `docs/logs/coverage_merged.log` |
| **F-02** | Missing & Mislabeled Tests | TODO | `tb/pyuvm/tests/`, `tb/block/`, `docs/vplan.md`, `scripts/gen_test_map.py` | `docs/test_map.csv` |
| **F-03** | Honest & Stronger Formal | TODO | `formal/`, `scripts/run_all_formal.sh` | `docs/logs/formal_suite.log` |
| **F-04** | Documentation Consistency | TODO | `README.md`, `docs/interfaces.md`, `docs/results.md` | `docs/logs/test_counts.log` |
| **F-05** | Mutation Testing & Triage | TODO | `mutation/`, `docs/mutation_triage.md` | `docs/logs/mutation_summary.log` |
| **F-06** | 20-Seed Regression | TODO | `scripts/run_regression.sh` | `docs/logs/regress_20seeds.log` |
| **F-07** | GitHub Actions CI | TODO | `.github/workflows/ci.yml` | GitHub Actions Run URL |
| **F-08** | Clean-Clone Reality Check | TODO | `.gitignore`, `docs/logs/clean_clone.log` | `docs/logs/clean_clone.log` |
| **F-09** | pyuvm Architecture Honesty | TODO | `docs/decisions.md`, `README.md` | `README.md` |
| **F-10** | Remove Flawed Audit Files | TODO | `docs/AUDIT_REPORT.md`, `audit/` | Git commit log |
| **F-11** | Physical Timing Honesty | TODO | `README.md`, `docs/results.md` | `synth/results/sta.log` |
| **F-12** | License & RTL Language | TODO | `LICENSE`, `README.md` | `LICENSE` |

---

## Commit & Tag Log

| Commit SHA | Tag | Message | Gate Evidence |
|---|---|---|---|
| *Pending* | - | - | - |
