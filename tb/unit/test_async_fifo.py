# L0 Unit Test for async_fifo
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_async_fifo_dual_clock(dut):
    """Verify dual-clock async FIFO across different clock ratios and data integrity."""
    dut._log.info("Starting test_async_fifo_dual_clock")

    # Start two independent clocks (wclk = 100 MHz [10 ns], rclk = 60 MHz [16.66 ns])
    cocotb.start_soon(Clock(dut.wclk, 10, unit="ns").start())
    cocotb.start_soon(Clock(dut.rclk, 17, unit="ns").start())

    # Apply resets in both domains
    dut.wrst_n.value = 0
    dut.rrst_n.value = 0
    dut.winc.value   = 0
    dut.rinc.value   = 0
    dut.wdata.value  = 0

    await Timer(50, unit="ns")
    dut.wrst_n.value = 1
    dut.rrst_n.value = 1
    await RisingEdge(dut.wclk)
    await RisingEdge(dut.rclk)

    # Allow synchronizers to settle
    for _ in range(5):
        await RisingEdge(dut.rclk)
    assert dut.rempty.value == 1, "Expected rempty=1 after reset settling"
    assert dut.wfull.value == 0,  "Expected wfull=0 after reset settling"

    # Push 4 items (depth is 4)
    test_items = [0xA1B2C3D4, 0x11223344, 0x55667788, 0x99AABBCC]
    for val in test_items:
        dut.winc.value = 1
        dut.wdata.value = val
        await RisingEdge(dut.wclk)

    dut.winc.value = 0
    await RisingEdge(dut.wclk)
    await Timer(1, unit="ns")
    assert dut.wfull.value == 1, "Expected wfull=1 after writing 4 items"

    # Wait for write pointer to cross into read domain (2-FF stages)
    for _ in range(5):
        await RisingEdge(dut.rclk)
    await Timer(1, unit="ns")
    assert dut.rempty.value == 0, "Expected rempty=0 after items synchronized"

    # FWFT Read: first item is already valid on rdata
    received_items = []
    for i in range(4):
        await Timer(1, unit="ns")
        received_items.append(int(dut.rdata.value))
        dut.rinc.value = 1
        await RisingEdge(dut.rclk)

    dut.rinc.value = 0
    await Timer(1, unit="ns")
    assert received_items == test_items, f"Data mismatch! Expected {test_items}, got {received_items}"

    # Wait for read pointer to cross into write domain
    for _ in range(6):
        await RisingEdge(dut.wclk)
    await Timer(1, unit="ns")
    assert dut.wfull.value == 0, "Expected wfull=0 after reading all items"

    for _ in range(4):
        await RisingEdge(dut.rclk)
    await Timer(1, unit="ns")
    assert dut.rempty.value == 1, "Expected rempty=1 after popping all items"

    dut._log.info("test_async_fifo_dual_clock PASSED")
