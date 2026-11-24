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

- **Status:** **COMPLETED** (Gate Passed & Tagged `phase-3-done`)
- **Timestamp:** 2026-11-23 16:48 IST
- **Active Branch:** `main` (merging `rtl`, `dv`, tag `phase-3-done`)

### 1. What was Completed
- **RTL Implementation (6 new modules, 1,521 new lines of Verilog, 17 total SoC modules / 3,238 lines):**
  - `rtl/apb/apb_timer.v`: 32-bit down-counter with programmable `LOAD` reload, one-shot and periodic modes, `TIMEOUT` flag, W1C status register, and interrupt generation.
  - `rtl/apb/apb_gpio.v`: 16-bit GPIO controller with `DIR` direction control, `OUT` output data register, 2-FF input synchronizer on `gpio_i` to `IN`, rising-edge interrupt detection with per-pin `IRQ_EN` mask, and W1C `IRQ_STATUS`.
  - `rtl/apb/apb_uart.v`: Full 8N1 UART transceiver with 16x oversampling baud rate generator, 8-entry synchronous TX FIFO, 8-entry synchronous RX FIFO, internal loopback mode (`LOOPBACK`), status flags (`TX_FULL`, `TX_EMPTY`, `RX_FULL`, `RX_EMPTY`, `FRAME_ERR`, `RX_OVF`, `TX_OVF`, `TX_BUSY`), and RX threshold interrupt.
  - `rtl/cdc/slow_regs.v`: Registers located in asynchronous `clk_slow` domain (`SLOW_ID: 0x510E_0001`, `SLOW_SCRATCH` with byte strobes, free-running 32-bit `SLOW_COUNTER`, `SLOW_CTRL` counter enable, and SLVERR on undefined offsets).
  - `rtl/cdc/axil_cdc_bridge.v`: AXI4-Lite slave on `clk_sys` translating read/write transfers to 4-entry request async FIFO (`clk_sys` -> `clk_slow`) and 4-entry response async FIFO (`clk_slow` -> `clk_sys`) connecting to `slow_regs`.
  - `rtl/amba_fabric_top.v`: Full SoC top-level integrating `rst_sync` x2 (`clk_sys`, `clk_slow`), 2-Master x 4-Slave `axil_xbar`, S0 APB subsystem (`axil2apb_bridge` + `apb_decoder` + `apb_uart` + `apb_timer` + `apb_gpio`), S1 Scratchpad RAM (`axil_ram`), S2 CSR Block with 3-source interrupt aggregation (`axil_csr` -> `irq_o`), and S3 CDC Bridge (`axil_cdc_bridge` + `slow_regs`).
- **DV Implementation (6 new testbench and driver files, 1,076 lines of Python):**
  - `tb/models/apb_driver.py`: Synchronous APB4 Master Driver class with `write(addr, data, strb, prot)` and `read(addr, prot)`.
  - `tb/block/test_apb_timer.py`: Directed tests `TM-01` (one-shot exact cycle count to timeout), `TM-02` (periodic intervals and repeated reloads), `TM-03` (W1C timeout and IRQ clear).
  - `tb/block/test_apb_gpio.py`: Directed tests `GP-01` (`DIR` and `OUT` control of external pins), `GP-02` (2-FF input synchronization latency on `IN`), `GP-03` (rising-edge IRQ detection, mask enable/disable, and W1C clear).
  - `tb/block/test_apb_uart.py`: Directed tests `UA-01` (loopback byte transfer across diverse patterns), `UA-02` (FIFO full/empty flags, TX_OVF, RX_OVF, and W1C clear), `UA-03` (`BAUDDIV` sweep verifying exact bit duration scaling for 0, 1, 2), `UA-05` (RX IRQ enable/disable following `RX_IRQ_EN & ~RX_EMPTY`).
  - `tb/block/test_axil_cdc_bridge.py`: Directed tests `CD-01` (cross-domain write and read data integrity on `SLOW_SCRATCH` with full 32-bit patterns and byte strobes), `CD-04` (free-running counter in `clk_slow` read continuously from `clk_sys`, start/stop via `SLOW_CTRL`), `CD-05` (`SLOW_ID` read-only protection, and `SLVERR` response propagation on unmapped offset).
  - `tb/block/test_amba_fabric_top.py`: Comprehensive SoC integration tests:
    - `TOP-01`: Verified every register-map entry in the spec across UART, Timer, GPIO, Scratchpad RAM, CSR Block, CDC Slow Regs, and Default Slave from both Master 0 and Master 1.
    - `TOP-02`: Verified peripheral interrupt aggregation from UART, Timer, and GPIO through CSR `IRQ_RAW`, `IRQ_MASK`, and level propagation to the top-level `irq_o` pin.
