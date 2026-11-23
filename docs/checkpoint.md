# AMBA-Fabric Project Checkpoint Log

This file tracks the iteration-by-iteration progress of the AMBA-Fabric project.
For every phase, it records what was completed, executed, created, observed, and verified.

---

## Phase 0: Setup and Contract

- **Status:** **COMPLETED** (Gate Passed & Tagged `phase-0-done`)
- **Timestamp:** 2026-11-23 12:16 IST
- **Active Branch:** `main` (commit `91399d4`, tag `phase-0-done`)

### 1. What was Completed
- Host toolchain audit: verified `iverilog` (v14.0 devel), `verilator` (v5.055 devel), `yosys` (v0.71+77), `sby` (v0.71-7), `sta` (v2.6.0), `gtkwave` (v4.0.0), and SKY130 Liberty files.
- Repository skeleton and directory layout created following spec Section 15.
- Pinned Python virtual environment with `cocotb 2.1.0`, `pyuvm 5.0.0`, `cocotb-coverage 2.0`, `pytest 9.2.0`, `numpy 2.5.5`, `matplotlib 3.11.2`.
- Unified top-level `Makefile` and toolchain environment wrapper `scripts/env.sh`.
- Integration smoke test `tb/unit/hello_world.v` and `tb/unit/test_hello_world.py` verifying pyuvm + cocotb execution on both Icarus Verilog and Verilator.
- Architectural contract `docs/interfaces.md` drafted in full detail and frozen.
- Verification plan baseline `docs/vplan.md` created mapping features to tests and checkers.
- Tracking logs initialized: `docs/decisions.md` (DEC-001..DEC-003), `docs/bugs.md`, `docs/results.md`.

### 2. Files Created
- `.gitignore`: Ignoring build dirs, waveforms, logs, and venv.
- `docs/spec.md`: Authoritative specification copy.
- `requirements.txt`: Pinned Python dependencies.
- `scripts/env.sh`: Environment variables and toolchain configuration.
- `Makefile`: Top-level make targets (`lint`, `unit`, `regress`, `formal`, `mutation`, `synth`, `sta`, `clean`).
- `tb/unit/hello_world.v`: Verilog counter testbench target.
- `tb/unit/test_hello_world.py`: pyuvm component/test verifying clock, reset, and count logic.
- `tb/unit/Makefile`: Unit test runner harness.
- `docs/interfaces.md`: Frozen architectural contract.
- `docs/vplan.md`: Verification plan traceability matrix.
- `docs/decisions.md`: Architectural decision log.
- `docs/bugs.md`: Bug tracking log.
- `docs/results.md`: Measured metrics tracking table.
- `docs/logs/phase0_gate.log`: Captured terminal log from gate execution.

### 3. Commands Executed & Results
- `make env-check`: Verified all 7 EDA tools, PDK libraries, and Python imports. (PASS)
- `make lint`: Verilator lint check on RTL. (PASS)
- `make unit SIM=icarus`: Ran hello-world test on Icarus Verilog. (PASS - 1/1 tests passed in 81 ns sim time)
- `make unit SIM=verilator`: Ran hello-world test on Verilator. (PASS - 1/1 tests passed in 81 ns sim time)
- `make clean`: Cleaned build directories. (PASS)
- `git tag phase-0-done`: Tagged repository at Phase 0 gate.

---

## Phase 1: Common Blocks and AXI-Lite Basics

- **Status:** **IN PROGRESS**
- **Timestamp:** 2026-11-23
- **Objectives:**
  - RTL: `rst_sync.v`, `sync_fifo.v`, `async_fifo.v`, `rr_arbiter.v`, `axil_ram.v`, `axil_csr.v`, `axil_default_slave.v`.
  - DV: L0 cocotb unit tests in `tb/unit/` for each module, basic AXI-Lite master driver.
  - Formal: SymbiYosys property sets and proofs for `rr_arbiter` and `async_fifo`.
  - Gate: All L0 unit tests pass, formal proofs pass, Verilator lint clean, tag `phase-1-done`.
