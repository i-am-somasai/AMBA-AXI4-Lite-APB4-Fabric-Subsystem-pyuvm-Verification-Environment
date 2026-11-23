# tb/models/apb_driver.py
# Simple APB4 Master Driver for peripheral unit and block testing
import cocotb
from cocotb.triggers import RisingEdge, Timer

class ApbMasterDriver:
    """Synchronous APB4 Master Driver adhering to AMBA APB4 protocol."""
    def __init__(self, dut, clk, prefix=""):
        self.dut = dut
        self.clk = clk
        self.prefix = prefix

        self.paddr   = getattr(dut, f"{prefix}paddr")
        self.pprot   = getattr(dut, f"{prefix}pprot", None)
        self.psel    = getattr(dut, f"{prefix}psel")
        self.penable = getattr(dut, f"{prefix}penable")
        self.pwrite  = getattr(dut, f"{prefix}pwrite")
        self.pwdata  = getattr(dut, f"{prefix}pwdata")
        self.pstrb   = getattr(dut, f"{prefix}pstrb", None)
        self.pready  = getattr(dut, f"{prefix}pready")
        self.prdata  = getattr(dut, f"{prefix}prdata")
        self.pslverr = getattr(dut, f"{prefix}pslverr")

        self.init_signals()

    def init_signals(self):
        self.psel.value = 0
        self.penable.value = 0
        self.pwrite.value = 0
        self.paddr.value = 0
        self.pwdata.value = 0
        if self.pprot is not None:
            self.pprot.value = 0
        if self.pstrb is not None:
            self.pstrb.value = 0

    async def write(self, addr, data, strb=0xF, prot=0):
        """Execute APB4 write transfer."""
        await RisingEdge(self.clk)
        # SETUP phase
        self.psel.value = 1
        self.penable.value = 0
        self.pwrite.value = 1
        self.paddr.value = addr
        self.pwdata.value = data
        if self.pstrb is not None:
            self.pstrb.value = strb
        if self.pprot is not None:
            self.pprot.value = prot

        # ACCESS phase
        await RisingEdge(self.clk)
        self.penable.value = 1

        while True:
            await RisingEdge(self.clk)
            if int(self.pready.value) == 1:
                break

        pslverr = int(self.pslverr.value)
        self.psel.value = 0
        self.penable.value = 0
        self.pwrite.value = 0
        await Timer(1, unit="step")
        return pslverr

    async def read(self, addr, prot=0):
        """Execute APB4 read transfer."""
        await RisingEdge(self.clk)
        # SETUP phase
        self.psel.value = 1
        self.penable.value = 0
        self.pwrite.value = 0
        self.paddr.value = addr
        if self.pstrb is not None:
            self.pstrb.value = 0
        if self.pprot is not None:
            self.pprot.value = prot

        # ACCESS phase
        await RisingEdge(self.clk)
        self.penable.value = 1

        while True:
            await RisingEdge(self.clk)
            if int(self.pready.value) == 1:
                break

        rdata = int(self.prdata.value)
        pslverr = int(self.pslverr.value)
        self.psel.value = 0
        self.penable.value = 0
        await Timer(1, unit="step")
        return rdata, pslverr
