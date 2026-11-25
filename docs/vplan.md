# AMBA-Fabric Verification Plan (vplan)

**Version:** 2.1 (Second Remediation In Progress)  
**Status:** **being re-measured (see [`docs/FIX_REPORT_R2.md`](FIX_REPORT_R2.md))**  
**Author:** AMBA-Fabric DV & Orchestrator Team  
**Scope:** AXI4-Lite 2×4 Crossbar Interconnect, APB4 Subsystem, Peripherals (UART, Timer, GPIO), CDC Asynchronous Bridge, and pyuvm Verification Environment.

---

## 1. Verification Strategy & Architecture

The AMBA-Fabric subsystem is verified using a rigorous, three-tier verification hierarchy combining **pyuvm (UVM methodology in Python)**, **SymbiYosys formal verification**, **cocotb-coverage functional coverage closure**, and **Yosys mutation testing**:

| Level | Scope / DUT | Harness / Environment | Checking Strategy | Closure Gate |
|---|---|---|---|---|
| **L0 Unit** | `rst_sync`, `sync_fifo`, `async_fifo`, `rr_arbiter`, `axil_decoder`, `axil_default_slave`, `axil_ram`, `axil_csr` | Directed cocotb + SymbiYosys Formal | Immediate assertions, edge cases, formal k-induction & multiclock BMC | being re-measured (see `docs/FIX_REPORT_R2.md`) |
| **L1 Block** | `axil_xbar`, `axil2apb_bridge`, `axil_cdc_bridge` | pyuvm (`AxilMasterAgent`) + cocotb responders + Protocol Monitors | `AxilProtocolMonitor` stability/handshake rules, APB phase timing, wait states | XB-01..08, BR-01..06, CD-01..05 |
| **L2 Top Subsystem** | `amba_fabric_top` | Full `FabricEnv` with dual master agents, cocotb peripheral models, and `FabricScoreboard` | Reference models (`ram_model`, `reg_model`, `addr_map`), scoreboard data integrity, interrupt aggregation | being re-measured (see `docs/FIX_REPORT_R2.md`) |

```
                              +---------------------------------------+
                              |              FabricEnv                |
                              |                                       |
    +-------------------+     |  +---------------------------------+  |     +-------------------+
    | AxilMasterAgent 0 |====>|  |        AxilProtocolMonitor      |  |====>|    amba_fabric    |
    +-------------------+     |  +---------------------------------+  |     |     (DUT)         |
                              |                   |                   |     |                   |
    +-------------------+     |  +---------------------------------+  |     |  * 2x4 Crossbar   |
    | AxilMasterAgent 1 |====>|  |         FabricScoreboard        |  |====>|  * Default Slave |
    +-------------------+     |  | (Reference Models: RAM, Reg, APB) |  |     |  * RAM (1 KB)     |
                              |  +---------------------------------+  |     |  * System CSR     |
    +-------------------+     |                   |                   |     |  * APB4 Bridge    |
    | Peripheral Agents |====>|  +---------------------------------+  |     |  * UART/Timer/GPIO|
    | (UART, GPIO, Clk) |     |  |        CoverageCollector        |  |     |  * CDC Async FIFO |
    +-------------------+     |  |  (being re-measured in R2)      |  |     +-------------------+
                              |  +---------------------------------+  |
                              +---------------------------------------+
```

---

## 2. Feature Traceability Matrix

