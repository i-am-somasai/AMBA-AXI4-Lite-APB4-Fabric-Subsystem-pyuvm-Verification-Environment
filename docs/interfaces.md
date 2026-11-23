# AMBA-Fabric Interface Specification & Architectural Contract

**Status:** **FROZEN**  
**Date:** 2026-11-23  
**Author:** Orchestrator  
**Authority:** Authoritative contract between Orchestrator, RTL Agent, DV Agent, and Formal/Backend Agent.  
**Rule:** Any changes to this document after freeze require an explicit entry in `docs/decisions.md` and approval by the Orchestrator.

---

## 1. Global Conventions

### 1.1 Language & Synthesis Style
- Standard: Verilog-2005 with minimal SystemVerilog constructs (`logic`, `always_ff`, `always_comb`, parameters, generate).
- **Prohibited:** No SV interfaces, classes, or packed structs on module ports. Modules must compile under Icarus Verilog, Verilator, and Yosys.
- File naming: Module `<name>` must reside in `<name>.v`.

### 1.2 Clocks & Resets
- `clk_sys`: Primary system clock (nominal 100 MHz in synthesis).
- `clk_slow`: Asynchronous secondary clock domain.
- `rst_n`: Asynchronous active-low external reset, synchronized internally per clock domain via `rst_sync`.
- Synchronized resets inside blocks: `rst_n` (active-low). Flops reset asynchronously asserting, synchronously deasserting (`always @(posedge clk or negedge rst_n)`).

### 1.3 Bus Protocols
- **AXI4-Lite:** 32-bit data (`DATA_WIDTH=32`), 32-bit address (`ADDR_WIDTH=32`).
  - Response encoding: `2'b00` = OKAY, `2'b10` = SLVERR, `2'b11` = DECERR (`2'b01` EXOKAY is unused).
  - Byte-aligned addresses, but word transfers assumed; address bits `[1:0]` are ignored for decoding.
  - Channels: AW (Write Address), W (Write Data), B (Write Response), AR (Read Address), R (Read Data & Response).
- **APB4:** 32-bit data, 32-bit address.
  - Signals: `PCLK`, `PRESETn`, `PADDR[31:0]`, `PPROT[2:0]`, `PSEL`, `PENABLE`, `PWRITE`, `PWDATA[31:0]`, `PSTRB[3:0]`, `PREADY`, `PRDATA[31:0]`, `PSLVERR`.

---

## 2. Memory Map & Peripheral Address Space

| Region Name | Target Slave | Base Address | Size | Description / Behavior |
|---|---|---|---|---|
| APB Subsystem | `S0` | `0x4000_0000` | 64 KB | Bridged to APB4 bus |
| ↳ UART | APB P0 | `0x4000_0000` | 4 KB | 8N1 UART with loopback and FIFOs |
| ↳ Timer | APB P1 | `0x4000_1000` | 4 KB | 32-bit countdown timer with IRQ |
| ↳ GPIO | APB P2 | `0x4000_2000` | 4 KB | 16-bit GPIO with edge IRQ |
| ↳ Unmapped APB | APB Default | `0x4000_3000`–`0x4000_FFFF` | 52 KB | APB decoder returns `PREADY=1`, `PSLVERR=1` |
| Scratch RAM | `S1` | `0x5000_0000` | 4 KB | Valid range: `0x5000_0000` to `0x5000_0000 + (RAM_DEPTH*4) - 1`. Out-of-range → `SLVERR` |
| System CSR | `S2` | `0x6000_0000` | 256 B | ID, Version, Scratchpads, IRQ aggregation, W1C hooks. Undefined offset → `SLVERR` |
| CDC Slow Regs | `S3` | `0x7000_0000` | 256 B | Crosses to `clk_slow`. ID, Scratch, Counter, Ctrl. Undefined offset → `SLVERR` |
| Default Slave | Unmapped | Everywhere else | - | Crossbar default slave returns `DECERR` on reads/writes |

