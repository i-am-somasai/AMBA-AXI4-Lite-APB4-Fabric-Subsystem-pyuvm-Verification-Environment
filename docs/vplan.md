# AMBA-Fabric Verification Plan (vplan)

<!-- BEGIN:metrics:vplan_header_status -->
**Version:** 2.2 (Generated from `docs/metrics.json`)  
**Status:** **COMPLETE (40/40 Spec Tests PASS | 267/267 Reachable Coverage 100.00% | 10/10 Formal Suites PASS | 85.42% Raw / 93.61% Adj Mutation)**  
**Author:** AMBA-Fabric DV & Orchestrator Team  
**Scope:** AXI4-Lite 2×4 Crossbar Interconnect, APB4 Subsystem, Peripherals (UART, Timer, GPIO), CDC Asynchronous Bridge, and pyuvm Verification Environment.
<!-- END:metrics:vplan_header_status -->

---

## 1. Verification Strategy & Architecture

The AMBA-Fabric subsystem is verified using a rigorous, three-tier verification hierarchy combining **pyuvm (UVM methodology in Python)**, **SymbiYosys formal verification**, **cocotb-coverage functional coverage closure**, and **Yosys mutation testing**:

<!-- BEGIN:metrics:vplan_tier_table -->
| Level | Scope / DUT | Harness / Environment | Checking Strategy | Closure Gate |
|---|---|---|---|---|
| **L0 Unit** | `rst_sync`, `sync_fifo`, `async_fifo`, `rr_arbiter`, `axil_decoder`, `axil_default_slave`, `axil_ram`, `axil_csr` | Directed cocotb (14 unit tests) + SymbiYosys Formal | Immediate assertions, edge cases, formal k-induction & multiclock BMC | **14/14 PASS**; CS-01..03, CD-02 PASS |
| **L1 Block** | `axil_xbar`, `axil2apb_bridge`, `axil_cdc_bridge`, APB UART/Timer/GPIO | pyuvm / cocotb responders (38 block/top tests) + Protocol Monitors | `AxilProtocolMonitor` stability/handshake rules, APB phase timing, wait states | **XB-01..10, BR-01..06, UA-01..05, TM-01..03, GP-01..03, CD-01/03/04/05 PASS** |
| **L2 Top Subsystem** | `amba_fabric_top` | Full `FabricEnv` (8 directed/closure + 1 stress tests) & `FabricScoreboard` | Reference models (`ram_model`, `reg_model`, `addr_map`), scoreboard data integrity, interrupt aggregation | **20 Verilator seeds (200,000 txns, 0 mismatches); 267/267 (100.00%)** |
<!-- END:metrics:vplan_tier_table -->

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
    +-------------------+     |  |  (cocotb-coverage, 9 cgs)       |  |     +-------------------+
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

<!-- BEGIN:metrics:vplan_test_catalog -->
### 3.1 Crossbar & AXI4-Lite Suite (`XB-*`)

