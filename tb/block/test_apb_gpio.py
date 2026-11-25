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
    """GP-02: 2-FF input synchronization latency on IN register (0x08) for 0->1, 1->0, and 1-cycle pulse."""
    tb = GpioTestbench(dut)
    await tb.reset()

    async def measure_in_after_step(target_val, init_val, offset_cycles):
        """Return IN register via APB with SETUP capture aligned to +offset_cycles after driving gpio_i."""
        assert offset_cycles >= 1
        dut.gpio_i.value = init_val
        for _ in range(3):
            await RisingEdge(dut.clk)

        # Drive step immediately after clock edge T0
        dut.gpio_i.value = target_val
        for _ in range(offset_cycles - 1):
            await RisingEdge(dut.clk)
        rdata, err = await tb.apb.read(addr=0x08)
        assert err == 0, f"APB read IN failed: pslverr={err}"
        return rdata

    async def measure_in_after_pulse(pulse_val, offset_cycles):
        """Drive a 1-cycle gpio_i pulse and read IN aligned to +offset_cycles (+1, +2, or +3)."""
        assert offset_cycles >= 1
        dut.gpio_i.value = 0
        for _ in range(3):
            await RisingEdge(dut.clk)

        # Drive pulse after T0; launch APB read at T0 for offset==1 so SETUP starts at T1
        dut.gpio_i.value = pulse_val
        if offset_cycles == 1:
            read_task = cocotb.start_soon(tb.apb.read(addr=0x08))
            await RisingEdge(dut.clk)
            dut.gpio_i.value = 0
            rdata, err = await read_task
        else:
            await RisingEdge(dut.clk)
            dut.gpio_i.value = 0
            for _ in range(offset_cycles - 2):
                await RisingEdge(dut.clk)
            rdata, err = await tb.apb.read(addr=0x08)
        assert err == 0, f"APB read IN failed: pslverr={err}"
        return rdata

    # 1. Verify 0 -> 1 step: unchanged at +1 cycle, updated at +2 cycles
    step_val = 0xBEEF
    in_rise_p1 = await measure_in_after_step(target_val=step_val, init_val=0x0000, offset_cycles=1)
    assert in_rise_p1 == 0x0000, (
        f"GP-02 0->1 (+1 cycle): expected unchanged 0x0000, got {hex(in_rise_p1)}"
    )
    in_rise_p2 = await measure_in_after_step(target_val=step_val, init_val=0x0000, offset_cycles=2)
    assert in_rise_p2 == step_val, (
        f"GP-02 0->1 (+2 cycles): expected {hex(step_val)}, got {hex(in_rise_p2)}"
    )

    # 2. Verify 1 -> 0 step: unchanged at +1 cycle, cleared at +2 cycles
    in_fall_p1 = await measure_in_after_step(target_val=0x0000, init_val=step_val, offset_cycles=1)
    assert in_fall_p1 == step_val, (
        f"GP-02 1->0 (+1 cycle): expected unchanged {hex(step_val)}, got {hex(in_fall_p1)}"
    )
    in_fall_p2 = await measure_in_after_step(target_val=0x0000, init_val=step_val, offset_cycles=2)
    assert in_fall_p2 == 0x0000, (
        f"GP-02 1->0 (+2 cycles): expected 0x0000, got {hex(in_fall_p2)}"
    )

    # 3. Verify 1-cycle pulse: unchanged (0) at +1, high at +2, back to 0 at +3
    pulse_val = 0xCAFE
    pulse_p1 = await measure_in_after_pulse(pulse_val=pulse_val, offset_cycles=1)
    assert pulse_p1 == 0x0000, (
        f"GP-02 1-cycle pulse (+1 cycle): expected 0x0000, got {hex(pulse_p1)}"
    )
    pulse_p2 = await measure_in_after_pulse(pulse_val=pulse_val, offset_cycles=2)
    assert pulse_p2 == pulse_val, (
        f"GP-02 1-cycle pulse (+2 cycles): expected {hex(pulse_val)}, got {hex(pulse_p2)}"
    )
    pulse_p3 = await measure_in_after_pulse(pulse_val=pulse_val, offset_cycles=3)
    assert pulse_p3 == 0x0000, (
        f"GP-02 1-cycle pulse (+3 cycles): expected 0x0000, got {hex(pulse_p3)}"
    )

    # Secondary read-only check of internal synchronizer flop timing on a single 1-cycle pulse
    if hasattr(dut, "sync_gpio_q2"):
        dut.gpio_i.value = 0
        for _ in range(3):
            await RisingEdge(dut.clk)
        dut.gpio_i.value = pulse_val
        await RisingEdge(dut.clk)
        dut.gpio_i.value = 0
        await cocotb.triggers.ReadOnly()
        assert int(dut.sync_gpio_q2.value) == 0x0000, (
            f"GP-02 flop check (+1): sync_gpio_q2 changed early: {hex(int(dut.sync_gpio_q2.value))}"
        )
        await RisingEdge(dut.clk)
        await cocotb.triggers.ReadOnly()
        assert int(dut.sync_gpio_q2.value) == pulse_val, (
            f"GP-02 flop check (+2): sync_gpio_q2 missed pulse: {hex(int(dut.sync_gpio_q2.value))}"
        )
        await RisingEdge(dut.clk)
        await cocotb.triggers.ReadOnly()
        assert int(dut.sync_gpio_q2.value) == 0x0000, (
            f"GP-02 flop check (+3): sync_gpio_q2 stayed high: {hex(int(dut.sync_gpio_q2.value))}"
        )

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