---

## 3. Detailed Module Specifications

### 3.1 Common Blocks (`rtl/common/`)

#### `rst_sync` (F-12)
- **Parameters:** None.
- **Ports:**
  - `input  wire clk`: Target domain clock.
  - `input  wire rst_n_in`: Raw asynchronous active-low reset.
  - `output wire rst_n_out`: Synchronized active-low reset (async assert, sync deassert via 2 cascaded flops).

#### `sync_fifo`
- **Parameters:**
  - `WIDTH` (default: 8): Data bus width.
  - `DEPTH` (default: 8): Number of entries (must be a power of 2).
- **Ports:**
  - `input  wire             clk`: Clock.
  - `input  wire             rst_n`: Active-low reset.
  - `input  wire             push`: Push write request.
  - `input  wire [WIDTH-1:0] wdata`: Write data.
  - `input  wire             pop`: Pop read request.
  - `output wire [WIDTH-1:0] rdata`: Read data.
  - `output wire             full`: FIFO full flag.
  - `output wire             empty`: FIFO empty flag.
  - `output wire [$clog2(DEPTH):0] count`: Current entry count.
  - `output wire             overflow`: Push while full error pulse.
  - `output wire             underflow`: Pop while empty error pulse.

#### `async_fifo` (F-11)
- **Parameters:**
  - `WIDTH` (default: 32): Data width.
  - `DEPTH` (default: 4): Number of entries (must be a power of 2).
  - `ASYNC_STAGES` (default: 2): Synchronizer stages.
- **Ports:**
  - `input  wire             wclk`: Write domain clock.
  - `input  wire             wrst_n`: Write domain reset.
  - `input  wire             winc`: Write increment / push.
  - `input  wire [WIDTH-1:0] wdata`: Write data.
  - `output wire             wfull`: Write domain full flag.
  - `input  wire             rclk`: Read domain clock.
  - `input  wire             rrst_n`: Read domain reset.
  - `input  wire             rinc`: Read increment / pop.
  - `output wire [WIDTH-1:0] rdata`: Read data.
  - `output wire             rempty`: Read domain empty flag.
- **Naming Rule:** Flops in the Gray synchronizer chains must be named `sync_w2r_q1`, `sync_w2r_q2`, `sync_r2w_q1`, `sync_r2w_q2` for STA false-path / max-delay constraints.

#### `rr_arbiter` (F-02)
- **Parameters:**
  - `NUM_REQS` (default: 2): Number of requesters.
- **Ports:**
  - `input  wire                  clk`: Clock.
  - `input  wire                  rst_n`: Active-low reset.
  - `input  wire [NUM_REQS-1:0]   req`: Requesters request bitmask.
  - `input  wire                  lock`: Hold current grant when asserted.
  - `output reg  [NUM_REQS-1:0]   grant`: One-hot grant output.
  - `output wire                  grant_valid`: High when any grant is active (`|grant`).

---

### 3.2 AXI4-Lite Interconnect (`rtl/axil/`)

#### `axil_decoder`
- **Parameters:** None (encodes Section 2 address map for S0..S3 + default).
- **Ports:**
  - `input  wire [31:0] addr`: 32-bit transaction address.
  - `output reg  [1:0]  slave_sel`: 0=S0 (APB), 1=S1 (RAM), 2=S2 (CSR), 3=S3 (CDC).
  - `output wire        decode_err`: High when `addr` does not match S0..S3.

#### `axil_default_slave` (F-03)
- **Ports:**
  - `input  wire        clk`, `rst_n`
  - `input  wire [31:0] s_axil_awaddr`, `input wire [2:0] s_axil_awprot`, `input wire s_axil_awvalid`, `output wire s_axil_awready`
  - `input  wire [31:0] s_axil_wdata`, `input wire [3:0] s_axil_wstrb`, `input wire s_axil_wvalid`, `output wire s_axil_wready`
  - `output wire [1:0]  s_axil_bresp`, `output wire s_axil_bvalid`, `input wire s_axil_bready`
  - `input  wire [31:0] s_axil_araddr`, `input wire [2:0] s_axil_arprot`, `input wire s_axil_arvalid`, `output wire s_axil_arready`
  - `output wire [31:0] s_axil_rdata`, `output wire [1:0] s_axil_rresp`, `output wire s_axil_rvalid`, `input wire s_axil_rready`
