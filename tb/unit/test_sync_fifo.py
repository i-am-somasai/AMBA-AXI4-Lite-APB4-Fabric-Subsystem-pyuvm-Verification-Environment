# L0 Unit Test for sync_fifo
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_sync_fifo_all(dut):
    """Test full, empty, count, overflow, underflow, and simultaneous push/pop."""
    dut._log.info("Starting test_sync_fifo_all")
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    depth = 8

    # Reset
    dut.rst_n.value = 0
    dut.push.value  = 0
    dut.pop.value   = 0
    dut.wdata.value = 0
    await Timer(25, unit="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # Check reset state
    assert dut.empty.value == 1, "Expected empty=1 after reset"
    assert dut.full.value == 0, "Expected full=0 after reset"
    assert int(dut.count.value) == 0, "Expected count=0 after reset"

    # Underflow check: pop when empty
    dut.pop.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert dut.underflow.value == 1, "Expected underflow=1 when popping empty FIFO"
    dut.pop.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert dut.underflow.value == 0

    # Push depth items (0x10 to 0x17)
    test_data = [0x10 + i for i in range(depth)]
    for i, val in enumerate(test_data):
        dut.push.value = 1
        dut.wdata.value = val
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.count.value) == i + 1, f"Expected count={i+1}, got {dut.count.value}"
        assert dut.empty.value == 0

    dut.push.value = 0
    await Timer(1, unit="ns")
    assert dut.full.value == 1, "Expected full=1 when filled to depth"

    # Overflow check: push when full
    dut.push.value = 1
    dut.wdata.value = 0xFF
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert dut.overflow.value == 1, "Expected overflow=1 when pushing full FIFO"
    assert int(dut.count.value) == depth
    dut.push.value = 0

    # Pop depth items and verify values
    for i, expected in enumerate(test_data):
        dut.pop.value = 1
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.rdata.value) == expected, f"Pop {i}: expected 0x{expected:02x}, got 0x{int(dut.rdata.value):02x}"
        assert int(dut.count.value) == depth - 1 - i

    dut.pop.value = 0
    await Timer(1, unit="ns")
    assert dut.empty.value == 1
    assert dut.full.value == 0

    # Simultaneous push and pop when partially full
    # Push 2 items first
    dut.push.value = 1
    dut.wdata.value = 0xAA
    await RisingEdge(dut.clk)
    dut.wdata.value = 0xBB
    await RisingEdge(dut.clk)
    dut.push.value = 0
    await Timer(1, unit="ns")
    assert int(dut.count.value) == 2

    # Simultaneous: push 0xCC and pop (should read 0xAA, count remains 2)
    dut.push.value = 1
    dut.wdata.value = 0xCC
    dut.pop.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.rdata.value) == 0xAA, f"Expected 0xAA, got {hex(int(dut.rdata.value))}"
    assert int(dut.count.value) == 2, f"Expected count=2 on simultaneous push/pop, got {int(dut.count.value)}"

    dut.push.value = 0
    dut.pop.value = 0
    await RisingEdge(dut.clk)

    dut._log.info("test_sync_fifo_all PASSED")
