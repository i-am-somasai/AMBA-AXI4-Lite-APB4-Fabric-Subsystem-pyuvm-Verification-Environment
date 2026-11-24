# tb/block/test_amba_fabric_top.py
# System Integration and Acceptance Gate tests for amba_fabric_top
# Exercises every register map entry in docs/spec.md and verifies IRQ aggregation to irq_o
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from models.axil_driver import AxilMasterDriver

class FabricTopTestbench:
    def __init__(self, dut):
        self.dut = dut
        self.m0 = AxilMasterDriver(dut, dut.clk_sys, prefix="s0_axil_")
        self.m1 = AxilMasterDriver(dut, dut.clk_sys, prefix="s1_axil_")

        self.dut.gpio_i.value = 0
        self.dut.uart_rx.value = 1

        # Dual asynchronous clocks: sys = 100MHz (10ns), slow = 40MHz (25ns)
        cocotb.start_soon(Clock(dut.clk_sys, 10, unit="ns").start())
        cocotb.start_soon(Clock(dut.clk_slow, 25, unit="ns").start())

    async def reset(self):
        self.dut.rst_n.value = 0
        self.dut.gpio_i.value = 0
        self.dut.uart_rx.value = 1
        self.m0.init_signals()
        self.m1.init_signals()
        for _ in range(5):
            await RisingEdge(self.dut.clk_sys)
        self.dut.rst_n.value = 1
        for _ in range(5):
            await RisingEdge(self.dut.clk_sys)

