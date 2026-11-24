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
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    return driver


@cocotb.test()
async def test_cs01_reset_values(dut):
    """CS-01: System CSR reset values verification."""
    dut._log.info("Starting CS-01: Reset values check")
    driver = await setup_csr(dut)

    # 1. Reset values
    rdata, rresp = await driver.read(0x6000_0000) # ID
    assert rresp == RESP_OKAY and rdata == 0xA3BA0001, f"ID check failed: {rdata:#x}"

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

    # 2. SCRATCH word RW
    await driver.write(0x6000_0008, 0x12345678)
    rdata, _ = await driver.read(0x6000_0008)
    assert rdata == 0x12345678

    # 3. SCRATCH2 byte-enable RW
    await driver.write(0x6000_000C, 0xAABBCCDD, strb=0xF)
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

    # 4. W1C Test Hook & Semantics
    # Write W1C_SET (offset 0x20) to set bits 1 and 3
    await driver.write(0x6000_0020, 0b1010)
    rdata, _ = await driver.read(0x6000_001C) # W1C_TEST
    assert rdata == 0b1010, f"Expected W1C_TEST=0b1010 after W1C_SET, got {rdata:#b}"

    # Write 1 to clear bit 1 (write 0b0010)
    await driver.write(0x6000_001C, 0b0010)
    rdata, _ = await driver.read(0x6000_001C)
    assert rdata == 0b1000, f"Expected bit 1 cleared (0b1000), got {rdata:#b}"

    # 5. Undefined offset -> SLVERR
    resp = await driver.write(0x6000_0030, 0x1234)
    assert resp == RESP_SLVERR, f"Expected SLVERR on undefined offset write, got {resp:#b}"

    rdata, rresp = await driver.read(0x6000_0030)
    assert rresp == RESP_SLVERR, f"Expected SLVERR on undefined offset read, got {rresp:#b}"

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

    # 4. Mask bit 0, unmask bit 1 (Timer, which is inactive)
    await driver.write(0x6000_0014, 0b010)
    await RisingEdge(dut.clk)
    rdata, _ = await driver.read(0x6000_0018)
    assert rdata == 0b000
    assert dut.irq_o.value == 0, "Expected irq_o=0 when active source is masked"

    # 5. Clear sources
    dut.irq_sources.value = 0
    await driver.write(0x6000_0014, 0b111)
    await RisingEdge(dut.clk)
    assert dut.irq_o.value == 0

    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")
    dut._log.info("CS-03 PASSED")
