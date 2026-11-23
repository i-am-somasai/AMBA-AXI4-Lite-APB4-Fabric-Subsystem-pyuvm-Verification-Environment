# L0 Unit Test for rst_sync (2-FF reset synchronizer)
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

@cocotb.test()
async def test_rst_sync_basic(dut):
    """Verify asynchronous assertion and 2-cycle synchronous deassertion."""
    dut._log.info("Starting test_rst_sync_basic")
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # Initially reset is asserted
    dut.rst_n_in.value = 0
    await Timer(1, unit="ns")
    assert dut.rst_n_out.value == 0, f"Expected rst_n_out=0 immediately upon rst_n_in=0, got {dut.rst_n_out.value}"

    # Wait several clock cycles with reset asserted
    for _ in range(3):
        await RisingEdge(dut.clk)
    assert dut.rst_n_out.value == 0

    # Deassert reset asynchronously (mid-clock cycle)
    await Timer(3, unit="ns")
    dut.rst_n_in.value = 1

    # First clock edge after deassertion: sync_q1=1, sync_q2 (rst_n_out)=0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert dut.rst_n_out.value == 0, "rst_n_out must remain 0 after only 1 clock edge"

    # Second clock edge after deassertion: sync_q2 (rst_n_out)=1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert dut.rst_n_out.value == 1, "rst_n_out must be 1 after exactly 2 clock edges"

    # Now verify asynchronous re-assertion (does not wait for clock)
    await Timer(4, unit="ns")
    dut.rst_n_in.value = 0
    await Timer(1, unit="ns")
    assert dut.rst_n_out.value == 0, "rst_n_out must assert asynchronously without waiting for clock"

    dut._log.info("test_rst_sync_basic PASSED")
