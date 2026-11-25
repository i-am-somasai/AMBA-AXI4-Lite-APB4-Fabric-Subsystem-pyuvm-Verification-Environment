# tb/pyuvm/tests/test_directed.py
# pyuvm directed tests for XB-09..XB-15, BR-04..BR-06
import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import pyuvm
from pyuvm import uvm_test
from env.fabric_env import FabricEnv
from sequences.directed_seqs import (
    SlverrPropagationSeq,
    ProtPassThroughSeq,
    UnalignedAddressSeq,
    WriteOrderSeq,
    StrobePatternSeq,
    ResetRecoverySeq,
    ContentionM0Seq,
    ContentionM1Seq
)
from sequences.coverage_closure_seq import CoverageClosureSeq
from sequences.axil_base_seq import AxilBaseSeq

class BaseFabricTest(uvm_test):
    """Base test initializing clocks, resets and FabricEnv."""
    def build_phase(self):
        super().build_phase()
        self.env = FabricEnv("env", self)

    async def init_clocks_and_reset(self):
        dut = cocotb.top
        dut.gpio_i.value = 0
        dut.uart_rx.value = 1

        slow_period = float(os.environ.get("CLK_SLOW_PERIOD_NS", "25.0"))
        slow_phase = float(os.environ.get("CLK_SLOW_PHASE_NS", "0.0"))

        cocotb.start_soon(Clock(dut.clk_sys, 10, unit="ns").start())
        if slow_phase > 0:
            await Timer(slow_phase, unit="ns")
        cocotb.start_soon(Clock(dut.clk_slow, slow_period, unit="ns").start())

        dut.rst_n.value = 0
        for _ in range(10):
            await RisingEdge(dut.clk_sys)
        dut.rst_n.value = 1
        for _ in range(10):
            await RisingEdge(dut.clk_sys)


@pyuvm.test()
class test_xb11_slverr_propagation(BaseFabricTest):
    """XB-11: SLVERR propagation from all subsystems."""
    async def run_phase(self):
        self.raise_objection()
        await self.init_clocks_and_reset()
        seq = SlverrPropagationSeq("slverr_seq")
        await seq.start(self.env.m0_agent.sequencer)
        for _ in range(10):
            await RisingEdge(cocotb.top.clk_sys)
        self.drop_objection()

TestSlverr = test_xb11_slverr_propagation


@pyuvm.test()
class test_xb14_prot_passthrough(BaseFabricTest):
    """XB-14: AWPROT and ARPROT pass-through."""
    async def run_phase(self):
        self.raise_objection()
        await self.init_clocks_and_reset()
        seq = ProtPassThroughSeq("prot_seq")
        await seq.start(self.env.m0_agent.sequencer)
        for _ in range(10):
            await RisingEdge(cocotb.top.clk_sys)
        self.drop_objection()

TestProtPassThrough = test_xb14_prot_passthrough


@pyuvm.test()
class test_xb15_unaligned_address(BaseFabricTest):
    """XB-15: Unaligned address LSBs."""
    async def run_phase(self):
        self.raise_objection()
        await self.init_clocks_and_reset()
        seq = UnalignedAddressSeq("unaligned_seq")
        await seq.start(self.env.m0_agent.sequencer)
        for _ in range(10):
            await RisingEdge(cocotb.top.clk_sys)
        self.drop_objection()

TestUnaligned = test_xb15_unaligned_address


@pyuvm.test()
class test_sys_write_ordering(BaseFabricTest):
    """System-level write channel ordering test (AW first, W first, simultaneous)."""
    async def run_phase(self):
        self.raise_objection()
        await self.init_clocks_and_reset()
        seq = WriteOrderSeq("write_order_seq")
        await seq.start(self.env.m0_agent.sequencer)
        for _ in range(10):
            await RisingEdge(cocotb.top.clk_sys)
        self.drop_objection()

TestWriteOrder = test_sys_write_ordering


@pyuvm.test()
class test_sys_strobe_patterns(BaseFabricTest):
    """System-level WSTRB patterns on RAM and CSR."""
    async def run_phase(self):
        self.raise_objection()
        await self.init_clocks_and_reset()
        seq = StrobePatternSeq("strobe_seq")
        await seq.start(self.env.m0_agent.sequencer)
        for _ in range(10):
            await RisingEdge(cocotb.top.clk_sys)
        self.drop_objection()

