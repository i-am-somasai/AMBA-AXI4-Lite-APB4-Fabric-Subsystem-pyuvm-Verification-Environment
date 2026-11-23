# L0 Unit Test for axil_default_slave
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from axil_driver import AxilMasterDriver

@cocotb.test()
async def test_axil_default_slave_all(dut):
    """Verify that default slave returns DECERR on writes and reads in all channel arrival orders."""
    dut._log.info("Starting test_axil_default_slave_all")
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.rst_n.value = 0
    driver = AxilMasterDriver(dut, dut.clk)
    await Timer(25, unit="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    RESP_DECERR = 0b11

    # 1. Write with simultaneous AW and W
    resp = await driver.write(0x1000_0000, 0xDEADBEEF, order="simultaneous")
    assert resp == RESP_DECERR, f"Expected DECERR (0b11), got {resp:#b}"

    # 2. Write with AW arriving first
    resp = await driver.write(0x2000_0000, 0x12345678, order="aw_first")
    assert resp == RESP_DECERR, f"Expected DECERR (0b11), got {resp:#b}"

    # 3. Write with W arriving first
    resp = await driver.write(0x3000_0000, 0x87654321, order="w_first")
    assert resp == RESP_DECERR, f"Expected DECERR (0b11), got {resp:#b}"

    # 4. Read from unmapped address
    rdata, rresp = await driver.read(0x9000_0000)
    assert rresp == RESP_DECERR, f"Expected DECERR (0b11) on read, got {rresp:#b}"
    assert rdata == 0, f"Expected rdata=0 on DECERR read, got {rdata:#x}"

    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")

    dut._log.info("test_axil_default_slave_all PASSED")
