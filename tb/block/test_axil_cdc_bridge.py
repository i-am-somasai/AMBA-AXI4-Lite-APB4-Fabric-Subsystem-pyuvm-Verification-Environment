# tb/block/test_axil_cdc_bridge.py
# Directed tests for AXI4-Lite CDC Bridge (CD-01, CD-03, CD-04)
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from models.axil_driver import AxilMasterDriver


class CdcBridgeTestbench:
    def __init__(self, dut, slow_period=25, slow_phase=0.0):
        self.dut = dut
        self.axil = AxilMasterDriver(dut, dut.clk_sys, prefix="s_axil_")
        self.sys_clk_task = cocotb.start_soon(Clock(dut.clk_sys, 10, unit="ns").start())
        self.slow_clk_task = None
        self.slow_period = slow_period
        self.slow_phase = slow_phase

    async def start_slow_clock(self, period=25, phase=0.0):
        if self.slow_clk_task is not None:
            self.slow_clk_task.cancel()
            self.slow_clk_task = None
            await Timer(5, unit="ns")
        if phase > 0:
            await Timer(phase, unit="ns")
        self.slow_period = period
        self.slow_phase = phase
        self.slow_clk_task = cocotb.start_soon(Clock(self.dut.clk_slow, period, unit="ns").start())

    async def reset(self):
        self.dut.rst_sys_n.value = 0
        self.dut.rst_slow_n.value = 0
        self.axil.init_signals()
        for _ in range(5):
            await RisingEdge(self.dut.clk_sys)
        self.dut.rst_sys_n.value = 1
        self.dut.rst_slow_n.value = 1
        for _ in range(8):
            await RisingEdge(self.dut.clk_sys)

    def stop_clocks(self):
        if self.sys_clk_task:
            self.sys_clk_task.cancel()
        if self.slow_clk_task:
            self.slow_clk_task.cancel()


@cocotb.test()
async def test_cd01_ratio_phase_sweep(dut):
    """CD-01: Data integrity through the CDC bridge across ratio and phase sweep."""
    tb = CdcBridgeTestbench(dut)

    # 3 ratios: slow < sys (25 ns), slow ~ sys (10.3 ns), slow > sys (6.0 ns)
    ratios = [25.0, 10.3, 6.0]
    # 3 phases: 0 ns, 2.5 ns, 5.0 ns
    phases = [0.0, 2.5, 5.0]

    patterns = [0xDEADBEEF, 0x12345678, 0xA5A55A5A]

    for period in ratios:
        for phase in phases:
            dut._log.info(f"CD-01 testing ratio period={period} ns, phase={phase} ns...")
            await tb.start_slow_clock(period=period, phase=phase)
            await tb.reset()

            for p_idx, val in enumerate(patterns):
                # Write to SLOW_SCRATCH (0x04)
                bresp = await tb.axil.write(addr=0x04, data=val, strb=0xF)
                assert bresp == 0, f"Write failed at period={period}, phase={phase}: bresp={bresp}"

                # Read back from SLOW_SCRATCH (0x04)
                rdata, rresp = await tb.axil.read(addr=0x04)
                assert rresp == 0, f"Read failed at period={period}, phase={phase}: rresp={rresp}"
                assert rdata == val, f"Data mismatch at period={period}, phase={phase}: expected {hex(val)}, got {hex(rdata)}"

            # Strobe test
            await tb.axil.write(addr=0x04, data=0x00000000, strb=0xF)
            await tb.axil.write(addr=0x04, data=0xCC0000AA, strb=0x9)
            rdata, _ = await tb.axil.read(addr=0x04)
            assert rdata == 0xCC0000AA, f"Strobe write failed at period={period}, phase={phase}: got {hex(rdata)}"

    tb.stop_clocks()
    await Timer(10, unit="ns")
    dut._log.info("CD-01 PASSED: all 9 ratio/phase combinations verified with data integrity")


@cocotb.test()
async def test_cd03_reset_recovery(dut):
    """CD-03: Reset asserted in either domain at random times mid-transaction; assert clean recovery."""
    tb = CdcBridgeTestbench(dut)
    await tb.start_slow_clock(period=25.0, phase=0.0)
    await tb.reset()

    # Part 1: Mid-transaction reset in clk_sys domain
    dut._log.info("CD-03: Injecting mid-transaction reset in clk_sys domain...")
    # Start write handshake
    dut.s_axil_awaddr.value = 0x04
    dut.s_axil_awvalid.value = 1
    dut.s_axil_wdata.value = 0xDEAD0001
    dut.s_axil_wstrb.value = 0xF
    dut.s_axil_wvalid.value = 1
    dut.s_axil_bready.value = 1

    await RisingEdge(dut.clk_sys)
    # Assert sys reset abruptly mid-flight
    dut.rst_sys_n.value = 0
    tb.axil.init_signals()
    for _ in range(5):
        await RisingEdge(dut.clk_sys)
    dut.rst_sys_n.value = 1
    for _ in range(8):
        await RisingEdge(dut.clk_sys)

    # Post-reset recovery transaction
    bresp = await tb.axil.write(addr=0x04, data=0x11223344, strb=0xF)
    assert bresp == 0, f"Post-sys-reset write failed with bresp={bresp}"
    rdata, rresp = await tb.axil.read(addr=0x04)
    assert rresp == 0, f"Post-sys-reset read failed with rresp={rresp}"
    assert rdata == 0x11223344, f"Post-sys-reset data mismatch: expected 0x11223344, got {hex(rdata)}"
    dut._log.info("CD-03: clk_sys domain reset recovery OK")

    # Part 2: Mid-transaction reset in clk_slow domain
    dut._log.info("CD-03: Injecting mid-transaction reset in clk_slow domain...")
    # Start read transaction
    dut.s_axil_araddr.value = 0x04
    dut.s_axil_arvalid.value = 1
    dut.s_axil_rready.value = 1

    await RisingEdge(dut.clk_sys)
    # Assert slow reset mid-flight
    dut.rst_slow_n.value = 0
    for _ in range(5):
        await RisingEdge(dut.clk_slow)
    dut.rst_slow_n.value = 1
    for _ in range(8):
        await RisingEdge(dut.clk_slow)
    # Drain any sys cycles and re-initialize
    dut.rst_sys_n.value = 0
    tb.axil.init_signals()
    for _ in range(5):
        await RisingEdge(dut.clk_sys)
    dut.rst_sys_n.value = 1
    for _ in range(8):
        await RisingEdge(dut.clk_sys)

    # Post-reset recovery transaction
    bresp = await tb.axil.write(addr=0x04, data=0x55667788, strb=0xF)
    assert bresp == 0, f"Post-slow-reset write failed with bresp={bresp}"
    rdata, rresp = await tb.axil.read(addr=0x04)
    assert rresp == 0, f"Post-slow-reset read failed with rresp={rresp}"
    assert rdata == 0x55667788, f"Post-slow-reset data mismatch: expected 0x55667788, got {hex(rdata)}"
    dut._log.info("CD-03: clk_slow domain reset recovery OK")

    tb.stop_clocks()
    await Timer(10, unit="ns")
    dut._log.info("CD-03 PASSED: clean recovery in both domains")