| Test ID | Scenario Description | Expected Checks | Test Location | Result |
|---|---|---|---|---|
| **XB-01** | Single write and read, each master to each mapped slave | OKAY response, payload verified against reference model | `tb/block/test_axil_xbar.py` (`test_xb01_single_rw_each_master_to_each_slave`) | **PASS** |
| **XB-02** | Write-then-read memory data integrity on RAM | Word and byte matches reference memory | `tb/block/test_axil_xbar.py` (`test_xb02_ram_data_integrity`); L0 `tb/unit/test_axil_ram.py` (`test_axil_ram_operations`); L2 `tb/block/test_amba_fabric_top.py` (`test_top01_register_map_connectivity`) | **PASS** |
| **XB-03** | All 16 WSTRB patterns on RAM and CSR scratch | Only strobed bytes change; non-strobed preserved | `tb/block/test_axil_xbar.py` (`test_xb03_wstrb_patterns`); L0 `tb/unit/test_axil_ram.py` (`test_axil_ram_operations`), `tb/unit/test_axil_csr.py` (`test_cs02_access_types_w1c`); L2 `tb/pyuvm/tests/test_directed.py` (`test_sys_strobe_patterns`) | **PASS** |
| **XB-04** | Unmapped address read and write access | DECERR, no bus stall, write data consumed | `tb/block/test_axil_xbar.py` (`test_xb04_unmapped_decerr`) | **PASS** |
| **XB-05** | Both masters to the same slave simultaneously | Clean serialization, no data corruption, transaction lock honored | `tb/block/test_axil_xbar.py` (`test_xb05_contention_same_slave`) | **PASS** |
| **XB-06** | Both masters to different slaves simultaneously | Parallel completion without serialization penalty | `tb/block/test_axil_xbar.py` (`test_xb06_parallel_different_slaves`) | **PASS** |
| **XB-07** | Arbitration fairness under sustained contention | Continuous AW/AR requests; completed count diff <= 1 (WR & RD) | `tb/block/test_axil_xbar.py` (`test_xb07_arbitration_fairness`) | **PASS** |
| **XB-08** | AW before W / W before AW / simultaneous orderings | Normal handshake completion in all three orderings | `tb/block/test_axil_xbar.py` (`test_xb08_write_orderings`) | **PASS** |
| **XB-09** | Random READY back-pressure on all channels | >= 2,000 transactions, no loss, no duplication | `tb/block/test_axil_xbar.py` (`test_xb09_random_ready_backpressure`) | **PASS** |
| **XB-10** | Delayed BREADY / RREADY response holding | BVALID/RVALID, response code and data held stable until accepted | `tb/block/test_axil_xbar.py` (`test_xb10_delayed_bready_rready_stability`) | **PASS** |
| **XB-11** | SLVERR response validation on out-of-bounds RAM and undefined regs | SLVERR response returned without hanging interconnect | `tb/pyuvm/tests/test_directed.py` (`test_xb11_slverr_propagation`) | **PASS** |
| **XB-12** | Asynchronous reset recovery during in-flight transaction | Mid-AW/W/B/AR/R reset flush; interrupted addr UNKNOWN; clean recovery | `tb/pyuvm/tests/test_directed.py` (`test_xb12_reset_recovery`) | **PASS** |
| **XB-13** | Multi-master constrained-random stress (>= 10,000 transactions) | Zero scoreboard mismatches, 100% data and response accuracy | `tb/pyuvm/tests/test_stress.py` (`test_xb13_stress`) | **PASS** |
| **XB-14** | AWPROT and ARPROT pass-through to APB PPROT | Physical APB PPROT matches AXI-Lite input protection bits (0..7) | `tb/pyuvm/tests/test_directed.py` (`test_xb14_prot_passthrough`) | **PASS** |
| **XB-15** | Address alignment handling (LSBs [1:0] non-zero) | Treated as word-aligned across RAM/CSR/APB/CDC without bus hang | `tb/pyuvm/tests/test_directed.py` (`test_xb15_unaligned_address`) | **PASS** |

### 3.2 APB Bridge Suite (`BR-*`)