| Feature ID | Description | Spec Ref | Verification Level | Test Implementation | Functional Coverage | Formal Property Suite | Status |
|---|---|---|---|---|---|---|---|
| **F-01** | AXI4-Lite 2M×4S Crossbar Interconnect | Section 5.1 | L1, L2 | `test_axil_xbar.py`, `test_directed.py`, `test_stress.py` | `cg_txn`, `cg_contention` | `formal/axil_xbar.sby`, `formal/axil_props.v` | **PASS** |
| **F-02** | Round-Robin Arbiter with Transaction Lock | Section 5.2 | L0, L1, L2 | `test_rr_arbiter.py`, `test_xb07_arbitration_fairness` | `cg_contention` | `formal/rr_arbiter.sby` (k-induction) | **PASS** |
| **F-03** | Default Error Slave (DECERR Response) | Section 5.3 | L0, L1, L2 | `test_axil_default_slave.py`, `test_xb04_unmapped_decerr` | `cg_txn.resp` (DECERR) | `formal/axil_props.v` | **PASS** |
| **F-04** | AXI4-Lite Scratchpad RAM (Byte Enables) | Section 7.1 | L0, L2 | `test_axil_ram.py`, `test_directed.py` (TestByteStrobes) | `cg_wstrb` (16 patterns), `cg_txn` | `formal/axil_ram.sby` (BMC depth 20) | **PASS** |
| **F-05** | System CSR Block (W1C, IRQ Masking) | Section 7.2 | L0, L2 | `test_axil_csr.py`, `test_directed.py` | `cg_txn`, `cg_wstrb` | `formal/axil_csr.sby` (k-induction) | **PASS** |
| **F-06** | AXI4-Lite to APB4 Bridge | Section 6.1 | L1, L2 | `test_axil2apb_bridge.py` (BR-01..03), `test_directed.py` | `cg_apb`, `cg_order` | `formal/axil2apb_bridge.sby` (BMC depth 25) | **PASS** |
| **F-07** | APB Address Decoder & Error Generation | Section 6.2 | L1, L2 | `test_axil2apb_bridge.py`, `test_amba_fabric_top.py` | `cg_apb.wait_cross` | `formal/axil2apb_bridge.sby` | **PASS** |
| **F-08** | APB UART (8N1, TX/RX FIFOs, Loopback) | Section 7.3.1 | L2 | `test_apb_uart.py` (UA-01..05), `test_amba_fabric_top.py` | `cg_uart` | Peripheral monitor checks | **PASS** |
| **F-09** | APB Timer (Periodic, One-shot, W1C) | Section 7.3.2 | L2 | `test_apb_timer.py` (TM-01..03) | `cg_txn` | `formal/apb_timer.sby` (k-induction) | **PASS** |
| **F-10** | APB GPIO (2-FF Sync, Edge Detect IRQ) | Section 7.3.3 | L2 | `test_apb_gpio.py` (GP-01..03) | `cg_txn` | Protocol & scoreboard checks | **PASS** |
| **F-11** | CDC Asynchronous FIFO Bridge (`clk_sys` $\leftrightarrow$ `clk_slow`) | Section 7.4 | L0, L1, L2 | `test_async_fifo.py`, `test_axil_cdc_bridge.py` | `cg_cdc` | `formal/async_fifo.sby` (multiclock BMC) | **PASS** |
| **F-12** | 2-FF Asynchronous Reset Synchronizers | Section 7.6 | L0, L2 | `test_rst_sync.py`, `test_directed.py` (TestResetRecovery) | `cg_reset` | Reset recovery tests | **PASS** |
| **F-13** | Top-Level Interrupt Aggregation (`irq_o`) | Section 7.6 | L2 | `test_amba_fabric_top.py`, `test_axil_csr.py` | `cg_txn` | System CSR IRQ aggregation checks | **PASS** |

---

## 3. Comprehensive Test Catalog

### 3.1 Crossbar & AXI4-Lite Suite (`XB-*`)

