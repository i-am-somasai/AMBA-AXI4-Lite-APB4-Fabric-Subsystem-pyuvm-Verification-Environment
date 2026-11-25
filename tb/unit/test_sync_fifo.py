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

    # Push depth items with diverse bit patterns exercising all bit positions
    test_data = [0x55, 0xAA, 0x0F, 0xF0, 0xC3, 0x3C, 0x81, 0x7E]
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

    # Walking 1s pass across all 8 FIFO depths
    walking_ones = [(1 << i) & 0xFF for i in range(depth)]
    for val in walking_ones:
        dut.push.value = 1
        dut.wdata.value = val
        await RisingEdge(dut.clk)
    dut.push.value = 0
    for i, exp in enumerate(walking_ones):
        dut.pop.value = 1
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.rdata.value) == exp, f"Walking 1s pop {i}: expected {exp:#x}, got {int(dut.rdata.value):#x}"
    dut.pop.value = 0

    # Walking 0s pass across all 8 FIFO depths
    walking_zeros = [(~(1 << i)) & 0xFF for i in range(depth)]
    for val in walking_zeros:
        dut.push.value = 1
        dut.wdata.value = val
        await RisingEdge(dut.clk)
    dut.push.value = 0
    for i, exp in enumerate(walking_zeros):
        dut.pop.value = 1
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.rdata.value) == exp, f"Walking 0s pop {i}: expected {exp:#x}, got {int(dut.rdata.value):#x}"
    dut.pop.value = 0

    # Bit-pair independence across all 8 FIFO slots with 0-cycle and 1-cycle idle hold
    slot_vals = [(0x08 | i) for i in range(depth)]
    for hold_cycles in (0, 1):
        for val in slot_vals:
            dut.push.value = 1
            dut.wdata.value = val
            await RisingEdge(dut.clk)
        dut.push.value = 0
        for _ in range(hold_cycles):
            await RisingEdge(dut.clk)
        for i, exp in enumerate(slot_vals):
            dut.pop.value = 1
            await RisingEdge(dut.clk)
            await Timer(1, unit="ns")
            assert int(dut.rdata.value) == exp, (
                f"Slot independence (hold={hold_cycles}) pop {i}: expected {exp:#x}, got {int(dut.rdata.value):#x}"
            )
        dut.pop.value = 0

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

    # Drain remaining 2 entries (0xBB, 0xCC) cleanly
    for exp in (0xBB, 0xCC):
        dut.pop.value = 1
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.rdata.value) == exp, f"Drain expected {exp:#x}, got {int(dut.rdata.value):#x}"
    dut.pop.value = 0
    await Timer(1, unit="ns")
    assert int(dut.empty.value) == 1 and int(dut.count.value) == 0

    # Simultaneous push+pop when EMPTY (should push 0x5A, count=1, underflow=1)
    dut.push.value = 1
    dut.pop.value = 1
    dut.wdata.value = 0x5A
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.count.value) == 1 and int(dut.underflow.value) == 1
    dut.push.value = 0
    dut.pop.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.rdata.value) == 0x5A and int(dut.empty.value) == 1
    dut.pop.value = 0

    # Full-depth 0xFF and 0x00 passes across non-zero pointer offsets + simultaneous push+pop when FULL
    for fill_pat in ([0xFF] * depth, [0x00] * depth, [0xA5 ^ (i * 0x11) for i in range(depth)]):
        for val in fill_pat:
            dut.push.value = 1
            dut.wdata.value = val
            await RisingEdge(dut.clk)
        dut.push.value = 0
        await Timer(1, unit="ns")
        assert int(dut.full.value) == 1 and int(dut.count.value) == depth

        # Simultaneous push+pop when FULL: pushes 0xE7, pops fill_pat[0], count remains 8, no overflow/underflow
        dut.push.value = 1
        dut.pop.value = 1
        dut.wdata.value = 0xE7
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.rdata.value) == fill_pat[0]
        assert int(dut.count.value) == depth and int(dut.full.value) == 1
        assert int(dut.overflow.value) == 0 and int(dut.underflow.value) == 0
        dut.push.value = 0
        dut.pop.value = 0

        for exp in fill_pat[1:] + [0xE7]:
            dut.pop.value = 1
            await RisingEdge(dut.clk)
            await Timer(1, unit="ns")
            assert int(dut.rdata.value) == exp, f"Wrap read expected {exp:#x}, got {int(dut.rdata.value):#x}"
        dut.pop.value = 0
        await Timer(1, unit="ns")
        assert int(dut.empty.value) == 1

    dut._log.info("test_sync_fifo_all PASSED")
