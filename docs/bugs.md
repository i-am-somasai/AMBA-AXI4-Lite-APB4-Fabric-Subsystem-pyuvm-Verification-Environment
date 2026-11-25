# Bug Tracking Log

This document tracks all bugs discovered across RTL, testbenches, reference models, and formal checkers.
Per project rules, every bug must be reproduced deterministically, diagnosed to root cause, resolved, and documented here.

## Bug Schema

```markdown
### [BUG-XXX] <Brief Title>
- **Date Discovered:** YYYY-MM-DD
- **Target Component:** e.g., `axil_xbar`, `async_fifo`
- **Detection Method:** Scoreboard / Protocol Monitor / Formal Proof / Mutation / Directed Test
- **Symptom:** What failed, error message, counterexample seed
- **Root Cause:** Detailed explanation of why the failure occurred
- **Fix Applied:** Description of changes in RTL or testbench
- **Regression Test:** Test name verifying the permanent fix
```

---

## Log Entries

### [BUG-001] Asynchronous FIFO Read Pointer Multi-driver Syntax Error
- **Date Discovered:** 2026-11-23
- **Target Component:** `rtl/common/async_fifo.v`
- **Detection Method:** Formal Proof (SymbiYosys elaboration)
- **Symptom:** `ERROR: Found multiple drivers for \rbin_next [0]` during SBY elaboration.
- **Root Cause:** `rbin_next` and `rgray_next` were assigned inline at wire declarations and subsequently assigned a second time with continuous `assign` statements.
- **Fix Applied:** Removed duplicate continuous assign statements in `rtl/common/async_fifo.v`.
- **Regression Test:** `formal/async_fifo.sby`

### [BUG-002] Asynchronous FIFO Data Integrity Lifecycle Violation in Formal Tracking
- **Date Discovered:** 2026-11-23
- **Target Component:** `formal/async_fifo.sby` & `rtl/common/async_fifo.v`
- **Detection Method:** Formal Proof (SymbiYosys BMC step 18)
- **Symptom:** Assertion `mem[f_magic_addr] == f_magic_val` failed at step 18 in BMC.
- **Root Cause:** Magic value formal tracker used `ADDR_WIDTH` index rather than full `PTR_WIDTH` pointer and lacked completion lifecycle tracking (`f_magic_read`), so subsequent wraparound writes to the same physical RAM cell after the tracked value was already consumed triggered false assertion failures.
- **Fix Applied:** Tracked full `PTR_WIDTH` binary pointer `f_magic_ptr <= wbin` and verified data matching only when read pointer `rbin == f_magic_ptr`, asserting `f_magic_read <= 1'b1` upon read consumption.
- **Regression Test:** `formal/async_fifo.sby`

### [BUG-003] SBY Unconstrained Intermediate Reset Glitch in Multi-clock Domain
- **Date Discovered:** 2026-11-23
- **Target Component:** `formal/async_fifo.sby` & `rtl/common/async_fifo.v`
- **Detection Method:** Formal Proof (SymbiYosys BMC step 14)
- **Symptom:** SMT solver pulsed `wrst_n` low while `rrst_n` stayed high mid-run, resetting write pointer to 0 and desynchronizing CDC pointer tracking.
- **Root Cause:** `always @(posedge wclk)` only assumed reset state at clock edges. In `async2sync`, asynchronous reset inputs were unconstrained between clock edges, allowing solver to inject single-domain reset pulses.
- **Fix Applied:** Added combinational invariant `always @(*) begin if (!f_w_past_valid) assume (!wrst_n); else assume (wrst_n); if (!f_r_past_valid) assume (!rrst_n); else assume (rrst_n); end`.
- **Regression Test:** `formal/async_fifo.sby`