- **Behavior:** Consumes AW and W (can arrive in any order); responds with `BRESP=2'b11` (DECERR). Consumes AR; responds with `RDATA=32'h0`, `RRESP=2'b11` (DECERR). Never hangs.

#### `axil_ram` (F-04)
- **Parameters:**
  - `DATA_WIDTH` (default: 32)
  - `ADDR_WIDTH` (default: 32)
  - `RAM_DEPTH` (default: 256 words; 64 for synthesis)
- **Ports:** Standard AXI4-Lite slave channel signals.
- **Behavior:**
  - Byte-enable writes using `WSTRB[3:0]`.
  - Read latency: 1 clock cycle.
  - Word offset: `offset = (addr - 32'h5000_0000) >> 2`.
  - If `offset >= RAM_DEPTH`: discard write, return `BRESP=SLVERR (2'b10)`. For read, return `RDATA=0`, `RRESP=SLVERR (2'b10)`.

#### `axil_csr` (F-05, F-13)
- **Parameters:**
  - `DATA_WIDTH` (default: 32)
  - `ADDR_WIDTH` (default: 32)
- **Ports:**
  - Standard AXI4-Lite slave channel signals.
  - `input  wire [2:0]  irq_sources`: `[0]` UART IRQ, `[1]` Timer IRQ, `[2]` GPIO IRQ.
  - `output wire        irq_o`: System aggregate interrupt (`|IRQ_STATUS`).
- **Registers:**
  - `0x00` (`ID`, RO): `0xA3BA_0001`
  - `0x04` (`VERSION`, RO): `0x0001_0000`
  - `0x08` (`SCRATCH`, RW): Word RW, reset = 0
  - `0x0C` (`SCRATCH2`, RW): Byte-writable RW via `WSTRB`, reset = 0
  - `0x10` (`IRQ_RAW`, RO): `{29'b0, irq_sources}`
  - `0x14` (`IRQ_MASK`, RW): Mask register, reset = 0
  - `0x18` (`IRQ_STATUS`, RO): `IRQ_RAW & IRQ_MASK`
  - `0x1C` (`W1C_TEST`, W1C): Writing 1 clears matching bits, reset = 0
  - `0x20` (`W1C_SET`, WO): Writing 1 sets matching bits in `W1C_TEST` (test hook)
  - Undefined offset → `SLVERR (2'b10)`.

#### `axil_xbar` (F-01, F-02)
- **Parameters:**
  - `NUM_MASTERS` = 2
  - `NUM_SLAVES` = 4 (S0..S3)
  - `DATA_WIDTH` = 32
  - `ADDR_WIDTH` = 32
- **Ports:**
  - `input  wire clk`, `rst_n`
  - Master ports: `s_axil_awaddr[2]`, `s_axil_awvalid[2]`, `s_axil_awready[2]`, etc.
  - Slave ports: `m_axil_awaddr[4]`, `m_axil_awvalid[4]`, `m_axil_awready[4]`, etc.
  - Default slave internal routing for decode errors.
- **Arbitration & Locking Rules:**
  - Independent write and read round-robin arbiters per slave.
  - Master wins slave arbitration upon AW handshake; target slave is locked to that master until the corresponding B handshake completes.
  - W channel forwarded only to the locked slave; `WREADY` stalled if W arrives before AW is granted.
  - Non-interfering transactions (different masters to different slaves) execute simultaneously in parallel.

---

### 3.3 APB Subsystem (`rtl/apb/`)

