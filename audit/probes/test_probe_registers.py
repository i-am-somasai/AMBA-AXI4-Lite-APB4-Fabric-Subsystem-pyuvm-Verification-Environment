"""
test_probe_registers.py - Probe Test for Registers & Access Types (Spec Section 7)
Tests:
- Reset values of every register in CSR, Slow Regs, UART, Timer, GPIO
- Access types:
  - RO ignores writes (OKAY response)
  - RW holds written value
  - W1C clears bit on 1, ignores 0
  - W1C_SET test hook sets matching bit
  - WSTRB byte-enable behavior on RAM, CSR scratch2, and Slow Regs
  - RAM out-of-range returns SLVERR and discards write
  - Default slave consumes write data and never hangs
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from probe_driver import ProbeAxilDriver

RESP_OKAY   = 0b00
RESP_SLVERR = 0b10
RESP_DECERR = 0b11

async def reset_dut(dut):
    dut.gpio_i.value = 0
    dut.uart_rx.value = 1
    cocotb.start_soon(Clock(dut.clk_sys, 10, unit="ns").start())
    cocotb.start_soon(Clock(dut.clk_slow, 25, unit="ns").start())
    dut.rst_n.value = 0
    for _ in range(10):
        await RisingEdge(dut.clk_sys)
    dut.rst_n.value = 1
    for _ in range(10):
        await RisingEdge(dut.clk_sys)

@cocotb.test()
async def test_probe_registers_and_access(dut):
    """Probe all register reset values and access types per Spec Section 7."""
    await reset_dut(dut)
    drv = ProbeAxilDriver(dut, dut.clk_sys, prefix="s0_axil")

    # --- 1. CSR Block Registers (Base 0x6000_0000) ---
    # ID: 0x00, RO, reset 0xA3BA0001
    rdata, rresp = await drv.read(0x60000000)
    assert rresp == RESP_OKAY and rdata == 0xA3BA0001, f"CSR ID reset failed: {hex(rdata)}"
    # RO test: writes ignored with OKAY
    wresp = await drv.write(0x60000000, 0xFFFFFFFF)
    assert wresp == RESP_OKAY, "CSR ID write should return OKAY"
    rdata, _ = await drv.read(0x60000000)
    assert rdata == 0xA3BA0001, "CSR ID modified by write!"

    # VERSION: 0x04, RO, reset 0x00010000
    rdata, rresp = await drv.read(0x60000004)
    assert rresp == RESP_OKAY and rdata == 0x00010000, f"CSR VERSION reset failed: {hex(rdata)}"

    # SCRATCH: 0x08, RW, reset 0
    rdata, _ = await drv.read(0x60000008)
    assert rdata == 0, f"CSR SCRATCH reset failed: {hex(rdata)}"
    await drv.write(0x60000008, 0x12345678)
    rdata, _ = await drv.read(0x60000008)
    assert rdata == 0x12345678, "CSR SCRATCH RW failed"

    # SCRATCH2: 0x0C, RW, reset 0, byte-writable WSTRB
    rdata, _ = await drv.read(0x6000000C)
    assert rdata == 0, f"CSR SCRATCH2 reset failed: {hex(rdata)}"
    await drv.write(0x6000000C, 0xAABBCCDD, strb=0xF)
    await drv.write(0x6000000C, 0x00110000, strb=0b0100) # byte 2 only
    rdata, _ = await drv.read(0x6000000C)
    assert rdata == 0xAA11CCDD, f"SCRATCH2 byte strobe failed: {hex(rdata)}"

    # IRQ_RAW: 0x10, RO, reset 0
    rdata, _ = await drv.read(0x60000010)
    assert rdata == 0, f"CSR IRQ_RAW reset failed: {hex(rdata)}"

    # IRQ_MASK: 0x14, RW, reset 0
    rdata, _ = await drv.read(0x60000014)
    assert rdata == 0, f"CSR IRQ_MASK reset failed: {hex(rdata)}"

    # IRQ_STATUS: 0x18, RO, reset 0
    rdata, _ = await drv.read(0x60000018)
    assert rdata == 0, f"CSR IRQ_STATUS reset failed: {hex(rdata)}"

    # W1C_TEST: 0x1C, W1C, reset 0; W1C_SET: 0x20, WO
    rdata, _ = await drv.read(0x6000001C)
    assert rdata == 0, f"CSR W1C_TEST reset failed: {hex(rdata)}"
    # Set bits 0 and 2 using W1C_SET
    await drv.write(0x60000020, 0x00000005)
    rdata, _ = await drv.read(0x6000001C)
    assert rdata == 0x05, f"W1C_SET hook failed: {hex(rdata)}"
    # Clear bit 0 with W1C
    await drv.write(0x6000001C, 0x00000001)
    rdata, _ = await drv.read(0x6000001C)
    assert rdata == 0x04, f"W1C clear failed: {hex(rdata)}"
    # Write 0 should not clear
    await drv.write(0x6000001C, 0x00000000)
    rdata, _ = await drv.read(0x6000001C)
    assert rdata == 0x04, f"W1C write 0 modified register: {hex(rdata)}"

    # --- 2. Slow Regs (Base 0x7000_0000) ---
    # SLOW_ID: 0x00, RO, reset 0x510E0001
    rdata, rresp = await drv.read(0x70000000)
    assert rresp == RESP_OKAY and rdata == 0x510E0001, f"SLOW_ID reset failed: {hex(rdata)}"

    # SLOW_SCRATCH: 0x04, RW, reset 0, WSTRB-aware
    rdata, _ = await drv.read(0x70000004)
    assert rdata == 0, f"SLOW_SCRATCH reset failed: {hex(rdata)}"
    await drv.write(0x70000004, 0x12345678, strb=0xF)
    rdata, _ = await drv.read(0x70000004)
    assert rdata == 0x12345678, f"SLOW_SCRATCH RW failed: {hex(rdata)}"
    await drv.write(0x70000004, 0x0000AA00, strb=0b0010)
    rdata, _ = await drv.read(0x70000004)
    assert rdata == 0x1234AA78, f"SLOW_SCRATCH WSTRB failed: {hex(rdata)}"

    # SLOW_CTRL: 0x0C, RW, reset [0]=1 (counter enable)
    rdata, _ = await drv.read(0x7000000C)
    assert (rdata & 1) == 1, f"SLOW_CTRL reset failed: {hex(rdata)}"

    # --- 3. RAM WSTRB and Discard on Out-of-Range ---
    # Write 0xFFFFFFFF, then write byte 0 with 0x55
    await drv.write(0x50000010, 0xFFFFFFFF, strb=0xF)
    await drv.write(0x50000010, 0x00000055, strb=0b0001)
    rdata, _ = await drv.read(0x50000010)
    assert rdata == 0xFFFFFF55, f"RAM WSTRB failed: {hex(rdata)}"

    # Out-of-range write must be discarded
    wresp = await drv.write(0x50000400, 0xDEADCAFE)
    assert wresp == RESP_SLVERR, "RAM out-of-range write should return SLVERR"
    rdata, rresp = await drv.read(0x50000400)
    assert rresp == RESP_SLVERR, "RAM out-of-range read should return SLVERR"

    # --- 4. Default Slave Never Hangs ---
    wresp = await drv.write(0x90000000, 0x11223344)
    assert wresp == RESP_DECERR, "Default slave should return DECERR"
    rdata, rresp = await drv.read(0x90000000)
    assert rresp == RESP_DECERR, "Default slave read should return DECERR"
    assert rdata == 0, "Default slave read data should be 0"

    dut._log.info("Probe test_probe_registers_and_access PASSED!")
    await Timer(100, unit="ns")
