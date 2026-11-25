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
        self.in_flight_item = None

    def build_phase(self):
        super().build_phase()
        dut = cocotb.top
        clk = dut.clk_sys
        self.raw_driver = AxilMasterDriver(dut, clk, prefix=self.prefix)

    def flush_pending(self):
        """Clear bus signals and return any interrupted in-flight write address on reset."""
        if self.raw_driver is not None:
            self.raw_driver.init_signals()
        flushed_addr = None
        if self.in_flight_item is not None and self.in_flight_item.is_write:
            flushed_addr = self.in_flight_item.addr
        self.in_flight_item = None
        return flushed_addr

    async def run_phase(self):
        while True:
            item = await self.seq_item_port.get_next_item()
            item.master_id = self.master_id
            self.in_flight_item = item

            if item.is_write:
                resp = await self.raw_driver.write(
                    addr=item.addr,
                    data=item.data,
                    strb=item.strb,
                    prot=item.prot,
                    order=item.order,
                    bready_delay=item.bready_delay
                )
                item.resp = resp
                item.rdata = 0
            else:
                rdata, resp = await self.raw_driver.read(
                    addr=item.addr,
                    prot=item.prot,
                    rready_delay=item.rready_delay
                )
                item.rdata = rdata
                item.resp = resp

            # Only broadcast if transaction was not flushed by an injected reset
            if self.in_flight_item is item:
                self.in_flight_item = None
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
