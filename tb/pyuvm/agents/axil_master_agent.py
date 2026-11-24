# tb/pyuvm/agents/axil_master_agent.py
# AXI4-Lite pyuvm Master Agent (Sequencer, Driver, Monitor)
from pyuvm import uvm_agent, uvm_driver, uvm_sequencer, uvm_analysis_port
import cocotb
from cocotb.triggers import RisingEdge, Timer
from models.axil_driver import AxilMasterDriver

class AxilSequencer(uvm_sequencer):
    def __init__(self, name, parent):
        super().__init__(name, parent)


class AxilDriver(uvm_driver):
    """pyuvm Driver driving AXI4-Lite physical signals on DUT."""
    def __init__(self, name, parent, master_id=0, prefix="s0_axil_"):
        super().__init__(name, parent)
        self.master_id = master_id
        self.prefix = prefix
        self.ap = uvm_analysis_port("ap", self)
        self.raw_driver = None

    def build_phase(self):
        super().build_phase()
        dut = cocotb.top
        clk = dut.clk_sys
        self.raw_driver = AxilMasterDriver(dut, clk, prefix=self.prefix)

    async def run_phase(self):
        while True:
            item = await self.seq_item_port.get_next_item()
            item.master_id = self.master_id

            if item.is_write:
                resp = await self.raw_driver.write(
                    addr=item.addr,
                    data=item.data,
                    strb=item.strb,
                    prot=item.prot,
                    order=item.order
                )
                item.resp = resp
                item.rdata = 0
            else:
                rdata, resp = await self.raw_driver.read(
                    addr=item.addr,
                    prot=item.prot
                )
                item.rdata = rdata
                item.resp = resp

            # Broadcast completed transaction to scoreboard
            self.ap.write(item)
            self.seq_item_port.item_done()


class AxilMasterAgent(uvm_agent):
    """pyuvm Agent encapsulating AXI-Lite Master Sequencer and Driver."""
    def __init__(self, name, parent, master_id=0, prefix="s0_axil_"):
        super().__init__(name, parent)
        self.master_id = master_id
        self.prefix = prefix
        self.sequencer = None
        self.driver = None

    def build_phase(self):
        super().build_phase()
        self.sequencer = AxilSequencer("sequencer", self)
        self.driver = AxilDriver("driver", self, master_id=self.master_id, prefix=self.prefix)

    def connect_phase(self):
        super().connect_phase()
        self.driver.seq_item_port.connect(self.sequencer.seq_item_export)
