# tb/block/test_apb_timer.py
# Directed tests for APB Timer Peripheral (TM-01, TM-02, TM-03)
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ReadOnly
from models.apb_driver import ApbMasterDriver

class TimerTestbench:
    def __init__(self, dut):
        self.dut = dut
        self.apb = ApbMasterDriver(dut, dut.clk)
        cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    async def reset(self):
        self.dut.rst_n.value = 0
        self.apb.init_signals()
        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        self.dut.rst_n.value = 1
        await RisingEdge(self.dut.clk)

@cocotb.test()
async def test_tm01_oneshot_countdown(dut):
    """TM-01: One-shot countdown: timeout after exactly LOAD+1 cycles."""
    tb = TimerTestbench(dut)
    await tb.reset()

    load_val = 10
    # 1. Write LOAD register (0x04)
    err = await tb.apb.write(addr=0x04, data=load_val)
    assert err == 0, f"Write LOAD failed: {err}"

    # Verify LOAD reads back correctly
    rdata, err = await tb.apb.read(addr=0x04)
    assert err == 0 and rdata == load_val, f"LOAD readback mismatch: {rdata}"

    # 2. Enable Timer in one-shot mode with IRQ enabled: CTRL (0x00) = EN(1) | IRQ_EN(4) = 0x05
    err = await tb.apb.write(addr=0x00, data=0x05)
    assert err == 0, f"Write CTRL failed: {err}"

    # Count cycles until timer_irq is asserted
    cycles = 0
    timeout_limit = 50
    while cycles < timeout_limit:
        await RisingEdge(dut.clk)
        await ReadOnly()
        cycles += 1
        if dut.timer_irq.value:
            break

    assert dut.timer_irq.value == 1, f"Timer IRQ did not assert within {timeout_limit} cycles"
    # Timeout period is LOAD + 1 cycles
    dut._log.info(f"One-shot timer fired after {cycles} cycles (LOAD={load_val})")
    assert cycles == load_val + 1, f"Expected {load_val+1} cycles, got {cycles}"

    # Check STATUS (0x0C): bit 0 TIMEOUT must be 1
    status, _ = await tb.apb.read(addr=0x0C)
    assert (status & 0x1) == 1, f"Expected TIMEOUT=1 in STATUS, got {hex(status)}"

    # Check CTRL (0x00): in one-shot mode, EN should be auto-cleared
    ctrl, _ = await tb.apb.read(addr=0x00)
    assert (ctrl & 0x1) == 0, f"Expected EN=0 after one-shot timeout, got {hex(ctrl)}"

    await RisingEdge(dut.clk)

@cocotb.test()
async def test_tm02_periodic_countdown(dut):
    """TM-02: Periodic mode: reloads and fires repeatedly with exact period."""
    tb = TimerTestbench(dut)
    await tb.reset()

    load_val = 5
    await tb.apb.write(addr=0x04, data=load_val) # LOAD = 5

    # CTRL = EN(1) | PERIODIC(2) | IRQ_EN(4) = 0x07
    await tb.apb.write(addr=0x00, data=0x07)

    # Monitor 3 consecutive periods
    for period in range(3):
        # Wait for IRQ assertion
        cycles = 0
        while not dut.timer_irq.value and cycles < 20:
            await RisingEdge(dut.clk)
            cycles += 1

        assert dut.timer_irq.value == 1, f"Period {period}: IRQ did not assert"
        dut._log.info(f"Periodic interval {period}: fired after {cycles} cycles")

        # Clear TIMEOUT via W1C
        await tb.apb.write(addr=0x0C, data=0x01)
        await RisingEdge(dut.clk)
        assert dut.timer_irq.value == 0, f"Period {period}: IRQ did not clear after W1C"

    # Stop timer
    await tb.apb.write(addr=0x00, data=0x00)
    await RisingEdge(dut.clk)

@cocotb.test()
async def test_tm03_w1c_timeout_and_irq_clear(dut):
    """TM-03: W1C of TIMEOUT bit clears STATUS[0] and timer_irq."""
    tb = TimerTestbench(dut)
    await tb.reset()

    # Fast timeout: LOAD = 2, CTRL = 0x05 (EN | IRQ_EN)
    await tb.apb.write(addr=0x04, data=2)
    await tb.apb.write(addr=0x00, data=0x05)

    # Wait for IRQ
    while not dut.timer_irq.value:
        await RisingEdge(dut.clk)

    assert dut.timer_irq.value == 1
    status, _ = await tb.apb.read(addr=0x0C)
    assert (status & 0x1) == 1

    # Write 0 to STATUS: should NOT clear W1C bit
    await tb.apb.write(addr=0x0C, data=0x00)
    status, _ = await tb.apb.read(addr=0x0C)
    assert (status & 0x1) == 1, "Writing 0 should not clear W1C bit"
    assert dut.timer_irq.value == 1

    # Write 1 to STATUS: must clear W1C bit
    await tb.apb.write(addr=0x0C, data=0x01)
    status, _ = await tb.apb.read(addr=0x0C)
    assert (status & 0x1) == 0, "Writing 1 must clear W1C bit"
    assert dut.timer_irq.value == 0, "IRQ must deassert after clearing TIMEOUT"

    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")
