# tb/block/test_axil_cdc_bridge.py
# Directed tests for AXI4-Lite CDC Bridge (CD-01, CD-04, CD-05)
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from models.axil_driver import AxilMasterDriver

class CdcBridgeTestbench:
    def __init__(self, dut):
        self.dut = dut
        self.axil = AxilMasterDriver(dut, dut.clk_sys, prefix="s_axil_")
        # Dual asynchronous clocks: sys = 100MHz (10ns), slow = 40MHz (25ns)
        cocotb.start_soon(Clock(dut.clk_sys, 10, unit="ns").start())
        cocotb.start_soon(Clock(dut.clk_slow, 25, unit="ns").start())

    async def reset(self):
        self.dut.rst_sys_n.value = 0
        self.dut.rst_slow_n.value = 0
        self.axil.init_signals()
        for _ in range(5):
            await RisingEdge(self.dut.clk_sys)
        self.dut.rst_sys_n.value = 1
        self.dut.rst_slow_n.value = 1
        for _ in range(5):
            await RisingEdge(self.dut.clk_sys)

@cocotb.test()
async def test_cd01_scratch_data_integrity(dut):
    """CD-01: Cross-domain write and read data integrity on SLOW_SCRATCH (0x04)."""
    tb = CdcBridgeTestbench(dut)
    await tb.reset()

    # Test full 32-bit write/read patterns
    test_patterns = [
        0x12345678,
        0xDEADBEEF,
        0xA5A55A5A,
        0xCAFEF00D,
        0x00000000,
        0xFFFFFFFF
    ]

    for val in test_patterns:
        # Write to SLOW_SCRATCH (0x04)
        bresp = await tb.axil.write(addr=0x04, data=val, strb=0xF)
        assert bresp == 0, f"Write to SLOW_SCRATCH failed with bresp={bresp}"

        # Read back from SLOW_SCRATCH (0x04)
        rdata, rresp = await tb.axil.read(addr=0x04)
        assert rresp == 0, f"Read from SLOW_SCRATCH failed with rresp={rresp}"
        assert rdata == val, f"Data mismatch: expected {hex(val)}, got {hex(rdata)}"
        dut._log.info(f"CD-01 pattern {hex(val)} verified successfully across CDC boundary")

    # Byte strobe verification on SLOW_SCRATCH
    # Reset scratch to 0
    await tb.axil.write(addr=0x04, data=0x00000000, strb=0xF)

    # Write byte 0
    await tb.axil.write(addr=0x04, data=0x000000AA, strb=0x1)
    rdata, _ = await tb.axil.read(addr=0x04)
    assert rdata == 0x000000AA, f"Byte 0 write failed: {hex(rdata)}"

    # Write byte 2
    await tb.axil.write(addr=0x04, data=0x00CC0000, strb=0x4)
    rdata, _ = await tb.axil.read(addr=0x04)
    assert rdata == 0x00CC00AA, f"Byte 2 write failed: {hex(rdata)}"

    # Write bytes 1 and 3
    await tb.axil.write(addr=0x04, data=0xBB00DD00, strb=0xA)
    rdata, _ = await tb.axil.read(addr=0x04)
    assert rdata == 0xBBCCDDAA, f"Bytes 1 and 3 write failed: {hex(rdata)}"

    await RisingEdge(dut.clk_sys)

@cocotb.test()
async def test_cd04_free_running_counter(dut):
    """CD-04: Free-running counter in clk_slow incrementing and controllable via SLOW_CTRL."""
    tb = CdcBridgeTestbench(dut)
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

    await RisingEdge(dut.clk_sys)

@cocotb.test()
async def test_cd05_slow_id_and_unmapped_error_response(dut):
    """CD-05: Read SLOW_ID (0x510E_0001), read-only protection, and SLVERR on unmapped offset."""
    tb = CdcBridgeTestbench(dut)
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

    await RisingEdge(dut.clk_sys)
    await Timer(10, unit="ns")