- **Testbench Execution:**
  - `tb/block/Makefile`: Expanded to 7 test targets encompassing all 26 block/integration test cases.
  - 26/26 tests passed on Icarus Verilog.
  - 26/26 tests passed on Verilator 5.055.
  - 8/8 L0 unit tests passed on Icarus Verilog.
  - 4/4 SBY formal proof suites passed.

### 2. Files Created & Modified
- `rtl/apb/apb_timer.v`: Created
- `rtl/apb/apb_gpio.v`: Created
- `rtl/apb/apb_uart.v`: Created & modified (fixed TX fetch race and RX start-bit timing)
- `rtl/cdc/slow_regs.v`: Created
- `rtl/cdc/axil_cdc_bridge.v`: Created
- `rtl/amba_fabric_top.v`: Created
- `tb/models/apb_driver.py`: Created & modified (added settling delay)
- `tb/block/test_apb_timer.py`: Created & modified (corrected await and ReadOnly timing)
- `tb/block/test_apb_gpio.py`: Created & modified (adjusted synchronizer sample window)
- `tb/block/test_apb_uart.py`: Created & modified (improved TX_BUSY wait and ReadOnly sample)
- `tb/block/test_axil_cdc_bridge.py`: Created
- `tb/block/test_amba_fabric_top.py`: Created
- `tb/block/Makefile`: Modified (added 5 new block and top-level test targets)
- `docs/logs/phase3_gate.log`: Created
- `docs/bugs.md`: Modified (added BUG-009..BUG-011)
- `docs/results.md`: Modified (updated overall metrics and Phase 3 gate record)

### 3. Commands Executed & Results
- `make lint`: 17 RTL modules clean on Verilator 5.055 (PASS - 0 errors, 0 warnings).
- `make unit SIM=icarus`: 8/8 L0 unit tests passed on Icarus Verilog (PASS).
- `make block SIM=icarus`: 26/26 L1 block and subsystem tests passed on Icarus Verilog (PASS).
- `make block SIM=verilator`: 26/26 L1 block and subsystem tests passed on Verilator 5.055 (PASS).
- `make formal`: 4/4 SBY formal proof suites passed (PASS):
  - `async_fifo`: BMC depth 25 multiclock (PASS), cover 4 traces (PASS).
  - `axil2apb_bridge`: BMC depth 25 (PASS), cover 5 traces (PASS).
  - `axil_xbar`: BMC depth 20 (PASS), cover 5 traces (PASS).
  - `rr_arbiter`: k-induction prove depth 20 (PASS), cover 5 traces (PASS).
- `git tag phase-3-done`: Tagged repository upon passing acceptance gate.

### 4. Bugs Found & Resolved
- `BUG-009`: UART Transmitter FSM multi-cycle pop race with synchronous FIFO where registered `tx_pop_req` caused `tx_shifter` to latch stale zero data. Resolved by making `tx_fifo_pop` combinational during `TX_ST_IDLE`.
- `BUG-010`: UART Receiver premature state transition on mid-start bit sample (tick 7 instead of tick 15) causing 8-tick sampling phase error and framing errors. Resolved by gating data-state transition with `rx_tick_cnt == 15`.
- `BUG-011`: UART Receiver `prdata` mux zero mask when FIFO emptied during APB SETUP phase. Resolved with registered `rx_had_data` flag set during SETUP.

---

## Phase 4: pyuvm Environment

- **Status:** **COMPLETED** (Gate Passed & Tagged `phase-4-done`)
- **Timestamp:** 2026-11-24 11:45 IST
- **Active Branch:** `main` (merging `dv`, tag `phase-4-done`)