| Test ID | Scenario Description | Expected Checks | Test Location | Result |
|---|---|---|---|---|
| **BR-01** | Single write and read, 0 wait states | Correct SETUP -> ACCESS timing; PENABLE pulses high; PPROT checked | `tb/block/test_axil2apb_bridge.py` (`test_br01_single_rw_zero_wait`) | **PASS** |
| **BR-02** | APB wait states (PREADY delayed 1..4 cycles) | Signals held stable during wait states; completes upon PREADY=1 | `tb/block/test_axil2apb_bridge.py` (`test_br02_wait_states`) | **PASS** |
| **BR-03** | PSLVERR on read and write maps to SLVERR | Maps cleanly to AXI-Lite SLVERR (2'b10) response on read and write | `tb/block/test_axil2apb_bridge.py` (`test_br03_pslverr_propagation`) | **PASS** |
| **BR-04** | APB strobe propagation (PSTRB) | m_apb_pstrb reflects s_axil_wstrb on writes and 0 on reads | `tb/block/test_axil2apb_bridge.py` (`test_br04_pstrb_patterns`) | **PASS** |
| **BR-05** | Back-to-back mixed read/write transfers | Dual-master APB contention & bridge read/write arbitration without starvation | `tb/block/test_axil2apb_bridge.py` (`test_br05_back_to_back_mixed_rw`) | **PASS** |
| **BR-06** | Delayed W data arrival relative to AW | Bridge waits in ST_WAIT_W; PSEL never rises before W arrives | `tb/block/test_axil2apb_bridge.py` (`test_br06_delayed_w_no_early_psel`) | **PASS** |

### 3.3 Peripheral Suite (`UA-*`, `TM-*`, `GP-*`, `CS-*`)

| Test ID | Scenario Description | Expected Checks | Test Location | Result |
|---|---|---|---|---|
| **UA-01** | UART internal loopback mode across byte values | RX data matches TX data; FIFO status flags update accurately | `tb/block/test_apb_uart.py` (`test_ua01_loopback_bytes`) | **PASS** |
| **UA-02** | UART FIFO full, empty, and overflow flags | TX_FULL, RX_EMPTY, TX_OVF, RX_OVF (9th RX byte) set and clear via W1C | `tb/block/test_apb_uart.py` (`test_ua02_fifo_full_and_overflow_flags`) | **PASS** |
| **UA-03** | UART baud rate divisor sweep | Bit timing verified against programmed BAUDDIV divisor | `tb/block/test_apb_uart.py` (`test_ua03_bauddiv_sweep`) | **PASS** |
| **UA-04** | External RX stimulus with bad stop bit | FRAME_ERR set, W1C clears it, next good frame received correctly | `tb/block/test_apb_uart.py` (`test_ua04_framing_error`) | **PASS** |
| **UA-05** | UART interrupt generation | uart_irq follows RX_IRQ_EN & ~RX_EMPTY | `tb/block/test_apb_uart.py` (`test_ua05_rx_irq`) | **PASS** |
| **TM-01** | Timer one-shot countdown mode | Generates timeout interrupt after exactly (LOAD+1) cycles | `tb/block/test_apb_timer.py` (`test_tm01_oneshot_countdown`) | **PASS** |
| **TM-02** | Timer periodic mode | Automatically reloads from LOAD register on timeout; periodic IRQ | `tb/block/test_apb_timer.py` (`test_tm02_periodic_countdown`) | **PASS** |
| **TM-03** | Timer interrupt W1C clearing | Writing 1 to TIMEOUT clears interrupt flag and deasserts IRQ | `tb/block/test_apb_timer.py` (`test_tm03_w1c_timeout_and_irq_clear`) | **PASS** |
| **GP-01** | GPIO direction and output drive | Output pins drive programmed value when configured as output | `tb/block/test_apb_gpio.py` (`test_gp01_direction_and_out`) | **PASS** |
| **GP-02** | GPIO 2-FF input synchronizer latency | Input sampled with exact 2-cycle synchronization pipeline delay | `tb/block/test_apb_gpio.py` (`test_gp02_input_sync_latency`) | **PASS** |
| **GP-03** | GPIO rising-edge interrupt detection | Pin rising edge triggers interrupt when unmasked; cleared via W1C | `tb/block/test_apb_gpio.py` (`test_gp03_rising_edge_irq_and_w1c`) | **PASS** |
| **CS-01** | System CSR reset values verification | ID (0xA3BA0001), VERSION (0x00010000), defaults & Rule 6 [1:0] align | `tb/unit/test_axil_csr.py` (`test_cs01_reset_values`) | **PASS** |
| **CS-02** | System CSR access types (RO, RW, W1C) | RO ignores writes with OKAY; W1C clears only set bits; W1C_SET hook | `tb/unit/test_axil_csr.py` (`test_cs02_access_types_w1c`) | **PASS** |
| **CS-03** | System CSR interrupt aggregation | UART, Timer, GPIO interrupts masked by IRQ_MASK and drive irq_o | `tb/unit/test_axil_csr.py` (`test_cs03_irq_aggregation`) | **PASS** |

### 3.4 CDC Bridge Suite (`CD-*`)

| Test ID | Scenario Description | Expected Checks | Test Location | Result |
|---|---|---|---|---|
| **CD-01** | Data integrity through bridge across ratio/phase sweep | 3 clock ratios (25ns, 10.3ns, 6ns) x 3 phases each; 0 errors | `tb/block/test_axil_cdc_bridge.py` (`test_cd01_ratio_phase_sweep`) | **PASS** |
| **CD-02** | Async FIFO continuous random-rate stream | Fast/slow and slow/fast streams; wfull/rempty reached; 0 loss/corruption | `tb/unit/test_async_fifo.py` (`test_cd02_async_fifo_stream`) | **PASS** |
| **CD-03** | Independent domain reset recovery mid-transaction | Separate clk_sys and clk_slow reset assertion mid-transaction without hang | `tb/block/test_axil_cdc_bridge.py` (`test_cd03_reset_recovery`) | **PASS** |
| **CD-04** | SLOW_COUNTER rate verification and control | Counter increments at clk_slow rate; pauses and resumes via SLOW_CTRL | `tb/block/test_axil_cdc_bridge.py` (`test_cd04_free_running_counter`) | **PASS** |
| **CD-05** | Interleaved multi-master access to slow registers | Both masters access slow_regs concurrently through full path | `tb/block/test_amba_fabric_top.py` (`test_cd05_dual_master_slow_regs`) | **PASS** |
<!-- END:metrics:vplan_test_catalog -->

---

## 4. Functional Coverage Closure Matrix

<!-- BEGIN:metrics:vplan_func_cov_matrix -->
All 9 covergroups defined in [`tb/pyuvm/func_cov/fabric_cov.py`](../tb/pyuvm/func_cov/fabric_cov.py) are merged from **24 real simulation YAML databases** (`20` Verilator seeds `1..20`, `test_directed`, `10.3 ns`/`6.0 ns` CDC sweeps, and block-tagged `cg_apb` wait-state runs) achieving **267/267 (100.00%)** with **36** documented waivers in [`docs/coverage_waivers.md`](coverage_waivers.md):

| Covergroup | Leaf Sub-Metrics | Defined Pre-Waiver | Waived | Reachable Target | Covered | Coverage % |
|---|---:|---:|---:|---:|---:|---:|
| `cg_apb` | 6 | 36 | 3 | 33 | 33 | **100.00%** |
| `cg_backpressure` | 3 | 29 | 0 | 29 | 29 | **100.00%** |
| `cg_cdc` | 4 | 25 | 6 | 19 | 19 | **100.00%** |
| `cg_contention` | 3 | 15 | 3 | 12 | 12 | **100.00%** |
| `cg_order` | 3 | 19 | 0 | 19 | 19 | **100.00%** |
| `cg_reset` | 1 | 5 | 0 | 5 | 5 | **100.00%** |
| `cg_txn` | 5 | 72 | 24 | 48 | 48 | **100.00%** |
| `cg_uart` | 4 | 18 | 0 | 18 | 18 | **100.00%** |
| `cg_wstrb` | 3 | 84 | 0 | 84 | 84 | **100.00%** |
| **TOTAL** | **32** | **303** | **36** | **267** | **267** | **100.00%** |
<!-- END:metrics:vplan_func_cov_matrix -->

---

## 5. Formal Verification Property Matrix

<!-- BEGIN:metrics:vplan_formal_matrix -->
Executed with `scripts/run_all_formal.sh` (SymbiYosys + Yosys + Boolector, [`docs/logs/formal_suite.log`](logs/formal_suite.log); `rr_arbiter` is standalone verified per `DEC-007`):

| Module | Mode | Depth | Result | Covers Reached | Runtime |
|---|---|---:|---|---:|---:|
| `apb_timer` | `prove` | 20 | **PASS** | 4 | 1s |
| `apb_uart` | `bmc` | 25 | **PASS** | 9 | 5s |
| `async_fifo` | `bmc` | 25 | **PASS** | 4 | 8s |
| `axil2apb_bridge` | `bmc` | 25 | **PASS** | 10 | 6s |
| `axil_cdc_bridge` | `bmc` | 30 | **PASS** | 5 | 78s |
| `axil_csr` | `prv+bmc` | 20 | **PASS** | 5 | 3s |
| `axil_ram` | `bmc` | 20 | **PASS** | 5 | 3s |
| `axil_xbar` | `bmc` | 20 | **PASS** | 31 | 42s |
| `rr_arbiter` | `prove` | 20 | **PASS** | 3 | 1s |
| `sync_fifo` | `prove` | 20 | **PASS** | 8 | 3s |
| **TOTAL** | **10 suites** | - | **10/10 PASS** | **84** | **150s** |
<!-- END:metrics:vplan_formal_matrix -->

---

## 6. Mutation Testing & Testbench Quality Matrix

<!-- BEGIN:metrics:vplan_mutation_matrix -->
Evaluated on frozen deterministic 240-mutant list [`mutation/mutant_list_240.json`](../mutation/mutant_list_240.json) (`30` per module × `8` modules, seed `42`; full analysis in [`docs/mutation_report.md`](mutation_report.md)) plus permanent sanity gate (**17/17 KILLED**, [`docs/logs/sanity.log`](logs/sanity.log)):

| Module | Gen | Baseline Kill / Score | Final Kill | Final Surv | Tmo | BldErr | Raw Score | Equiv | Adj. Score |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| `rr_arbiter` | 30 | 19/30 (63.33%) | 22 | 8 | 0 | 0 | 73.33% | 6 | **91.67% (22/24)** |
| `sync_fifo` | 30 | 25/30 (83.33%) | 28 | 2 | 0 | 0 | 93.33% | 2 | **100.00% (28/28)** |
| `async_fifo` | 30 | 18/30 (60.00%) | 30 | 0 | 0 | 0 | 100.00% | 0 | **100.00% (30/30)** |
| `axil_decoder` | 30 | 26/30 (86.67%) | 27 | 3 | 0 | 0 | 90.00% | 3 | **100.00% (27/27)** |
| `axil_ram` | 30 | 17/30 (56.67%) | 24 | 6 | 0 | 0 | 80.00% | 0 | **80.00% (24/30)** |
| `axil_csr` | 30 | 15/30 (50.00%) | 25 | 5 | 0 | 0 | 83.33% | 4 | **96.15% (25/26)** |
| `axil2apb_bridge` | 30 | 23/30 (76.67%) | 26 | 4 | 0 | 0 | 86.67% | 3 | **96.30% (26/27)** |
| `axil_xbar` | 30 | 22/30 (73.33%) | 23 | 7 | 0 | 0 | 76.67% | 3 | **85.19% (23/27)** |
| **TOTAL** | **240** | **165/240 (68.75%)** | **205** | **35** | **0** | **0** | **85.42%** | **21** | **93.61% (205/219)** |
<!-- END:metrics:vplan_mutation_matrix -->
