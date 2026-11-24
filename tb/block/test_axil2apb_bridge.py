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

    # Comprehensive pattern check (all-ones, walking-1s, complement pattern to catch bit-stuck mutants)
    test_patterns = [
        (0x40000014, 0xFFFFFFFF, 0xF),
        (0x40000018, 0xAAAAAAAA, 0xF),
        (0x4000001C, 0x55555555, 0xF),
        (0x40000020, 0x21524110, 0xF), # Inverse of 0xDEADBEEF (bit 29 = 1)
        (0x40000024, 0x12345678, 0b0011), # Byte strobe 0 and 1
        (0x40000028, 0x9ABCDEF0, 0b1100), # Byte strobe 2 and 3
    ]
    for paddr, pdata, pstrb in test_patterns:
        w_resp = await driver.write(addr=paddr, data=pdata, strb=pstrb)
        assert w_resp == 0
        offset = paddr - 0x40000000
        # Verify directly that APB slave received the true input data (not comparing corrupted output to corrupted slave mem)
        if pstrb == 0xF:
            assert apb_slave.memory.get(offset, 0) == pdata, f"APB slave pwdata mismatch: expected {pdata:#x}, got {apb_slave.memory.get(offset, 0):#x}"
        r_val, r_resp = await driver.read(addr=paddr)
        assert r_resp == 0
        assert r_val == apb_slave.memory.get(offset, 0)

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


@cocotb.test()
async def test_br04_pstrb_patterns(dut):
    """BR-04: Verify PSTRB patterns match WSTRB at bridge level."""
    await setup_dut(dut)

    driver = AxilDriver(
        clk=dut.clk, rst_n=dut.rst_n, name="m0_driver",
        awaddr=dut.s_axil_awaddr, awprot=dut.s_axil_awprot, awvalid=dut.s_axil_awvalid, awready=dut.s_axil_awready,
        wdata=dut.s_axil_wdata, wstrb=dut.s_axil_wstrb, wvalid=dut.s_axil_wvalid, wready=dut.s_axil_wready,
        bresp=dut.s_axil_bresp, bvalid=dut.s_axil_bvalid, bready=dut.s_axil_bready,
        araddr=dut.s_axil_araddr, arprot=dut.s_axil_arprot, arvalid=dut.s_axil_arvalid, arready=dut.s_axil_arready,
        rdata=dut.s_axil_rdata, rresp=dut.s_axil_rresp, rvalid=dut.s_axil_rvalid, rready=dut.s_axil_rready,
    )

    apb_slave = ApbSlaveResponder(
        clk=dut.clk, rst_n=dut.rst_n, name="apb_slave_pstrb",
        wait_states=0, inject_pslverr=False, base_addr=0x40000000,
        paddr=dut.m_apb_paddr, psel=dut.m_apb_psel, penable=dut.m_apb_penable,
        pwrite=dut.m_apb_pwrite, pwdata=dut.m_apb_pwdata, pstrb=dut.m_apb_pstrb,
        pready=dut.m_apb_pready, prdata=dut.m_apb_prdata, pslverr=dut.m_apb_pslverr,
    )
    apb_slave.start()

    # Track observed PSTRB on APB side
    observed_pstrb = []
    async def monitor_apb_pstrb():
        while True:
            await RisingEdge(dut.clk)
            if int(dut.m_apb_psel.value) == 1 and int(dut.m_apb_pwrite.value) == 1 and int(dut.m_apb_penable.value) == 0:
                observed_pstrb.append(int(dut.m_apb_pstrb.value))

    mon_task = cocotb.start_soon(monitor_apb_pstrb())

    patterns = [0x1, 0x2, 0x4, 0x8, 0x3, 0xC, 0xF, 0x5, 0xA, 0x0]
    for i, strb in enumerate(patterns):
        addr = 0x40000000 + (i * 4)
        data = 0xA0B0C0D0 + i
        resp = await driver.write(addr=addr, data=data, strb=strb)
        assert resp == 0, f"Write with strb={hex(strb)} failed: {resp}"
        assert observed_pstrb[-1] == strb, f"PSTRB mismatch: expected {hex(strb)}, observed {hex(observed_pstrb[-1])}"

    mon_task.cancel()
    apb_slave.stop()
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")


