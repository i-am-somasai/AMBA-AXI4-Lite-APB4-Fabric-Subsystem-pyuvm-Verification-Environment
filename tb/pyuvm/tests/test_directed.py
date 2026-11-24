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
    """XB-12: Reset during in-flight transaction, then verify clean recovery."""
    async def run_phase(self):
        self.raise_objection()
        await self.init_clocks_and_reset()
        dut = cocotb.top

        # Initial clean transaction
        seq = ResetRecoverySeq("seq")
        await seq.start(self.env.m0_agent.sequencer)

        # Pulse reset
        dut.rst_n.value = 0
        for _ in range(5):
            await RisingEdge(dut.clk_sys)
        dut.rst_n.value = 1
        for _ in range(5):
            await RisingEdge(dut.clk_sys)

        # Post-reset recovery: perform clean write and readback
        seq2 = ResetRecoverySeq("seq2")
        await seq2.start(self.env.m0_agent.sequencer)

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
