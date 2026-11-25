# tb/block/test_axil_xbar.py
"""
Block-level directed tests for AXI4-Lite Crossbar (axil_xbar).
Implements verification plan tests:
- XB-01: Single write and read, each master to each mapped slave (S0..S3)
- XB-02: Write-then-read data integrity on RAM (S1)
- XB-03: All 16 WSTRB patterns on RAM
- XB-04: Unmapped read and write (DECERR, no hang)
- XB-05: Both masters to the same slave simultaneously (contention serialization)
- XB-06: Both masters to different slaves simultaneously (parallel completion)
- XB-07: Arbitration fairness under sustained contention (grant difference <= 1)
- XB-08: Write ordering permutations (AW first, W first, simultaneous)
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import sys
import os
import random
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../models")))
from axil_driver import AxilDriver
from axil_slave_responder import AxilSlaveResponder
from axil_monitor import AxilProtocolMonitor


class XbarTestbench:
    def __init__(self, dut):
        self.dut = dut

        # Master 0 Driver
        self.m0 = AxilDriver(
            clk=dut.clk, rst_n=dut.rst_n, name="m0_driver",
            awaddr=dut.m0_awaddr, awprot=dut.m0_awprot, awvalid=dut.m0_awvalid, awready=dut.m0_awready,
            wdata=dut.m0_wdata, wstrb=dut.m0_wstrb, wvalid=dut.m0_wvalid, wready=dut.m0_wready,
            bresp=dut.m0_bresp, bvalid=dut.m0_bvalid, bready=dut.m0_bready,
            araddr=dut.m0_araddr, arprot=dut.m0_arprot, arvalid=dut.m0_arvalid, arready=dut.m0_arready,
            rdata=dut.m0_rdata, rresp=dut.m0_rresp, rvalid=dut.m0_rvalid, rready=dut.m0_rready,
        )

        # Master 1 Driver
        self.m1 = AxilDriver(
            clk=dut.clk, rst_n=dut.rst_n, name="m1_driver",
            awaddr=dut.m1_awaddr, awprot=dut.m1_awprot, awvalid=dut.m1_awvalid, awready=dut.m1_awready,
            wdata=dut.m1_wdata, wstrb=dut.m1_wstrb, wvalid=dut.m1_wvalid, wready=dut.m1_wready,
            bresp=dut.m1_bresp, bvalid=dut.m1_bvalid, bready=dut.m1_bready,
            araddr=dut.m1_araddr, arprot=dut.m1_arprot, arvalid=dut.m1_arvalid, arready=dut.m1_arready,
            rdata=dut.m1_rdata, rresp=dut.m1_rresp, rvalid=dut.m1_rvalid, rready=dut.m1_rready,
        )

        # Slave Responders (S0: APB, S1: RAM, S2: CSR, S3: CDC)
        self.s0 = AxilSlaveResponder(
            clk=dut.clk, rst_n=dut.rst_n, name="s0_apb", base_addr=0x40000000,
            awaddr=dut.s0_awaddr, awprot=dut.s0_awprot, awvalid=dut.s0_awvalid, awready=dut.s0_awready,
            wdata=dut.s0_wdata, wstrb=dut.s0_wstrb, wvalid=dut.s0_wvalid, wready=dut.s0_wready,
            bresp=dut.s0_bresp, bvalid=dut.s0_bvalid, bready=dut.s0_bready,
            araddr=dut.s0_araddr, arprot=dut.s0_arprot, arvalid=dut.s0_arvalid, arready=dut.s0_arready,
            rdata=dut.s0_rdata, rresp=dut.s0_rresp, rvalid=dut.s0_rvalid, rready=dut.s0_rready,
        )

        self.s1 = AxilSlaveResponder(
            clk=dut.clk, rst_n=dut.rst_n, name="s1_ram", base_addr=0x50000000,
            awaddr=dut.s1_awaddr, awprot=dut.s1_awprot, awvalid=dut.s1_awvalid, awready=dut.s1_awready,
            wdata=dut.s1_wdata, wstrb=dut.s1_wstrb, wvalid=dut.s1_wvalid, wready=dut.s1_wready,
            bresp=dut.s1_bresp, bvalid=dut.s1_bvalid, bready=dut.s1_bready,
            araddr=dut.s1_araddr, arprot=dut.s1_arprot, arvalid=dut.s1_arvalid, arready=dut.s1_arready,
            rdata=dut.s1_rdata, rresp=dut.s1_rresp, rvalid=dut.s1_rvalid, rready=dut.s1_rready,
        )

        self.s2 = AxilSlaveResponder(
            clk=dut.clk, rst_n=dut.rst_n, name="s2_csr", base_addr=0x60000000,
            awaddr=dut.s2_awaddr, awprot=dut.s2_awprot, awvalid=dut.s2_awvalid, awready=dut.s2_awready,
            wdata=dut.s2_wdata, wstrb=dut.s2_wstrb, wvalid=dut.s2_wvalid, wready=dut.s2_wready,
            bresp=dut.s2_bresp, bvalid=dut.s2_bvalid, bready=dut.s2_bready,
            araddr=dut.s2_araddr, arprot=dut.s2_arprot, arvalid=dut.s2_arvalid, arready=dut.s2_arready,
            rdata=dut.s2_rdata, rresp=dut.s2_rresp, rvalid=dut.s2_rvalid, rready=dut.s2_rready,
        )

        self.s3 = AxilSlaveResponder(
            clk=dut.clk, rst_n=dut.rst_n, name="s3_cdc", base_addr=0x70000000,
            awaddr=dut.s3_awaddr, awprot=dut.s3_awprot, awvalid=dut.s3_awvalid, awready=dut.s3_awready,
            wdata=dut.s3_wdata, wstrb=dut.s3_wstrb, wvalid=dut.s3_wvalid, wready=dut.s3_wready,
            bresp=dut.s3_bresp, bvalid=dut.s3_bvalid, bready=dut.s3_bready,
            araddr=dut.s3_araddr, arprot=dut.s3_arprot, arvalid=dut.s3_arvalid, arready=dut.s3_arready,
            rdata=dut.s3_rdata, rresp=dut.s3_rresp, rvalid=dut.s3_rvalid, rready=dut.s3_rready,
        )

        # Monitors
        self.mon0 = AxilProtocolMonitor(
            clk=dut.clk, rst_n=dut.rst_n, name="m0_mon",
            awaddr=dut.m0_awaddr, awprot=dut.m0_awprot, awvalid=dut.m0_awvalid, awready=dut.m0_awready,
            wdata=dut.m0_wdata, wstrb=dut.m0_wstrb, wvalid=dut.m0_wvalid, wready=dut.m0_wready,
            bresp=dut.m0_bresp, bvalid=dut.m0_bvalid, bready=dut.m0_bready,
            araddr=dut.m0_araddr, arprot=dut.m0_arprot, arvalid=dut.m0_arvalid, arready=dut.m0_arready,
            rdata=dut.m0_rdata, rresp=dut.m0_rresp, rvalid=dut.m0_rvalid, rready=dut.m0_rready,
        )

        self.mon1 = AxilProtocolMonitor(
            clk=dut.clk, rst_n=dut.rst_n, name="m1_mon",
            awaddr=dut.m1_awaddr, awprot=dut.m1_awprot, awvalid=dut.m1_awvalid, awready=dut.m1_awready,
            wdata=dut.m1_wdata, wstrb=dut.m1_wstrb, wvalid=dut.m1_wvalid, wready=dut.m1_wready,
            bresp=dut.m1_bresp, bvalid=dut.m1_bvalid, bready=dut.m1_bready,
            araddr=dut.m1_araddr, arprot=dut.m1_arprot, arvalid=dut.m1_arvalid, arready=dut.m1_arready,
            rdata=dut.m1_rdata, rresp=dut.m1_rresp, rvalid=dut.m1_rvalid, rready=dut.m1_rready,
        )

    async def reset(self):
        cocotb.start_soon(Clock(self.dut.clk, 10, unit="ns").start())
        self.dut.rst_n.value = 0
        self.dut.m0_awvalid.value = 0
        self.dut.m0_wvalid.value = 0
        self.dut.m0_bready.value = 0
        self.dut.m0_arvalid.value = 0
        self.dut.m0_rready.value = 0

        self.dut.m1_awvalid.value = 0
        self.dut.m1_wvalid.value = 0
        self.dut.m1_bready.value = 0
        self.dut.m1_arvalid.value = 0
        self.dut.m1_rready.value = 0

        self.s0.start()
        self.s1.start()
        self.s2.start()
        self.s3.start()
        self.mon0.start()
        self.mon1.start()

        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        self.dut.rst_n.value = 1
        await RisingEdge(self.dut.clk)

    def stop_all(self):
        self.s0.stop()
        self.s1.stop()
        self.s2.stop()
        self.s3.stop()
        self.mon0.stop()
        self.mon1.stop()


@cocotb.test()
async def test_xb01_single_rw_each_master_to_each_slave(dut):
    """XB-01: Single write and read, each master to each mapped slave (S0..S3)."""
    tb = XbarTestbench(dut)
    await tb.reset()

    slaves = [
        ("S0_APB", 0x40000000),
        ("S1_RAM", 0x50000000),
        ("S2_CSR", 0x60000000),
        ("S3_CDC", 0x70000000),
    ]

    for name, base in slaves:
        # Master 0 access
        data_m0 = 0xA0000000 | (base >> 16)
        bresp0 = await tb.m0.write(addr=base + 0x10, data=data_m0, strb=0xF)
        assert bresp0 == 0, f"M0 write to {name} failed with resp {bresp0}"
        rdata0, rresp0 = await tb.m0.read(addr=base + 0x10)
        assert rresp0 == 0, f"M0 read from {name} failed with resp {rresp0}"
        assert rdata0 == data_m0, f"M0 data mismatch on {name}: expected {hex(data_m0)}, got {hex(rdata0)}"

        # Master 1 access
        data_m1 = 0xB0000000 | (base >> 16)
        bresp1 = await tb.m1.write(addr=base + 0x20, data=data_m1, strb=0xF)
        assert bresp1 == 0, f"M1 write to {name} failed with resp {bresp1}"
        rdata1, rresp1 = await tb.m1.read(addr=base + 0x20)
        assert rresp1 == 0, f"M1 read from {name} failed with resp {rresp1}"
        assert rdata1 == data_m1, f"M1 data mismatch on {name}: expected {hex(data_m1)}, got {hex(rdata1)}"

    tb.stop_all()
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")


@cocotb.test()
async def test_xb02_ram_data_integrity(dut):
    """XB-02 (L1 crossbar): Write-then-read data integrity across S1 via AxilSlaveResponder.

    Real axil_ram RTL storage is covered by L0 (tb/unit/test_axil_ram.py::test_axil_ram_operations)
    and L2 subsystem tests (tb/block/test_amba_fabric_top.py::test_top01_register_map_connectivity).
    """
    tb = XbarTestbench(dut)
    await tb.reset()

    base = 0x50000000
    test_data = [0x11112222, 0x33334444, 0x55556666, 0x77778888, 0x9999AAAA, 0xBBBBCCCC]

    # Write burst
    for i, val in enumerate(test_data):
        bresp = await tb.m0.write(addr=base + i * 4, data=val)
        assert bresp == 0, f"RAM write at offset {i*4} failed with {bresp}"

    # Read back and verify
    for i, expected in enumerate(test_data):
        rdata, rresp = await tb.m0.read(addr=base + i * 4)
        assert rresp == 0, f"RAM read at offset {i*4} failed with {rresp}"
        assert rdata == expected, f"RAM data mismatch at offset {i*4}: expected {hex(expected)}, got {hex(rdata)}"

    tb.stop_all()
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")


@cocotb.test()
async def test_xb03_wstrb_patterns(dut):
    """XB-03 (L1 crossbar): All 16 WSTRB patterns routed across S1/S2 via AxilSlaveResponder.

    Real axil_ram and axil_csr RTL byte-strobe masking is covered by L0
    (tb/unit/test_axil_ram.py::test_axil_ram_operations, tb/unit/test_axil_csr.py::test_cs02_access_types_w1c)
    and L2 (tb/pyuvm/tests/test_directed.py::test_sys_strobe_patterns).
    """
    tb = XbarTestbench(dut)
    await tb.reset()

    targets = [
        ("RAM_S1", 0x50000100, False),
        ("CSR_S2", 0x6000000C, True),
    ]
    for label, base_or_addr, single_addr in targets:
        for strb in range(16):
            addr = base_or_addr if single_addr else (base_or_addr + strb * 4)
            # Initialize word with 0xA5A55A5A so strb=0 and partial clears are proven
            await tb.m0.write(addr=addr, data=0xA5A55A5A, strb=0xF)

            # Write pattern with tested strb
            write_val = 0x1234C3D4 ^ (strb * 0x01010101)
            bresp = await tb.m0.write(addr=addr, data=write_val, strb=strb)
            assert bresp == 0, f"{label} write failed for strb {hex(strb)}: bresp={bresp}"

            # Read back
            rdata, rresp = await tb.m0.read(addr=addr)
            assert rresp == 0, f"{label} read failed for strb {hex(strb)}: rresp={rresp}"

            # Compute expected byte-merged value against initial 0xA5A55A5A
            expected = 0
            for b in range(4):
                mask = 0xFF << (8 * b)
                if (strb >> b) & 1:
                    expected |= (write_val & mask)
                else:
                    expected |= (0xA5A55A5A & mask)

            assert rdata == expected, (
                f"{label} WSTRB {hex(strb)} mismatch: expected {hex(expected)}, got {hex(rdata)}"
            )

    tb.stop_all()
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")


@cocotb.test()
async def test_xb04_unmapped_decerr(dut):
    """XB-04: Unmapped addresses return DECERR (2'b11), without hang."""
    tb = XbarTestbench(dut)
    await tb.reset()

    unmapped_addrs = [
        0x10000000, # Below APB
        0x30000000, # Region 0x3000_0000
        0x40100000, # Outside 64KB APB
        0x50010000, # Outside 4KB RAM
        0x80000000, # High unmapped address
        0xFFFFFFFC, # Top of 32-bit address space
    ]

    for addr in unmapped_addrs:
        # Write to unmapped address
        bresp = await tb.m0.write(addr=addr, data=0xDEADBEEF)
        assert bresp == 3, f"Expected DECERR (3) for write to unmapped {hex(addr)}, got {bresp}"

        # Read from unmapped address
        _, rresp = await tb.m0.read(addr=addr)
        assert rresp == 3, f"Expected DECERR (3) for read from unmapped {hex(addr)}, got {rresp}"

    tb.stop_all()
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")


@cocotb.test()
async def test_xb05_contention_same_slave(dut):
    """XB-05: Both masters to the same slave simultaneously (contention serialization)."""
    tb = XbarTestbench(dut)
    await tb.reset()

    # Both target S1 (RAM)
    addr0 = 0x50000080
    addr1 = 0x50000084
    val0 = 0x12345678
    val1 = 0x87654321

    # Issue writes concurrently
    t0 = cocotb.start_soon(tb.m0.write(addr=addr0, data=val0))
    t1 = cocotb.start_soon(tb.m1.write(addr=addr1, data=val1))

    resp0 = await t0
    resp1 = await t1

    assert resp0 == 0, f"M0 contention write failed: {resp0}"
    assert resp1 == 0, f"M1 contention write failed: {resp1}"

    # Read back from both masters
    d0, r0 = await tb.m0.read(addr=addr0)
    d1, r1 = await tb.m1.read(addr=addr1)

    assert r0 == 0 and d0 == val0, f"M0 data corrupted under contention: got {hex(d0)}"
    assert r1 == 0 and d1 == val1, f"M1 data corrupted under contention: got {hex(d1)}"

    tb.stop_all()
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")


@cocotb.test()
async def test_xb06_parallel_different_slaves(dut):
    """XB-06: Both masters access different slaves simultaneously without serialization stall."""
    tb = XbarTestbench(dut)
    await tb.reset()

    # M0 targets S0 (APB), M1 targets S1 (RAM)
    addr0 = 0x40000040
    addr1 = 0x50000040

    cycle_start = cocotb.utils.get_sim_time('ns')

    t0 = cocotb.start_soon(tb.m0.write(addr=addr0, data=0xAAAA1111))
    t1 = cocotb.start_soon(tb.m1.write(addr=addr1, data=0xBBBB2222))

    r0 = await t0
    r1 = await t1

    cycle_end = cocotb.utils.get_sim_time('ns')
    duration_ns = cycle_end - cycle_start

    assert r0 == 0 and r1 == 0, "Parallel writes to S0 and S1 failed"
    # 2 writes running in parallel should take ~30-40 ns (3-4 clock cycles)
    assert duration_ns <= 60, f"Parallel execution took unexpectedly long: {duration_ns} ns"

    tb.stop_all()
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")


@cocotb.test()
async def test_xb07_arbitration_fairness(dut):
    """XB-07: Arbitration fairness under continuous contention (diff <= 1 for WR and RD)."""
    tb = XbarTestbench(dut)
    await tb.reset()

    window_txns = 100
    max_cycles = 4000

    # ------------------------------------------------------------------
    # 1. Continuous back-to-back WRITE contention on S1 (0x5000_0050/54)
    # Masters re-assert AWVALID/WVALID on the same cycle as B handshake.
    # ------------------------------------------------------------------
    wr_done = [0, 0]
    m_wr_state = [
        {"aw_hs": False, "w_hs": False, "addr": 0x50000050},
        {"aw_hs": False, "w_hs": False, "addr": 0x50000054},
    ]

    dut.m0_awaddr.value = m_wr_state[0]["addr"]
    dut.m0_awprot.value = 0
    dut.m0_wdata.value = 0x1000
    dut.m0_wstrb.value = 0xF
    dut.m0_awvalid.value = 1
    dut.m0_wvalid.value = 1
    dut.m0_bready.value = 1

    dut.m1_awaddr.value = m_wr_state[1]["addr"]
    dut.m1_awprot.value = 0
    dut.m1_wdata.value = 0x2000
    dut.m1_wstrb.value = 0xF
    dut.m1_awvalid.value = 1
    dut.m1_wvalid.value = 1
    dut.m1_bready.value = 1

    for _ in range(max_cycles):
        await RisingEdge(dut.clk)
        ports = [
            (dut.m0_awvalid, dut.m0_awready, dut.m0_wvalid, dut.m0_wready,
             dut.m0_bvalid, dut.m0_bready, dut.m0_bresp, dut.m0_wdata, 0),
            (dut.m1_awvalid, dut.m1_awready, dut.m1_wvalid, dut.m1_wready,
             dut.m1_bvalid, dut.m1_bready, dut.m1_bresp, dut.m1_wdata, 1),
        ]
        completed_this_cycle = False
        for awv, awr, wv, wr, bv, br, bresp_sig, wdata_sig, idx in ports:
            st = m_wr_state[idx]
            if int(awv.value) == 1 and int(awr.value) == 1:
                st["aw_hs"] = True
                awv.value = 0
            if int(wv.value) == 1 and int(wr.value) == 1:
                st["w_hs"] = True
                wv.value = 0
            if int(bv.value) == 1 and int(br.value) == 1:
                assert int(bresp_sig.value) == 0, f"XB-07 M{idx} write failed with bresp={int(bresp_sig.value)}"
                wr_done[idx] += 1
                completed_this_cycle = True
                st["aw_hs"] = False
                st["w_hs"] = False
                if (wr_done[0] + wr_done[1]) < window_txns:
                    wdata_sig.value = ((idx + 1) << 12) + wr_done[idx]
                    awv.value = 1
                    wv.value = 1

        if completed_this_cycle:
            diff = abs(wr_done[0] - wr_done[1])
            assert diff <= 1, (
                f"XB-07 WRITE arbitration unfair mid-window at total={wr_done[0] + wr_done[1]}: "
                f"M0={wr_done[0]}, M1={wr_done[1]} (diff={diff} > 1)"
            )
            if (wr_done[0] + wr_done[1]) >= window_txns:
                break

    # Drain any still-asserted AWVALID/WVALID/BVALID without ever dropping VALID before READY
    for _ in range(30):
        m0_idle = (int(dut.m0_awvalid.value) == 0 and int(dut.m0_wvalid.value) == 0 and int(dut.m0_bvalid.value) == 0)
        m1_idle = (int(dut.m1_awvalid.value) == 0 and int(dut.m1_wvalid.value) == 0 and int(dut.m1_bvalid.value) == 0)
        if m0_idle and m1_idle:
            break
        await RisingEdge(dut.clk)
        for awv, awr, wv, wr, bv, br in [
            (dut.m0_awvalid, dut.m0_awready, dut.m0_wvalid, dut.m0_wready, dut.m0_bvalid, dut.m0_bready),
            (dut.m1_awvalid, dut.m1_awready, dut.m1_wvalid, dut.m1_wready, dut.m1_bvalid, dut.m1_bready),
        ]:
            if int(awv.value) == 1 and int(awr.value) == 1:
                awv.value = 0
            if int(wv.value) == 1 and int(wr.value) == 1:
                wv.value = 0
    dut.m0_bready.value = 0
    dut.m1_bready.value = 0

    assert (wr_done[0] + wr_done[1]) >= window_txns, (
        f"XB-07 WRITE window timed out: M0={wr_done[0]}, M1={wr_done[1]}"
    )
    assert abs(wr_done[0] - wr_done[1]) <= 1, (
        f"XB-07 WRITE final count difference > 1: M0={wr_done[0]}, M1={wr_done[1]}"
    )

    # ------------------------------------------------------------------
    # 2. Continuous back-to-back READ contention on S1 (0x5000_0050/54)
    # Masters re-assert ARVALID on the same cycle as R handshake.
    # ------------------------------------------------------------------
    rd_done = [0, 0]
    dut.m0_araddr.value = 0x50000050
    dut.m0_arprot.value = 0
    dut.m0_arvalid.value = 1
    dut.m0_rready.value = 1

    dut.m1_araddr.value = 0x50000054
    dut.m1_arprot.value = 0
    dut.m1_arvalid.value = 1
    dut.m1_rready.value = 1

    for _ in range(max_cycles):
        await RisingEdge(dut.clk)
        ports_rd = [
            (dut.m0_arvalid, dut.m0_arready, dut.m0_rvalid, dut.m0_rready, dut.m0_rresp, 0),
            (dut.m1_arvalid, dut.m1_arready, dut.m1_rvalid, dut.m1_rready, dut.m1_rresp, 1),
        ]
        completed_this_cycle = False
        for arv, arr, rv, rr, rresp_sig, idx in ports_rd:
            if int(arv.value) == 1 and int(arr.value) == 1:
                arv.value = 0
            if int(rv.value) == 1 and int(rr.value) == 1:
                assert int(rresp_sig.value) == 0, f"XB-07 M{idx} read failed with rresp={int(rresp_sig.value)}"
                rd_done[idx] += 1
                completed_this_cycle = True
                if (rd_done[0] + rd_done[1]) < window_txns:
                    arv.value = 1

        if completed_this_cycle:
            diff = abs(rd_done[0] - rd_done[1])
            assert diff <= 1, (
                f"XB-07 READ arbitration unfair mid-window at total={rd_done[0] + rd_done[1]}: "
                f"M0={rd_done[0]}, M1={rd_done[1]} (diff={diff} > 1)"
            )
            if (rd_done[0] + rd_done[1]) >= window_txns:
                break

    # Drain any still-asserted ARVALID/RVALID without ever dropping ARVALID before ARREADY
    for _ in range(30):
        m0_idle = (int(dut.m0_arvalid.value) == 0 and int(dut.m0_rvalid.value) == 0)
        m1_idle = (int(dut.m1_arvalid.value) == 0 and int(dut.m1_rvalid.value) == 0)
        if m0_idle and m1_idle:
            break
        await RisingEdge(dut.clk)
        for arv, arr in [(dut.m0_arvalid, dut.m0_arready), (dut.m1_arvalid, dut.m1_arready)]:
            if int(arv.value) == 1 and int(arr.value) == 1:
                arv.value = 0
    dut.m0_rready.value = 0
    dut.m1_rready.value = 0

    assert (rd_done[0] + rd_done[1]) >= window_txns, (
        f"XB-07 READ window timed out: M0={rd_done[0]}, M1={rd_done[1]}"
    )
    assert abs(rd_done[0] - rd_done[1]) <= 1, (
        f"XB-07 READ final count difference > 1: M0={rd_done[0]}, M1={rd_done[1]}"
    )

    dut._log.info(
        f"XB-07 PASSED: WR M0={wr_done[0]}/M1={wr_done[1]}, RD M0={rd_done[0]}/M1={rd_done[1]}"
    )
    tb.stop_all()
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")


@cocotb.test()
async def test_xb08_write_orderings(dut):
    """XB-08: Test AW before W, W before AW, and simultaneous AW+W."""
    tb = XbarTestbench(dut)
    await tb.reset()

    orderings = ["aw_first", "w_first", "simultaneous"]
    for i, ord_mode in enumerate(orderings):
        addr = 0x50000060 + (i * 4)
        val = 0xF00D0000 + i

        bresp = await tb.m0.write(addr=addr, data=val, order=ord_mode)
        assert bresp == 0, f"Write with order {ord_mode} failed with resp {bresp}"

        rdata, rresp = await tb.m0.read(addr=addr)
        assert rresp == 0, f"Read failed after write with order {ord_mode}"
        assert rdata == val, f"Data mismatch with order {ord_mode}: expected {hex(val)}, got {hex(rdata)}"

    tb.stop_all()
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")


@cocotb.test()
async def test_xb09_random_ready_backpressure(dut):
    """XB-09: Random READY back-pressure on all channels, >= 2,000 transactions, no loss or duplication."""
    tb = XbarTestbench(dut)
    await tb.reset()

    # Configure random backpressure on all slave responders
    for s in [tb.s0, tb.s1, tb.s2, tb.s3]:
        s.awready_delay = (0, 3)
        s.wready_delay = (0, 3)
        s.arready_delay = (0, 3)
        s.bvalid_delay = (0, 3)
        s.rvalid_delay = (0, 3)

    base_addrs = [0x40000000, 0x50000000, 0x60000000, 0x70000000]
    total_txns = 2000
    num_rounds = total_txns // 2 # 1,000 writes + 1,000 reads = 2,000 transactions

    dut._log.info(f"Starting XB-09 random backpressure test with {total_txns} transactions...")

    for i in range(num_rounds):
        m_idx = i % 2
        driver = tb.m0 if m_idx == 0 else tb.m1
        slave_idx = (i // 2) % 4
        addr = base_addrs[slave_idx] + ((i % 32) * 4)
        wdata = (0x80000000 | (m_idx << 20) | (slave_idx << 16) | (i & 0xFFFF))

        # Write with random master-side BREADY delay
        b_del = random.randint(0, 3)
        w_resp = await driver.write(addr=addr, data=wdata, strb=0xF, bready_delay=b_del)
        assert w_resp == 0, f"Txn {i}: Write to {hex(addr)} failed with resp {w_resp}"

        # Read back with random master-side RREADY delay
        r_del = random.randint(0, 3)
        rdata, r_resp = await driver.read(addr=addr, rready_delay=r_del)
        assert r_resp == 0, f"Txn {i}: Read from {hex(addr)} failed with resp {r_resp}"
        assert rdata == wdata, f"Txn {i}: Data integrity mismatch on {hex(addr)}: expected {hex(wdata)}, got {hex(rdata)}"

        if (i + 1) % 500 == 0:
            dut._log.info(f"XB-09 progress: {(i + 1) * 2}/{total_txns} transactions complete")

    dut._log.info("XB-09: 2,000 transactions passed with zero loss and zero duplication.")
    tb.stop_all()
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")


@cocotb.test()
async def test_xb10_delayed_bready_rready_stability(dut):
    """XB-10: Delayed BREADY/RREADY; assert that BVALID/RVALID, response code and data stay stable until accepted."""
    tb = XbarTestbench(dut)
    await tb.reset()

    # Fixed slave delays
    tb.s1.awready_delay = 1
    tb.s1.wready_delay = 1
    tb.s1.bvalid_delay = 1
    tb.s1.arready_delay = 1
    tb.s1.rvalid_delay = 1

    # Stability monitor for Write B channel
    async def monitor_b_stability(bvalid_sig, bresp_sig, bready_sig, name):
        while True:
            await RisingEdge(dut.clk)
            if int(bvalid_sig.value) == 1 and int(bready_sig.value) == 0:
                expected_resp = int(bresp_sig.value)
                # Verify stability on every clock cycle until BREADY rises
                while int(bready_sig.value) == 0:
                    assert int(bvalid_sig.value) == 1, f"{name}: BVALID dropped before BREADY handshake!"
                    assert int(bresp_sig.value) == expected_resp, f"{name}: BRESP mutated while waiting for BREADY!"
                    await RisingEdge(dut.clk)

    # Stability monitor for Read R channel
    async def monitor_r_stability(rvalid_sig, rresp_sig, rdata_sig, rready_sig, name):
        while True:
            await RisingEdge(dut.clk)
            if int(rvalid_sig.value) == 1 and int(rready_sig.value) == 0:
                expected_resp = int(rresp_sig.value)
                expected_data = int(rdata_sig.value)
                # Verify stability on every clock cycle until RREADY rises
                while int(rready_sig.value) == 0:
                    assert int(rvalid_sig.value) == 1, f"{name}: RVALID dropped before RREADY handshake!"
                    assert int(rresp_sig.value) == expected_resp, f"{name}: RRESP mutated while waiting for RREADY!"
                    assert int(rdata_sig.value) == expected_data, f"{name}: RDATA mutated while waiting for RREADY!"
                    await RisingEdge(dut.clk)

    task_b0 = cocotb.start_soon(monitor_b_stability(dut.m0_bvalid, dut.m0_bresp, dut.m0_bready, "M0_B"))
    task_r0 = cocotb.start_soon(monitor_r_stability(dut.m0_rvalid, dut.m0_rresp, dut.m0_rdata, dut.m0_rready, "M0_R"))
    task_b1 = cocotb.start_soon(monitor_b_stability(dut.m1_bvalid, dut.m1_bresp, dut.m1_bready, "M1_B"))
    task_r1 = cocotb.start_soon(monitor_r_stability(dut.m1_rvalid, dut.m1_rresp, dut.m1_rdata, dut.m1_rready, "M1_R"))

    # Test prolonged delays (5 to 12 cycles) on both masters
    test_cases = [
        (tb.m0, 0x50000010, 0xCAFEBABE, 8, 8),
        (tb.m0, 0x50000014, 0x12345678, 12, 10),
        (tb.m1, 0x50000020, 0xDEADBEEF, 6, 8),
        (tb.m1, 0x50000024, 0xA5A55A5A, 10, 12),
    ]

    for driver, addr, val, b_del, r_del in test_cases:
        w_resp = await driver.write(addr=addr, data=val, strb=0xF, bready_delay=b_del)
        assert w_resp == 0
        r_val, r_resp = await driver.read(addr=addr, rready_delay=r_del)
        assert r_resp == 0
        assert r_val == val

    task_b0.cancel()
    task_r0.cancel()
    task_b1.cancel()
    task_r1.cancel()

    tb.stop_all()
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")


@cocotb.test()
async def test_xb11_all_targets_contention_and_backpressure(dut):
    """XB-11: Contention, w_first/aw_first, and B/R hold across all 4 mapped targets + default slave."""
    tb = XbarTestbench(dut)
    await tb.reset()

    targets = [
        (0x40000010, 0x40000014, 0),  # S0 APB
        (0x50000010, 0x50000014, 0),  # S1 RAM
        (0x60000010, 0x60000014, 0),  # S2 CSR
        (0x70000010, 0x70000014, 0),  # S3 CDC
        (0x90000010, 0x90000014, 3),  # Default slave (DECERR)
    ]

    for a0, a1, exp_resp in targets:
        # 1. Both masters write to the SAME target with delayed BREADY & mixed order
        for round_idx in range(4):
            d0 = 0xA0000000 + (round_idx << 8) + ((a0 >> 28) & 0xF)
            d1 = 0xB0000000 + (round_idx << 8) + ((a1 >> 28) & 0xF)
            ord0 = "w_first" if (round_idx % 2 == 0) else "aw_first"
            ord1 = "aw_first" if (round_idx % 2 == 0) else "simultaneous"

            t0 = cocotb.start_soon(tb.m0.write(a0, d0, strb=0xF, order=ord0, bready_delay=2))
            t1 = cocotb.start_soon(tb.m1.write(a1, d1, strb=0xF, order=ord1, bready_delay=2))
            r0 = await t0
            r1 = await t1
            assert r0 == exp_resp and r1 == exp_resp

            tr0 = cocotb.start_soon(tb.m0.read(a0, rready_delay=2))
            tr1 = cocotb.start_soon(tb.m1.read(a1, rready_delay=2))
            v0, rr0 = await tr0
            v1, rr1 = await tr1
            assert rr0 == exp_resp and rr1 == exp_resp
            if exp_resp == 0:
                assert v0 == d0 and v1 == d1

    tb.stop_all()
    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")