### [BUG-004] AXI-Lite Default Slave VPI Teardown Segfault in Icarus
- **Date Discovered:** 2026-11-23
- **Target Component:** `tb/unit/test_axil_default_slave.py`
- **Detection Method:** Unit Test execution on Icarus Verilog (`vvp`)
- **Symptom:** `Segmentation fault (core dumped)` in `vvp` immediately after all assertions passed during test exit.
- **Root Cause:** Cocotb test exited immediately following a response handshake without allowing the VPI callback queue to settle before `vpi_control(vpiFinish)`.
- **Fix Applied:** Added a settled clock edge delay before test completion in `tb/unit/test_axil_default_slave.py`.
- **Regression Test:** `tb/unit/test_axil_default_slave.py`

### [BUG-005] APB Bridge Premature Access Completion on Zero Wait States
- **Date Discovered:** 2026-11-23
- **Target Component:** `rtl/apb/axil2apb_bridge.v`
- **Detection Method:** Directed Test (`BR-01`) & Waveform Analysis
- **Symptom:** APB transfer completed in `ST_ACCESS` before `m_apb_penable` was ever observed high on the bus.
- **Root Cause:** In `ST_ACCESS`, `m_apb_penable <= 1'b1; if (m_apb_pready)` was evaluated in the very first clock cycle of `ST_ACCESS` when `m_apb_penable` was still 0 from `ST_SETUP`. Because `m_apb_pready` was already 1 (zero wait states), the bridge immediately transitioned to response state without ever presenting `PENABLE=1` to the slave.
- **Fix Applied:** Qualified completion condition with `if (m_apb_penable && m_apb_pready)`.
- **Regression Test:** `tb/block/test_axil2apb_bridge.py` (`test_br01_single_rw_zero_wait`)

### [BUG-006] Protocol Checker False Handshake Stability Assertion Failure
- **Date Discovered:** 2026-11-23
- **Target Component:** `tb/models/axil_monitor.py`
- **Detection Method:** Block Test execution (`test_xb01_single_rw_each_master_to_each_slave`)
- **Symptom:** `AssertionError: AXI-Lite stability violation` fired on valid handshake completion cycle.
- **Root Cause:** Monitor checked `if last_valid and not cur_ready`, asserting that `valid` must remain high. On the cycle where handshake completed, `cur_ready` was 0 (slave deasserted ready for the next transaction), but `last_ready` was 1 (handshake completed in previous cycle).
- **Fix Applied:** Changed condition to `if self.last_valid and not self.last_ready:` so stability is only checked when previous cycle handshake was unacknowledged.
- **Regression Test:** `tb/block/test_axil_xbar.py` (`test_xb01_single_rw_each_master_to_each_slave`)

### [BUG-007] Cocotb Scheduler Incompatibility with asyncio.gather
- **Date Discovered:** 2026-11-23
- **Target Component:** `tb/block/test_axil_xbar.py`
- **Detection Method:** Block Test execution (`test_xb07_arbitration_fairness`)
- **Symptom:** `TypeError: Coroutine yielded <_GatheringFuture pending>, which the scheduler can't handle`.
- **Root Cause:** `asyncio.gather` returns an asyncio future incompatible with cocotb's native coroutine scheduler.
- **Fix Applied:** Started parallel background tasks with `cocotb.start_soon(tb.m0.write(...))` and awaited each task directly (`await t0; await t1`).
- **Regression Test:** `tb/block/test_axil_xbar.py` (`test_xb07_arbitration_fairness`)

### [BUG-008] Master Driver Staggered W-First Transaction Hang on Multi-Slave Crossbar
- **Date Discovered:** 2026-11-23
- **Target Component:** `tb/models/axil_driver.py`
- **Detection Method:** Block Test execution (`test_xb08_write_orderings`)
- **Symptom:** `TimeoutError: AXI-Lite write handshake timeout on addr 0x50000064` when test executed `order="w_first"`.
- **Root Cause:** In multi-slave crossbar without store-and-forward write data FIFOs, write data `W` is routed to the target slave decoded from `AWADDR`. Master driver held `AWVALID=0` waiting for `WREADY=1` before asserting `AWVALID=1`. Because crossbar cannot route W to the addressed slave until AW arrives, neither side could proceed (mutual wait).
- **Fix Applied:** In `tb/models/axil_driver.py`, for `order="w_first"`, master asserts `WVALID=1`, waits 2 clock cycles stagger, and then asserts `AWVALID=1` without waiting for `WREADY`.
- **Regression Test:** `tb/block/test_axil_xbar.py` (`test_xb08_write_orderings`)

