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
    # Write initial reference value
    addr_strobe = 0x5000_0020
    await driver.write(addr_strobe, 0x11223344, strb=0xF)

    # Modify only byte 0 (bits [7:0], strb=0b0001)
    await driver.write(addr_strobe, 0x00000055, strb=0b0001)
    rdata, _ = await driver.read(addr_strobe)
    assert rdata == 0x11223355, f"Expected 0x11223355, got {rdata:#x}"

    # Modify only byte 1 (bits [15:8], strb=0b0010)
    await driver.write(addr_strobe, 0x0000AA00, strb=0b0010)
    rdata, _ = await driver.read(addr_strobe)
    assert rdata == 0x1122AA55, f"Expected 0x1122AA55, got {rdata:#x}"

    # Modify only byte 2 (bits [23:16], strb=0b0100)
    await driver.write(addr_strobe, 0x00770000, strb=0b0100)
    rdata, _ = await driver.read(addr_strobe)
    assert rdata == 0x1177AA55, f"Expected 0x1177AA55, got {rdata:#x}"

    # Modify only byte 3 (bits [31:24], strb=0b1000)
    await driver.write(addr_strobe, 0x88000000, strb=0b1000)
    rdata, _ = await driver.read(addr_strobe)
    assert rdata == 0x8877AA55, f"Expected 0x8877AA55, got {rdata:#x}"

    # Modify upper half-word (bits [31:16], strb=0b1100)
    await driver.write(addr_strobe, 0xBBCC0000, strb=0b1100)
    rdata, _ = await driver.read(addr_strobe)
    assert rdata == 0xBBCCAA55, f"Expected 0xBBCCAA55, got {rdata:#x}"

    # 3. Comprehensive multi-address memory sweep across depth
    # Addresses sampled across 256 words: 0, 1, 16, 64, 128, 206, 255
    sweep_indices = [0, 1, 16, 64, 128, 206, 255]
    for idx in sweep_indices:
        w_addr = 0x5000_0000 + (idx * 4)
        val = 0xA5A50000 ^ (idx * 0x01010101) ^ 0x5A5A
        val = val & 0xFFFFFFFF
        resp = await driver.write(w_addr, val, strb=0xF)
        assert resp == RESP_OKAY
    for idx in sweep_indices:
        w_addr = 0x5000_0000 + (idx * 4)
        expected = (0xA5A50000 ^ (idx * 0x01010101) ^ 0x5A5A) & 0xFFFFFFFF
        rdata, rresp = await driver.read(w_addr)
        assert rresp == RESP_OKAY
        assert rdata == expected, f"RAM sweep mismatch at word {idx} (addr {w_addr:#x}): expected {expected:#x}, got {rdata:#x}"

    # Write all zeros to detect any stuck-at-1 bits across memory words
    for idx in sweep_indices:
        w_addr = 0x5000_0000 + (idx * 4)
        resp = await driver.write(w_addr, 0x00000000, strb=0xF)
        assert resp == RESP_OKAY
    for idx in sweep_indices:
        w_addr = 0x5000_0000 + (idx * 4)
        rdata, rresp = await driver.read(w_addr)
        assert rresp == RESP_OKAY
        assert rdata == 0, f"Stuck-at-1 bit detected at word {idx}: expected 0, got {rdata:#x}"

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
