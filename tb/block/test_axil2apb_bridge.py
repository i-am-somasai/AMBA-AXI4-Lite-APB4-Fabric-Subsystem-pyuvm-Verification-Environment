# tb/block/test_axil2apb_bridge.py
"""
Block-level tests for AXI4-Lite to APB4 Bridge (axil2apb_bridge).
Implements verification plan tests:
- BR-01: Single write and read, 0 wait states (checks APB SETUP/ACCESS timing)
- BR-02: Wait states 1..N (checks PENABLE stable, signals held)
- BR-03: PSLVERR on read and write (maps to SLVERR)
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../models")))
from axil_driver import AxilDriver
from apb_slave_responder import ApbSlaveResponder
from axil_monitor import AxilProtocolMonitor


async def setup_dut(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst_n.value = 0
    dut.s_axil_awvalid.value = 0
    dut.s_axil_wvalid.value = 0
    dut.s_axil_bready.value = 0
    dut.s_axil_arvalid.value = 0
    dut.s_axil_rready.value = 0
    dut.m_apb_pready.value = 1
    dut.m_apb_prdata.value = 0
    dut.m_apb_pslverr.value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_br01_single_rw_zero_wait(dut):
    """BR-01: Verify single write and read with zero wait states."""
    await setup_dut(dut)

    driver = AxilDriver(
        clk=dut.clk, rst_n=dut.rst_n, name="m0_driver",
        awaddr=dut.s_axil_awaddr, awprot=dut.s_axil_awprot, awvalid=dut.s_axil_awvalid, awready=dut.s_axil_awready,
        wdata=dut.s_axil_wdata, wstrb=dut.s_axil_wstrb, wvalid=dut.s_axil_wvalid, wready=dut.s_axil_wready,
        bresp=dut.s_axil_bresp, bvalid=dut.s_axil_bvalid, bready=dut.s_axil_bready,
        araddr=dut.s_axil_araddr, arprot=dut.s_axil_arprot, arvalid=dut.s_axil_arvalid, arready=dut.s_axil_arready,
        rdata=dut.s_axil_rdata, rresp=dut.s_axil_rresp, rvalid=dut.s_axil_rvalid, rready=dut.s_axil_rready,
    )

    monitor = AxilProtocolMonitor(
        clk=dut.clk, rst_n=dut.rst_n, name="axil_mon",
        awaddr=dut.s_axil_awaddr, awprot=dut.s_axil_awprot, awvalid=dut.s_axil_awvalid, awready=dut.s_axil_awready,
        wdata=dut.s_axil_wdata, wstrb=dut.s_axil_wstrb, wvalid=dut.s_axil_wvalid, wready=dut.s_axil_wready,
        bresp=dut.s_axil_bresp, bvalid=dut.s_axil_bvalid, bready=dut.s_axil_bready,
        araddr=dut.s_axil_araddr, arprot=dut.s_axil_arprot, arvalid=dut.s_axil_arvalid, arready=dut.s_axil_arready,
        rdata=dut.s_axil_rdata, rresp=dut.s_axil_rresp, rvalid=dut.s_axil_rvalid, rready=dut.s_axil_rready,
    )
    monitor.start()

    apb_slave = ApbSlaveResponder(
        clk=dut.clk, rst_n=dut.rst_n, name="apb_slave",
        wait_states=0, inject_pslverr=False, base_addr=0x40000000,
        paddr=dut.m_apb_paddr, psel=dut.m_apb_psel, penable=dut.m_apb_penable,
        pwrite=dut.m_apb_pwrite, pwdata=dut.m_apb_pwdata, pstrb=dut.m_apb_pstrb,
        pready=dut.m_apb_pready, prdata=dut.m_apb_prdata, pslverr=dut.m_apb_pslverr,
    )
    apb_slave.start()

    # Write test
    resp = await driver.write(addr=0x40000010, data=0xDEADBEEF, strb=0xF)
    assert resp == 0, f"Expected OKAY (0), got {resp}"
    assert apb_slave.memory.get(0x10) == 0xDEADBEEF, f"APB memory mismatch: {hex(apb_slave.memory.get(0x10, 0))}"

    # Read test
    data, rresp = await driver.read(addr=0x40000010)
    assert rresp == 0, f"Expected OKAY (0), got {rresp}"
    assert data == 0xDEADBEEF, f"Expected 0xDEADBEEF, got {hex(data)}"

    monitor.stop()
    apb_slave.stop()
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")


@cocotb.test()
async def test_br02_wait_states(dut):
    """BR-02: Verify APB wait states (PREADY delayed 1..4 cycles)."""
    await setup_dut(dut)

    driver = AxilDriver(
        clk=dut.clk, rst_n=dut.rst_n, name="m0_driver",
        awaddr=dut.s_axil_awaddr, awprot=dut.s_axil_awprot, awvalid=dut.s_axil_awvalid, awready=dut.s_axil_awready,
        wdata=dut.s_axil_wdata, wstrb=dut.s_axil_wstrb, wvalid=dut.s_axil_wvalid, wready=dut.s_axil_wready,
        bresp=dut.s_axil_bresp, bvalid=dut.s_axil_bvalid, bready=dut.s_axil_bready,
        araddr=dut.s_axil_araddr, arprot=dut.s_axil_arprot, arvalid=dut.s_axil_arvalid, arready=dut.s_axil_arready,
        rdata=dut.s_axil_rdata, rresp=dut.s_axil_rresp, rvalid=dut.s_axil_rvalid, rready=dut.s_axil_rready,
    )

    for ws in [1, 2, 4]:
        apb_slave = ApbSlaveResponder(
            clk=dut.clk, rst_n=dut.rst_n, name=f"apb_slave_ws{ws}",
            wait_states=ws, inject_pslverr=False, base_addr=0x40000000,
            paddr=dut.m_apb_paddr, psel=dut.m_apb_psel, penable=dut.m_apb_penable,
            pwrite=dut.m_apb_pwrite, pwdata=dut.m_apb_pwdata, pstrb=dut.m_apb_pstrb,
            pready=dut.m_apb_pready, prdata=dut.m_apb_prdata, pslverr=dut.m_apb_pslverr,
        )
        apb_slave.start()

        # Write with wait states
        test_val = 0xCAFE0000 + ws
        resp = await driver.write(addr=0x40000020, data=test_val, strb=0xF)
        assert resp == 0, f"Expected OKAY, got {resp}"

        # Read back
        data, rresp = await driver.read(addr=0x40000020)
        assert rresp == 0, f"Expected OKAY, got {rresp}"
        assert data == test_val, f"Expected {hex(test_val)}, got {hex(data)}"

        apb_slave.stop()
        await RisingEdge(dut.clk)

    await Timer(10, unit="ns")


@cocotb.test()
async def test_br03_pslverr_propagation(dut):
    """BR-03: Verify PSLVERR propagation to AXI-Lite SLVERR (2'b10)."""
    await setup_dut(dut)

    driver = AxilDriver(
        clk=dut.clk, rst_n=dut.rst_n, name="m0_driver",
        awaddr=dut.s_axil_awaddr, awprot=dut.s_axil_awprot, awvalid=dut.s_axil_awvalid, awready=dut.s_axil_awready,
        wdata=dut.s_axil_wdata, wstrb=dut.s_axil_wstrb, wvalid=dut.s_axil_wvalid, wready=dut.s_axil_wready,
        bresp=dut.s_axil_bresp, bvalid=dut.s_axil_bvalid, bready=dut.s_axil_bready,
        araddr=dut.s_axil_araddr, arprot=dut.s_axil_arprot, arvalid=dut.s_axil_arvalid, arready=dut.s_axil_arready,
        rdata=dut.s_axil_rdata, rresp=dut.s_axil_rresp, rvalid=dut.s_axil_rvalid, rready=dut.s_axil_rready,
    )

    # Configure APB slave with PSLVERR injected
    apb_slave = ApbSlaveResponder(
        clk=dut.clk, rst_n=dut.rst_n, name="apb_slave_err",
        wait_states=1, inject_pslverr=True, base_addr=0x40000000,
        paddr=dut.m_apb_paddr, psel=dut.m_apb_psel, penable=dut.m_apb_penable,
        pwrite=dut.m_apb_pwrite, pwdata=dut.m_apb_pwdata, pstrb=dut.m_apb_pstrb,
        pready=dut.m_apb_pready, prdata=dut.m_apb_prdata, pslverr=dut.m_apb_pslverr,
    )
    apb_slave.start()

    # Write should yield SLVERR (0b10 = 2)
    bresp = await driver.write(addr=0x40000030, data=0x11223344)
    assert bresp == 2, f"Expected SLVERR (2), got {bresp}"

    # Read should yield SLVERR (0b10 = 2)
    _, rresp = await driver.read(addr=0x40000030)
    assert rresp == 2, f"Expected SLVERR (2), got {rresp}"

    apb_slave.stop()
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")
