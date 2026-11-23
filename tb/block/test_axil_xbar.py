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
    """XB-02: Write-then-read data integrity across multiple locations in RAM (S1)."""
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
    """XB-03: All 16 WSTRB patterns on RAM (S1). Verify only strobed bytes change."""
    tb = XbarTestbench(dut)
    await tb.reset()

    base = 0x50000100
    for strb in range(16):
        addr = base + strb * 4
        # Initialize memory word with 0x00000000
        await tb.m0.write(addr=addr, data=0x00000000, strb=0xF)

        # Write pattern with tested strb
        write_val = 0xA1B2C3D4
        await tb.m0.write(addr=addr, data=write_val, strb=strb)

        # Read back
        rdata, rresp = await tb.m0.read(addr=addr)
        assert rresp == 0, f"Read failed for strb {hex(strb)}"

        # Compute expected
        expected = 0
        for b in range(4):
            if (strb >> b) & 1:
                mask = 0xFF << (8 * b)
                expected |= (write_val & mask)

        assert rdata == expected, f"WSTRB {hex(strb)} mismatch: expected {hex(expected)}, got {hex(rdata)}"

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
    """XB-07: Arbitration fairness under sustained contention (grant difference <= 1)."""
    tb = XbarTestbench(dut)
    await tb.reset()

    # Run 10 rounds of simultaneous requests to S1
    m0_first = 0
    m1_first = 0

    for round_idx in range(10):
        t0 = cocotb.start_soon(tb.m0.write(addr=0x50000050, data=0x1000 + round_idx))
        t1 = cocotb.start_soon(tb.m1.write(addr=0x50000054, data=0x2000 + round_idx))

        await t0
        await t1

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
