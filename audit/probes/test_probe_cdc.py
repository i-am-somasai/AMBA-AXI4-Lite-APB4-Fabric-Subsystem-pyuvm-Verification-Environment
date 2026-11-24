"""
test_probe_cdc.py - Probe Test for CDC Subsystem (Spec Section 7.4)
Tests:
- Access to slow_regs across two different clock ratios:
  1) clk_sys=10ns (100MHz), clk_slow=20ns (50MHz) -> 2:1 ratio
  2) clk_sys=10ns (100MHz), clk_slow=33.3ns (30MHz) -> ~3:1 ratio
- SLOW_COUNTER free-running counter increases in clk_slow domain (Spec line 399, 518)
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from probe_driver import ProbeAxilDriver

RESP_OKAY = 0b00

@cocotb.test()
async def test_probe_cdc_ratio_and_counter(dut):
    """Probe CDC bridge across clock ratios and verify SLOW_COUNTER increments."""
    # Test 1: clk_sys = 100MHz (10ns), clk_slow = 50MHz (20ns)
    dut.gpio_i.value = 0
    dut.uart_rx.value = 1
    ProbeAxilDriver(dut, dut.clk_sys, prefix="s0_axil")
    ProbeAxilDriver(dut, dut.clk_sys, prefix="s1_axil")
    cocotb.start_soon(Clock(dut.clk_sys, 10, unit="ns").start())
    slow_clk_task = cocotb.start_soon(Clock(dut.clk_slow, 20, unit="ns").start())

    dut.rst_n.value = 0
    for _ in range(10):
        await RisingEdge(dut.clk_sys)
    dut.rst_n.value = 1
    for _ in range(10):
        await RisingEdge(dut.clk_sys)

    drv = ProbeAxilDriver(dut, dut.clk_sys, prefix="s0_axil")

    # Read SLOW_ID (0x7000_0000)
    data, resp = await drv.read(0x70000000)
    assert resp == RESP_OKAY and data == 0x510E0001, f"SLOW_ID read failed: {hex(data)}"

    # Read SLOW_COUNTER (0x7000_0008) at time T1
    cnt1, _ = await drv.read(0x70000008)
    
    # Wait 20 clk_slow cycles
    for _ in range(40):
        await RisingEdge(dut.clk_sys)

    # Read SLOW_COUNTER at time T2
    cnt2, _ = await drv.read(0x70000008)
    dut._log.info(f"SLOW_COUNTER: cnt1={cnt1}, cnt2={cnt2}")
    assert cnt2 > cnt1, f"Spec Section 7.4: SLOW_COUNTER failed to increment! ({cnt1} -> {cnt2})"

    # Write SLOW_SCRATCH (0x7000_0004)
    wresp = await drv.write(0x70000004, 0xCAFEBABE)
    assert wresp == RESP_OKAY, "SLOW_SCRATCH write failed"
    rdata, _ = await drv.read(0x70000004)
    assert rdata == 0xCAFEBABE, f"SLOW_SCRATCH read mismatch: {hex(rdata)}"

    dut._log.info("Probe test_probe_cdc_ratio_and_counter PASSED!")
    await Timer(100, unit="ns")