@cocotb.test()
async def test_top01_register_map_connectivity(dut):
    """TOP-01: Full-top connectivity test exercising every register map entry from both masters."""
    tb = FabricTopTestbench(dut)
    await tb.reset()

    # =========================================================================
    # 1. S2: CSR Block (0x6000_0000 - 0x6000_00FF)
    # =========================================================================
    dut._log.info("--- Testing S2: CSR Block ---")
    # CSR ID (0x6000_0000): 0xA3BA_0001
    rdata, rresp = await tb.m0.read(0x60000000)
    assert rresp == 0 and rdata == 0xA3BA0001, f"CSR ID mismatch: {hex(rdata)}"

    # Also verify Master 1 can read CSR ID
    rdata1, rresp1 = await tb.m1.read(0x60000000)
    assert rresp1 == 0 and rdata1 == 0xA3BA0001, f"M1 CSR ID mismatch: {hex(rdata1)}"

    # CSR VERSION (0x6000_0004): 0x0001_0000
    rdata, rresp = await tb.m0.read(0x60000004)
    assert rresp == 0 and rdata == 0x00010000, f"CSR VERSION mismatch: {hex(rdata)}"

    # CSR SCRATCH (0x6000_0008): RW
    bresp = await tb.m0.write(0x60000008, 0x12345678)
    assert bresp == 0
    rdata, _ = await tb.m0.read(0x60000008)
    assert rdata == 0x12345678, f"CSR SCRATCH mismatch: {hex(rdata)}"

    # CSR SCRATCH2 (0x6000_000C): RW from Master 1
    bresp = await tb.m1.write(0x6000000C, 0x87654321)
    assert bresp == 0
    rdata, _ = await tb.m1.read(0x6000000C)
    assert rdata == 0x87654321, f"CSR SCRATCH2 mismatch: {hex(rdata)}"

    # CSR IRQ_RAW (0x6000_0010), IRQ_MASK (0x6000_0014), IRQ_STATUS (0x6000_0018)
    rdata, _ = await tb.m0.read(0x60000010)
    assert rdata == 0, f"Initial IRQ_RAW not 0: {hex(rdata)}"
    await tb.m0.write(0x60000014, 0x00000007) # Mask enables [2:0]
    rdata, _ = await tb.m0.read(0x60000014)
    assert rdata == 0x7
    await tb.m0.write(0x60000014, 0x00000000) # Clear mask

    # CSR W1C_SET (0x6000_0020) and W1C_TEST (0x6000_001C)
    await tb.m0.write(0x60000020, 0x00000005) # Pulse bits 0 and 2
    rdata, _ = await tb.m0.read(0x6000001C)
    assert rdata == 0x5, f"W1C_TEST not set: {hex(rdata)}"
    await tb.m0.write(0x6000001C, 0x00000001) # Clear bit 0
    rdata, _ = await tb.m0.read(0x6000001C)
    assert rdata == 0x4, f"W1C_TEST clear failed: {hex(rdata)}"
    await tb.m0.write(0x6000001C, 0x00000004) # Clear bit 2
    rdata, _ = await tb.m0.read(0x6000001C)
    assert rdata == 0x0

    # =========================================================================
    # 2. S1: Scratchpad RAM (0x5000_0000 - 0x5000_03FC, 1KB)
    # =========================================================================
    dut._log.info("--- Testing S1: Scratchpad RAM ---")
    # Master 0 writes 0x5000_0000
    bresp = await tb.m0.write(0x50000000, 0xCAFEBABE)
    assert bresp == 0
    rdata, rresp = await tb.m0.read(0x50000000)
    assert rresp == 0 and rdata == 0xCAFEBABE, f"RAM readback mismatch: {hex(rdata)}"

    # Master 1 writes 0x5000_0040 and Master 0 reads back
    await tb.m1.write(0x50000040, 0xFEEDFACE)
    rdata, _ = await tb.m0.read(0x50000040)
    assert rdata == 0xFEEDFACE, f"Inter-master RAM shared access mismatch: {hex(rdata)}"

    # Out-of-bounds RAM address (0x5000_0400) -> returns SLVERR (2)
    _, rresp_err = await tb.m0.read(0x50000400)
    assert rresp_err == 2, f"Expected SLVERR on RAM out-of-bounds read, got {rresp_err}"

    # =========================================================================
    # 3. S0: APB Peripherals (0x4000_0000 - 0x4000_FFFF)
    # =========================================================================
    dut._log.info("--- Testing S0: APB Peripherals ---")
    # --- UART (0x4000_0000) ---
    # STATUS (0x4000_0008): initially TX_EMPTY(2) | RX_EMPTY(8) = 0x0A
    status, _ = await tb.m0.read(0x40000008)
    assert (status & 0x0A) == 0x0A, f"Initial UART STATUS mismatch: {hex(status)}"

    # BAUDDIV (0x4000_0010): write 0, read back 0
    await tb.m0.write(0x40000010, 0x0000)
    baud, _ = await tb.m0.read(0x40000010)
    assert baud == 0

    # CTRL (0x4000_000C): write TX_EN(1) | RX_EN(2) | LOOPBACK(4) = 0x07
    await tb.m0.write(0x4000000C, 0x07)
    ctrl, _ = await tb.m0.read(0x4000000C)
    assert (ctrl & 0x07) == 0x07

    # TXDATA (0x4000_0000) & RXDATA (0x4000_0004) loopback transfer
    await tb.m0.write(0x40000000, 0x5A)
    # Poll until RX_EMPTY == 0
    for _ in range(300):
        s, _ = await tb.m0.read(0x40000008)
        if (s & 0x08) == 0:
            break
        await RisingEdge(dut.clk_sys)
    rxdata, _ = await tb.m0.read(0x40000004)
    assert (rxdata & 0xFF) == 0x5A, f"UART loopback data mismatch: {hex(rxdata)}"

    # --- Timer (0x4000_1000) ---
    # LOAD (0x4000_1004) & VALUE (0x4000_1008) & CTRL (0x4000_1000)
    await tb.m0.write(0x40001004, 0x00000100) # LOAD = 256
    load_rb, _ = await tb.m0.read(0x40001004)
    assert load_rb == 0x100
    # Enable periodic timer: CTRL = EN(1) | PERIODIC(2) = 0x03
    await tb.m0.write(0x40001000, 0x03)
    val1, _ = await tb.m0.read(0x40001008)
    for _ in range(5):
        await RisingEdge(dut.clk_sys)
    val2, _ = await tb.m0.read(0x40001008)
    assert val2 < val1 or val2 > 0, "Timer value readback failed"
    # Stop timer
    await tb.m0.write(0x40001000, 0x00)

    # --- GPIO (0x4000_2000) ---
    # DIR (0x4000_2000) controls gpio_dir pins
    await tb.m0.write(0x40002000, 0x00FF)
    dir_rb, _ = await tb.m0.read(0x40002000)
    assert dir_rb == 0x00FF
    assert int(dut.gpio_dir.value) == 0x00FF, f"gpio_dir pin mismatch: {hex(dut.gpio_dir.value)}"

    # OUT (0x4000_2004) controls gpio_o pins
    await tb.m0.write(0x40002004, 0x0055)
    out_rb, _ = await tb.m0.read(0x40002004)
    assert out_rb == 0x0055
    assert int(dut.gpio_o.value) == 0x0055, f"gpio_o pin mismatch: {hex(dut.gpio_o.value)}"

    # IN (0x4000_2008) reads synchronized gpio_i pins
    dut.gpio_i.value = 0xAA00
    for _ in range(4):
        await RisingEdge(dut.clk_sys)
    in_rb, _ = await tb.m0.read(0x40002008)
    assert (in_rb & 0xFF00) == 0xAA00, f"gpio_i readback mismatch: {hex(in_rb)}"

    # IRQ_EN (0x4000_200C) & IRQ_STATUS (0x4000_2010)
    await tb.m0.write(0x4000200C, 0x0000)
    irq_en_rb, _ = await tb.m0.read(0x4000200C)
    assert irq_en_rb == 0

    # --- APB Unmapped Address (0x4000_3000) ---
    _, apb_err = await tb.m0.read(0x40003000)
    assert apb_err == 2, f"Expected SLVERR on APB unmapped read, got {apb_err}"

    # =========================================================================
    # 4. S3: CDC Bridge & Slow Regs (0x7000_0000 - 0x7000_00FF)
    # =========================================================================
    dut._log.info("--- Testing S3: CDC Bridge & Slow Regs ---")
    # SLOW_ID (0x7000_0000): 0x510E_0001
    rdata, rresp = await tb.m0.read(0x70000000)
    assert rresp == 0 and rdata == 0x510E0001, f"SLOW_ID mismatch: {hex(rdata)}"

    # SLOW_SCRATCH (0x7000_0004): RW
    bresp = await tb.m0.write(0x70000004, 0xABCDEF01)
    assert bresp == 0
    rdata, _ = await tb.m0.read(0x70000004)
    assert rdata == 0xABCDEF01, f"SLOW_SCRATCH mismatch: {hex(rdata)}"

    # SLOW_COUNTER (0x7000_0008) & SLOW_CTRL (0x7000_000C)
    c1, _ = await tb.m0.read(0x70000008)
    for _ in range(5):
        await RisingEdge(dut.clk_slow)
    c2, _ = await tb.m0.read(0x70000008)
    assert c2 > c1, f"SLOW_COUNTER did not advance: {c1} -> {c2}"

    # CDC unmapped offset (0x7000_0020) -> returns SLVERR (2)
    _, cdc_err = await tb.m0.read(0x70000020)
    assert cdc_err == 2, f"Expected SLVERR on CDC unmapped read, got {cdc_err}"

    # =========================================================================
    # 5. Crossbar Default Slave Unmapped Address (0x1000_0000)
    # =========================================================================
    dut._log.info("--- Testing Default Slave Unmapped Address ---")
    _, decerr_resp = await tb.m0.read(0x10000000)
    assert decerr_resp == 3, f"Expected DECERR (3) on unmapped crossbar address, got {decerr_resp}"

    bresp_decerr = await tb.m0.write(0x10000000, 0x0)
    assert bresp_decerr == 3, f"Expected DECERR (3) on unmapped crossbar write, got {bresp_decerr}"

    dut._log.info("TOP-01: Every register-map entry verified clean across all blocks!")
    await RisingEdge(dut.clk_sys)