#### `axil2apb_bridge` (F-06)
- **Ports:**
  - Slave: AXI4-Lite channel signals (`s_axil_*`).
  - Master: APB4 bus signals (`m_apb_paddr`, `m_apb_pprot`, `m_apb_psel`, `m_apb_penable`, `m_apb_pwrite`, `m_apb_pwdata`, `m_apb_pstrb`, `m_apb_pready`, `m_apb_prdata`, `m_apb_pslverr`).
- **State Machine:**
  - `IDLE`: Wait for valid AXI transaction. (Write requires both AW and W valid).
  - `SETUP`: Assert `PSEL=1`, `PENABLE=0`. Drive `PADDR`, `PWRITE`, `PWDATA`, `PSTRB`, `PPROT`.
  - `ACCESS`: Assert `PSEL=1`, `PENABLE=1`. Wait for `PREADY=1`.
  - `RESP`: Capture `PRDATA` / `PSLVERR`. Deassert `PSEL`, `PENABLE`. Drive `BVALID`/`BRESP` or `RVALID`/`RRESP`.

#### `apb_decoder` (F-07)
- **Ports:**
  - Input: APB4 master bus from bridge.
  - Output: 3 one-hot `PSEL` lines (`psel_uart`, `psel_timer`, `psel_gpio`), demuxed `PREADY`, `PRDATA`, `PSLVERR`.
  - Unmapped APB addresses: Drive `PREADY=1`, `PSLVERR=1`, `PRDATA=32'h0` in `ACCESS` phase.

#### `apb_uart` (F-08)
- **Parameters:**
  - `FIFO_DEPTH` = 8
- **Ports:**
  - APB4 slave interface.
  - `input  wire uart_rx`: Serial input pin.
  - `output wire uart_tx`: Serial output pin.
  - `output wire uart_irq`: Interrupt output (`RX_IRQ_EN & ~RX_EMPTY`).
- **Registers:**
  - `0x00` (`TXDATA`, WO): `[7:0]` byte to TX FIFO. Write when full sets `TX_OVF`.
  - `0x04` (`RXDATA`, RO): `[7:0]` byte from RX FIFO. Read when empty returns 0.
  - `0x08` (`STATUS`, RO/W1C): `[0]` TX_FULL, `[1]` TX_EMPTY, `[2]` RX_FULL, `[3]` RX_EMPTY, `[4]` FRAME_ERR (W1C), `[5]` RX_OVF (W1C), `[6]` TX_OVF (W1C), `[7]` TX_BUSY.
  - `0x0C` (`CTRL`, RW): `[0]` TX_EN, `[1]` RX_EN, `[2]` LOOPBACK, `[3]` RX_IRQ_EN.
  - `0x10` (`BAUDDIV`, RW): `[15:0]` Baud divisor. Baud clock tick = `clk_sys / (BAUDDIV + 1)` with 16x oversampling.

#### `apb_timer` (F-09)
- **Ports:**
  - APB4 slave interface.
  - `output wire timer_irq`: Interrupt output (`IRQ_EN & TIMEOUT`).
- **Registers:**
  - `0x00` (`CTRL`, RW): `[0]` EN, `[1]` PERIODIC, `[2]` IRQ_EN.
  - `0x04` (`LOAD`, RW): `[31:0]` Reload value.
  - `0x08` (`VALUE`, RO): `[31:0]` Current countdown value.
  - `0x0C` (`STATUS`, W1C): `[0]` TIMEOUT.
- **Behavior:** Down-counter. Period is `(LOAD + 1)` clock cycles.

#### `apb_gpio` (F-10)
- **Parameters:**
  - `GPIO_WIDTH` = 16
- **Ports:**
  - APB4 slave interface.
  - `input  wire [15:0] gpio_i`: Input pins (internally synchronized via 2-FF synchronizers).
  - `output wire [15:0] gpio_o`: Output pins.
  - `output wire [15:0] gpio_dir`: Output enable/direction (1 = output).
  - `output wire        gpio_irq`: Interrupt output (`|(IRQ_STATUS)`).
