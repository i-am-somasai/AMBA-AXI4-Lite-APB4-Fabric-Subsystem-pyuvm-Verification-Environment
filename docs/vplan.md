# AMBA-Fabric Verification Plan (vplan)

**Version:** 1.0  
**Status:** Baseline (Phase 0)  
**Author:** Orchestrator / DV Team  
**Scope:** AXI4-Lite 2x4 Interconnect, APB4 Subsystem, Peripherals (UART, Timer, GPIO), CDC Bridge, and pyuvm Environment.

---

## 1. Verification Strategy & Hierarchy

The design is verified at three distinct levels to ensure fast debug turnaround and hierarchical confidence:

| Level | Target Scope | Environment / Harness | Key Focus |
|---|---|---|---|
| **L0 Unit** | `rst_sync`, `sync_fifo`, `async_fifo`, `rr_arbiter`, `axil_decoder`, `axil_default_slave`, `axil_ram`, `axil_csr` | Directed cocotb + SBY Formal | Basic functionality, boundary conditions, formal safety/liveness |
| **L1 Block** | `axil_xbar`, `axil2apb_bridge`, `axil_cdc_bridge` | pyuvm UVCs (Master Agent + Slave Responders) + SBY Formal | Protocol compliance, arbitration fairness, wait-state injection, CDC ratios |
| **L2 Top Subsystem** | `amba_fabric_top` | Full `FabricEnv` with 2 Master UVCs, peripheral monitors, Scoreboards | Multi-master concurrency, end-to-end register access, interrupt aggregation, stress regressions |

---

## 2. Feature Traceability Matrix

| Feature ID | Description | Verification Level | Test IDs | Coverage Goals | Formal / SVA Checkers |
|---|---|---|---|---|---|
| **F-01** | AXI4-Lite 2Mx4S Crossbar | L1, L2 | XB-01, XB-05, XB-06, XB-13 | `cg_txn`, `cg_contention` | `axil_xbar.sby`, `axil_props.v` |
| **F-02** | Per-slave RR Arbiter + Lock | L0, L1, L2 | XB-05, XB-07 | `cg_contention` | `rr_arbiter.sby`, `axil_props.v` |
| **F-03** | Default Slave (DECERR) | L0, L1, L2 | XB-04 | `cg_txn` | `axil_props.v` |
| **F-04** | AXI4-Lite Scratch RAM | L0, L2 | XB-01, XB-02, XB-03, XB-11 | `cg_wstrb`, `cg_txn` | `axil_props.v` |
| **F-05** | System CSR Block | L0, L2 | CS-01, CS-02, CS-03 | `cg_txn`, `cg_wstrb` | `axil_props.v` |
| **F-06** | AXI4-Lite to APB4 Bridge | L1, L2 | BR-01..BR-06 | `cg_apb`, `cg_order` | `axil2apb_bridge.sby` |
| **F-07** | APB Decoder & Error Slave | L1, L2 | BR-03 | `cg_apb` | APB protocol checks |
| **F-08** | APB UART (8N1, FIFOs, Loopback) | L2 | UA-01..UA-05 | `cg_uart` | UART monitor checks |
| **F-09** | APB Timer (Periodic/One-shot) | L2 | TM-01..TM-03 | `cg_txn` | `apb_timer.sby` |
| **F-10** | APB GPIO (Sync, Edge IRQ) | L2 | GP-01..GP-03 | `cg_txn` | GPIO monitor checks |
| **F-11** | CDC Async FIFO Bridge | L0, L1, L2 | CD-01..CD-05 | `cg_cdc` | `async_fifo.sby` |
| **F-12** | 2-FF Reset Synchronizers | L0, L2 | XB-12, CD-03 | `cg_reset` | Reset recovery tests |
| **F-13** | IRQ Aggregation (`irq_o`) | L2 | CS-03, UA-05, TM-03, GP-03 | `cg_txn` | Scoreboard IRQ model |

---

## 3. Test Catalog

### 3.1 Crossbar & AXI4-Lite Tests (`XB-*`)
- **XB-01:** Single write and read from each master to each mapped slave (RAM, CSR, APB, CDC).
- **XB-02:** Write-then-read data integrity across all addresses of RAM with reference model scoreboard.
- **XB-03:** All 16 `WSTRB` combinations tested on RAM and CSR byte-writable registers.
- **XB-04:** Unmapped address reads and writes; verify `DECERR` returned, no bus stalls, write data consumed.
- **XB-05:** Master contention: Both masters simultaneously targeting the same slave; verify serialization without corruption.
- **XB-06:** Master parallelism: Both masters targeting different slaves; verify concurrent completion.
- **XB-07:** Bounded arbitration fairness under continuous contention (grants balanced within $\pm 1$).
- **XB-08:** Write address vs write data skew: AW before W, W before AW, and simultaneous arrival.
- **XB-09:** Random back-pressure delays on `READY` across all channels (0 to 16 cycles).
- **XB-10:** Delayed `BREADY` and `RREADY` assertions; verify response payload stability.
- **XB-11:** `SLVERR` response validation on RAM out-of-bounds, CSR undefined registers, APB errors, CDC errors.
- **XB-12:** Asynchronous reset asserted mid-transaction; verify graceful recovery and next transaction success.
- **XB-13:** Constrained-random stress: $\ge 10,000$ transactions across 2 masters with zero scoreboard mismatches.
- **XB-14:** `AWPROT` and `ARPROT` pass-through verification to APB `PPROT`.
- **XB-15:** Unaligned address accesses; verify word alignment behavior.