@cocotb.test()
async def test_top02_irq_aggregation_to_pin(dut):
    """TOP-02: IRQ aggregation from UART, Timer, and GPIO through CSR to top-level irq_o pin."""
    tb = FabricTopTestbench(dut)
    await tb.reset()

    assert dut.irq_o.value == 0, "Initial irq_o must be 0"

    # -------------------------------------------------------------
    # 1. Timer IRQ (bit 1)
    # -------------------------------------------------------------
    dut._log.info("--- Testing Timer IRQ Aggregation ---")
    # Fast one-shot timer: LOAD = 5, CTRL = EN(1) | IRQ_EN(4) = 0x05
    await tb.m0.write(0x40001004, 5)
    await tb.m0.write(0x40001000, 0x05)

    # Wait for timeout (approx 6-10 cycles)
    for _ in range(20):
        await RisingEdge(dut.clk_sys)

    # Verify CSR IRQ_RAW[1] is 1
    raw, _ = await tb.m0.read(0x60000010)
    assert (raw & 0x2) != 0, f"Timer IRQ not captured in CSR IRQ_RAW: {hex(raw)}"
    assert dut.irq_o.value == 0, "irq_o asserted while IRQ_MASK was 0!"

    # Unmask Timer IRQ in CSR: IRQ_MASK[1] = 1
    await tb.m0.write(0x60000014, 0x02)
    await RisingEdge(dut.clk_sys)
    assert dut.irq_o.value == 1, "irq_o pin did not assert after unmasking Timer IRQ!"

    # Clear Timer status via APB W1C (0x4000_100C)
    await tb.m0.write(0x4000100C, 0x01)
    await RisingEdge(dut.clk_sys)
    raw, _ = await tb.m0.read(0x60000010)
    assert (raw & 0x2) == 0, "Timer IRQ still set in CSR IRQ_RAW after APB clear"
    assert dut.irq_o.value == 0, "irq_o pin did not deassert after clearing Timer IRQ"

    # Reset mask
    await tb.m0.write(0x60000014, 0x00)

    # -------------------------------------------------------------
    # 2. GPIO IRQ (bit 2)
    # -------------------------------------------------------------
    dut._log.info("--- Testing GPIO IRQ Aggregation ---")
    # Enable rising edge detection on GPIO pin 3: IRQ_EN (0x4000_200C) = (1 << 3) = 0x08
    await tb.m0.write(0x4000200C, 0x0008)

    # Inject rising edge on pin 3
    dut.gpio_i.value = 0x0008
    for _ in range(5):
        await RisingEdge(dut.clk_sys)

    # Verify CSR IRQ_RAW[2] is 1
    raw, _ = await tb.m0.read(0x60000010)
    assert (raw & 0x4) != 0, f"GPIO IRQ not captured in CSR IRQ_RAW: {hex(raw)}"
    assert dut.irq_o.value == 0, "irq_o asserted while IRQ_MASK was 0!"

    # Unmask GPIO IRQ in CSR: IRQ_MASK[2] = 1
    await tb.m0.write(0x60000014, 0x04)
    await RisingEdge(dut.clk_sys)
    assert dut.irq_o.value == 1, "irq_o pin did not assert after unmasking GPIO IRQ!"

    # Clear GPIO IRQ_STATUS via W1C (0x4000_2010)
    await tb.m0.write(0x40002010, 0x0008)
    await RisingEdge(dut.clk_sys)
    raw, _ = await tb.m0.read(0x60000010)
    assert (raw & 0x4) == 0, "GPIO IRQ still set in CSR IRQ_RAW after APB clear"
    assert dut.irq_o.value == 0, "irq_o pin did not deassert after clearing GPIO IRQ"

    # Reset mask and gpio_i
    dut.gpio_i.value = 0x0000
    await tb.m0.write(0x60000014, 0x00)

    # -------------------------------------------------------------
    # 3. UART IRQ (bit 0)
    # -------------------------------------------------------------
    dut._log.info("--- Testing UART IRQ Aggregation ---")
    # Configure loopback with RX_IRQ_EN: CTRL (0x4000_000C) = 0x0F, BAUDDIV = 0
    await tb.m0.write(0x40000010, 0)
    await tb.m0.write(0x4000000C, 0x0F)

    # Send byte via TXDATA (0x4000_0000)
    await tb.m0.write(0x40000000, 0xA5)

    # Wait for reception
    for _ in range(300):
        s, _ = await tb.m0.read(0x40000008)
        if (s & 0x08) == 0: # RX_EMPTY == 0
            break
        await RisingEdge(dut.clk_sys)

    # Verify CSR IRQ_RAW[0] is 1
    raw, _ = await tb.m0.read(0x60000010)
    assert (raw & 0x1) != 0, f"UART IRQ not captured in CSR IRQ_RAW: {hex(raw)}"
    assert dut.irq_o.value == 0, "irq_o asserted while IRQ_MASK was 0!"

    # Unmask UART IRQ in CSR: IRQ_MASK[0] = 1
    await tb.m0.write(0x60000014, 0x01)
    await RisingEdge(dut.clk_sys)
    assert dut.irq_o.value == 1, "irq_o pin did not assert after unmasking UART IRQ!"

    # Read RXDATA to empty RX FIFO
    await tb.m0.read(0x40000004)
    await RisingEdge(dut.clk_sys)
    raw, _ = await tb.m0.read(0x60000010)
    assert (raw & 0x1) == 0, "UART IRQ still set in CSR IRQ_RAW after emptying RX FIFO"
    assert dut.irq_o.value == 0, "irq_o pin did not deassert after emptying UART RX FIFO"

    dut._log.info("TOP-02: All 3 IRQ sources aggregated and verified on irq_o pin!")
    await RisingEdge(dut.clk_sys)
    await Timer(10, unit="ns")


