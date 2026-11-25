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
from cocotb.triggers import RisingEdge, Timer, ReadOnly
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../models")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../pyuvm")))
from axil_driver import AxilDriver
from apb_slave_responder import ApbSlaveResponder
from axil_monitor import AxilProtocolMonitor
from monitors.fabric_monitors import ApbBusMonitor
from func_cov.fabric_cov import CoverageCollector


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

    # Protection bit pass-through checks (AWPROT/ARPROT -> PPROT for all 8 values 0..7)
    observed_pprot = []
    async def monitor_apb_pprot():
        while True:
            await RisingEdge(dut.clk)
            if int(dut.m_apb_psel.value) == 1 and int(dut.m_apb_penable.value) == 0:
                observed_pprot.append((int(dut.m_apb_pwrite.value), int(dut.m_apb_pprot.value)))

    pprot_task = cocotb.start_soon(monitor_apb_pprot())
    for prot in range(8):
        paddr = 0x40000040 + (prot * 4)
        pdata = 0x55AA0000 + prot
        w_resp = await driver.write(addr=paddr, data=pdata, strb=0xF, prot=prot)
        assert w_resp == 0
        assert observed_pprot and observed_pprot[-1] == (1, prot), (
            f"BR-01 AWPROT->PPROT mismatch: expected (1, {prot}), observed {observed_pprot[-1] if observed_pprot else None}"
        )
        r_val, r_resp = await driver.read(addr=paddr, prot=prot)
        assert r_resp == 0
        assert r_val == pdata
        assert observed_pprot and observed_pprot[-1] == (0, prot), (
            f"BR-01 ARPROT->PPROT mismatch: expected (0, {prot}), observed {observed_pprot[-1] if observed_pprot else None}"
        )
    pprot_task.cancel()

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

        wait_checks = {"count": 0}

        async def _check_apb_wait_hold(checks=wait_checks):
            prev_hold = None
            while True:
                await RisingEdge(dut.clk)
                await ReadOnly()
                psel = int(dut.m_apb_psel.value)
                penable = int(dut.m_apb_penable.value)
                pready = int(dut.m_apb_pready.value)
                cur_bus = (
                    int(dut.m_apb_paddr.value),
                    int(dut.m_apb_pwrite.value),
                    int(dut.m_apb_pwdata.value),
                    int(dut.m_apb_pstrb.value),
                )
                if prev_hold is not None:
                    assert psel == 1, "BR-02: PSEL dropped while waiting for PREADY=0"
                    assert penable == 1, "BR-02: PENABLE dropped while waiting for PREADY=0"
                    assert cur_bus == prev_hold, (
                        f"BR-02: APB control/data signals mutated while PREADY=0: "
                        f"expected {prev_hold}, got {cur_bus}"
                    )
                    checks["count"] += 1
                if psel == 1 and penable == 1 and pready == 0:
                    prev_hold = cur_bus
                else:
                    prev_hold = None

        hold_task = cocotb.start_soon(_check_apb_wait_hold())

        # Write with non-all-ones PSTRB first, then full word write/readback (verifies PSTRB hold under PREADY=0)
        test_val = 0xCAFE0000 + ws
        resp = await driver.write(addr=0x40000020, data=test_val, strb=0xA)
        assert resp == 0, f"Expected OKAY, got {resp}"

        resp_full = await driver.write(addr=0x40000020, data=test_val, strb=0xF)
        assert resp_full == 0, f"Expected OKAY, got {resp_full}"

        data, rresp = await driver.read(addr=0x40000020)
        assert rresp == 0, f"Expected OKAY, got {rresp}"
        assert data == test_val, f"Expected {hex(test_val)}, got {hex(data)}"

        hold_task.cancel()
        assert wait_checks["count"] >= 3 * ws, (
            f"BR-02 ws={ws}: expected >= {3 * ws} PREADY=0 hold cycles, observed {wait_checks['count']}"
        )
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


