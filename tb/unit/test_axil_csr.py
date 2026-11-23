# L0 Unit Test for axil_csr
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from axil_driver import AxilMasterDriver

@cocotb.test()
async def test_axil_csr_all(dut):
    """Verify CSR register map, read-only behavior, W1C semantics, and IRQ aggregation."""
    dut._log.info("Starting test_axil_csr_all")
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.rst_n.value = 0
    dut.irq_sources.value = 0
    driver = AxilMasterDriver(dut, dut.clk)
    await Timer(25, unit="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    RESP_OKAY   = 0b00
    RESP_SLVERR = 0b10

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

    # 2. Read-only registers ignore writes with OKAY
    resp = await driver.write(0x6000_0000, 0xFFFFFFFF)
    assert resp == RESP_OKAY
    rdata, _ = await driver.read(0x6000_0000)
    assert rdata == 0xA3BA0001, "RO register ID modified by write!"

    # 3. SCRATCH word RW
    await driver.write(0x6000_0008, 0x12345678)
    rdata, _ = await driver.read(0x6000_0008)
    assert rdata == 0x12345678

    # 4. SCRATCH2 byte-enable RW
    await driver.write(0x6000_000C, 0xAABBCCDD, strb=0xF)
    await driver.write(0x6000_000C, 0x00110000, strb=0b0100) # byte 2
    rdata, _ = await driver.read(0x6000_000C)
    assert rdata == 0xAA11CCDD

    # 5. IRQ Aggregation & Masking
    dut.irq_sources.value = 0b101 # UART (bit 0) and GPIO (bit 2) active
    await RisingEdge(dut.clk)
    rdata, _ = await driver.read(0x6000_0010) # IRQ_RAW
    assert rdata == 0b101, f"Expected IRQ_RAW=0b101, got {rdata:#b}"

    # Initially mask is 0, so IRQ_STATUS=0 and irq_o=0
    rdata, _ = await driver.read(0x6000_0018)
    assert rdata == 0
    assert dut.irq_o.value == 0

    # Unmask UART only (bit 0)
    await driver.write(0x6000_0014, 0b001)
    await RisingEdge(dut.clk)
    rdata, _ = await driver.read(0x6000_0018)
    assert rdata == 0b001
    assert dut.irq_o.value == 1, "Expected irq_o=1 when unmasked IRQ is active"

    # 6. W1C Test Hook & Semantics
    # Write W1C_SET (offset 0x20) to set bits 1 and 3
    await driver.write(0x6000_0020, 0b1010)
    rdata, _ = await driver.read(0x6000_001C) # W1C_TEST
    assert rdata == 0b1010, f"Expected W1C_TEST=0b1010 after W1C_SET, got {rdata:#b}"

    # Write 1 to clear bit 1 (write 0b0010)
    await driver.write(0x6000_001C, 0b0010)
    rdata, _ = await driver.read(0x6000_001C)
    assert rdata == 0b1000, f"Expected bit 1 cleared (0b1000), got {rdata:#b}"

    # 7. Undefined offset -> SLVERR
    resp = await driver.write(0x6000_0030, 0x1234)
    assert resp == RESP_SLVERR, f"Expected SLVERR on undefined offset write, got {resp:#b}"

    rdata, rresp = await driver.read(0x6000_0030)
    assert rresp == RESP_SLVERR, f"Expected SLVERR on undefined offset read, got {rresp:#b}"

    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")

    dut._log.info("test_axil_csr_all PASSED")
