"""
test_probe_peripherals.py - Probe Test for Peripherals (Spec Section 7.3)
Tests:
- Timer period: timeout after exactly LOAD+1 cycles (Spec Section 7.3.2)
- GPIO input synchronizer latency: 2-cycle latency on IN (Spec Section 7.3.3)
- UART loopback: byte loopback verification (Spec Section 7.3.1)
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from probe_driver import ProbeAxilDriver

async def reset_dut(dut):
    dut.gpio_i.value = 0
    dut.uart_rx.value = 1
    ProbeAxilDriver(dut, dut.clk_sys, prefix="s0_axil")
    ProbeAxilDriver(dut, dut.clk_sys, prefix="s1_axil")
    cocotb.start_soon(Clock(dut.clk_sys, 10, unit="ns").start())
    cocotb.start_soon(Clock(dut.clk_slow, 25, unit="ns").start())
    dut.rst_n.value = 0
    for _ in range(10):
        await RisingEdge(dut.clk_sys)
    dut.rst_n.value = 1
    for _ in range(10):
        await RisingEdge(dut.clk_sys)

@cocotb.test()
async def test_probe_timer_exact_period(dut):
    """Timer timeout period must equal exactly LOAD + 1 cycles (Spec line 371)."""
    await reset_dut(dut)
    drv = ProbeAxilDriver(dut, dut.clk_sys, prefix="s0_axil")

    # Enable Timer IRQ in CSR (bit 1 of 0x6000_0014)
    await drv.write(0x60000014, 0x02)

    # Set LOAD = 10 (timeout should occur after exactly 11 cycles)
    LOAD_VAL = 10
    await drv.write(0x40001004, LOAD_VAL) # LOAD register
    
    # Enable timer in one-shot mode: CTRL[0]=1, CTRL[1]=0, CTRL[2]=1 (IRQ_EN) -> 0x05
    await drv.write(0x40001000, 0x05)

    # Monitor cycles until irq_o asserts
    cycles = 0
    while not dut.irq_o.value:
        await RisingEdge(dut.clk_sys)
        cycles += 1
        if cycles > 50:
            raise TimeoutError("Timer failed to timeout via irq_o")

    dut._log.info(f"Timer LOAD={LOAD_VAL} timed out in {cycles} cycles")
    assert cycles == LOAD_VAL + 1, f"Spec Section 7.3.2: Expected exactly {LOAD_VAL+1} cycles, got {cycles}"
    await Timer(100, unit="ns")

@cocotb.test()
async def test_probe_gpio_sync_latency(dut):
    """GPIO input synchronizer latency: 2-FF latency (Spec line 381, 505)."""
    await reset_dut(dut)
    drv = ProbeAxilDriver(dut, dut.clk_sys, prefix="s0_axil")

    # Initially gpio_i = 0
    dut.gpio_i.value = 0
    for _ in range(5):
        await RisingEdge(dut.clk_sys)

    rdata, _ = await drv.read(0x40002008) # IN register
    assert rdata == 0, f"Initial IN not 0: {hex(rdata)}"

    # Drive gpio_i = 0x0001
    dut.gpio_i.value = 0x0001
    # Cycle 1: samples into sync_gpio_q1
    await RisingEdge(dut.clk_sys)
    rdata_c1, _ = await drv.read(0x40002008)
    # Cycle 2: samples into sync_gpio_q2 (now visible on IN)
    await RisingEdge(dut.clk_sys)
    rdata_c2, _ = await drv.read(0x40002008)

    dut._log.info(f"GPIO sync: cycle 1 IN={hex(rdata_c1)}, cycle 2 IN={hex(rdata_c2)}")
    assert (rdata_c2 & 0x0001) == 1, "GPIO input not visible on IN after 2 clock cycles"
    await Timer(100, unit="ns")

@cocotb.test()
async def test_probe_uart_loopback(dut):
    """UART loopback transmission of bytes (Spec line 358, 496)."""
    await reset_dut(dut)
    drv = ProbeAxilDriver(dut, dut.clk_sys, prefix="s0_axil")

    # BAUDDIV = 0 (16 clk ticks per bit)
    await drv.write(0x40000010, 0)
    # CTRL = TX_EN(1) | RX_EN(2) | LOOPBACK(4) = 0x07
    await drv.write(0x4000000C, 0x07)

    # Send 0x42
    await drv.write(0x40000000, 0x42)

    # Wait for reception (poll STATUS[3] RX_EMPTY == 0)
    for _ in range(300):
        status, _ = await drv.read(0x40000008)
        if ((status >> 3) & 1) == 0:
            break
        await RisingEdge(dut.clk_sys)

    assert ((status >> 3) & 1) == 0, "UART loopback byte not received in RX FIFO"
    rx_data, _ = await drv.read(0x40000004)
    assert (rx_data & 0xFF) == 0x42, f"UART loopback mismatch: expected 0x42, got {hex(rx_data & 0xFF)}"
    dut._log.info("UART loopback successfully verified byte 0x42")
    await Timer(100, unit="ns")