### [BUG-009] UART Transmitter FSM Multi-Cycle Pop Race with Synchronous FIFO
- **Date Discovered:** 2026-11-23
- **Target Component:** `rtl/apb/apb_uart.v`
- **Detection Method:** Block Test execution (`test_ua03_bauddiv_sweep`, `test_ua01_loopback_bytes`)
- **Symptom:** Start bit length measured 145 cycles instead of 16; transmitted data bits were all zeros.
- **Root Cause:** In `TX_ST_IDLE`, `tx_pop_req <= 1'b1` was registered with non-blocking assignment (`<=`), delaying the FIFO pop pulse to `TX_ST_LOAD`. In `TX_ST_LOAD`, `tx_shifter <= tx_fifo_rdata` executed at the exact same clock edge where the FIFO registered its new output, causing `tx_shifter` to sample the stale (zero) pre-pop value.
- **Fix Applied:** Changed `tx_fifo_pop` to a combinational assignment `assign tx_fifo_pop = (tx_state == TX_ST_IDLE) && reg_ctrl[0] && !tx_fifo_empty;`. This pops `sync_fifo` synchronously during `TX_ST_IDLE` so that by the time `TX_ST_LOAD` executes, `tx_fifo_rdata` is stable and valid.
- **Regression Test:** `tb/block/test_apb_uart.py` (`test_ua01_loopback_bytes`, `test_ua03_bauddiv_sweep`)

### [BUG-010] UART Receiver Premature State Transition on Mid-Start Bit Sample
- **Date Discovered:** 2026-11-23
- **Target Component:** `rtl/apb/apb_uart.v`
- **Detection Method:** Block Test execution (`test_ua01_loopback_bytes`)
- **Symptom:** Loopback data timeout; all received bytes dropped with framing error (`reg_frame_err`).
- **Root Cause:** In `RX_ST_START`, when `rx_tick_cnt == 7` (mid-point of start bit), the FSM immediately reset `rx_tick_cnt <= 0` and transitioned to `RX_ST_DATA` after only 8 oversampling ticks instead of waiting for the full 16 ticks of the start bit. This shifted all subsequent data bit sampling by 8 ticks, causing data bit 7 to be sampled during stop bit, triggering false framing errors and dropping frames.
- **Fix Applied:** In `RX_ST_START`, tick 7 only verifies that the line is still 0 (aborting on glitch); the transition to `RX_ST_DATA` is gated by `rx_tick_cnt == 15` so that the full 16-tick start bit duration elapses before data bits are sampled.
- **Regression Test:** `tb/block/test_apb_uart.py` (`test_ua01_loopback_bytes`, `test_ua02_fifo_full_and_overflow_flags`)

### [BUG-011] UART Receiver Read Data Mux Zero Mask on FIFO Empty
- **Date Discovered:** 2026-11-23
- **Target Component:** `rtl/apb/apb_uart.v`
- **Detection Method:** Block Test execution (`test_ua01_loopback_bytes`)
- **Symptom:** Reading `RXDATA` register (0x04) returned `0x00` even though FIFO contained a valid received byte.
- **Root Cause:** `assign prdata` used `rx_fifo_empty ? 8'd0 : rx_fifo_rdata`. Because `rx_fifo_pop` occurs during the APB SETUP phase, by the time the ACCESS phase was entered and `prdata` was sampled, a single-byte FIFO was already empty, forcing the mux to return 0.
- **Fix Applied:** Added registered indicator `rx_had_data` set in the SETUP phase if `!rx_fifo_empty`, and used `rx_had_data ? rx_fifo_rdata : 8'd0` in the read data mux.
- **Regression Test:** `tb/block/test_apb_uart.py` (`test_ua01_loopback_bytes`)

