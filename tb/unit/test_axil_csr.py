# L0 Unit Test for axil_csr (CS-01, CS-02, CS-03)
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from axil_driver import AxilMasterDriver

RESP_OKAY   = 0b00
RESP_SLVERR = 0b10


async def setup_csr(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst_n.value = 0
    dut.irq_sources.value = 0
    driver = AxilMasterDriver(dut, dut.clk)
    await Timer(25, unit="ns")
    assert dut.s_axil_bvalid.value == 0, "bvalid must be 0 during reset"
    assert dut.s_axil_rvalid.value == 0, "rvalid must be 0 during reset"
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert dut.s_axil_bvalid.value == 0, "bvalid must be 0 after reset"
    assert dut.s_axil_rvalid.value == 0, "rvalid must be 0 after reset"
    return driver


@cocotb.test()
async def test_cs01_reset_values(dut):
    """CS-01: System CSR reset values verification."""
    dut._log.info("Starting CS-01: Reset values check")
    driver = await setup_csr(dut)

    # 1. Reset values
    rdata, rresp = await driver.read(0x6000_0000) # ID
    assert rresp == RESP_OKAY and rdata == 0xA3BA0001, f"ID check failed: {rdata:#x}"

    # Rule 6 check: unaligned LSBs [1:0] ignored on read
    for unaligned_off in (1, 2, 3):
        rdata, rresp = await driver.read(0x6000_0000 + unaligned_off)
        assert rresp == RESP_OKAY and rdata == 0xA3BA0001, (
            f"Rule 6 unaligned ID read failed at +{unaligned_off}: resp={rresp}, data={rdata:#x}"
        )

    rdata, rresp = await driver.read(0x6000_0004) # VERSION
    assert rresp == RESP_OKAY and rdata == 0x00010000, f"VERSION check failed: {rdata:#x}"

    rdata, _ = await driver.read(0x6000_0008) # SCRATCH
    assert rdata == 0

    rdata, _ = await driver.read(0x6000_000C) # SCRATCH2
    assert rdata == 0

    rdata, _ = await driver.read(0x6000_0010) # IRQ_RAW
    assert rdata == 0

    rdata, _ = await driver.read(0x6000_0014) # IRQ_MASK
    assert rdata == 0

    rdata, _ = await driver.read(0x6000_0018) # IRQ_STATUS
    assert rdata == 0

    rdata, _ = await driver.read(0x6000_001C) # W1C_TEST
    assert rdata == 0

    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")
    dut._log.info("CS-01 PASSED")


@cocotb.test()
async def test_cs02_access_types_w1c(dut):
    """CS-02: System CSR access types (RO, RW, W1C) and W1C_SET hook."""
    dut._log.info("Starting CS-02: Access types and W1C check")
    driver = await setup_csr(dut)

    # 1. Read-only registers ignore writes with OKAY
    resp = await driver.write(0x6000_0000, 0xFFFFFFFF)
    assert resp == RESP_OKAY
    rdata, _ = await driver.read(0x6000_0000)
    assert rdata == 0xA3BA0001, "RO register ID modified by write!"

    # 2. SCRATCH word RW with walking patterns
    for bit in range(32):
        wval = (1 << bit)
        await driver.write(0x6000_0008, wval)
        rdata, rresp = await driver.read(0x6000_0008)
        assert rresp == RESP_OKAY and rdata == wval, f"SCRATCH walking 1 mismatch at bit {bit}"
        wval_inv = (~(1 << bit)) & 0xFFFFFFFF
        await driver.write(0x6000_0008, wval_inv)
        rdata, rresp = await driver.read(0x6000_0008)
        assert rresp == RESP_OKAY and rdata == wval_inv, f"SCRATCH walking 0 mismatch at bit {bit}"

    # 3. SCRATCH2 byte-enable RW
    await driver.write(0x6000_000C, 0xAABBCCDD, strb=0xF)
    rdata, rresp = await driver.read(0x6000_000C)
    assert rresp == RESP_OKAY and rdata == 0xAABBCCDD
    # Modify only byte 2 (strb=0b0100)
    await driver.write(0x6000_000C, 0x00110000, strb=0b0100)
    rdata, _ = await driver.read(0x6000_000C)
    assert rdata == 0xAA11CCDD

    # Modify only byte 0 (strb=0b0001) - byte 2 must NOT change
    await driver.write(0x6000_000C, 0x00000022, strb=0b0001)
    rdata, _ = await driver.read(0x6000_000C)
    assert rdata == 0xAA11CC22, f"Expected 0xAA11CC22, got {rdata:#x}"

    # Modify only byte 1 (strb=0b0010) - byte 2 must NOT change
    await driver.write(0x6000_000C, 0x00003300, strb=0b0010)
    rdata, _ = await driver.read(0x6000_000C)
    assert rdata == 0xAA113322, f"Expected 0xAA113322, got {rdata:#x}"

    # Modify only byte 3 (strb=0b1000)
    await driver.write(0x6000_000C, 0x44000000, strb=0b1000)
    rdata, _ = await driver.read(0x6000_000C)
    assert rdata == 0x44113322, f"Expected 0x44113322, got {rdata:#x}"

    # 4. W1C Test Hook & Semantics across all 8 bits
    # Write W1C_SET (offset 0x20) to set all 8 bits
    await driver.write(0x6000_0020, 0xFF)
    rdata, rresp = await driver.read(0x6000_001C) # W1C_TEST
    assert rresp == RESP_OKAY and rdata == 0xFF, f"Expected W1C_TEST=0xFF after W1C_SET, got {rdata:#x}"

    # Clear each bit individually and verify
    current_val = 0xFF
    for b in range(8):
        mask = (1 << b)
        current_val &= ~mask
        await driver.write(0x6000_001C, mask)
        rdata, _ = await driver.read(0x6000_001C)
        assert rdata == current_val, f"Bit {b} clear failed: expected {current_val:#x}, got {rdata:#x}"

    # 5. Undefined offsets -> SLVERR
    for unmapped_offset in [0x0024, 0x0028, 0x0030, 0x0034, 0x0050, 0x0080, 0x00FC]:
        resp = await driver.write(0x6000_0000 + unmapped_offset, 0x1234)
        assert resp == RESP_SLVERR, f"Expected SLVERR on offset {unmapped_offset:#x} write, got {resp:#b}"
        rdata, rresp = await driver.read(0x6000_0000 + unmapped_offset)
        assert rresp == RESP_SLVERR, f"Expected SLVERR on offset {unmapped_offset:#x} read, got {rresp:#b}"
        assert rdata == 0

    # Rule 6 write check: unaligned write to SCRATCH+1 updates word 0x6000_0008 with OKAY
    resp = await driver.write(0x6000_0009, 0xCAFE5A5A, strb=0xF)
    assert resp == RESP_OKAY, f"Rule 6 unaligned write to 0x6000_0009 failed: resp={resp:#b}"
    rdata, rresp = await driver.read(0x6000_0008)
    assert rresp == RESP_OKAY and rdata == 0xCAFE5A5A, f"Rule 6 readback mismatch: {rdata:#x}"

    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")
    dut._log.info("CS-02 PASSED")


@cocotb.test()
async def test_cs03_irq_aggregation(dut):
    """CS-03: System CSR interrupt aggregation, masking, and irq_o driving."""
    dut._log.info("Starting CS-03: IRQ aggregation check")
    driver = await setup_csr(dut)

    # 1. Drive external IRQ sources
    dut.irq_sources.value = 0b101 # UART (bit 0) and GPIO (bit 2) active
    await RisingEdge(dut.clk)
    rdata, _ = await driver.read(0x6000_0010) # IRQ_RAW
    assert rdata == 0b101, f"Expected IRQ_RAW=0b101, got {rdata:#b}"

    # 2. Initially mask is 0, so IRQ_STATUS=0 and irq_o=0
    rdata, _ = await driver.read(0x6000_0018) # IRQ_STATUS
    assert rdata == 0
    assert dut.irq_o.value == 0

    # 3. Unmask UART only (bit 0)
    await driver.write(0x6000_0014, 0b001) # IRQ_MASK
    await RisingEdge(dut.clk)
    rdata, _ = await driver.read(0x6000_0018)
    assert rdata == 0b001
    assert dut.irq_o.value == 1, "Expected irq_o=1 when unmasked IRQ is active"

    # 4. Test Timer alone (bit 1 active)
    dut.irq_sources.value = 0b010
    await driver.write(0x6000_0014, 0b010) # unmask Timer
    await RisingEdge(dut.clk)
    rdata, _ = await driver.read(0x6000_0018)
    assert rdata == 0b010
    assert dut.irq_o.value == 1, "Expected irq_o=1 when Timer IRQ is unmasked and active"

    # 5. Mask bit 0, unmask bit 1 (Timer, which is inactive)
    dut.irq_sources.value = 0b101 # UART and GPIO active, Timer inactive
    await driver.write(0x6000_0014, 0b010) # mask UART/GPIO, unmask Timer
    await RisingEdge(dut.clk)
    rdata, _ = await driver.read(0x6000_0018)
    assert rdata == 0b000
    assert dut.irq_o.value == 0, "Expected irq_o=0 when active source is masked"

    # 6. All 3 active and unmasked
    dut.irq_sources.value = 0b111
    await driver.write(0x6000_0014, 0b111)
    await RisingEdge(dut.clk)
    rdata, _ = await driver.read(0x6000_0018)
    assert rdata == 0b111
    assert dut.irq_o.value == 1

    # 7. Clear sources
    dut.irq_sources.value = 0
    await driver.write(0x6000_0014, 0b111)
    await RisingEdge(dut.clk)
    assert dut.irq_o.value == 0

    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")
    dut._log.info("CS-03 PASSED")


@cocotb.test()
async def test_cs04_ooo_w1c32_ro_wo_and_backpressure(dut):
    """CS-04: CSR aw_first/w_first staging, 32-bit W1C, RO writes, WO reads, and B/R hold."""
    driver = await setup_csr(dut)

    # 1. All RO registers ignore writes with OKAY and hold fixed/external values
    dut.irq_sources.value = 0b101
    for ro_addr, exp_val in [(0x6000_0000, 0xA3BA0001), (0x6000_0004, 0x00010000), (0x6000_0010, 0b101), (0x6000_0018, 0b000)]:
        bresp = await driver.write(ro_addr, 0xFFFFFFFF, order="w_first", bready_delay=2)
        assert bresp == RESP_OKAY
        rdata, rresp = await driver.read(ro_addr, rready_delay=2)
        assert rresp == RESP_OKAY and rdata == exp_val, f"RO {ro_addr:#x}: exp {exp_val:#x}, got {rdata:#x}"
    dut.irq_sources.value = 0

    # 2. W1C_SET (0x20) is WO: reading it returns 0 with OKAY, after writing full 32-bit patterns
    for wpat in [0xFFFFFFFF, 0xAAAAAAAA, 0x55555555]:
        assert await driver.write(0x6000_001C, 0xFFFFFFFF) == RESP_OKAY  # Clear all
        assert await driver.write(0x6000_0020, wpat, order="w_first") == RESP_OKAY
        wo_rd, wo_resp = await driver.read(0x6000_0020)
        assert wo_resp == RESP_OKAY and wo_rd == 0, f"W1C_SET read must be 0 OKAY, got {wo_rd:#x} resp={wo_resp}"
        t_rd, t_resp = await driver.read(0x6000_001C)
        assert t_resp == RESP_OKAY and t_rd == wpat
        assert await driver.write(0x6000_001C, wpat, order="aw_first") == RESP_OKAY
        t_clr, _ = await driver.read(0x6000_001C)
        assert t_clr == 0

    # 3. Walking 1s across all 32 bits of W1C_SET / W1C_TEST via both w_first and aw_first
    for bit in range(32):
        mask = 1 << bit
        ord_m = "w_first" if (bit % 2 == 0) else "aw_first"
        assert await driver.write(0x6000_0020, mask, order=ord_m) == RESP_OKAY
        val, _ = await driver.read(0x6000_001C)
        assert val == mask, f"32-bit W1C set bit {bit} failed: got {val:#x}"
        assert await driver.write(0x6000_001C, mask, order=("aw_first" if ord_m == "w_first" else "w_first")) == RESP_OKAY
        val2, _ = await driver.read(0x6000_001C)
        assert val2 == 0, f"32-bit W1C clear bit {bit} failed: got {val2:#x}"

    # 4. SCRATCH (0x08) and SCRATCH2 (0x0C) under aw_first / w_first and full 16 WSTRB values
    assert await driver.write(0x6000_0008, 0x12345678, order="w_first") == RESP_OKAY
    assert await driver.write(0x6000_000D, 0x87654321, strb=0xF, order="aw_first") == RESP_OKAY
    s1, _ = await driver.read(0x6000_0008)
    s2, _ = await driver.read(0x6000_000C)
    assert s1 == 0x12345678 and s2 == 0x87654321
    for ord_m in ("aw_first", "w_first"):
        for bit in (0, 9, 17, 25, 31):
            v = 1 << bit
            assert await driver.write(0x6000_0009, v, order=ord_m) == RESP_OKAY
            rv, _ = await driver.read(0x6000_0008)
            assert rv == v
        for strb in range(16):
            assert await driver.write(0x6000_000C, 0xA55A3CC3, strb=0xF) == RESP_OKAY
            wval = 0xF0E1D2C3 ^ (strb * 0x01010101)
            assert await driver.write(0x6000_000E, wval, strb=strb, order=ord_m) == RESP_OKAY
            exp = 0
            for b in range(4):
                m = 0xFF << (8 * b)
                exp |= (wval & m) if ((strb >> b) & 1) else (0xA55A3CC3 & m)
            rv2, _ = await driver.read(0x6000_000C)
            assert rv2 == exp, f"CSR SCRATCH2 {ord_m} strb={strb:#x} mismatch: {rv2:#x} != {exp:#x}"

    # 5. Backpressure BREADY=0 stability hold, BVALID clear, unrelated write retention (axil_csr #04),
    #    and odd-cycle w_first WSTRB latch retention (axil_csr #25)
    bresp_slv = await driver.write(0x6000_0030, 0x1, order="w_first", bready_delay=3)
    assert bresp_slv == RESP_SLVERR
    rdata_slv, rresp_slv = await driver.read(0x6000_0030, rready_delay=3)
    assert rresp_slv == RESP_SLVERR and rdata_slv == 0

    # 5a. Hold W1C_TEST = 0xFFFFFFFF across an unrelated write to SCRATCH, then clear all bits except bit 7
    assert await driver.write(0x6000_0020, 0xFFFFFFFF) == RESP_OKAY
    assert await driver.write(0x6000_0008, 0xCAFEBABE) == RESP_OKAY
    w1c_hold, _ = await driver.read(0x6000_001C)
    assert w1c_hold == 0xFFFFFFFF, f"W1C_TEST mutated during unrelated write: {w1c_hold:#x}"
    assert await driver.write(0x6000_001C, 0xFFFFFF7F) == RESP_OKAY
    w1c_rem, _ = await driver.read(0x6000_001C)
    assert w1c_rem == 0x00000080, f"W1C_TEST bit 7 corrupted on multi-bit clear: {w1c_rem:#x}"
    assert await driver.write(0x6000_001C, 0xFFFFFFFF) == RESP_OKAY

    # 5b. 1-cycle (odd stagger) w_first WSTRB latch test on SCRATCH2 (kills axil_csr #25 double-inversion escape)
    for strb in range(16):
        assert await driver.write(0x6000_000C, 0xA55A3CC3, strb=0xF) == RESP_OKAY
        wval = 0x13579BDF ^ (strb * 0x01010101)
        dut.s_axil_awvalid.value = 0
        dut.s_axil_wdata.value = wval
        dut.s_axil_wstrb.value = strb
        dut.s_axil_wvalid.value = 1
        dut.s_axil_bready.value = 1
        for _ in range(10):
            await RisingEdge(dut.clk)
            if int(dut.s_axil_wready.value) == 1:
                dut.s_axil_wvalid.value = 0
                break
        # Exactly 1 cycle later (odd stagger): drive AW
        dut.s_axil_awaddr.value = 0x6000_000C
        dut.s_axil_awvalid.value = 1
        for _ in range(10):
            await RisingEdge(dut.clk)
            if int(dut.s_axil_awready.value) == 1:
                dut.s_axil_awvalid.value = 0
            if int(dut.s_axil_bvalid.value) == 1:
                break
        await RisingEdge(dut.clk)
        dut.s_axil_bready.value = 0
        exp = 0
        for b in range(4):
            m = 0xFF << (8 * b)
            exp |= (wval & m) if ((strb >> b) & 1) else (0xA55A3CC3 & m)
        rv3, _ = await driver.read(0x6000_000C)
        assert rv3 == exp, f"Odd-stagger w_first strb={strb:#x} mismatch: {rv3:#x} != {exp:#x}"

    # 5c. Verify BVALID holds while BREADY=0 and clears on next cycle after BREADY=1 (kills axil_csr #19)
    dut.s_axil_awaddr.value = 0x6000_0008
    dut.s_axil_wdata.value = 0xDEADBEEF
    dut.s_axil_wstrb.value = 0xF
    dut.s_axil_awvalid.value = 1
    dut.s_axil_wvalid.value = 1
    dut.s_axil_bready.value = 0
    for _ in range(10):
        await RisingEdge(dut.clk)
        if int(dut.s_axil_awready.value) == 1:
            dut.s_axil_awvalid.value = 0
        if int(dut.s_axil_wready.value) == 1:
            dut.s_axil_wvalid.value = 0
        if int(dut.s_axil_bvalid.value) == 1:
            break
    assert int(dut.s_axil_bvalid.value) == 1, "BVALID did not assert"
    for hold_cyc in range(3):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.s_axil_bvalid.value) == 1, f"BVALID dropped while BREADY=0 at cycle {hold_cyc}"
    dut.s_axil_bready.value = 1
    await RisingEdge(dut.clk)
    dut.s_axil_bready.value = 0
    await Timer(1, unit="ns")
    assert int(dut.s_axil_bvalid.value) == 0, "BVALID did not clear after BVALID && BREADY handshake"

    await Timer(10, unit="ns")
