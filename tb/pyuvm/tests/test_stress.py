# tb/pyuvm/tests/test_stress.py
# pyuvm stress test for XB-13: >= 10,000 transactions across 2 masters with zero mismatches
import os
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import pyuvm
from pyuvm import uvm_test
from env.fabric_env import FabricEnv
from sequences.fabric_stress_seq import FabricStressSeq

@pyuvm.test()
class TestStress(uvm_test):
    """XB-13: 10,000-transaction concurrent random stress test across Master 0 and Master 1."""
    def __init__(self, name="TestStress", parent=None):
        super().__init__(name, parent)
        self.env = None

    def build_phase(self):
        super().build_phase()
        # Seed initialization
        seed = int(os.environ.get("SEED", "42"))
        random.seed(seed)
        self.logger.info(f"=== Starting XB-13 Stress Test with SEED={seed} ===")
        self.env = FabricEnv("env", self)

    async def run_phase(self):
        self.raise_objection()
        dut = cocotb.top

        # Initialize pins
        dut.gpio_i.value = 0
        dut.uart_rx.value = 1

        # Start asynchronous dual clocks: sys = 100MHz (10ns), slow = 40MHz (25ns)
        cocotb.start_soon(Clock(dut.clk_sys, 10, unit="ns").start())
        cocotb.start_soon(Clock(dut.clk_slow, 25, unit="ns").start())

        # Reset sequence
        dut.rst_n.value = 0
        for _ in range(10):
            await RisingEdge(dut.clk_sys)
        dut.rst_n.value = 1
        for _ in range(10):
            await RisingEdge(dut.clk_sys)

        # Determine transaction count (spec requires >= 10,000 total)
        # Default: 5000 per master = 10,000 total transactions
        num_per_master = int(os.environ.get("NUM_TRANS_PER_MASTER", "5000"))
        self.logger.info(
            f"Launching FabricStressSeq with {num_per_master} transactions per master "
            f"({num_per_master * 2} total)..."
        )

        stress_seq = FabricStressSeq("stress_seq", num_trans_per_master=num_per_master)
        stress_seq.m0_sequencer = self.env.m0_agent.sequencer
        stress_seq.m1_sequencer = self.env.m1_agent.sequencer

        await stress_seq.start()

        # Let remaining pipeline cycles settle
        for _ in range(20):
            await RisingEdge(dut.clk_sys)

        self.logger.info("=== Stress sequence completed successfully ===")
        self.drop_objection()
