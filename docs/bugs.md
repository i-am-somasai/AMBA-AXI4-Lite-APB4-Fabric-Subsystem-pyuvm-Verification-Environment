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

