# tb/pyuvm/env/fabric_env.py
# pyuvm Environment for AMBA fabric subsystem
from pyuvm import uvm_env
from agents.axil_master_agent import AxilMasterAgent
from env.fabric_scoreboard import FabricScoreboard

class FabricEnv(uvm_env):
    """Top-level pyuvm verification environment for amba_fabric_top."""
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.m0_agent = None
        self.m1_agent = None
        self.scoreboard = None

    def build_phase(self):
        super().build_phase()
        self.m0_agent = AxilMasterAgent("m0_agent", self, master_id=0, prefix="s0_axil_")
        self.m1_agent = AxilMasterAgent("m1_agent", self, master_id=1, prefix="s1_axil_")
        self.scoreboard = FabricScoreboard("scoreboard", self)

    def connect_phase(self):
        super().connect_phase()
        self.m0_agent.driver.ap.connect(self.scoreboard.m0_sub.analysis_export)
        self.m1_agent.driver.ap.connect(self.scoreboard.m1_sub.analysis_export)