TestStrobes = test_sys_strobe_patterns


@pyuvm.test()
class test_xb12_reset_recovery(BaseFabricTest):
    """XB-12: Reset injected mid-flight across AW, W, B, AR, R phases, agent/scoreboard flush, and recovery."""
    async def _pulse_reset_and_flush(self, dut, in_flight_wr_addrs):
        # Reset immediately and deassert valid signals from master agents
        dut.rst_n.value = 0
        m0_flushed = self.env.m0_agent.driver.flush_pending()
        m1_flushed = self.env.m1_agent.driver.flush_pending()
        self.env.m0_agent.driver.raw_driver.init_signals()
        self.env.m1_agent.driver.raw_driver.init_signals()
        wr_addrs = list(in_flight_wr_addrs)
        for a in (m0_flushed, m1_flushed):
            if a is not None:
                wr_addrs.append(a)
        self.env.scoreboard.flush_on_reset(in_flight_wr_addrs=wr_addrs, preserve_ram=True)

        for _ in range(5):
            await RisingEdge(dut.clk_sys)
            assert int(dut.s0_axil_bvalid.value) == 0, "M0 bvalid must clear during reset"
            assert int(dut.s0_axil_rvalid.value) == 0, "M0 rvalid must clear during reset"
            assert int(dut.s1_axil_bvalid.value) == 0, "M1 bvalid must clear during reset"
            assert int(dut.s1_axil_rvalid.value) == 0, "M1 rvalid must clear during reset"

        dut.rst_n.value = 1
        for _ in range(6):
            await RisingEdge(dut.clk_sys)
        assert int(dut.s0_axil_bvalid.value) == 0 and int(dut.s0_axil_rvalid.value) == 0
        assert int(dut.s1_axil_bvalid.value) == 0 and int(dut.s1_axil_rvalid.value) == 0

    async def run_phase(self):
        self.raise_objection()
        await self.init_clocks_and_reset()
        dut = cocotb.top

        # Pre-seed RAM (0x5000_0050) and CSR SCRATCH (0x6000_0008) cleanly
        init_seq = AxilBaseSeq("xb12_init")
        init_seq.sequencer = self.env.m0_agent.sequencer
        await init_seq.start(self.env.m0_agent.sequencer)  # harmless start check below
        seq_setup = ResetRecoverySeq("setup")
        await seq_setup.start(self.env.m0_agent.sequencer)

        # ------------------------------------------------------------------
        # Scenario 1: AW in flight (AW accepted / locked by xbar, W not yet driven -> aw_done=1, wr_locked=1)
        # Wait: drive AWVALID=1, WVALID=0 on M0 targeting RAM (0x5000_0054) until awready=1,
        # OR capture mid-AWVALID if slave locked. Kills SMUT-14 if wr_locked/aw_done not reset!
        # ------------------------------------------------------------------
        dut.s0_axil_awaddr.value = 0x50000054
        dut.s0_axil_awprot.value = 0
        dut.s0_axil_awvalid.value = 1
        dut.s0_axil_wvalid.value = 0
        dut.s0_axil_bready.value = 0
        for _ in range(10):
            await RisingEdge(dut.clk_sys)
            if int(dut.s0_axil_awready.value) == 1:
                dut.s0_axil_awvalid.value = 0
                break
        await self._pulse_reset_and_flush(dut, [0x50000054])

        # Verify ref model marked interrupted write address UNKNOWN, and M1 can immediately claim S1
        assert (0x50000054 & ~0x3) in self.env.scoreboard.ref_model.unknown_words
        seq_m1_rec = ResetRecoverySeq("m1_after_aw_rst")
        await seq_m1_rec.start(self.env.m1_agent.sequencer)
        assert (0x50000054 & ~0x3) not in self.env.scoreboard.ref_model.unknown_words

        # ------------------------------------------------------------------
        # Scenario 2: W in flight (WVALID=1 while AW held/unacked or W accepted before AW)
        # ------------------------------------------------------------------
        dut.s0_axil_awvalid.value = 0
        dut.s0_axil_wdata.value = 0xDEAD1111
        dut.s0_axil_wstrb.value = 0xF
        dut.s0_axil_wvalid.value = 1
        await RisingEdge(dut.clk_sys)
        await self._pulse_reset_and_flush(dut, [0x50000058])

        # ------------------------------------------------------------------
        # Scenario 3: B response pending (write issued to APB, hold BREADY=0 while BVALID=1)
        # ------------------------------------------------------------------
        dut.s1_axil_awaddr.value = 0x40001004
        dut.s1_axil_awprot.value = 0
        dut.s1_axil_wdata.value = 0x55556666
        dut.s1_axil_wstrb.value = 0xF
        dut.s1_axil_awvalid.value = 1
        dut.s1_axil_wvalid.value = 1
        dut.s1_axil_bready.value = 0
        b_seen = False
        for _ in range(25):
            await RisingEdge(dut.clk_sys)
            if int(dut.s1_axil_awready.value):
                dut.s1_axil_awvalid.value = 0
            if int(dut.s1_axil_wready.value):
                dut.s1_axil_wvalid.value = 0
            if int(dut.s1_axil_bvalid.value):
                b_seen = True
                break
        assert b_seen, "XB-12 Scenario 3: BVALID never asserted before reset"
        await self._pulse_reset_and_flush(dut, [0x40001004])

        # ------------------------------------------------------------------
        # Scenario 4 & 5: AR in flight / R pending (CDC read in flight + RVALID held with RREADY=0)
        # ------------------------------------------------------------------
        dut.s0_axil_araddr.value = 0x70000000
        dut.s0_axil_arprot.value = 0
        dut.s0_axil_arvalid.value = 1
        dut.s0_axil_rready.value = 0
        r_seen = False
        for _ in range(40):
            await RisingEdge(dut.clk_sys)
            if int(dut.s0_axil_arready.value):
                dut.s0_axil_arvalid.value = 0
            if int(dut.s0_axil_rvalid.value):
                r_seen = True
                break
        assert r_seen, "XB-12 Scenario 4: RVALID never asserted before reset"
        await self._pulse_reset_and_flush(dut, [])

        # Also assert reset right while ARVALID=1 is mid-flight to CDC before RVALID returns
        dut.s1_axil_araddr.value = 0x70000004
        dut.s1_axil_arvalid.value = 1
        dut.s1_axil_rready.value = 0
        await RisingEdge(dut.clk_sys)
        await RisingEdge(dut.clk_sys)
        dut.s1_axil_arvalid.value = 0
        await self._pulse_reset_and_flush(dut, [])

        # Post-reset full recovery across both masters and slaves
        seq2 = ResetRecoverySeq("seq_final")
        await seq2.start(self.env.m0_agent.sequencer)
        seq3 = ResetRecoverySeq("seq_final_m1")
        await seq3.start(self.env.m1_agent.sequencer)

        for _ in range(10):
            await RisingEdge(cocotb.top.clk_sys)
        self.drop_objection()