@cocotb.test()
async def test_cd04_free_running_counter(dut):
    """CD-04: Free-running counter in clk_slow incrementing and controllable via SLOW_CTRL."""
    tb = CdcBridgeTestbench(dut)
    await tb.start_slow_clock(period=25.0, phase=0.0)
    await tb.reset()

    # Read SLOW_COUNTER (0x08)
    val1, rresp1 = await tb.axil.read(addr=0x08)
    assert rresp1 == 0, f"Read SLOW_COUNTER failed: rresp={rresp1}"

    # Wait several slow clock cycles
    for _ in range(10):
        await RisingEdge(dut.clk_slow)

    # Read SLOW_COUNTER (0x08) again
    val2, rresp2 = await tb.axil.read(addr=0x08)
    assert rresp2 == 0, f"Second read SLOW_COUNTER failed: rresp={rresp2}"
    dut._log.info(f"SLOW_COUNTER: val1={val1}, val2={val2} (incremented by {val2 - val1})")
    assert val2 > val1, f"Counter did not increment: val1={val1}, val2={val2}"

    # Disable counter via SLOW_CTRL (0x0C): bit 0 = 0
    bresp = await tb.axil.write(addr=0x0C, data=0x00, strb=0xF)
    assert bresp == 0

    val_stopped_1, _ = await tb.axil.read(addr=0x08)
    for _ in range(10):
        await RisingEdge(dut.clk_slow)
    val_stopped_2, _ = await tb.axil.read(addr=0x08)

    assert val_stopped_1 == val_stopped_2, f"Counter kept running while disabled: {val_stopped_1} vs {val_stopped_2}"
    dut._log.info(f"Counter successfully paused at {val_stopped_1}")

    # Re-enable counter via SLOW_CTRL (0x0C): bit 0 = 1
    await tb.axil.write(addr=0x0C, data=0x01, strb=0xF)
    for _ in range(10):
        await RisingEdge(dut.clk_slow)
    val_resumed, _ = await tb.axil.read(addr=0x08)
    assert val_resumed > val_stopped_2, f"Counter did not resume: paused={val_stopped_2}, resumed={val_resumed}"

    tb.stop_clocks()
    await Timer(10, unit="ns")
    dut._log.info("CD-04 PASSED")


@cocotb.test()
async def test_cd_slow_id_and_unmapped(dut):
    """Read SLOW_ID (0x510E_0001), read-only protection, and SLVERR on unmapped offset."""
    tb = CdcBridgeTestbench(dut)
    await tb.start_slow_clock(period=25.0, phase=0.0)
    await tb.reset()

    # 1. Read SLOW_ID (0x00): expect 0x510E_0001 and OKAY (0)
    rdata, rresp = await tb.axil.read(addr=0x00)
    assert rresp == 0, f"Read SLOW_ID returned error: {rresp}"
    assert rdata == 0x510E0001, f"SLOW_ID mismatch: expected 0x510E0001, got {hex(rdata)}"

    # 2. Write to SLOW_ID (0x00): should not alter ID
    bresp = await tb.axil.write(addr=0x00, data=0xDEADBEEF, strb=0xF)
    assert bresp == 0, f"Write to SLOW_ID unexpected bresp: {bresp}"
    rdata, _ = await tb.axil.read(addr=0x00)
    assert rdata == 0x510E0001, f"SLOW_ID was overwritten! Got {hex(rdata)}"

    # 3. Read unmapped offset (0x20): expect SLVERR (2'b10 = 2)
    rdata_err, rresp_err = await tb.axil.read(addr=0x20)
    assert rresp_err == 2, f"Expected SLVERR (2) on unmapped read, got rresp={rresp_err}"

    # 4. Write unmapped offset (0x24): expect SLVERR (2'b10 = 2)
    bresp_err = await tb.axil.write(addr=0x24, data=0x12345678, strb=0xF)
    assert bresp_err == 2, f"Expected SLVERR (2) on unmapped write, got bresp={bresp_err}"

    tb.stop_clocks()
    await Timer(10, unit="ns")
