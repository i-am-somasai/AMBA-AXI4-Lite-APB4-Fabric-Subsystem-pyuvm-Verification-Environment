# tb/pyuvm/env/fabric_env.py
# pyuvm Environment for AMBA fabric subsystem
import cocotb
from pyuvm import uvm_env
from agents.axil_master_agent import AxilMasterAgent
from env.fabric_scoreboard import FabricScoreboard
from monitors.fabric_monitors import (
    AxilBusMonitor,
    CrossbarContentionMonitor,
    ApbBusMonitor,
    CdcMonitor,
    UartActivityMonitor,
    ResetPhaseMonitor
)

class FabricEnv(uvm_env):
    """Top-level pyuvm verification environment for amba_fabric_top."""
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.m0_agent = None
        self.m1_agent = None
        self.scoreboard = None
        self.m0_mon = None
        self.m1_mon = None
        self.contention_mon = None
        self.apb_mon = None
        self.cdc_mon = None
        self.uart_mon = None
        self.reset_mon = None

    def build_phase(self):
        super().build_phase()
        self.m0_agent = AxilMasterAgent("m0_agent", self, master_id=0, prefix="s0_axil_")
        self.m1_agent = AxilMasterAgent("m1_agent", self, master_id=1, prefix="s1_axil_")
        self.scoreboard = FabricScoreboard("scoreboard", self)

        # Passive physical bus monitors for honest functional coverage
        dut = cocotb.top
        self.m0_mon = AxilBusMonitor(dut.clk_sys, dut.rst_n, master_id=0, prefix="s0_axil_", dut=dut)
        self.m1_mon = AxilBusMonitor(dut.clk_sys, dut.rst_n, master_id=1, prefix="s1_axil_", dut=dut)
        self.contention_mon = CrossbarContentionMonitor(dut.clk_sys, dut.rst_n, dut=dut)
        self.apb_mon = ApbBusMonitor(dut.clk_sys, dut.rst_n, dut=dut)
        self.cdc_mon = CdcMonitor(dut.clk_sys, dut.clk_slow, dut.rst_n, dut=dut)
        self.uart_mon = UartActivityMonitor(dut.clk_sys, dut.rst_n, dut=dut)
        self.reset_mon = ResetPhaseMonitor(dut.clk_sys, dut.rst_n, dut=dut)

        self.m0_mon.start()
        self.m1_mon.start()
        self.contention_mon.start()
        self.apb_mon.start()
        self.cdc_mon.start()
        self.uart_mon.start()
        self.reset_mon.start()

    def connect_phase(self):
        super().connect_phase()
        self.m0_agent.driver.ap.connect(self.scoreboard.m0_sub.analysis_export)
        self.m1_agent.driver.ap.connect(self.scoreboard.m1_sub.analysis_export)