### 1. What was Completed
- **Independent Reference Models (`tb/models/`):**
  - `tb/models/addr_map.py`: Spec-authoritative address decoder model mapping APB peripherals (UART, Timer, GPIO), 1 KB Scratchpad RAM, CSR Block, CDC Slow Regs, and unmapped error spaces.
  - `tb/models/ram_model.py`: Byte-accurate 1 KB scratchpad RAM model supporting arbitrary byte strobes (`WSTRB`), 32-bit reads, and out-of-bounds `SLVERR` generation.
  - `tb/models/reg_model.py`: CSR model (`CsrModel`) tracking `REV_ID`, `VERSION`, `SCRATCH`, `SCRATCH2`, `IRQ_MASK`, and W1C registers (`W1C_TEST`, `W1C_SET`); and CDC Slow Regs model (`SlowRegsModel`) tracking `SLOW_ID`, `SLOW_SCRATCH` with byte strobes, and `SLOW_CTRL`.
  - `tb/models/peripheral_model.py`: Peripheral models for `ApbUartModel` (loopback FIFO semantics), `ApbTimerModel` (one-shot/periodic down-counter with auto-stop and reload), and `ApbGpioModel` (direction, output registers, and interrupt mask).
  - `tb/models/fabric_ref_model.py`: Unified system-level reference model predicting read/write responses (`OKAY`, `SLVERR`, `DECERR`), expected read data, and exact-data check qualification.
- **pyuvm Verification Architecture (`tb/pyuvm/`):**
  - `tb/pyuvm/sequences/axil_seq_item.py`: Constrained-random AXI4-Lite transaction sequence item with target distribution (RAM 40%, CSR 20%, CDC 15%, APB 15%, Unmapped 10%), channel ordering permutations (`simultaneous`, `aw_first`, `w_first`), random byte strobes, and per-master address partitioning.
  - `tb/pyuvm/sequences/axil_base_seq.py`: Base sequence providing atomic helper routines (`write`, `read`) with response capture.
  - `tb/pyuvm/sequences/directed_seqs.py`: Sequences covering directed test scenarios (`XB-11` SLVERR, `XB-14` PROT pass-through, `XB-15` unaligned LSBs, `BR-04` byte strobes, `BR-06` write ordering permutations, `XB-12` reset recovery, and `BR-05` contention).
  - `tb/pyuvm/sequences/fabric_stress_seq.py`: Top-level stress sequence driving concurrent constrained-random streams from Master 0 and Master 1.
  - `tb/pyuvm/agents/axil_master_agent.py`: Encapsulates `AxilSequencer`, `AxilDriver` (driving physical DUT signals via `AxilMasterDriver`), and analysis broadcast ports.
  - `tb/pyuvm/env/fabric_scoreboard.py`: Synchronous scoreboard (`FabricScoreboard`) subscribing to Master 0 and Master 1 transactions, predicting expected responses via `FabricRefModel`, and asserting zero mismatches on completion.
  - `tb/pyuvm/env/fabric_env.py`: Connects master agents and scoreboard analysis ports.
  - `tb/pyuvm/tests/test_directed.py`: 7 directed test cases verifying protocol rules and edge conditions across both Icarus Verilog and Verilator.
  - `tb/pyuvm/tests/test_stress.py`: Milestone `XB-13` stress test running dual asynchronous clocks (`clk_sys` 100 MHz, `clk_slow` 40 MHz) and driving concurrent transactions across both masters.
  - `tb/pyuvm/Makefile` and `tb/pyuvm/Makefile.single`: Multi-simulator build harnesses supporting `SIM=icarus` and `SIM=verilator`.
  - `scripts/run_phase4_gate.sh`: Automated Phase 4 acceptance gate runner script.
- **Acceptance Gate Verification:**
  - Directed pyuvm tests: 7/7 PASS on Icarus Verilog; 7/7 PASS on Verilator 5.055.
  - `XB-13` Random Stress Regression: Executed 50,000 transactions across 5 seeds (42, 123, 777, 2024, 9999; 10,000 transactions each).
  - Zero scoreboard mismatches measured across all 50,000 transactions.
  - Full regression clean: 8/8 L0 unit tests PASS, 26/26 L1 block tests PASS, 4/4 SBY formal suites PASS.

