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
    assert dut.s_axil_bvalid.value == 0, "bvalid must be 0 during reset"
    assert dut.s_axil_rvalid.value == 0, "rvalid must be 0 during reset"
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert dut.s_axil_bvalid.value == 0, "bvalid must be 0 after reset"
    assert dut.s_axil_rvalid.value == 0, "rvalid must be 0 after reset"

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

    # 3. Comprehensive full-depth memory sweep across all 256 words
    # Pass A: Write distinct non-zero walking pattern to every single word, wait odd cycle, read back
    for idx in range(256):
        w_addr = 0x5000_0000 + (idx * 4)
        val = ((idx * 0x01010101) ^ 0xA55A3CC3) & 0xFFFFFFFF
        resp = await driver.write(w_addr, val, strb=0xF)
        assert resp == RESP_OKAY, f"Write failed at word {idx}"
    await RisingEdge(dut.clk)  # Break even-cycle write-to-read parity against DFF Q oscillating mutants
    for idx in range(256):
        w_addr = 0x5000_0000 + (idx * 4)
        expected = ((idx * 0x01010101) ^ 0xA55A3CC3) & 0xFFFFFFFF
        rdata, rresp = await driver.read(w_addr)
        assert rresp == RESP_OKAY
        assert rdata == expected, f"RAM mismatch at word {idx}: expected {expected:#x}, got {rdata:#x}"
        # Re-read immediately at +0 extra idle cycles (even/odd cycle cross-check)
        if idx in (16, 44, 48, 123, 163, 208, 224):
            await RisingEdge(dut.clk)
            rdata2, rresp2 = await driver.read(w_addr)
            assert rresp2 == RESP_OKAY and rdata2 == expected, (
                f"RAM 1-cycle retention parity fail at word {idx}: expected {expected:#x}, got {rdata2:#x}"
            )

    # Pass B: Write inverted bitwise complement to every word, wait odd cycle, read back
    for idx in range(256):
        w_addr = 0x5000_0000 + (idx * 4)
        val = (~((idx * 0x01010101) ^ 0xA55A3CC3)) & 0xFFFFFFFF
        resp = await driver.write(w_addr, val, strb=0xF)
        assert resp == RESP_OKAY
    await RisingEdge(dut.clk)
    for idx in range(256):
        w_addr = 0x5000_0000 + (idx * 4)
        expected = (~((idx * 0x01010101) ^ 0xA55A3CC3)) & 0xFFFFFFFF
        rdata, rresp = await driver.read(w_addr)
        assert rresp == RESP_OKAY
        assert rdata == expected, f"RAM complement mismatch at word {idx}: expected {expected:#x}, got {rdata:#x}"

    # Pass C: Write all zeros to detect stuck-at-1 bits across memory words + odd-cycle retention check
    for idx in range(256):
        w_addr = 0x5000_0000 + (idx * 4)
        resp = await driver.write(w_addr, 0x00000000, strb=0xF)
        assert resp == RESP_OKAY
    await RisingEdge(dut.clk)
    for idx in range(256):
        w_addr = 0x5000_0000 + (idx * 4)
        rdata, rresp = await driver.read(w_addr)
        assert rresp == RESP_OKAY
        assert rdata == 0, f"Stuck-at-1 bit detected at word {idx}: expected 0, got {rdata:#x}"

    # 3b. Exhaustive 16 WSTRB patterns across simultaneous, aw_first, and w_first orders
    for ord_mode in ("simultaneous", "aw_first", "w_first"):
        for strb in range(16):
            target_addr = 0x5000_0040 + ((strb % 4) * 4)
            await driver.write(target_addr, 0xA5A55A5A, strb=0xF)
            wdata = 0x13579BDF ^ (strb * 0x01010101)
            resp = await driver.write(target_addr, wdata, strb=strb, order=ord_mode)
            assert resp == RESP_OKAY
            exp = 0
            for b in range(4):
                m = 0xFF << (8 * b)
                exp |= (wdata & m) if ((strb >> b) & 1) else (0xA5A55A5A & m)
            rdata, rresp = await driver.read(target_addr)
            assert rresp == RESP_OKAY and rdata == exp, (
                f"RAM {ord_mode} strb={strb:#x} mismatch: expected {exp:#x}, got {rdata:#x}"
            )

    # 4. Out-of-order write handshakes: W before AW (w_first)
    dut.s_axil_wdata.value = 0x12345678
    dut.s_axil_wstrb.value = 0xF
    dut.s_axil_wvalid.value = 1
    while True:
        await RisingEdge(dut.clk)
        if int(dut.s_axil_wready.value) == 1:
            dut.s_axil_wvalid.value = 0
            break
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.s_axil_awaddr.value = 0x5000_0030
    dut.s_axil_awvalid.value = 1
    dut.s_axil_bready.value = 1
    while True:
        await RisingEdge(dut.clk)
        if int(dut.s_axil_awready.value) == 1:
            dut.s_axil_awvalid.value = 0
        if int(dut.s_axil_bvalid.value) == 1:
            break
    await RisingEdge(dut.clk)
    rdata, rresp = await driver.read(0x5000_0030)
    assert rresp == RESP_OKAY and rdata == 0x12345678, "w_first write data mismatch"

    # 5. Out-of-order write handshakes: AW before W (aw_first)
    dut.s_axil_awaddr.value = 0x5000_0034
    dut.s_axil_awvalid.value = 1
    dut.s_axil_bready.value = 1
    while True:
        await RisingEdge(dut.clk)
        if int(dut.s_axil_awready.value) == 1:
            dut.s_axil_awvalid.value = 0
            break
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.s_axil_wdata.value = 0x87654321
    dut.s_axil_wstrb.value = 0xF
    dut.s_axil_wvalid.value = 1
    while True:
        await RisingEdge(dut.clk)
        if int(dut.s_axil_wready.value) == 1:
            dut.s_axil_wvalid.value = 0
        if int(dut.s_axil_bvalid.value) == 1:
            break
    await RisingEdge(dut.clk)
    rdata, rresp = await driver.read(0x5000_0034)
    assert rresp == RESP_OKAY and rdata == 0x87654321, "aw_first write data mismatch"

    # 6. Out-of-range tests (RAM_DEPTH=256 words -> offset 256*4 = 0x400)
    # First read all-ones word so residual s_axil_rdata bits are non-zero before OOR read
    await driver.write(0x5000_0000, 0xFFFFFFFF, strb=0xF)
    rdata_ones, rresp_ones = await driver.read(0x5000_0000)
    assert rresp_ones == RESP_OKAY and rdata_ones == 0xFFFFFFFF

    oor_addr = 0x5000_0400
    resp = await driver.write(oor_addr, 0xBAD0BAD0, strb=0xF, bready_delay=3)
    assert resp == RESP_SLVERR, f"Expected SLVERR on OOR write, got {resp:#b}"

    rdata, rresp = await driver.read(oor_addr, rready_delay=3)
    assert rresp == RESP_SLVERR, f"Expected SLVERR on OOR read, got {rresp:#b}"
    assert rdata == 0, f"Expected rdata=0 on OOR read, got {rdata:#x}"

    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")

    dut._log.info("test_axil_ram_operations PASSED")