- **Registers:**
  - `0x00` (`DIR`, RW): 1 = Output, 0 = Input.
  - `0x04` (`OUT`, RW): Output value driving `gpio_o`.
  - `0x08` (`IN`, RO): Synchronized input value from `gpio_i`.
  - `0x0C` (`IRQ_EN`, RW): Per-pin interrupt enable.
  - `0x10` (`IRQ_STATUS`, W1C): Rising-edge interrupt status.

---

### 3.4 CDC Subsystem (`rtl/cdc/`)

#### `axil_cdc_bridge` (F-11)
- **Ports:**
  - `clk_sys`, `rst_sys_n`
  - `clk_slow`, `rst_slow_n`
  - AXI4-Lite slave interface on `clk_sys`.
  - Simple decoupled request/response interface to `slow_regs` on `clk_slow`.
- **Implementation:**
  - Request async FIFO (`clk_sys` → `clk_slow`): Payload `{is_write, addr[7:0], wdata[31:0], wstrb[3:0]}`, depth 4.
  - Response async FIFO (`clk_slow` → `clk_sys`): Payload `{rdata[31:0], resp[1:0]}`, depth 4.

#### `slow_regs`
- **Ports:**
  - `clk_slow`, `rst_slow_n`
  - Interface to CDC bridge FIFOs.
- **Registers:**
  - `0x00` (`SLOW_ID`, RO): `0x510E_0001`
  - `0x04` (`SLOW_SCRATCH`, RW): 32-bit RW with `WSTRB` support.
  - `0x08` (`SLOW_COUNTER`, RO): 32-bit free-running up-counter incrementing on `clk_slow`.
  - `0x0C` (`SLOW_CTRL`, RW): `[0]` Counter enable.
  - Undefined offset → `SLVERR (2'b10)`.

---

### 3.5 Top-Level Subsystem (`rtl/amba_fabric_top.v`)

#### `amba_fabric_top`
- **Parameters:**
  - `DATA_WIDTH` = 32
  - `ADDR_WIDTH` = 32
  - `RAM_DEPTH` = 256 (64 for synthesis)
  - `GPIO_WIDTH` = 16
- **Ports:**
  - **Clocks & Resets:**
    - `input  wire clk_sys`
    - `input  wire clk_slow`
    - `input  wire rst_n` (external raw asynchronous active-low reset)
  - **AXI4-Lite Master 0 Interface (`s0_axil_*`):**
    - `input  wire [31:0] s0_axil_awaddr`, `input wire [2:0] s0_axil_awprot`, `input wire s0_axil_awvalid`, `output wire s0_axil_awready`
    - `input  wire [31:0] s0_axil_wdata`, `input wire [3:0] s0_axil_wstrb`, `input wire s0_axil_wvalid`, `output wire s0_axil_wready`
    - `output wire [1:0]  s0_axil_bresp`, `output wire s0_axil_bvalid`, `input wire s0_axil_bready`
    - `input  wire [31:0] s0_axil_araddr`, `input wire [2:0] s0_axil_arprot`, `input wire s0_axil_arvalid`, `output wire s0_axil_arready`
    - `output wire [31:0] s0_axil_rdata`, `output wire [1:0] s0_axil_rresp`, `output wire s0_axil_rvalid`, `input wire s0_axil_rready`
  - **AXI4-Lite Master 1 Interface (`s1_axil_*`):**
    - Identical port set as Master 0.
  - **Peripheral I/O:**
    - `input  wire                   uart_rx`
    - `output wire                   uart_tx`
    - `input  wire [GPIO_WIDTH-1:0]  gpio_i`
    - `output wire [GPIO_WIDTH-1:0]  gpio_o`
    - `output wire [GPIO_WIDTH-1:0]  gpio_dir`
    - `output wire                   irq_o`