### 3.2 APB Bridge Tests (`BR-*`)
- **BR-01:** Basic APB read/write with 0 wait states; verify APB SETUP/ACCESS timing.
- **BR-02:** APB random wait states (1 to 10 cycles); verify signal stability during wait states.
- **BR-03:** APB `PSLVERR` assertion on read and write; verify translation to AXI `SLVERR`.
- **BR-04:** `PSTRB` byte enables; verify match with `WSTRB`.
- **BR-05:** Back-to-back mixed read and write transactions from both masters.
- **BR-06:** Extreme write skew: W data arriving many cycles after AW.

### 3.3 Peripheral Tests (`UA-*`, `TM-*`, `GP-*`, `CS-*`)
- **UA-01:** UART internal loopback mode: verify transmission and reception of all 256 byte values.
- **UA-02:** UART FIFO full, empty, and overflow flags (`TX_OVF`, `RX_OVF`) with W1C clearing.
- **UA-03:** UART baud rate divisor sweep; verify bit period against `BAUDDIV`.
- **UA-04:** UART framing error injection (bad stop bit); verify `FRAME_ERR` flag.
- **UA-05:** UART RX interrupt generation and clearing.
- **TM-01:** Timer one-shot countdown; verify timeout assertion after exactly $(LOAD+1)$ cycles.
- **TM-02:** Timer periodic mode; verify continuous timeouts at reload intervals.
- **TM-03:** Timer W1C clearing of `TIMEOUT` and interrupt deassertion.
- **GP-01:** GPIO direction control and output pin drive.
- **GP-02:** GPIO input synchronization latency (2 clock cycles).
- **GP-03:** GPIO rising-edge interrupt detection and W1C clear.
- **CS-01:** System CSR reset values match register table.
- **CS-02:** CSR RO fields ignore writes; W1C behavior; `W1C_SET` test hook.
- **CS-03:** CSR interrupt masking and aggregation to `irq_o`.

### 3.4 CDC Tests (`CD-*`)
- **CD-01:** CDC data integrity across clock ratio and phase sweeps ($f_{\text{slow}} < f_{\text{sys}}$, $f_{\text{slow}} \approx f_{\text{sys}}$, $f_{\text{slow}} > f_{\text{sys}}$).
- **CD-02:** CDC FIFO occupancy boundaries (full and empty handling).
- **CD-03:** Random asynchronous reset in either clock domain during transactions.
- **CD-04:** `SLOW_COUNTER` rate verification (confirming increment rate matches `clk_slow`).
- **CD-05:** Multi-master interleaved access to slow domain registers.

---

## 4. Functional Coverage Model

Implemented via `cocotb-coverage` with 100% closure goal (or written waivers):

1. `cg_txn`: Cross of `{Master0, Master1} x {S0, S1, S2, S3, Default} x {Read, Write} x {OKAY, SLVERR, DECERR}`.
2. `cg_wstrb`: Cross of all 16 `WSTRB` patterns x `{RAM, CSR, APB, CDC}`.
3. `cg_order`: Cross of write channel arrival `{AW before W, W before AW, simultaneous}` x Target Slaves.
4. `cg_backpressure`: Binned ready delays `{0, 1, 2-4, 5-16}` across AW, W, B, AR, R channels.
5. `cg_contention`: Master contention `{Same Slave, Different Slaves, One Idle}` x Op combos `{R/R, R/W, W/W}`.
6. `cg_apb`: APB wait states `{0, 1, 2-4, 5+}` x `PSLVERR {Yes, No}` x `{Read, Write}`.
7. `cg_cdc`: Clock ratios `{slow < sys, slow ~ sys, slow > sys}` x FIFO occupancy `{empty, partial, full}`.
8. `cg_uart`: Divisor bins x FIFO states x Framing errors.
9. `cg_reset`: Reset applied during `{Idle, AW pending, W pending, B pending, R pending}`.

---

## 5. Formal Verification Property Catalog

Implemented in `formal/` with SymbiYosys (BMC depth 20–30 + k-induction):
1. **`axil_props.v`**: AXI4-Lite handshake rules, stability rules, response validity, single-response property.
2. **`rr_arbiter.sby`**: Mutual exclusion, one-hot grant, starvation-free bounded fairness, lock persistence.
3. **`axil_xbar.sby`**: Slave routing isolation, W-channel lock consistency, absence of deadlock.
4. **`axil2apb_bridge.sby`**: APB protocol phases (SETUP -> ACCESS), signal stability, error propagation.
5. **`async_fifo.sby`**: Multi-clock pointer Gray coding, full/empty safety, magic-value data integrity.
6. **`apb_timer.sby`**: Deterministic down-counter expiration after $(LOAD+1)$ cycles, W1C status.