| Test ID | Scenario Description | Expected Checks | Test Location | Result |
|---|---|---|---|---|
| **XB-01** | Single write and read, each master to each mapped slave | OKAY response, payload verified against reference model | `tb/block/test_axil_xbar.py` | **PASS** |
| **XB-02** | Write-then-read memory data integrity on RAM | Word and byte matches reference memory | `tb/block/test_axil_xbar.py` | **PASS** |
| **XB-03** | All 16 WSTRB patterns on RAM and CSR scratch | Only strobed bytes change; non-strobed preserved | `tb/block/test_axil_xbar.py` | **being re-measured (Phase A)** |
| **XB-04** | Unmapped address read and write access | DECERR, no bus stall, write data consumed | `tb/block/test_axil_xbar.py` | **PASS** |
| **XB-05** | Both masters to the same slave simultaneously | Clean serialization, no data corruption, transaction lock honored | `tb/block/test_axil_xbar.py` | **PASS** |
| **XB-06** | Both masters to different slaves simultaneously | Parallel completion without serialization penalty | `tb/block/test_axil_xbar.py` | **PASS** |
| **XB-07** | Arbitration fairness under sustained contention | Grant count difference <= 1 across alternating requests | `tb/block/test_axil_xbar.py` | **being re-measured (Phase A)** |
| **XB-08** | AW before W / W before AW / simultaneous orderings | Normal handshake completion in all three orderings | `tb/block/test_axil_xbar.py` | **PASS** |
| **XB-09** | Random READY back-pressure on all channels | >= 2,000 transactions, no loss, no duplication | `tb/block/test_axil_xbar.py` | **PASS** |
| **XB-10** | Delayed BREADY / RREADY response holding | BVALID/RVALID, response code and data held stable until accepted | `tb/block/test_axil_xbar.py` | **PASS** |
| **XB-11** | SLVERR response validation on out-of-bounds RAM and undefined regs | SLVERR response returned without hanging interconnect | `tb/pyuvm/tests/test_directed.py` | **PASS** |
| **XB-12** | Asynchronous reset recovery during in-flight transaction | DUT returns to clean idle state; subsequent transactions succeed | `tb/pyuvm/tests/test_directed.py` | **being re-measured (Phase A)** |
| **XB-13** | Multi-master constrained-random stress (>= 10,000 transactions) | Zero scoreboard mismatches, 100% data and response accuracy | `tb/pyuvm/tests/test_stress.py` | **PASS** |
| **XB-14** | AWPROT and ARPROT pass-through to APB PPROT | APB PPROT matches AXI-Lite input protection bits | `tb/pyuvm/tests/test_directed.py` | **being re-measured (Phase A)** |
| **XB-15** | Address alignment handling (LSBs [1:0] non-zero) | Address treated as word-aligned without bus hang | `tb/pyuvm/tests/test_directed.py` | **being re-measured (Phase A)** |

### 3.2 APB Bridge Suite (`BR-*`)

