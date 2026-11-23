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

- **Status:** **COMPLETED** (Gate Passed & Tagged `phase-1-done`)
- **Timestamp:** 2026-11-23 12:44 IST
- **Active Branch:** `main` (merging `rtl`, `dv`, `formal`, tag `phase-1-done`)

### 1. What was Completed
- **RTL Implementation (7 modules, 913 lines of Verilog):**
  - `rtl/common/rst_sync.v`: 2-FF reset synchronizer with asynchronous assert, synchronous deassert.
  - `rtl/common/sync_fifo.v`: Single-clock synchronous FIFO with occupancy counter, overflow/underflow flags, and simultaneous read/write handling.
  - `rtl/common/async_fifo.v`: Cummings dual-clock Gray pointer asynchronous FIFO with registered empty/full flags and CDC multi-clock formal hooks.
  - `rtl/common/rr_arbiter.v`: Round-robin arbiter with transaction lock, one-hot priority pointer rotation, and formal induction invariants.
  - `rtl/axil/axil_default_slave.v`: AXI4-Lite error termination slave responding DECERR on arbitrary request arrival orders (AW before W, W before AW, simultaneous).
  - `rtl/axil/axil_ram.v`: 1 KB scratchpad RAM supporting byte-strobe writes (`WSTRB`), 32-bit single-cycle reads/writes, and out-of-range address SLVERR response.
  - `rtl/axil/axil_csr.v`: CSR block implementing 5 registers (RO identification `REV_ID`, RW `SCRATCH`, W1C `STATUS`, RW `INT_ENABLE`, RO `VERSION`) and level interrupt aggregation to `irq_o`.
- **DV Implementation:**
  - `tb/models/axil_driver.py`: Reusable AXI4-Lite master driver class supporting non-blocking concurrent channel drivers for AW, W, B, AR, R channels with write ordering permutation controls (`aw_first`, `w_first`, `simultaneous`).
  - Unit test harnesses and Makefiles (`tb/unit/Makefile`, `tb/unit/Makefile.single`) executing clean, isolated simulation builds for both Icarus Verilog and Verilator.
  - 8 L0 cocotb unit tests: `test_hello_world.py`, `test_rst_sync.py`, `test_sync_fifo.py`, `test_async_fifo.py`, `test_rr_arbiter.py`, `test_axil_default_slave.py`, `test_axil_ram.py`, `test_axil_csr.py`.
- **Formal Verification (SymbiYosys):**
  - `formal/rr_arbiter.sby`: Verified one-hot grant, no spurious grant, requester grant consistency, transaction lock persistence, and 5 cover scenarios via k-induction (depth 20) with Boolector.
  - `formal/async_fifo.sby`: Verified 1-bit Gray pointer transitions, binary/Gray pointer consistency, and cross-domain data integrity via magic value tracking over multi-clock domains (`multiclock on`, `async2sync`) with Boolector (BMC depth 25, 4 cover traces reached).
  - `scripts/run_all_formal.sh`: Automated formal runner generating summary pass/fail tables across all SBY targets.

### 2. Files Created
- `rtl/common/rst_sync.v`
- `rtl/common/sync_fifo.v`
- `rtl/common/async_fifo.v`
- `rtl/common/rr_arbiter.v`
- `rtl/axil/axil_default_slave.v`
- `rtl/axil/axil_ram.v`
- `rtl/axil/axil_csr.v`
- `tb/models/axil_driver.py`
- `tb/unit/Makefile.single`
- `tb/unit/test_rst_sync.py`
- `tb/unit/test_sync_fifo.py`
- `tb/unit/test_async_fifo.py`
- `tb/unit/test_rr_arbiter.py`
- `tb/unit/test_axil_default_slave.py`
- `tb/unit/test_axil_ram.py`
- `tb/unit/test_axil_csr.py`
- `formal/rr_arbiter.sby`
- `formal/rr_arbiter_props.v`
- `formal/async_fifo.sby`
- `scripts/run_all_formal.sh`
- `docs/logs/phase1_gate.log`

### 3. Commands Executed & Results
- `make lint`: 9 RTL modules linted cleanly with Verilator 5.055. (PASS - 0 errors, 0 warnings)
- `make unit SIM=icarus`: 8/8 unit tests passed on Icarus Verilog. (PASS)
- `make unit SIM=verilator`: 8/8 unit tests passed on Verilator 5.055. (PASS)
- `make formal`: 2/2 SBY targets passed. (PASS)
  - `rr_arbiter`: k-induction prove depth 20 (PASS), cover 5 traces (PASS).
  - `async_fifo`: BMC depth 25 multiclock (PASS), cover 4 traces (PASS).