TestResetRecovery = test_xb12_reset_recovery


@pyuvm.test()
class test_sys_contention(BaseFabricTest):
    """System-level dual-master contention on RAM."""
    async def run_phase(self):
        self.raise_objection()
        await self.init_clocks_and_reset()

        seq0 = ContentionM0Seq("seq0")
        seq1 = ContentionM1Seq("seq1")

        t0 = cocotb.start_soon(seq0.start(self.env.m0_agent.sequencer))
        t1 = cocotb.start_soon(seq1.start(self.env.m1_agent.sequencer))
        await t0
        await t1

        for _ in range(10):
            await RisingEdge(cocotb.top.clk_sys)
        self.drop_objection()

TestContention = test_sys_contention


@pyuvm.test()
class TestCoverageClosure(BaseFabricTest):
    """Phase 5: Functional coverage closure exercising all Section 10 covergroups."""
    async def run_phase(self):
        self.raise_objection()
        await self.init_clocks_and_reset()

        seq0 = CoverageClosureSeq("seq0", master_id=0)
        seq1 = CoverageClosureSeq("seq1", master_id=1)

        t0 = cocotb.start_soon(seq0.start(self.env.m0_agent.sequencer))
        t1 = cocotb.start_soon(seq1.start(self.env.m1_agent.sequencer))
        await t0
        await t1

        for _ in range(20):
            await RisingEdge(cocotb.top.clk_sys)
        self.drop_objection()