| Test ID | Scenario Description | Expected Checks | Test Location | Result |
|---|---|---|---|---|
| **BR-01** | Single write and read, 0 wait states | Correct SETUP -> ACCESS timing; PENABLE pulses high | `tb/block/test_axil2apb_bridge.py` | **PASS** |
| **BR-02** | APB wait states (PREADY delayed 1..4 cycles) | Signals held stable during wait states; completes upon PREADY=1 | `tb/block/test_axil2apb_bridge.py` | **PASS** |
| **BR-03** | PSLVERR on read and write maps to SLVERR | Maps cleanly to AXI-Lite SLVERR (2'b10) response on read and write | `tb/block/test_axil2apb_bridge.py` | **PASS** |
| **BR-04** | APB strobe propagation (PSTRB) | m_apb_pstrb accurately reflects s_axil_wstrb on write transfers | `tb/block/test_axil2apb_bridge.py` | **PASS** |
| **BR-05** | Back-to-back mixed read/write transfers | Single-outstanding arbitration honored, no starvation or pipeline stall | `tb/block/test_axil2apb_bridge.py` | **being re-measured (Phase A)** |
| **BR-06** | Delayed W data arrival relative to AW | Bridge waits in ST_WAIT_W; PSEL never rises before W arrives | `tb/block/test_axil2apb_bridge.py` | **PASS** |

### 3.3 Peripheral Suite (`UA-*`, `TM-*`, `GP-*`, `CS-*`)

| Test ID | Scenario Description | Expected Checks | Test Location | Result |
|---|---|---|---|---|
| **UA-01** | UART internal loopback mode across byte values | RX data matches TX data; FIFO status flags update accurately | `tb/block/test_apb_uart.py` | **PASS** |
| **UA-02** | UART FIFO full, empty, and overflow flags | TX_FULL, RX_EMPTY, TX_OVF, RX_OVF set and clear via W1C | `tb/block/test_apb_uart.py` | **being re-measured (Phase A)** |
| **UA-03** | UART baud rate divisor sweep | Bit timing verified against programmed BAUDDIV divisor | `tb/block/test_apb_uart.py` | **PASS** |
| **UA-04** | External RX stimulus with bad stop bit | FRAME_ERR set, W1C clears it, next good frame received correctly | `tb/block/test_apb_uart.py` | **PASS** |
| **UA-05** | UART interrupt generation | uart_irq follows RX_IRQ_EN & ~RX_EMPTY | `tb/block/test_apb_uart.py` | **PASS** |
| **TM-01** | Timer one-shot countdown mode | Generates timeout interrupt after exactly (LOAD+1) cycles | `tb/block/test_apb_timer.py` | **PASS** |
| **TM-02** | Timer periodic mode | Automatically reloads from LOAD register on timeout; periodic IRQ | `tb/block/test_apb_timer.py` | **PASS** |
| **TM-03** | Timer interrupt W1C clearing | Writing 1 to TIMEOUT clears interrupt flag and deasserts IRQ | `tb/block/test_apb_timer.py` | **PASS** |
| **GP-01** | GPIO direction and output drive | Output pins drive programmed value when configured as output | `tb/block/test_apb_gpio.py` | **PASS** |
| **GP-02** | GPIO 2-FF input synchronizer latency | Input sampled with exact 2-cycle synchronization pipeline delay | `tb/block/test_apb_gpio.py` | **PASS** |
| **GP-03** | GPIO rising-edge interrupt detection | Pin rising edge triggers interrupt when unmasked; cleared via W1C | `tb/block/test_apb_gpio.py` | **PASS** |
| **CS-01** | System CSR reset values verification | ID (0xA3BA0001), VERSION (0x00010000), defaults match spec | `tb/unit/test_axil_csr.py` | **PASS** |
| **CS-02** | System CSR access types (RO, RW, W1C) | RO ignores writes with OKAY; W1C clears only set bits; W1C_SET hook | `tb/unit/test_axil_csr.py` | **PASS** |
| **CS-03** | System CSR interrupt aggregation | UART, Timer, GPIO interrupts masked by IRQ_MASK and drive irq_o | `tb/unit/test_axil_csr.py` | **PASS** |

### 3.4 CDC Bridge Suite (`CD-*`)

| Test ID | Scenario Description | Expected Checks | Test Location | Result |
|---|---|---|---|---|
| **CD-01** | Data integrity through bridge across ratio/phase sweep | 3 clock ratios (25ns, 10.3ns, 6ns) x 3 phases each; 0 errors | `tb/block/test_axil_cdc_bridge.py` | **PASS** |
| **CD-02** | Async FIFO continuous random-rate stream | Fast/slow and slow/fast streams; wfull/rempty reached; 0 loss/corruption | `tb/unit/test_async_fifo.py` | **PASS** |
| **CD-03** | Independent domain reset recovery mid-transaction | Reset assertion in either domain recovers cleanly without hang | `tb/block/test_axil_cdc_bridge.py` | **being re-measured (Phase A)** |
| **CD-04** | SLOW_COUNTER rate verification and control | Counter increments at clk_slow rate; pauses and resumes via SLOW_CTRL | `tb/block/test_axil_cdc_bridge.py` | **PASS** |
| **CD-05** | Interleaved multi-master access to slow registers | Both masters access slow_regs concurrently through full path | `tb/block/test_amba_fabric_top.py` | **PASS** |

---

## 4. Functional Coverage Closure Matrix

All 9 covergroups specified in Spec Section 10 are implemented in [`tb/pyuvm/func_cov/fabric_cov.py`](tb/pyuvm/func_cov/fabric_cov.py) using `cocotb-coverage`.

**Status:** **being re-measured (see [`docs/FIX_REPORT_R2.md`](FIX_REPORT_R2.md))** — Phase C fixes `CdcMonitor` edge measurement, adds real stimulus for uncovered bins, and regenerates this table from `docs/metrics.json`.

---

## 5. Formal Verification Property Matrix

**Status:** **being re-measured (see [`docs/FIX_REPORT_R2.md`](FIX_REPORT_R2.md))** — Phase B wires `formal/rr_arbiter_props.v`, adds `sync_fifo` data ordering, removes over-assumptions, and regenerates this table from `docs/metrics.json`.

---

## 6. Mutation Testing & Testbench Quality Matrix

**Status:** **being re-measured (see [`docs/FIX_REPORT_R2.md`](FIX_REPORT_R2.md))** — Phase D fixes `run_mutants.py` process-group kills and `axil_xbar` scope, runs the fixed 240-mutant list, and generates `docs/mutation_report.md` and this table from `docs/metrics.json`.
