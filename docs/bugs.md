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