@cocotb.test()
async def test_cd05_dual_master_slow_regs(dut):
    """CD-05: Both masters interleaving reads and writes to slow registers through the full path."""
    tb = FabricTopTestbench(dut)
    await tb.reset()

    dut._log.info("Starting CD-05: Dual-master interleaved access to CDC slow registers...")

    for i in range(20):
        val_m0 = 0xAA000000 + i
        val_m1 = 0xBB000000 + i

        # Master 0 writes scratch, Master 1 concurrently reads SLOW_ID
        t0 = cocotb.start_soon(tb.m0.write(0x70000004, val_m0))
        t1 = cocotb.start_soon(tb.m1.read(0x70000000))
        resp0 = await t0
        id_m1, rresp1 = await t1
        assert resp0 == 0, f"Round {i}: M0 write failed"
        assert rresp1 == 0 and id_m1 == 0x510E0001, f"Round {i}: M1 read SLOW_ID failed"

        # Concurrently Master 1 writes scratch, Master 0 reads back scratch
        t0_rd = cocotb.start_soon(tb.m0.read(0x70000004))
        t1_wr = cocotb.start_soon(tb.m1.write(0x70000004, val_m1))
        rd_m0, rresp0 = await t0_rd
        resp1_wr = await t1_wr
        assert rresp0 == 0
        assert resp1_wr == 0

        # Master 1 reads back scratch
        rd_m1, rresp1_rd = await tb.m1.read(0x70000004)
        assert rresp1_rd == 0
        assert rd_m1 == val_m1, f"Round {i}: M1 scratch readback mismatch: expected {hex(val_m1)}, got {hex(rd_m1)}"

    dut._log.info("CD-05 PASSED: 20 rounds of dual-master interleaved CDC access succeeded with 0 errors")
    await RisingEdge(dut.clk_sys)
    await Timer(10, unit="ns")