- `git tag phase-1-done`: Tagged repository upon passing acceptance gate.

### 4. Bugs Found & Resolved
- `BUG-001`: Asynchronous FIFO read pointer duplicate continuous assignment. Resolved in `rtl/common/async_fifo.v`.
- `BUG-002`: Magic-value data integrity formal tracker lifecycle reset on wraparound. Resolved in `rtl/common/async_fifo.v` with full `PTR_WIDTH` tracking.
- `BUG-003`: Multi-clock reset glitch injection by SMT solver between clock edges. Resolved with combinational invariant `always @(*)`.
- `BUG-004`: VPI teardown race causing `vvp` segfault on exit in `test_axil_default_slave.py`. Resolved with post-handshake clock settling delay.

---

## Phase 2: Crossbar and APB Bridge

- **Status:** **COMPLETED** (Gate Passed & Tagged `phase-2-done`)
- **Timestamp:** 2026-11-23 13:16 IST
- **Active Branch:** `main` (merging `rtl`, `dv`, `formal`, tag `phase-2-done`)

### 1. What was Completed
- **RTL Implementation (4 modules, 804 lines of Verilog, 13 total modules in system):**
  - `rtl/axil/axil_decoder.v`: Address decoder for 4 external slaves (`S0_APB: 0x4000_0000`, `S1_RAM: 0x5000_0000`, `S2_CSR: 0x6000_0000`, `S3_CDC: 0x7000_0000`) and unmapped space decode error flag.
  - `rtl/axil/axil_xbar.v`: 2-Master × 4-Slave (+ internal default slave) crossbar with independent write and read round-robin arbiters (`rr_arbiter`), transaction locking from address phase until response handshake completes, 0-cycle added routing latency, and per-master response isolation.
  - `rtl/apb/axil2apb_bridge.v`: AXI4-Lite to APB4 bridge FSM (`ST_IDLE`, `ST_WAIT_W`, `ST_WAIT_AW`, `ST_SETUP`, `ST_ACCESS`, `ST_BRESP`, `ST_RRESP`) with strict APB setup/access timing and `PSLVERR` to `SLVERR` translation.
  - `rtl/apb/apb_decoder.v`: APB peripheral address decoder routing `PSEL` to UART (`0x4000_0000`), Timer (`0x4000_1000`), GPIO (`0x4000_2000`), and unmapped APB error space.
- **DV Implementation:**
  - `tb/models/axil_slave_responder.py`: Configurable reactive AXI4-Lite slave responder supporting arbitrary backpressure delays and byte strobe verification.
  - `tb/models/apb_slave_responder.py`: Synchronous APB4 slave responder handling byte strobes, programmable wait-state insertion, and `PSLVERR` injection.
  - `tb/models/axil_monitor.py`: Passive protocol monitor checking AXI4-Lite handshake stability rules, legal response codes, and request-response matching.
  - `tb/block/tb_axil_xbar.v`: Verilog top-level wrapper exposing individual M0/M1 and S0..S3 ports with VCD waveform dumping.
  - `tb/block/test_axil_xbar.py`: Directed tests `XB-01` through `XB-08` verifying master-slave routing, RAM data integrity, all 16 `WSTRB` patterns, unmapped DECERR handling, concurrent same-slave contention serialization, concurrent different-slave parallel execution, round-robin fairness, and write channel orderings (AW-first, W-first, simultaneous).
  - `tb/block/test_axil2apb_bridge.py`: Directed tests `BR-01` through `BR-03` verifying 0 wait-state transfers, 1..4 cycle wait states, and `PSLVERR` propagation to `SLVERR`.
  - `tb/block/Makefile` & `tb/block/Makefile.single`: Block test runner harness supporting both Icarus Verilog and Verilator 5.055.
