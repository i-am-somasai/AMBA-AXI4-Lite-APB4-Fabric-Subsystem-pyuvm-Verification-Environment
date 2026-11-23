# Hello World cocotb + pyuvm test
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import pyuvm
from pyuvm import uvm_test, uvm_component, uvm_env

class HelloEnv(uvm_env):
    def build_phase(self):
        super().build_phase()
        self.logger.info("HelloEnv: build_phase executed")

class HelloTest(uvm_test):
    def build_phase(self):
        super().build_phase()
        self.env = HelloEnv("env", self)
        self.logger.info("HelloTest: build_phase executed")

    async def run_phase(self):
        self.raise_objection()
        dut = cocotb.top
        self.logger.info("HelloTest: driving clock and reset")
        cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

        dut.rst_n.value = 0
        dut.en.value = 0
        await Timer(25, unit="ns")
        dut.rst_n.value = 1
        await RisingEdge(dut.clk)

        assert int(dut.count.value) == 0, f"Expected count=0, got {dut.count.value}"

        dut.en.value = 1
        for i in range(5):
            await RisingEdge(dut.clk)
        await Timer(1, unit="ns")

        assert int(dut.count.value) == 5, f"Expected count=5, got {dut.count.value}"
        self.logger.info(f"HelloTest: count verified successfully ({int(dut.count.value)})")
        self.drop_objection()

@cocotb.test()
async def test_hello_world(dut):
    """Phase 0 cocotb + pyuvm integration smoke test"""
    dut._log.info("Starting Phase 0 cocotb + pyuvm smoke test")
    await pyuvm.uvm_root().run_test("HelloTest")
    dut._log.info("Phase 0 cocotb + pyuvm smoke test PASSED")
