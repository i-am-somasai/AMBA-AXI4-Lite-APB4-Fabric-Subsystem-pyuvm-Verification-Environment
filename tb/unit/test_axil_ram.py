# L0 Unit Test for axil_ram
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from axil_driver import AxilMasterDriver

@cocotb.test()
async def test_axil_ram_operations(dut):
    """Verify RAM reads, writes, byte enables, and out-of-range SLVERR."""
    dut._log.info("Starting test_axil_ram_operations")
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.rst_n.value = 0
    driver = AxilMasterDriver(dut, dut.clk)
    await Timer(25, unit="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    RESP_OKAY   = 0b00
    RESP_SLVERR = 0b10

    # 1. Basic word write and read
    addr = 0x5000_0010
    resp = await driver.write(addr, 0xDEADBEEF, strb=0xF)
    assert resp == RESP_OKAY, f"Expected OKAY, got {resp:#b}"

    rdata, rresp = await driver.read(addr)
    assert rresp == RESP_OKAY, f"Expected OKAY read, got {rresp:#b}"
    assert rdata == 0xDEADBEEF, f"Expected 0xDEADBEEF, got {rdata:#x}"

    # 2. Byte strobe tests
    # Write lower byte only (strb=0b0001)
    addr_strobe = 0x5000_0020
    await driver.write(addr_strobe, 0x11223344, strb=0xF)

    # Modify only byte 1 (bits [15:8], strb=0b0010)
    await driver.write(addr_strobe, 0x0000AA00, strb=0b0010)
    rdata, _ = await driver.read(addr_strobe)
    assert rdata == 0x1122AA44, f"Expected 0x1122AA44, got {rdata:#x}"

    # Modify upper half-word (bits [31:16], strb=0b1100)
    await driver.write(addr_strobe, 0xBBCC0000, strb=0b1100)
    rdata, _ = await driver.read(addr_strobe)
    assert rdata == 0xBBCCAA44, f"Expected 0xBBCCAA44, got {rdata:#x}"

    # 3. Out-of-range tests (RAM_DEPTH=256 words -> offset 256*4 = 0x400)
    oor_addr = 0x5000_0400
    resp = await driver.write(oor_addr, 0xBAD0BAD0, strb=0xF)
    assert resp == RESP_SLVERR, f"Expected SLVERR on OOR write, got {resp:#b}"

    rdata, rresp = await driver.read(oor_addr)
    assert rresp == RESP_SLVERR, f"Expected SLVERR on OOR read, got {rresp:#b}"
    assert rdata == 0, f"Expected rdata=0 on OOR read, got {rdata:#x}"

    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")

    dut._log.info("test_axil_ram_operations PASSED")