### 2. Files Created & Modified
- `tb/models/addr_map.py`: Created
- `tb/models/ram_model.py`: Created
- `tb/models/reg_model.py`: Created
- `tb/models/peripheral_model.py`: Created
- `tb/models/fabric_ref_model.py`: Created
- `tb/models/axil_driver.py`: Modified (added `safe_int` for robust integer conversion)
- `tb/pyuvm/sequences/axil_seq_item.py`: Created
- `tb/pyuvm/sequences/axil_base_seq.py`: Created
- `tb/pyuvm/sequences/fabric_stress_seq.py`: Created
- `tb/pyuvm/sequences/directed_seqs.py`: Created
- `tb/pyuvm/agents/axil_master_agent.py`: Created
- `tb/pyuvm/env/fabric_scoreboard.py`: Created
- `tb/pyuvm/env/fabric_env.py`: Created
- `tb/pyuvm/tests/test_directed.py`: Created
- `tb/pyuvm/tests/test_stress.py`: Created
- `tb/pyuvm/Makefile`: Created
- `tb/pyuvm/Makefile.single`: Created
- `scripts/run_phase4_gate.sh`: Created
- `rtl/axil/axil_xbar.v`: Modified (immediate target locking on transfer grant)
- `rtl/cdc/slow_regs.v`: Modified (synchronous request latching in IDLE)
- `docs/logs/phase4_gate.log`: Created
- `docs/logs/xb13_stress.log`: Created
- `docs/bugs.md`: Modified (added BUG-012..BUG-015)
- `docs/results.md`: Modified
- `docs/checkpoint.md`: Modified

### 3. Commands Executed & Results
- `make lint`: 17 RTL modules clean on Verilator 5.055 (PASS - 0 errors, 0 warnings).
- `make unit SIM=icarus`: 8/8 L0 unit tests passed (PASS).
- `make block SIM=icarus`: 26/26 L1 block and integration tests passed (PASS).
- `make formal`: 4/4 SymbiYosys formal verification suites passed (PASS):
  - `async_fifo`: BMC depth 25 multiclock (PASS), cover 4 traces (PASS).
  - `axil2apb_bridge`: BMC depth 25 (PASS), cover 5 traces (PASS).
  - `axil_xbar`: BMC depth 20 (PASS), cover 5 traces (PASS).
  - `rr_arbiter`: k-induction prove depth 20 (PASS), cover 5 traces (PASS).
- `bash scripts/run_phase4_gate.sh`: (PASS)
  - Directed pyuvm tests (Icarus): 7/7 PASS (`test_directed.py`).
  - Directed pyuvm tests (Verilator): 7/7 PASS (`test_directed.py`).
  - XB-13 Stress Regression (Verilator): 5/5 seeds PASS (50,000 transactions total, 0 mismatches).
- `git tag phase-4-done`: Tagged repository upon passing acceptance gate.

### 4. Bugs Found & Resolved
- `BUG-012`: Crossbar Multi-Master Target Locking on Transfer Initiation. Resolved in `rtl/axil/axil_xbar.v` by asserting target lock immediately upon transfer initiation.
- `BUG-013`: CDC Slow Registers Asynchronous FIFO Pop Off-by-One Pipeline Skew. Resolved in `rtl/cdc/slow_regs.v` by latching request fields upon state transition into `ST_RESP`.
- `BUG-014`: Icarus Verilog Signal Declaration Order Elaboration Error in `slow_regs.v`. Resolved by moving `wire _unused` after signal declaration.
- `BUG-015`: Cocotb 2.1 Unresolved LogicArray Integer Conversion Exception. Resolved in `tb/models/axil_driver.py` via `safe_int()`.

---

## Phase 5: Coverage and Formal Closure

- **Status:** **COMPLETED** (Gate Passed & Tagged `phase-5-done`)
- **Timestamp:** 2026-11-24 12:22 IST
- **Active Branch:** `main` (commit to be merged, tag `phase-5-done`)

### 1. What was Completed
- **Formal Verification Closure (Spec Section 11):**
  - Completed all 8 SymbiYosys formal verification suites:
    1. `apb_timer`: k-induction proof (depth 20) with Boolector proving down-counting, timeout assertion on reaching zero, periodic reload, one-shot stop, and W1C status clear. 4 cover scenarios reached.
    2. `async_fifo`: Multi-clock BMC (depth 25) proving Gray code sequencing, pointer consistency, and cross-domain data integrity via magic value tracking. 4 cover scenarios reached.
    3. `axil2apb_bridge`: BMC (depth 25) proving APB setup/access protocol timing, wait-state stability, single-cycle completion, and PSLVERR-to-SLVERR mapping. 5 cover scenarios reached.
    4. `axil_csr`: k-induction proof (depth 20) proving read-only constants (`REV_ID`), scratch read/write byte strobes, W1C status behavior, and interrupt aggregation. 4 cover scenarios reached.
    5. `axil_ram`: BMC (depth 20) proving in-bounds OKAY responses, out-of-bounds SLVERR responses, response stability, and byte strobes. 4 cover scenarios reached.
    6. `axil_xbar`: BMC (depth 20) proving mutual exclusivity, decode isolation, default slave DECERR routing, and master response isolation. 5 cover scenarios reached.
    7. `rr_arbiter`: k-induction proof (depth 20) proving one-hot grants, no spurious grant, priority rotation, and transaction lock persistence. 5 cover scenarios reached.
    8. `sync_fifo`: k-induction proof (depth 20) proving occupancy count consistency with simultaneous push/pop, full/empty flags, and no data corruption. 6 cover scenarios reached.
  - Total: **8/8 formal proof targets PASS (100%)**, 37 cover traces reached.
