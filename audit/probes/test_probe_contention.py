"""
test_probe_contention.py - Probe Test for Multi-Master Contention (Spec Section 7.2, XB-05, XB-06)
Tests:
- Two-master contention to the same slave (RAM): both execute without deadlock or data corruption.
- Two-master access to different slaves (RAM vs CSR): both execute concurrently in parallel.
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from probe_driver import ProbeAxilDriver

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
async def test_probe_same_slave_contention(dut):
    """M0 and M1 contending for the same slave (RAM) simultaneously (Spec XB-05)."""
    await reset_dut(dut)
    drv0 = ProbeAxilDriver(dut, dut.clk_sys, prefix="s0_axil")
    drv1 = ProbeAxilDriver(dut, dut.clk_sys, prefix="s1_axil")

    # M0 writes to 0x5000_0000, M1 writes to 0x5000_0004 simultaneously
    t0 = cocotb.start_soon(drv0.write(0x50000000, 0x11111111))
    t1 = cocotb.start_soon(drv1.write(0x50000004, 0x22222222))
    
    resp0 = await t0
    resp1 = await t1
    assert resp0 == 0 and resp1 == 0, f"Contention writes failed: {resp0}, {resp1}"

    # Read back and verify neither word corrupted the other
    d0, _ = await drv0.read(0x50000000)
    d1, _ = await drv1.read(0x50000004)
    assert d0 == 0x11111111, f"M0 RAM data corrupted: {hex(d0)}"
    assert d1 == 0x22222222, f"M1 RAM data corrupted: {hex(d1)}"
    dut._log.info("Same slave contention PASSED!")
    await Timer(100, unit="ns")

@cocotb.test()
async def test_probe_different_slave_parallel(dut):
    """M0 and M1 accessing different slaves simultaneously (Spec XB-06)."""
    await reset_dut(dut)
    drv0 = ProbeAxilDriver(dut, dut.clk_sys, prefix="s0_axil")
    drv1 = ProbeAxilDriver(dut, dut.clk_sys, prefix="s1_axil")

    # M0 writes to RAM (0x5000_0010), M1 writes to CSR SCRATCH (0x6000_0008)
    t0 = cocotb.start_soon(drv0.write(0x50000010, 0xA5A5A5A5))
    t1 = cocotb.start_soon(drv1.write(0x60000008, 0x5A5A5A5A))

    resp0 = await t0
    resp1 = await t1
    assert resp0 == 0 and resp1 == 0

    d0, _ = await drv0.read(0x50000010)
    d1, _ = await drv1.read(0x60000008)
    assert d0 == 0xA5A5A5A5 and d1 == 0x5A5A5A5A
    dut._log.info("Different slave parallel access PASSED!")
    await Timer(100, unit="ns")
