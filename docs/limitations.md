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

*This section is populated during remediation tasks (simulator warnings and static timing constraints).*
