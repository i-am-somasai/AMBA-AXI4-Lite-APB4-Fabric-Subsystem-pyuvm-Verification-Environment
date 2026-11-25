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