@cocotb.test()
async def test_br07_apb_wait_err_cov(dut):
    """BR-07: Exercise APB wait states (0, 1, 2-4, 5+), PSLVERR, PSTRB classes, and W-before-AW ordering."""
    await setup_dut(dut)

    driver = AxilDriver(
        clk=dut.clk, rst_n=dut.rst_n, name="m0_driver",
        awaddr=dut.s_axil_awaddr, awprot=dut.s_axil_awprot, awvalid=dut.s_axil_awvalid, awready=dut.s_axil_awready,
        wdata=dut.s_axil_wdata, wstrb=dut.s_axil_wstrb, wvalid=dut.s_axil_wvalid, wready=dut.s_axil_wready,
        bresp=dut.s_axil_bresp, bvalid=dut.s_axil_bvalid, bready=dut.s_axil_bready,
        araddr=dut.s_axil_araddr, arprot=dut.s_axil_arprot, arvalid=dut.s_axil_arvalid, arready=dut.s_axil_arready,
        rdata=dut.s_axil_rdata, rresp=dut.s_axil_rresp, rvalid=dut.s_axil_rvalid, rready=dut.s_axil_rready,
    )

    apb_mon = ApbBusMonitor(
        clk=dut.clk, rst_n=dut.rst_n,
        psel=dut.m_apb_psel, penable=dut.m_apb_penable, pwrite=dut.m_apb_pwrite,
        pready=dut.m_apb_pready, pslverr=dut.m_apb_pslverr, pstrb=dut.m_apb_pstrb,
        paddr=dut.m_apb_paddr, dut=dut,
    )
    apb_mon.start()

    for ws in [0, 1, 3, 6]:
        for inject_err in [False, True]:
            apb_slave = ApbSlaveResponder(
                clk=dut.clk, rst_n=dut.rst_n, name=f"apb_cov_ws{ws}_err{int(inject_err)}",
                wait_states=ws, inject_pslverr=inject_err, base_addr=0x40000000,
                paddr=dut.m_apb_paddr, psel=dut.m_apb_psel, penable=dut.m_apb_penable,
                pwrite=dut.m_apb_pwrite, pwdata=dut.m_apb_pwdata, pstrb=dut.m_apb_pstrb,
                pready=dut.m_apb_pready, prdata=dut.m_apb_prdata, pslverr=dut.m_apb_pslverr,
            )
            apb_slave.start()

            exp_resp = 2 if inject_err else 0
            # Exercise W-first and AW-first staggered writes as well as byte/halfword/word/sparse strobes
            w_strbs = [0xF, 0x1, 0x3, 0x5] if ws == 0 and not inject_err else [0xF]
            for idx, strb in enumerate(w_strbs):
                order = "w_first" if (idx == 0 and ws == 1) else ("aw_first" if idx == 1 else "simultaneous")
                addr = 0x40000080 + (idx * 4)
                val = 0x10203040 + ws * 16 + idx
                resp = await driver.write(addr=addr, data=val, strb=strb, order=order)
                assert resp == exp_resp

                rdata, rresp = await driver.read(addr=addr)
                assert rresp == exp_resp
                assert int(dut.m_apb_pstrb.value) == 0, "APB4 requires PSTRB=0 on reads"
                if not inject_err and strb == 0xF:
                    assert rdata == val

            apb_slave.stop()
            await RisingEdge(dut.clk)

    apb_mon.stop()
    proj_dir = os.environ.get("PROJ_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    cov_path = os.path.join(proj_dir, "docs/logs/cov_bridge_block.yaml")
    CoverageCollector.get().configure(source="block", allowed_groups=["cg_apb"])
    CoverageCollector.get().export(cov_path, source="block", allowed_groups=["cg_apb"])
    await Timer(10, unit="ns")


@cocotb.test()
async def test_br08_addr_walk_and_ooo_backpressure(dut):
    """BR-08: Full 32-bit PADDR walking-1 pass-through, W-before-AW, PSTRB=0 on reads, and B/R backpressure."""
    await setup_dut(dut)

    driver = AxilDriver(
        clk=dut.clk, rst_n=dut.rst_n, name="m0_driver",
        awaddr=dut.s_axil_awaddr, awprot=dut.s_axil_awprot, awvalid=dut.s_axil_awvalid, awready=dut.s_axil_awready,
        wdata=dut.s_axil_wdata, wstrb=dut.s_axil_wstrb, wvalid=dut.s_axil_wvalid, wready=dut.s_axil_wready,
        bresp=dut.s_axil_bresp, bvalid=dut.s_axil_bvalid, bready=dut.s_axil_bready,
        araddr=dut.s_axil_araddr, arprot=dut.s_axil_arprot, arvalid=dut.s_axil_arvalid, arready=dut.s_axil_arready,
        rdata=dut.s_axil_rdata, rresp=dut.s_axil_rresp, rvalid=dut.s_axil_rvalid, rready=dut.s_axil_rready,
    )

    apb_captures = []

    async def monitor_apb_pins():
        while True:
            await RisingEdge(dut.clk)
            if int(dut.m_apb_psel.value) == 1 and int(dut.m_apb_penable.value) == 0:
                pwrite = int(dut.m_apb_pwrite.value)
                pstrb = int(dut.m_apb_pstrb.value)
                if pwrite == 0:
                    assert pstrb == 0, f"APB4 read transfer had non-zero PSTRB={pstrb:#x}"
                apb_captures.append((
                    int(dut.m_apb_paddr.value),
                    pwrite,
                    int(dut.m_apb_pprot.value),
                    int(dut.m_apb_pwdata.value),
                    pstrb,
                ))

    mon_task = cocotb.start_soon(monitor_apb_pins())

    # Custom lightweight APB responder supporting full 32-bit address decode cleanly
    async def full_addr_apb_responder():
        mem = {}
        while True:
            await RisingEdge(dut.clk)
            if int(dut.m_apb_psel.value) == 1 and int(dut.m_apb_penable.value) == 1:
                # 1 wait state then respond
                dut.m_apb_pready.value = 0
                await RisingEdge(dut.clk)
                pa = int(dut.m_apb_paddr.value)
                if int(dut.m_apb_pwrite.value) == 1:
                    mem[pa] = int(dut.m_apb_pwdata.value)
                else:
                    dut.m_apb_prdata.value = mem.get(pa, 0)
                dut.m_apb_pslverr.value = 0
                dut.m_apb_pready.value = 1
            else:
                dut.m_apb_pready.value = 0

    dut.m_apb_pready.value = 0
    dut.m_apb_pslverr.value = 0
    resp_task = cocotb.start_soon(full_addr_apb_responder())

    # 1. Full 32-bit walking-1 address check on both write (w_first/aw_first) and read
    for bit in range(32):
        addr = 1 << bit
        val = (0xA5000001 ^ (bit << 8)) & 0xFFFFFFFF
        ord_m = "w_first" if (bit % 2 == 0) else "aw_first"
        bresp = await driver.write(addr=addr, data=val, strb=0xF, prot=(bit & 7), order=ord_m, bready_delay=(bit % 3))
        assert bresp == 0
        assert apb_captures[-1][0] == addr and apb_captures[-1][2] == (bit & 7) and apb_captures[-1][3] == val
        rdata, rresp = await driver.read(addr=addr, prot=((7 - bit) & 7), rready_delay=(bit % 3))
        assert rresp == 0 and rdata == val
        assert apb_captures[-1][0] == addr and apb_captures[-1][2] == ((7 - bit) & 7) and apb_captures[-1][4] == 0

    # 2. Manual W-before-AW long stagger verifying PSEL stays 0 until AW arrives (kills ST_WAIT_AW gaps)
    dut.s_axil_wdata.value = 0x13572468
    dut.s_axil_wstrb.value = 0b0101
    dut.s_axil_wvalid.value = 1
    dut.s_axil_awvalid.value = 0
    dut.s_axil_bready.value = 0
    for _ in range(8):
        await RisingEdge(dut.clk)
        assert int(dut.m_apb_psel.value) == 0, "PSEL asserted before AW arrived in w_first"
        if int(dut.s_axil_wready.value) == 1:
            dut.s_axil_wvalid.value = 0
    dut.s_axil_awaddr.value = 0x40000100
    dut.s_axil_awprot.value = 0b101
    dut.s_axil_awvalid.value = 1
    b_seen = False
    for _ in range(20):
        await RisingEdge(dut.clk)
        if int(dut.s_axil_awready.value) == 1:
            dut.s_axil_awvalid.value = 0
        if int(dut.s_axil_bvalid.value) == 1:
            b_seen = True
            break
    assert b_seen
    for _ in range(3):
        await RisingEdge(dut.clk)
        assert int(dut.s_axil_bvalid.value) == 1
    dut.s_axil_bready.value = 1
    await RisingEdge(dut.clk)
    dut.s_axil_bready.value = 0
    assert apb_captures[-1] == (0x40000100, 1, 0b101, 0x13572468, 0b0101)

    mon_task.cancel()
    resp_task.cancel()
    await Timer(10, unit="ns")