- **Formal Verification (SymbiYosys):**
  - `formal/axil_props.v`: Reusable AXI4-Lite protocol property checker validating handshake stability, legal response codes (excluding EXOKAY 2'b01), and request-response causality tracking.
  - `formal/axil_xbar.sby` & `formal/axil_xbar_props.v`: Proved mutual exclusivity, decode isolation, default slave DECERR routing, and response stability across 20 BMC steps; reached 5 cover scenarios including simultaneous M0/M1 contention for S1 RAM and parallel multi-slave transactions.
  - `formal/axil2apb_bridge.sby` & `formal/axil2apb_bridge_props.v`: Proved APB protocol compliance (`PENABLE` sequencing, signal stability during wait states, single-cycle completion, `PSLVERR` translation to `SLVERR`) across 25 BMC steps; reached 5 cover scenarios.
- **Waveform & Visual Artifacts:**
  - `scripts/render_waveform.py`: Python script parsing VCD dumps and rendering publication-quality digital timing diagrams.
  - `docs/img/contention.png`: High-resolution timing diagram capturing M0 and M1 concurrent contention for S1 RAM (XB-05), illustrating arbitration grant, M1 backpressure stall, and subsequent serialized completion.
  - `docs/img/contention.vcd`: Raw VCD trace for inspection in GTKWave.

### 2. Files Created & Modified
- `rtl/axil/axil_decoder.v`: Created
- `rtl/axil/axil_xbar.v`: Created
- `rtl/apb/axil2apb_bridge.v`: Created
- `rtl/apb/apb_decoder.v`: Created
- `tb/models/axil_driver.py`: Modified (enhanced kwargs, alias, staggered W-first handling)
- `tb/models/axil_slave_responder.py`: Created
- `tb/models/apb_slave_responder.py`: Created
- `tb/models/axil_monitor.py`: Created
- `tb/block/tb_axil_xbar.v`: Created
- `tb/block/test_axil_xbar.py`: Created
- `tb/block/test_axil2apb_bridge.py`: Created
- `tb/block/Makefile`: Created
- `tb/block/Makefile.single`: Created
- `formal/axil_props.v`: Created
- `formal/axil_xbar.sby`: Created
- `formal/axil_xbar_props.v`: Created
- `formal/axil2apb_bridge.sby`: Created
- `formal/axil2apb_bridge_props.v`: Created
- `scripts/render_waveform.py`: Created
- `docs/img/contention.png`: Created
- `docs/img/contention.vcd`: Created
- `docs/logs/phase2_gate.log`: Created
- `Makefile`: Modified (added `block` target)
- `docs/bugs.md`: Modified (added BUG-005..BUG-008)
- `docs/decisions.md`: Modified (added DEC-004)
- `docs/results.md`: Modified (updated metrics table and gate log)

### 3. Commands Executed & Results
- `make lint`: 13 RTL modules linted cleanly with Verilator 5.055 (PASS - 0 errors, 0 warnings).
- `make unit SIM=icarus`: 8/8 L0 unit tests passed on Icarus Verilog (PASS).
- `make block SIM=icarus`: 11/11 L1 block tests passed on Icarus Verilog (PASS).
- `make block SIM=verilator`: 11/11 L1 block tests passed on Verilator 5.055 (PASS).
- `make formal`: 4/4 SBY formal proof suites passed (PASS):
  - `async_fifo`: BMC depth 25 (PASS), cover 4 traces (PASS).
  - `axil2apb_bridge`: BMC depth 25 (PASS), cover 5 traces (PASS).
  - `axil_xbar`: BMC depth 20 (PASS), cover 5 traces (PASS).
  - `rr_arbiter`: k-induction prove depth 20 (PASS), cover 5 traces (PASS).
- `git tag phase-2-done`: Tagged repository upon passing acceptance gate.

### 4. Bugs Found & Resolved
- `BUG-005`: APB Bridge premature completion on zero wait states when `PREADY` sampled before `PENABLE` was asserted. Resolved in `rtl/apb/axil2apb_bridge.v` by qualifying with `m_apb_penable && m_apb_pready`.
- `BUG-006`: `axil_monitor.py` protocol checker false stability assertion failure when checking `not cur_ready`. Resolved by checking `not self.last_ready`.
- `BUG-007`: Cocotb scheduler incompatibility with `asyncio.gather`. Resolved by starting background tasks with `cocotb.start_soon` and awaiting directly.
- `BUG-008`: Master driver staggered W-first transaction deadlock on multi-slave crossbar. Resolved by driving `AWVALID=1` after 2 cycles stagger without waiting for `WREADY`.

### 5. Architectural Decisions
- `DEC-004`: AXI-Lite W-First Ordering on Multi-Slave Crossbar (spec Section 6.2 clarification for non-buffered crossbar).

---

## Phase 3: Peripherals, CDC, and Top Level

- **Status:** **PAUSED (Awaiting Next Phase Instruction)**
- **User Instruction:** Stopped after Phase 2 per user directive (`stop after phase 2`).
- **Upcoming Scope:**
  - RTL: `apb_uart.v`, `apb_timer.v`, `apb_gpio.v`, IRQ aggregation, `axil_cdc_bridge.v`, `slow_regs.v`, `amba_fabric_top.v`.
  - DV: Peripheral agents, clock-reset driver, directed tests UA-01, TM-01..TM-03, GP-01..GP-03, CS-01..CS-03, CD-01..CD-05, and top-level connectivity test.