### [BUG-012] Crossbar Multi-Master Target Locking on Transfer Initiation
- **Date Discovered:** 2026-11-24
- **Target Component:** `rtl/axil/axil_xbar.v`
- **Detection Method:** Directed Test (`TestContentionHandshake`) & pyuvm Stress Test (`test_stress`)
- **Symptom:** Deadlock and timeout under concurrent multi-master contention or staggered writes (`order="w_first"`), where a granted master was preempted before both write channels completed.
- **Root Cause:** Target locking in `axil_xbar` was initially conditioned on `aw_hs` or `ar_hs`. When an access was granted but one of the channels was delayed across cycles (or during staggered writes), the other master could win arbitration and reassign `active_wr_owner`, stranding the first master.
- **Fix Applied:** In `rtl/axil/axil_xbar.v`, asserted `wr_locked[gt] <= 1'b1; wr_owner[gt] <= active_wr_owner[gt];` immediately upon `wr_active[gt] && !wr_locked[gt]`, and similarly for `rd_active[gt] && !rd_locked[gt]`.
- **Regression Test:** `tb/pyuvm/tests/test_directed.py` (`TestContentionHandshake`), `tb/pyuvm/tests/test_stress.py`

### [BUG-013] CDC Slow Registers Asynchronous FIFO Pop Off-by-One Pipeline Skew
- **Date Discovered:** 2026-11-24
- **Target Component:** `rtl/cdc/slow_regs.v`
- **Detection Method:** pyuvm Scoreboard (`FabricScoreboard`) in `test_stress`
- **Symptom:** Scoreboard reported read/write mismatches on CDC slow registers (e.g., reading `0x70000000` returned register `0x0C`'s value `0x00000001` instead of `0x510e0001`).
- **Root Cause:** Request fields were latched on `if (req_pop)`. Because `req_pop` was scheduled non-blocking in `ST_IDLE`, it was active during `ST_RESP`, causing `req_is_write_q` and `req_addr_q` to latch at the exit of `ST_RESP`. During `ST_RESP`, the FSM evaluated the request using the previous transaction's address and write flag.
- **Fix Applied:** Changed request latch condition to `if (state == ST_IDLE && !req_empty && !resp_full)` so fields are latched directly into `req_is_write_q`, `req_addr_q`, `req_wdata_q`, `req_wstrb_q` at the start of `ST_RESP`.
- **Regression Test:** `tb/pyuvm/tests/test_stress.py` (5-seed 50,000 transaction regression)

### [BUG-014] Icarus Verilog Signal Declaration Order Elaboration Error in slow_regs.v
- **Date Discovered:** 2026-11-24
- **Target Component:** `rtl/cdc/slow_regs.v`
- **Detection Method:** `iverilog` elaboration in `scripts/run_phase4_gate.sh`
- **Symptom:** `error: Unable to bind wire/reg/memory req_addr_q['sd1:'sd0]... A symbol with that name was declared here. Check for declaration after use.`
- **Root Cause:** `wire _unused` referenced `req_addr_q` before its declaration on line 48. Verilator accepted this, but Icarus Verilog strictly enforces declaration before use.
- **Fix Applied:** Moved `wire _unused` to follow the declaration of `req_addr_q`.
- **Regression Test:** `scripts/run_phase4_gate.sh` (`test_directed` on Icarus)

### [BUG-015] Cocotb 2.1 Unresolved LogicArray Integer Conversion Exception
- **Date Discovered:** 2026-11-24
- **Target Component:** `tb/models/axil_driver.py`
- **Detection Method:** pyuvm test execution with cocotb 2.1 (`test_stress`)
- **Symptom:** `ValueError: Can't convert LogicArray to int: it contains non-0/1 values ('x')`.
- **Root Cause:** In cocotb 2.1+, calling `int(signal.value)` throws `ValueError` if any bit in the bus is unresolved (`x`/`z`), such as unmapped or uninitialized bus lines.
- **Fix Applied:** Implemented `safe_int()` helper that verifies `val.is_resolvable` and substitutes unresolved bits with `'0'`.
- **Regression Test:** `tb/pyuvm/tests/test_stress.py`

### [BUG-016] APB Timer Countdown Formal Assertion False Failure on APB Write Collision
- **Date Discovered:** 2026-11-24
- **Target Component:** `formal/apb_timer.sby`, `rtl/apb/apb_timer.v`
- **Detection Method:** SymbiYosys k-induction formal check (`sby -f formal/apb_timer.sby`)
- **Symptom:** `assert (reg_ctrl[0] == 1'b0)` failed at induction step 4.
- **Root Cause:** In `apb_timer.v`, APB register writes override autonomous timer counting and reload logic. The assertion checked that `reg_ctrl[0]` was cleared on timeout under `!reg_ctrl[1]`, but did not check if an APB write occurred in the preceding cycle writing `1` to `CTRL`.
- **Fix Applied:** Qualified autonomous timer assertions with `!$past(apb_write && (paddr[3:2] == 2'b00))`.
- **Regression Test:** `make formal` (`apb_timer.sby`)

### [BUG-017] AXI-Lite RAM Slave Response Latency Tracking Skew under Backpressure
- **Date Discovered:** 2026-11-24
- **Target Component:** `formal/axil_ram.sby`, `rtl/axil/axil_ram.v`
- **Detection Method:** SymbiYosys BMC formal check (`sby -f formal/axil_ram.sby`)
- **Symptom:** `assert (s_axil_bresp == ($past(write_in_bounds) ? RESP_OKAY : RESP_SLVERR))` failed at step 5.
- **Root Cause:** When `s_axil_bready` was held low, `bvalid` remained high while `awready`/`wready` were briefly high, allowing a second write address to arrive. The property was asserting the new write's response while `bresp` still held the previous write's response waiting for `bready`.
- **Fix Applied:** Verified that `bresp` matches bounds on the cycle following `write_commit = ((aw_hs || aw_done) && (w_hs || w_done) && (!bvalid || bready))`, and asserted `$stable(s_axil_bresp)` while waiting for `bready`.
- **Regression Test:** `make formal` (`axil_ram.sby`)

### [BUG-018] Cocotb COVERAGE Variable Collision with pyuvm Functional Coverage Directory
- **Date Discovered:** 2026-11-24
- **Target Component:** `tb/pyuvm/func_cov/`, `tb/pyuvm/Makefile.single`
- **Detection Method:** Make regression with `COVERAGE=1`
- **Symptom:** `AttributeError: module 'coverage' has no attribute 'coverage'`.
- **Root Cause:** Cocotb uses `COVERAGE=1` to invoke Python code coverage (`import coverage`). Having a directory named `tb/pyuvm/coverage` on `PYTHONPATH` caused Python to import the local directory instead of the standard Python coverage package.
- **Fix Applied:** Renamed `tb/pyuvm/coverage` to `tb/pyuvm/func_cov`, and used `VERILATOR_COVERAGE=1` in the Makefiles to distinguish HDL code coverage from Python code coverage.
- **Regression Test:** `make cov-report`

### [BUG-019] Yosys SymbiYosys Downward Hierarchical Reference Width Detection Rejection
- **Date Discovered:** 2026-11-24
- **Target Component:** `formal/` sby suites
- **Detection Method:** `sby` elaboration
- **Symptom:** `ERROR: Failed to resolve identifier \dut.reg_load for width detection`.
- **Root Cause:** Yosys AST parser does not support downward cross-module hierarchical references for port/wire width detection in separate wrapper modules.
- **Fix Applied:** Embedded formal properties directly within each RTL module under `` `ifdef FORMAL ``, keeping formal verification clean, self-contained, and portable.
- **Regression Test:** `make formal` (all 8 suites)

### [BUG-020] APB Bridge Test Stimulus Self-Comparison Masking Write Data Bit-Corruption
- **Date Discovered:** 2026-11-24
- **Target Component:** `tb/block/test_axil2apb_bridge.py`
- **Detection Method:** Mutation Testing (`mutation/results/survivors/axil2apb_bridge_mut_0.v`)
- **Symptom:** Mutant with `reg_wdata[29]` stuck at 0 survived test execution without detection.
- **Root Cause:** The testbench read back from the APB slave memory and compared read data against `apb_slave.memory.get(offset)`. Because the APB slave memory captured the already-corrupted write data presented on `pwdata`, the assertion `rdata == apb_slave.memory` evaluated true, comparing the corrupted output to the corrupted internal state rather than the golden driven input stimulus. Furthermore, the test data vector `0xDEADBEEF` had bit 29 equal to 0, masking the fault.
- **Fix Applied:** In `tb/block/test_axil2apb_bridge.py`, added direct verification that `apb_slave.memory[offset] == pdata` against the golden input stimulus, and added complementary test patterns (`0xFFFFFFFF`, `0xAAAAAAAA`, `0x55555555`, `0x21524110`) where bit 29 is 1.
- **Regression Test:** `make mutation-sample` (`axil2apb_bridge`)

### [BUG-021] AXI-Lite RAM Directed Test Address Locality Masking Memory Word Faults
- **Date Discovered:** 2026-11-24
- **Target Component:** `tb/unit/test_axil_ram.py`
- **Detection Method:** Mutation Testing (`mutation/results/survivors/axil_ram_mut_1.v`)
- **Symptom:** Mutant with `mem[206]` bit 15 stuck at 1 survived test execution without detection.
- **Root Cause:** `test_axil_ram.py` only exercised two word addresses (word 4: `0x50000010` and word 8: `0x50000020`), leaving the remaining 254 words in the 256-word scratchpad RAM completely untouched during unit test verification.
- **Fix Applied:** In `tb/unit/test_axil_ram.py`, added a memory sweep across the full depth (words 0, 1, 16, 64, 128, 206, 255) writing unique pseudorandom patterns, followed by an all-zero write/read pass to detect any stuck-at-1 bits across the memory array.
- **Regression Test:** `make mutation-sample` (`axil_ram`)

### [BUG-022] AXI Crossbar WREADY Gating on Combinational AWADDR Decoder Causing Write Deadlock
- **Date Discovered:** 2026-11-24
- **Target Component:** `rtl/axil/axil_xbar.v`
- **Detection Method:** SymbiYosys Formal BMC verification (`formal/axil_xbar.sby`)
- **Symptom:** Crossbar BMC failed at step 3 due to write channel deadlock. After master AW handshake completed, master deasserted `awvalid` and changed `awaddr` before W data arrived. Subsequently `s_axil_wready` was held low (0) even though `wvalid` was high and the targeted slave had `wready` high (`tgt_wready=1`).
- **Root Cause:** In `rtl/axil/axil_xbar.v`, `s_axil_wready` for both master 0 and master 1 was generated using the combinationally decoded address target `m_aw_tgt[m][gt]`. If the master changed `s_axil_awaddr` after the AW handshake while the target slave was already locked (`wr_locked[gt] && wr_owner[gt] == m`), `m_aw_tgt[m][gt]` became 0, gating `s_axil_wready` to 0. This caused a permanent write channel stall while `tgt_wvalid[gt]` was asserted to the slave.
- **Fix Applied:** In `rtl/axil/axil_xbar.v`, updated the `m_wready_grant` logic for all masters to check `(wr_locked[gt] ? (wr_owner[gt] == m) : (active_wr_owner[gt] == m && m_aw_tgt[m][gt]))`. When a write channel is locked to a slave, WREADY gating depends on the recorded owner, not the transient input `awaddr`.
- **Regression Test:** `formal/axil_xbar.sby` (BMC depth 20), `tb/pyuvm/tests/test_xb09_backpressure_burst.py`

### [BUG-023] AXI-Lite CSR Full Byte-Offset Decode Violating AXI4-Lite Rule 6 (`[1:0]` Ignored)
- **Date Discovered:** 2026-11-25
- **Target Component:** `rtl/axil/axil_csr.v` (and aligned `tb/models/reg_model.py`, `tb/models/addr_map.py`, `tb/models/ram_model.py`, `tb/models/peripheral_model.py`)
- **Detection Method:** Audit Finding `AXIL-R6` / `PROBE-02` / `RTL-axil_csr`
- **Symptom:** Accessing unaligned byte offsets inside mapped CSR addresses (e.g., `0x6000_0001` instead of `0x6000_0000`) returned `SLVERR` (`2'b10`) and `0` instead of returning `OKAY` (`2'b00`) and word `ID = 0xA3BA_0001`.
- **Root Cause:** `rtl/axil/axil_csr.v` decoded the full 8-bit offset `s_axil_awaddr[7:0]` / `s_axil_araddr[7:0]` against word-aligned constants (`8'h00`, `8'h04`, ..., `8'h20`), treating `[1:0] != 2'b00` as unmapped addresses in violation of `docs/spec.md` Section 6 Rule 6.
- **Fix Applied:** Changed `axil_csr.v` address decode to 6-bit word index `s_axil_awaddr[7:2]` / `s_axil_araddr[7:2]` (`6'h00..6'h08`), ignoring `[1:0]`, added Rule 6 assertions in `axil_csr.v` formal block, and aligned all Python reference models (`tb/models/`).
- **Regression Test:** `test_cs01_reset_values`, `test_cs02_access_types_w1c`, `test_xb15_unaligned_address`

### [BUG-024] AXI-Lite CDC Bridge Hang and FIFO Pointer Desynchronization on Independent Domain Reset
- **Date Discovered:** 2026-11-25
- **Target Component:** `rtl/cdc/axil_cdc_bridge.v`
- **Detection Method:** Remediation R2 analysis of `CD-03` (`audit_input/AUDIT_REPORT.md`)
- **Symptom:** Asserting `rst_slow_n` independently while an AXI4-Lite transaction is in flight on `clk_sys` (`ST_WAIT_RESP`) caused `slow_regs` and `u_resp_fifo` to reset while `clk_sys` FSM waited forever on `resp_empty`, permanently hanging the AXI master. Similarly, independent `rst_sys_n` or `rst_slow_n` resets desynchronized `async_fifo` read/write pointers across domains.
- **Root Cause:** `u_req_fifo`, `u_resp_fifo`, and `u_slow_regs` used uncoordinated domain resets (`rst_sys_n`, `rst_slow_n`), and `axil_cdc_bridge` had no reset notification into the `clk_sys` FSM to abort an in-flight `ST_WAIT_RESP` wait.
- **Fix Applied:** Added cross-domain reset synchronizers (`both_rst_n = rst_sys_n & rst_slow_n` -> `fifo_rst_sys_n`, `fifo_rst_slow_n`) for both FIFOs and `u_slow_regs`, gated `ST_IDLE` acceptance on `fifo_rst_sys_n`, and added `slow_rst_aborted` handling in `axil_cdc_bridge.v` so in-flight AXI transactions complete cleanly with `SLVERR` (`2'b10`) without hanging.
- **Regression Test:** `test_cd03_reset_recovery`




