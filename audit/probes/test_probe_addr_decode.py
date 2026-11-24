"""
test_probe_addr_decode.py - Probe Test for Address Decode (Spec Section 5.3)
Tests:
- Read and write to mapped regions: APB UART (0x4000_0000), APB Timer (0x4000_1000), APB GPIO (0x4000_2000), RAM (0x5000_0000), CSR (0x6000_0000), CDC (0x7000_0000)
- APB unmapped address (0x4000_3000) -> SLVERR (Spec Section 5.3)
- RAM out of range (0x5000_0400) -> SLVERR (Spec Section 5.3, 7.2)
- CSR undefined offset (0x6000_0030) -> SLVERR (Spec Section 5.3, 7.2)
- CDC undefined offset (0x7000_0020) -> SLVERR (Spec Section 5.3, 7.4)
- Unmapped address space (0x1000_0000, 0x8000_0000) -> DECERR (Spec Section 5.3)
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
    ProbeAxilDriver(dut, dut.clk_sys, prefix="s0_axil")
    ProbeAxilDriver(dut, dut.clk_sys, prefix="s1_axil")
    cocotb.start_soon(Clock(dut.clk_sys, 10, unit="ns").start())
    cocotb.start_soon(Clock(dut.clk_slow, 25, unit="ns").start())
    dut.rst_n.value = 0
    for _ in range(10):
        await RisingEdge(dut.clk_sys)
    dut.rst_n.value = 1
    for _ in range(10):
        await RisingEdge(dut.clk_sys)

@cocotb.test()
async def test_probe_address_decode(dut):
    """Probe address decode across all regions per Spec Section 5.3."""
    await reset_dut(dut)
    drv = ProbeAxilDriver(dut, dut.clk_sys, prefix="s0_axil")
    
    # 1. RAM Region (0x5000_0000) -> OKAY
    wresp = await drv.write(0x50000000, 0x12345678)
    assert wresp == RESP_OKAY, f"Spec Section 5.3: Expected OKAY on RAM write, got {wresp}"
    rdata, rresp = await drv.read(0x50000000)
    assert rresp == RESP_OKAY, f"Spec Section 5.3: Expected OKAY on RAM read, got {rresp}"
    assert rdata == 0x12345678, f"RAM read mismatch: expected 0x12345678, got {hex(rdata)}"

    # 2. CSR Region (0x6000_0000) -> OKAY
    rdata, rresp = await drv.read(0x60000000)
    assert rresp == RESP_OKAY, f"Spec Section 5.3: Expected OKAY on CSR read, got {rresp}"
    assert rdata == 0xA3BA0001, f"CSR ID mismatch: expected 0xA3BA0001, got {hex(rdata)}"

    # 3. APB Subsystem Regions -> OKAY
    # UART BAUDDIV (0x4000_0010)
    wresp = await drv.write(0x40000010, 0x00000004)
    assert wresp == RESP_OKAY, f"Spec Section 5.3: Expected OKAY on UART write, got {wresp}"
    rdata, rresp = await drv.read(0x40000010)
    assert rresp == RESP_OKAY and rdata == 4, f"UART BAUDDIV read failed: {rresp}, {rdata}"

    # Timer LOAD (0x4000_1004)
    wresp = await drv.write(0x40001004, 0x00000100)
    assert wresp == RESP_OKAY, f"Spec Section 5.3: Expected OKAY on Timer write, got {wresp}"
    rdata, rresp = await drv.read(0x40001004)
    assert rresp == RESP_OKAY and rdata == 0x100, f"Timer LOAD read failed: {rresp}, {rdata}"

    # GPIO DIR (0x4000_2000)
    wresp = await drv.write(0x40002000, 0x000000FF)
    assert wresp == RESP_OKAY, f"Spec Section 5.3: Expected OKAY on GPIO write, got {wresp}"
    rdata, rresp = await drv.read(0x40002000)
    assert rresp == RESP_OKAY and rdata == 0xFF, f"GPIO DIR read failed: {rresp}, {rdata}"

    # 4. CDC Region (0x7000_0000) -> OKAY
    rdata, rresp = await drv.read(0x70000000)
    assert rresp == RESP_OKAY, f"Spec Section 5.3: Expected OKAY on CDC read, got {rresp}"
    assert rdata == 0x510E0001, f"SLOW_ID mismatch: expected 0x510E0001, got {hex(rdata)}"

    # 5. APB Unmapped Address (0x4000_3000) -> PSLVERR -> SLVERR
    wresp = await drv.write(0x40003000, 0xDEADBEEF)
    assert wresp == RESP_SLVERR, f"Spec Section 5.3: Expected SLVERR on unmapped APB write, got {wresp}"
    rdata, rresp = await drv.read(0x40003000)
    assert rresp == RESP_SLVERR, f"Spec Section 5.3: Expected SLVERR on unmapped APB read, got {rresp}"

    # 6. RAM Out-of-Range (0x5000_0400 = 1024 bytes = word 256) -> SLVERR
    wresp = await drv.write(0x50000400, 0xCAFEBABE)
    assert wresp == RESP_SLVERR, f"Spec Section 5.3/7.2: Expected SLVERR on RAM out-of-range write, got {wresp}"
    rdata, rresp = await drv.read(0x50000400)
    assert rresp == RESP_SLVERR, f"Spec Section 5.3/7.2: Expected SLVERR on RAM out-of-range read, got {rresp}"

    # 7. CSR Undefined Offset (0x6000_0030) -> SLVERR
    wresp = await drv.write(0x60000030, 0x99999999)
    assert wresp == RESP_SLVERR, f"Spec Section 5.3/7.2: Expected SLVERR on CSR undefined write, got {wresp}"
    rdata, rresp = await drv.read(0x60000030)
    assert rresp == RESP_SLVERR, f"Spec Section 5.3/7.2: Expected SLVERR on CSR undefined read, got {rresp}"

    # 8. CDC Undefined Offset (0x7000_0020) -> SLVERR
    wresp = await drv.write(0x70000020, 0x88888888)
    assert wresp == RESP_SLVERR, f"Spec Section 5.3/7.4: Expected SLVERR on CDC undefined write, got {wresp}"
    rdata, rresp = await drv.read(0x70000020)
    assert rresp == RESP_SLVERR, f"Spec Section 5.3/7.4: Expected SLVERR on CDC undefined read, got {rresp}"

    # 9. Default Slave: Unmapped Addresses (0x1000_0000 and 0x8000_0000) -> DECERR
    wresp = await drv.write(0x10000000, 0x11112222)
    assert wresp == RESP_DECERR, f"Spec Section 5.3: Expected DECERR on unmapped 0x10000000 write, got {wresp}"
    rdata, rresp = await drv.read(0x10000000)
    assert rresp == RESP_DECERR, f"Spec Section 5.3: Expected DECERR on unmapped 0x10000000 read, got {rresp}"

    wresp = await drv.write(0x80000000, 0x33334444)
    assert wresp == RESP_DECERR, f"Spec Section 5.3: Expected DECERR on unmapped 0x80000000 write, got {wresp}"
    rdata, rresp = await drv.read(0x80000000)
    assert rresp == RESP_DECERR, f"Spec Section 5.3: Expected DECERR on unmapped 0x80000000 read, got {rresp}"
    
    dut._log.info("Probe test_probe_address_decode PASSED!")
    await Timer(100, unit="ns")