- **Functional Coverage Model (Spec Section 10):**
  - Implemented `tb/pyuvm/func_cov/fabric_cov.py` using `cocotb-coverage`:
    - `cg_txn`: Master (0, 1) x Target (RAM, CSR, CDC, APB, UNMAPPED) x Op (RD, WR) x Resp (OKAY, SLVERR, DECERR). Legal cross bins = 36 (illegal DECERR on mapped slaves and OKAY/SLVERR on unmapped space cleanly excluded via `ign_bins`).
    - `cg_wstrb`: 16 `WSTRB` patterns x 4 mapped targets = 64 bins.
    - `cg_order`: 3 write orders (`simultaneous`, `aw_first`, `w_first`) x 4 mapped targets = 12 bins.
    - `cg_backpressure`: 5 channels (AW, W, B, AR, R) x 4 delay buckets {0, 1, 2-4, 5-16} = 20 bins.
    - `cg_contention`: 3 contention scenarios (`same_slave`, `diff_slaves`, `one_idle`) x 3 op combinations (R/R, R/W, W/W) = 9 bins.
    - `cg_apb`: 4 wait-state buckets x 2 error values x 2 ops = 16 bins; 4 strobe pattern classes x 2 ops = 8 bins.
    - `cg_cdc`: 3 clock ratio buckets x 3 FIFO occupancy states x 2 ops = 18 bins.
    - `cg_uart`: 3 baud divisor buckets x 3 FIFO states = 9 bins; 3 error types = 3 bins.
    - `cg_reset`: 5 reset phases (`idle`, `aw_in_flight`, `w_in_flight`, `b_pending`, `r_pending`) = 5 bins.
    - Plus 80 individual coverpoints = **280 total defined bins**.
  - Integrated automatic transaction sampling in `FabricScoreboard.check_transaction()`.
  - Integrated backpressure delay cycle sampling in `AxilMasterDriver.write()` and `read()`.
  - Added `TestCoverageClosure` in `tb/pyuvm/tests/test_directed.py` exercising edge strobe combinations, write channel ordering permutations, and multi-master protocol corners.
  - Implemented `scripts/merge_cov.py` to aggregate YAML coverage databases across multi-seed runs, compute coverage statistics, and detect holes.
  - **Achieved 100.00% Functional Coverage (280/280 bins hit, 0 holes, 0 waivers).**
- **Verilator HDL Code Coverage (Spec Section 10):**
  - Configured Verilator `--coverage` build via `VERILATOR_COVERAGE=1` in `tb/pyuvm/Makefile.single`.
  - Executed full multi-seed regression (directed tests + 5 stress seeds = 25,000 transactions).
  - Merged coverage data from all runs into `docs/logs/coverage_merged.dat`.
  - Measured metrics:
    - **Line Coverage:** 87.8% (430 / 490 lines)
    - **Toggle Coverage:** 75.1% (10,155 / 13,514 transitions)
    - **Branch Coverage:** 86.9% (433 / 498 branches)
    - **Expression Coverage:** 92.9% (1,016 / 1,094 sub-expressions)
    - **FSM State Coverage:** 100.0% (5 / 5 states)
    - **FSM Transition Arc Coverage:** 25.0% (1 / 4 transitions)
  - Generated source code coverage annotations for all 17 RTL modules under `docs/logs/code_cov/`.
- **Regression & Tool Automation:**
  - Created `scripts/run_regression.sh` automating end-to-end regression execution, Verilator coverage data merging, annotation generation, and functional coverage reporting.
  - Updated `Makefile` targets `formal` and `cov-report`.