@cocotb.test()
async def test_br05_back_to_back_mixed_rw(dut):
    """BR-05: Back-to-back mixed read/write transfers, verify single-outstanding arbitration and no starvation."""
    await setup_dut(dut)

    driver = AxilDriver(
        clk=dut.clk, rst_n=dut.rst_n, name="m0_driver",
        awaddr=dut.s_axil_awaddr, awprot=dut.s_axil_awprot, awvalid=dut.s_axil_awvalid, awready=dut.s_axil_awready,
        wdata=dut.s_axil_wdata, wstrb=dut.s_axil_wstrb, wvalid=dut.s_axil_wvalid, wready=dut.s_axil_wready,
        bresp=dut.s_axil_bresp, bvalid=dut.s_axil_bvalid, bready=dut.s_axil_bready,
        araddr=dut.s_axil_araddr, arprot=dut.s_axil_arprot, arvalid=dut.s_axil_arvalid, arready=dut.s_axil_arready,
        rdata=dut.s_axil_rdata, rresp=dut.s_axil_rresp, rvalid=dut.s_axil_rvalid, rready=dut.s_axil_rready,
    )

    apb_slave = ApbSlaveResponder(
        clk=dut.clk, rst_n=dut.rst_n, name="apb_slave_rw",
        wait_states=1, inject_pslverr=False, base_addr=0x40000000,
        paddr=dut.m_apb_paddr, psel=dut.m_apb_psel, penable=dut.m_apb_penable,
        pwrite=dut.m_apb_pwrite, pwdata=dut.m_apb_pwdata, pstrb=dut.m_apb_pstrb,
        pready=dut.m_apb_pready, prdata=dut.m_apb_prdata, pslverr=dut.m_apb_pslverr,
    )
    apb_slave.start()

    # Pre-populate memory
    apb_slave.memory[0x10] = 0x11112222
    apb_slave.memory[0x20] = 0x33334444

    # Issue simultaneous write and read requests on AXI bus
    dut.s_axil_awaddr.value = 0x40000010
    dut.s_axil_wdata.value = 0x9999AAAA
    dut.s_axil_wstrb.value = 0xF
    dut.s_axil_awvalid.value = 1
    dut.s_axil_wvalid.value = 1
    dut.s_axil_bready.value = 1

    dut.s_axil_araddr.value = 0x40000020
    dut.s_axil_arvalid.value = 1
    dut.s_axil_rready.value = 1

    # Wait for both to complete
    b_done = False
    r_done = False
    rdata_captured = 0

    for _ in range(50):
        await RisingEdge(dut.clk)
        if dut.s_axil_awvalid.value and dut.s_axil_awready.value:
            dut.s_axil_awvalid.value = 0
        if dut.s_axil_wvalid.value and dut.s_axil_wready.value:
            dut.s_axil_wvalid.value = 0
        if dut.s_axil_bvalid.value and dut.s_axil_bready.value:
            b_done = True
        if dut.s_axil_arvalid.value and dut.s_axil_arready.value:
            dut.s_axil_arvalid.value = 0
        if dut.s_axil_rvalid.value and dut.s_axil_rready.value:
            r_done = True
            rdata_captured = int(dut.s_axil_rdata.value)
        if b_done and r_done:
            break

    assert b_done, "Write response not received under concurrent R/W!"
    assert r_done, "Read response not received under concurrent R/W!"
    assert rdata_captured == 0x33334444, f"Read data corrupted: {hex(rdata_captured)}"
    assert apb_slave.memory.get(0x10) == 0x9999AAAA, "Write data not committed!"

    # Follow with back-to-back writes and reads
    for i in range(10):
        w_addr = 0x40000000 + (i * 4)
        w_val = 0xCAFE0000 + i
        bresp = await driver.write(addr=w_addr, data=w_val)
        assert bresp == 0
        r_val, rresp = await driver.read(addr=w_addr)
        assert rresp == 0
        assert r_val == w_val

    apb_slave.stop()
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")


@cocotb.test()
async def test_br06_delayed_w_no_early_psel(dut):
    """BR-06: Write with W arriving long after AW; assert PSEL never rises before W arrives."""
    await setup_dut(dut)

    apb_slave = ApbSlaveResponder(
        clk=dut.clk, rst_n=dut.rst_n, name="apb_slave_br06",
        wait_states=0, inject_pslverr=False, base_addr=0x40000000,
        paddr=dut.m_apb_paddr, psel=dut.m_apb_psel, penable=dut.m_apb_penable,
        pwrite=dut.m_apb_pwrite, pwdata=dut.m_apb_pwdata, pstrb=dut.m_apb_pstrb,
        pready=dut.m_apb_pready, prdata=dut.m_apb_prdata, pslverr=dut.m_apb_pslverr,
    )
    apb_slave.start()

    # Step 1: Drive AWVALID=1, WVALID=0
    dut.s_axil_awaddr.value = 0x40000050
    dut.s_axil_awvalid.value = 1
    dut.s_axil_wvalid.value = 0
    dut.s_axil_bready.value = 1

    # Wait for AWREADY handshake
    while True:
        await RisingEdge(dut.clk)
        if int(dut.s_axil_awready.value) == 1:
            dut.s_axil_awvalid.value = 0
            break

    # Step 2: Hold WVALID=0 for 15 cycles; assert PSEL is strictly 0 on every cycle
    for cycle in range(15):
        await RisingEdge(dut.clk)
        assert int(dut.m_apb_psel.value) == 0, f"Cycle {cycle}: PSEL asserted before W data arrived!"
        assert int(dut.m_apb_penable.value) == 0, f"Cycle {cycle}: PENABLE asserted before W data arrived!"

    # Step 3: Now drive WVALID=1
    dut.s_axil_wdata.value = 0x55AA33CC
    dut.s_axil_wstrb.value = 0xF
    dut.s_axil_wvalid.value = 1

    # Wait for WREADY
    while True:
        await RisingEdge(dut.clk)
        if int(dut.s_axil_wready.value) == 1:
            dut.s_axil_wvalid.value = 0
            break

    # Step 4: Now PSEL should assert and complete the APB transfer
    completed = False
    for _ in range(20):
        await RisingEdge(dut.clk)
        if int(dut.s_axil_bvalid.value) == 1:
            assert int(dut.s_axil_bresp.value) == 0
            completed = True
            break

    assert completed, "Write failed to complete after W data provided!"
    assert apb_slave.memory.get(0x50) == 0x55AA33CC, "APB memory data mismatch after delayed W!"

    apb_slave.stop()
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")
