# Known Formal Verification & Tooling Limitations (`docs/limitations.md`)

This document records the scope boundaries, bounded formal verification limits, and known tool warnings that remain open in the AMBA-Fabric deliverable.

---

## 1. Formal Verification Scope & Bounded Suites (`Section 11`)

Across the **10 SymbiYosys formal suites** in `formal/`, **5 suites execute unbounded proofs** (`3` `k-induction (prove)` via `smtbmc boolector`, `1` unbounded `PDR (prove)` via `abc pdr` on `axil2apb_bridge`, and `1` hybrid `prv+bmc` on `axil_csr`), while **5 suites remain bounded model checking (`BMC depth N`)**:

| Suite | Mode / Depth | Technical Reason for Remaining Bounded |
|---|---|---|
| `axil_cdc_bridge` | `BMC depth 30` (`multiclock on`) | Dual asynchronous clock domains (`clk_sys` and `clk_slow`) verified via SymbiYosys `async2sync` transformation. Multiclock `async2sync` requires bounded unrolling across asynchronous phase relationships. |
| `async_fifo` | `BMC depth 25` (`multiclock on`) | Independent write/read clocks (`wclk`, `rclk`) with Cummings Gray-pointer synchronizers (`sync_w2r`, `sync_r2w`) modeled via `async2sync`; pointer reachability and full/empty edge cases are verified to depth 25. |
| `axil_xbar` | `BMC depth 20` | 2-master × 5-target crossbar (`4` external slaves + internal `u_default_slave`) with 32-bit address/data channels, target locking, and 5-bit bounded-liveness timers (`f_m_wr_timer`, `f_m_rd_timer`). Unbounded `abc pdr` timed out on individual liveness/stability outputs across > 5 min (`PRV=135` with repeated anytime timeouts), and `smtbmc` k-induction fails at induction step 0 because Yosys cannot resolve downward hierarchical references (`dut.aw_done`, `dut.w_done`, `dut.ar_done`) to invariant-link internal crossbar target state without modifying frozen RTL. Depth 20 exceeds the worst-case contention/liveness bound (`< 18` cycles) under fair responder assumptions. |
| `axil_ram` | `BMC depth 20` | Parameterized memory array (`RAM_DEPTH=16` in formal) creates an inductive state space proportional to the full `mem[]` contents unless universally quantified memory invariants are added. Depth 20 exhaustively covers single-cycle handshake stability, all 4 byte-enable (`WSTRB`) lanes, and out-of-bounds `SLVERR`. |
| `apb_uart` | `BMC depth 25` | Programmable 16-bit baud divider (`BAUDDIV`, 16× oversampling), dual 8-entry TX/RX FIFOs, and bit-serial TX/RX FSMs produce multi-hundred-cycle full-frame transitions whose unrolled bit-level state exceeds practical k-induction bounds; depth 25 covers register interface, APB handshake/error handling, FIFO push/pop pointers, and baud-tick initiation. Serial frame integrity across full byte transmissions is covered by `UA-01`..`UA-05` simulation tests. |

Additionally, **`axil_csr`** runs hybrid **`prv+bmc`** (`k-induction (prove)` with `CHECK_CAUSALITY=0` plus `BMC depth 20` with `CHECK_CAUSALITY=1`, see [`docs/decisions.md`](decisions.md) `DEC-006`) because `axil_props.v` tracks channel handshakes using 8-bit wrapping counters that wrap in arbitrary k-induction start states.

---

## 2. Simulator & Synthesis Tool Notes

### 2.1 Icarus Verilog `@*` Array-Sensitivity Warnings in `rtl/axil/axil_xbar.v`

When compiling `rtl/axil/axil_xbar.v` with `iverilog -g2012 -Wall`, Icarus emits non-fatal sensitivity warnings on the `always @(*)` combinational muxing blocks:
- Lines `203`–`213` (`gen_slaves`): `warning: @* is sensitive to all 5 words in array 'tgt_awaddr'` / `tgt_awprot` / `tgt_awvalid` / `tgt_wdata` / `tgt_wstrb` / `tgt_wvalid` / `tgt_bready` / `tgt_araddr` / `tgt_arprot` / `tgt_arvalid` / `tgt_rready`.
- Lines `370`–`377` and `494`–`513` (master write/read feedback): `@* is sensitive to all 5 words in array` (`wr_active`, `active_wr_owner`, `tgt_awready`, `tgt_wready`, `tgt_bvalid`, `tgt_bresp`, `rd_active`, `active_rd_owner`, `tgt_arready`, `tgt_rvalid`, `tgt_rdata`, `tgt_rresp`, `wr_owner`, `rd_owner`) and `all 2 words in array` (`m_aw_tgt`, `m_ar_tgt`).

**Impact & Disposition:**
- `rtl/axil/axil_xbar.v` is **intentionally left untouched** so frozen mutant line/cell hashes (`mutation/mutant_list_240.json`), `17/17` sanity mutants, SKY130 synthesis, and coverage databases remain valid.
- The warnings are benign IEEE 1364-2001/1800 event-scheduling diagnostics from indexing unpacked arrays (`wire [...] arr [0:NUM_TARGETS-1]`) inside `always @(*)`. Verilator (`make lint`: `verilator --lint-only -Wall`) compiles cleanly with zero warnings, and Yosys synthesis elaborates the combinational multiplexers identically.

### 2.2 Pre-Layout Reset Fanout in OpenSTA

As recorded in [`docs/decisions.md`](decisions.md) (`DEC-011`) and [`docs/results.md`](results.md), pre-layout Yosys synthesis leaves synchronized reset net `rst_sys_n` unbuffered (`fanout=958`, `cap=3.46 pF`, `slew=29.27 ns`), causing `100 MHz` `clk_sys` reset recovery to report `VIOLATED` (`WNS = -18.60 ns` / `34.97 MHz` full netlist vs `62.89 MHz` datapath+I/O reference with `rst_sync` Q isolated in STA). Physical reset-tree buffering / CTS (`S-03` OpenLane) is out of scope.