### 2. Files Created & Modified
- `rtl/apb/apb_timer.v`: Modified (added formal properties for countdown, reload, timeout, and APB write priority)
- `rtl/axil/axil_ram.v`: Modified (added formal properties for bounds check and response stability)
- `rtl/axil/axil_csr.v`: Modified (added formal properties for register read/write and interrupt aggregation)
- `formal/apb_timer.sby`: Created
- `formal/axil_ram.sby`: Created
- `formal/axil_csr.sby`: Created
- `formal/sync_fifo.sby`: Created
- `formal/sync_fifo_props.v`: Created
- `tb/pyuvm/func_cov/fabric_cov.py`: Created
- `tb/pyuvm/func_cov/__init__.py`: Created
- `tb/pyuvm/sequences/coverage_closure_seq.py`: Created
- `tb/pyuvm/tests/test_directed.py`: Modified (added `TestCoverageClosure`)
- `tb/pyuvm/env/fabric_scoreboard.py`: Modified (integrated coverage sampling & export)
- `tb/models/axil_driver.py`: Modified (integrated backpressure delay tracking & sampling)
- `tb/pyuvm/Makefile.single`: Modified (added `VERILATOR_COVERAGE` flag)
- `scripts/merge_cov.py`: Created
- `scripts/run_regression.sh`: Created
- `Makefile`: Modified (`cov-report` targets)
- `docs/logs/formal_suite.log`: Created
- `docs/logs/func_cov.log`: Created
- `docs/logs/code_cov_summary.txt`: Created
- `docs/results.md`: Modified (updated with real measured metrics)
- `docs/checkpoint.md`: Modified

### 3. Commands Executed & Results
- `make formal`: 8/8 formal proof suites passed (PASS).
  - `apb_timer`: PASS (k-induction depth 20, cover 4 traces)
  - `async_fifo`: PASS (BMC depth 25, cover 4 traces)
  - `axil2apb_bridge`: PASS (BMC depth 25, cover 5 traces)
  - `axil_csr`: PASS (k-induction depth 20, cover 4 traces)
  - `axil_ram`: PASS (BMC depth 20, cover 4 traces)
  - `axil_xbar`: PASS (BMC depth 20, cover 5 traces)
  - `rr_arbiter`: PASS (k-induction depth 20, cover 5 traces)
  - `sync_fifo`: PASS (k-induction depth 20, cover 6 traces)
- `make cov-report`: Executed full regression and coverage pipeline (PASS):
  - Directed verification suite: 8/8 PASS (`test_directed.py`)
  - Stress multi-seed regression: 5/5 seeds PASS (25,000 transactions, 0 mismatches)
  - Verilator code coverage: Line 87.8%, Toggle 75.1%, Branch 86.9%, Expr 92.9%
  - Functional coverage: 280/280 bins hit (100.00%, 0 holes)
- `git tag phase-5-done`: Tagged repository upon passing acceptance gate.

### 4. Bugs Found & Resolved
- `BUG-016`: APB Timer countdown formal assertion failing due to unconstrained past APB register write collision. Resolved by qualifying countdown check with `!$past(apb_write && (paddr[3:2] == 2'b00))`.
- `BUG-017`: AXI-Lite RAM response assertion failing when multiple writes arrived without `bready`. Resolved by checking response validity on exact `write_commit` cycles and checking stability while waiting for `bready`.
- `BUG-018`: Cocotb Makefile `COVERAGE=1` reserving Python coverage module name, causing namespace shadowing with local `coverage/` package. Resolved by renaming local package to `func_cov` and using `VERILATOR_COVERAGE=1` for HDL coverage.
- `BUG-019`: Yosys SBY parser rejecting cross-module hierarchical references for width detection. Resolved by embedding assertions within module bodies under `` `ifdef FORMAL ``.

---

## Phase 6: Mutation Testing, Synthesis/STA, and CI

- **Status:** **PAUSED (Awaiting Instruction Before Starting Phase 6)**
- **User Instruction:** Stopped after completing Phase 5 per user directive (`stop after every phase completed and checkpoint was written`).
- **Upcoming Scope:**
  - Mutation flow using Yosys `mutate` with survivor analysis.
  - Synthesis and OpenSTA on SKY130 HD library with timing constraints.
  - GitHub Actions CI workflow creation.



