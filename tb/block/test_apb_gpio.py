# tb/block/test_apb_gpio.py
# Directed tests for APB GPIO Peripheral (GP-01, GP-02, GP-03)
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from models.apb_driver import ApbMasterDriver

class GpioTestbench:
    def __init__(self, dut):
        self.dut = dut
        self.apb = ApbMasterDriver(dut, dut.clk)
        self.dut.gpio_i.value = 0
        cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    async def reset(self):
        self.dut.rst_n.value = 0
        self.dut.gpio_i.value = 0
        self.apb.init_signals()
        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        self.dut.rst_n.value = 1
        await RisingEdge(self.dut.clk)

@cocotb.test()
async def test_gp01_direction_and_out(dut):
    """GP-01: Verify DIR and OUT registers control gpio_dir and gpio_o."""
    tb = GpioTestbench(dut)
    await tb.reset()

    # 1. Write DIR register (0x00)
    dir_val = 0xA5A5
    err = await tb.apb.write(addr=0x00, data=dir_val)
    assert err == 0, f"Write DIR failed: {err}"
    assert int(dut.gpio_dir.value) == dir_val, f"gpio_dir mismatch: {hex(dut.gpio_dir.value)}"

    rdata, err = await tb.apb.read(addr=0x00)
    assert err == 0 and rdata == dir_val, f"DIR readback mismatch: {hex(rdata)}"

    # 2. Write OUT register (0x04)
    out_val = 0x5A5A
    err = await tb.apb.write(addr=0x04, data=out_val)
    assert err == 0, f"Write OUT failed: {err}"
    assert int(dut.gpio_o.value) == out_val, f"gpio_o mismatch: {hex(dut.gpio_o.value)}"

    rdata, err = await tb.apb.read(addr=0x04)
    assert err == 0 and rdata == out_val, f"OUT readback mismatch: {hex(rdata)}"

    await RisingEdge(dut.clk)

@cocotb.test()
async def test_gp02_input_sync_latency(dut):
    """GP-02: 2-FF input synchronization latency on IN register (0x08)."""
    tb = GpioTestbench(dut)
    await tb.reset()

    # Initial state: gpio_i is 0
    rdata, _ = await tb.apb.read(addr=0x08)
    assert rdata == 0, f"Initial IN not 0: {hex(rdata)}"

    # Set gpio_i to 0xBEEF
    input_val = 0xBEEF
    await RisingEdge(dut.clk)
    dut.gpio_i.value = input_val

    # Cycle 1: still in synchronizer flop 1
    await RisingEdge(dut.clk)

    # Cycle 2: synchronizer flop 2 latches input_val
    await RisingEdge(dut.clk)

    # Read IN register
    rdata, _ = await tb.apb.read(addr=0x08)
    assert rdata == input_val, f"IN register after 2-FF latency mismatch: expected {hex(input_val)}, got {hex(rdata)}"

    await RisingEdge(dut.clk)

@cocotb.test()
async def test_gp03_rising_edge_irq_and_w1c(dut):
    """GP-03: Rising-edge IRQ detection, masking, and W1C clearing."""
    tb = GpioTestbench(dut)
    await tb.reset()

    # Enable IRQ on pin 2 and pin 5: IRQ_EN = (1 << 2) | (1 << 5) = 0x0024
    irq_mask = 0x0024
    await tb.apb.write(addr=0x0C, data=irq_mask)

    # Verify no spurious IRQ initially
    assert dut.gpio_irq.value == 0

    # 1. Drive rising edge on unmasked pin 1: should NOT assert gpio_irq
    dut.gpio_i.value = 0x0002
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert dut.gpio_irq.value == 0, "Unmasked pin 1 asserted IRQ!"

    # 2. Drive rising edge on masked pin 2: should assert gpio_irq
    dut.gpio_i.value = 0x0006 # Pin 1 and Pin 2 high
    for _ in range(4):
        await RisingEdge(dut.clk)

    assert dut.gpio_irq.value == 1, "gpio_irq not asserted on enabled pin 2 rising edge"
    status, _ = await tb.apb.read(addr=0x10)
    assert (status & (1 << 2)) != 0, f"Pin 2 not set in IRQ_STATUS: {hex(status)}"

    # 3. W1C clearing: write 1 to bit 2
    await tb.apb.write(addr=0x10, data=(1 << 2))
    status, _ = await tb.apb.read(addr=0x10)
    assert (status & (1 << 2)) == 0, f"Pin 2 did not clear in IRQ_STATUS: {hex(status)}"
    assert dut.gpio_irq.value == 0, "gpio_irq did not deassert after W1C clear"

    # 4. Falling edge should NOT trigger IRQ
    dut.gpio_i.value = 0x0000
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert dut.gpio_irq.value == 0, "Falling edge caused false IRQ!"

    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")
