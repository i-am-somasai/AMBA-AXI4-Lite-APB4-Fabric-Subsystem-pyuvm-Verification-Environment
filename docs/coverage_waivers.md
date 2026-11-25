# AMBA-Fabric Functional Coverage Waivers (docs/coverage_waivers.md)

This document records all functional coverage waivers for the AMBA-Fabric verification environment.
Per project rules, every waiver must have a detailed architectural justification explaining why the bin is provably unreachable under valid system operation. No bin may be hit via synthetic sampling.

---

## Summary of Defined Covergroups & Waiver Status

| Covergroup | Description | Total Defined Bins | Waived / Ignored Bins | Reachable Target Bins | Justification Reference |
|---|---|---|---|---|---|
| `cg_txn` | Master × Target × Op × Resp | 60 | 24 (illegal DECERR/OKAY combinations) | 36 | Protocol legality (Section 5.3 & 6) |
| `cg_wstrb` | WSTRB patterns × Target | 64 | 0 | 64 | Fully reachable |
| `cg_order` | Write ordering × Target | 12 | 0 | 12 | Fully reachable |
| `cg_backpressure` | Channel × Delay bucket | 20 | 0 | 20 | Fully reachable |
| `cg_contention` | Contention type × Op combo | 9 | 3 (`one_idle` × op-pair combinations) | 6 | Definitional contradiction (`DEC-009`) |
| `cg_apb` | Wait-state × Error × Op & Strobe classes | 24 | 3 (`byte`/`halfword`/`word` × `RD`) | 21 | APB4 spec Sec 2.1 (`PSTRB=0` on reads, `DEC-010`) |
| `cg_cdc` | Clock ratio × Occupancy × Op | 18 | 6 (FIFO full occupancy) | 12 | Architectural constraint (single-outstanding bridge) |
| `cg_uart` | Baud × FIFO state & Error types | 12 | 0 | 12 | Fully reachable |
| `cg_reset` | Reset assertion during in-flight phases | 5 | 0 | 5 | Fully reachable |

---

## Detailed Waiver Justifications

### 1. `cg_cdc.cross`: FIFO Occupancy `full` Bins (6 Bins)

- **Waived Bins:**
  1. `("slow<sys", "full", "RD")`
  2. `("slow<sys", "full", "WR")`
  3. `("approx_equal", "full", "RD")`
  4. `("approx_equal", "full", "WR")`
  5. `("slow>sys", "full", "RD")`
  6. `("slow>sys", "full", "WR")`
- **Exclusion Method:** Explicitly excluded from `cg_cdc.cross` via `ign_bins` in `tb/pyuvm/func_cov/fabric_cov.py`.
- **Architectural Justification:**
  - In `rtl/cdc/axil_cdc_bridge.v`, the AXI4-Lite slave FSM is strictly **single-outstanding**.
  - Upon receiving an AXI address handshake (AW/W or AR), the FSM transitions from `ST_IDLE` to `ST_PUSH_REQ`, asserting `req_push` for exactly one cycle to enqueue a single transaction into `u_req_fifo` (`DEPTH=4`).
  - The FSM then immediately enters `ST_WAIT_RESP` and deasserts all `READY` signals (`s_axil_awready`, `s_axil_wready`, `s_axil_arready`). It remains in `ST_WAIT_RESP` until the target peripheral in the `clk_slow` domain processes the request, enqueues the response into `u_rsp_fifo`, and the bridge consumes it via `resp_pop`.
  - Because no subsequent request can be accepted while a request is in flight, the maximum concurrent entries in `u_req_fifo` and `u_rsp_fifo` is exactly **1**.
  - With `DEPTH=4`, the async FIFO occupancy under normal bridge operation alternates strictly between `empty` (0 entries) and `partial` (1 entry). Occupancy `full` (4 entries) is physically impossible to reach in this architecture.
- **Alternative Verification Evidence:**
  - The asynchronous FIFO full boundary condition (`wfull == 1`), push-when-full drop, and Gray-pointer synchronization under full conditions are verified via bounded model checking (multiclock BMC depth 25) in `formal/async_fifo.sby` and unit-tested in `tb/unit/test_async_fifo.py`.

---

### 2. `cg_txn.cross`: Illegal Transaction Combinations (24 Bins)

- **Waived Bins:**
  - `(master, "UNMAPPED", op, "OKAY")` (4 bins across M0/M1 and RD/WR)
  - `(master, "UNMAPPED", op, "SLVERR")` (4 bins across M0/M1 and RD/WR)
  - `(master, target, op, "DECERR")` for mapped targets `RAM`, `CSR`, `CDC`, `APB` (16 bins across M0/M1, 4 targets, and RD/WR)
- **Exclusion Method:** Excluded via `ign_bins` in `tb/pyuvm/func_cov/fabric_cov.py`.
- **Protocol Justification:**
  - Per AMBA AXI4-Lite specification and `docs/spec.md` Section 5.3:
    - The crossbar default error slave exclusively decodes unmapped addresses and responds with `DECERR` (`2'b11`). It is incapable of returning `OKAY` or `SLVERR`.
    - Mapped slaves (`axil_ram`, `axil_csr`, `axil2apb_bridge`, `axil_cdc_bridge`) only respond with `OKAY` (`2'b00`) on valid access or `SLVERR` (`2'b10`) on out-of-bounds or peripheral errors. They never return `DECERR`.
  - These 24 combinations are illegal protocol states and are excluded from functional coverage goals.

---

### 3. `cg_contention.cross`: `one_idle` with Two-Master Operation Pairs (3 Bins, `DEC-009`)

- **Waived Bins:**
  - `("one_idle", "R/R")`, `("one_idle", "R/W")`, `("one_idle", "W/W")`
- **Exclusion Method:** Excluded via `ign_bins` on `cg_contention.cross` in `tb/pyuvm/func_cov/fabric_cov.py` (while `"one_idle"` remains active in `cg_contention.type`).
- **Justification:**
  - `"one_idle"` denotes cycles where only a single AXI4-Lite master has an active transaction, so pairing it with a simultaneous two-master operation pair (`R/R`, `R/W`, `W/W`) is contradictory by definition.

---

### 4. `cg_apb.strb_cross`: Non-Zero Strobe Classes on APB Reads (3 Bins, `DEC-010`)

- **Waived Bins:**
  - `("byte", "RD")`, `("halfword", "RD")`, `("word", "RD")`
- **Exclusion Method:** Excluded via `ign_bins` on `cg_apb.strb_cross` in `tb/pyuvm/func_cov/fabric_cov.py`.
- **Protocol Justification:**
  - Per AMBA APB4 Specification Section 2.1 and `rtl/apb/axil2apb_bridge.v`, read transfers (`PWRITE == 1'b0`) must drive `PSTRB == 4'b0000` (mapped to `"sparse"` alongside non-contiguous write strobes). Byte, halfword, and word strobes on a read transfer violate APB4 protocol rules.
