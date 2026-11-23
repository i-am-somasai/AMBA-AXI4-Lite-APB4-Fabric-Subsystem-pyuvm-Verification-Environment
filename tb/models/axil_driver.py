# Reusable AXI4-Lite Master Driver for cocotb testbenches
import cocotb
from cocotb.triggers import RisingEdge, Timer

class AxilMasterDriver:
    """Simple single-master AXI4-Lite driver for L0/L1 tests."""
    def __init__(self, dut, clk, prefix="s_axil_"):
        self.dut = dut
        self.clk = clk
        self.prefix = prefix
        self.timeout_cycles = 2000

        self.awaddr  = getattr(dut, f"{prefix}awaddr")
        self.awprot  = getattr(dut, f"{prefix}awprot", None)
        self.awvalid = getattr(dut, f"{prefix}awvalid")
        self.awready = getattr(dut, f"{prefix}awready")

        self.wdata   = getattr(dut, f"{prefix}wdata")
        self.wstrb   = getattr(dut, f"{prefix}wstrb")
        self.wvalid  = getattr(dut, f"{prefix}wvalid")
        self.wready  = getattr(dut, f"{prefix}wready")

        self.bresp   = getattr(dut, f"{prefix}bresp")
        self.bvalid  = getattr(dut, f"{prefix}bvalid")
        self.bready  = getattr(dut, f"{prefix}bready")

        self.araddr  = getattr(dut, f"{prefix}araddr")
        self.arprot  = getattr(dut, f"{prefix}arprot", None)
        self.arvalid = getattr(dut, f"{prefix}arvalid")
        self.arready = getattr(dut, f"{prefix}arready")

        self.rdata   = getattr(dut, f"{prefix}rdata")
        self.rresp   = getattr(dut, f"{prefix}rresp")
        self.rvalid  = getattr(dut, f"{prefix}rvalid")
        self.rready  = getattr(dut, f"{prefix}rready")

        self.init_signals()

    def init_signals(self):
        self.awvalid.value = 0
        self.wvalid.value  = 0
        self.bready.value  = 0
        self.arvalid.value = 0
        self.rready.value  = 0

    async def write(self, addr, data, strb=0xF, prot=0, order="simultaneous"):
        """Performs an AXI-Lite write transaction.
           order can be: 'simultaneous', 'aw_first', 'w_first'
        """
        self.awaddr.value = addr
        if self.awprot is not None:
            self.awprot.value = prot
        self.wdata.value = data
        self.wstrb.value = strb

        aw_done = False
        w_done = False

        if order == "simultaneous":
            self.awvalid.value = 1
            self.wvalid.value = 1
        elif order == "aw_first":
            self.awvalid.value = 1
            self.wvalid.value = 0
        elif order == "w_first":
            self.awvalid.value = 0
            self.wvalid.value = 1

        cycles = 0
        while not (aw_done and w_done):
            await RisingEdge(self.clk)
            cycles += 1
            if cycles > self.timeout_cycles:
                raise TimeoutError(f"AXI-Lite write handshake timeout on addr 0x{addr:08x}")

            if not aw_done and self.awvalid.value and self.awready.value:
                aw_done = True
                self.awvalid.value = 0

            if not w_done and self.wvalid.value and self.wready.value:
                w_done = True
                self.wvalid.value = 0

            # Advance second channel if staggered
            if order == "aw_first" and aw_done and not w_done and not self.wvalid.value:
                self.wvalid.value = 1
            elif order == "w_first" and w_done and not aw_done and not self.awvalid.value:
                self.awvalid.value = 1

        # Wait for B response
        self.bready.value = 1
        cycles = 0
        while True:
            await RisingEdge(self.clk)
            cycles += 1
            if cycles > self.timeout_cycles:
                raise TimeoutError(f"AXI-Lite write response timeout on addr 0x{addr:08x}")
            if self.bvalid.value:
                resp = int(self.bresp.value)
                break

        self.bready.value = 0
        return resp

    async def read(self, addr, prot=0):
        """Performs an AXI-Lite read transaction."""
        self.araddr.value = addr
        if self.arprot is not None:
            self.arprot.value = prot
        self.arvalid.value = 1

        cycles = 0
        while True:
            await RisingEdge(self.clk)
            cycles += 1
            if cycles > self.timeout_cycles:
                raise TimeoutError(f"AXI-Lite read address timeout on addr 0x{addr:08x}")
            if self.arready.value:
                break
        self.arvalid.value = 0

        # Wait for R response
        self.rready.value = 1
        cycles = 0
        while True:
            await RisingEdge(self.clk)
            cycles += 1
            if cycles > self.timeout_cycles:
                raise TimeoutError(f"AXI-Lite read response timeout on addr 0x{addr:08x}")
            if self.rvalid.value:
                rdata = int(self.rdata.value)
                rresp = int(self.rresp.value)
                break

        self.rready.value = 0
        return rdata, rresp
