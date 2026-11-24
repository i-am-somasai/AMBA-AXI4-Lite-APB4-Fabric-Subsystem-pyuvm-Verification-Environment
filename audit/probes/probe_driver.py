"""
probe_driver.py - Minimal, independent AXI4-Lite Master Driver
Authored strictly from ARM AMBA AXI4-Lite specification (spec Section 6).
Independent of all project models/drivers.
"""
import cocotb
from cocotb.triggers import RisingEdge, ReadOnly, Timer

class ProbeAxilDriver:
    """Independent AXI4-Lite Master Driver strictly following Section 6 protocol rules."""
    def __init__(self, dut, clk, prefix="s0_axil"):
        self.dut = dut
        self.clk = clk
        self.prefix = prefix
        
        # Signals
        self.awaddr  = getattr(dut, f"{prefix}_awaddr")
        self.awprot  = getattr(dut, f"{prefix}_awprot")
        self.awvalid = getattr(dut, f"{prefix}_awvalid")
        self.awready = getattr(dut, f"{prefix}_awready")
        
        self.wdata   = getattr(dut, f"{prefix}_wdata")
        self.wstrb   = getattr(dut, f"{prefix}_wstrb")
        self.wvalid  = getattr(dut, f"{prefix}_wvalid")
        self.wready  = getattr(dut, f"{prefix}_wready")
        
        self.bresp   = getattr(dut, f"{prefix}_bresp")
        self.bvalid  = getattr(dut, f"{prefix}_bvalid")
        self.bready  = getattr(dut, f"{prefix}_bready")
        
        self.araddr  = getattr(dut, f"{prefix}_araddr")
        self.arprot  = getattr(dut, f"{prefix}_arprot")
        self.arvalid = getattr(dut, f"{prefix}_arvalid")
        self.arready = getattr(dut, f"{prefix}_arready")
        
        self.rdata   = getattr(dut, f"{prefix}_rdata")
        self.rresp   = getattr(dut, f"{prefix}_rresp")
        self.rvalid  = getattr(dut, f"{prefix}_rvalid")
        self.rready  = getattr(dut, f"{prefix}_rready")
        
        self.init_signals()

    def init_signals(self):
        self.awaddr.value  = 0
        self.awprot.value  = 0
        self.awvalid.value = 0
        self.wdata.value   = 0
        self.wstrb.value   = 0
        self.wvalid.value  = 0
        self.bready.value  = 0
        self.araddr.value  = 0
        self.arprot.value  = 0
        self.arvalid.value = 0
        self.rready.value  = 0

    async def write(self, addr, data, strb=0xF, prot=0, timeout_cycles=500):
        """Perform AXI4-Lite write transfer per Section 6."""
        # Drive AW and W simultaneously
        self.awaddr.value  = addr
        self.awprot.value  = prot
        self.awvalid.value = 1
        self.wdata.value   = data
        self.wstrb.value   = strb
        self.wvalid.value  = 1
        aw_done = False
        w_done  = False
        cycles = 0
        
        while not (aw_done and w_done):
            await RisingEdge(self.clk)
            cycles += 1
            if cycles > timeout_cycles:
                raise TimeoutError(f"AXI Write handshake timed out on addr=0x{addr:08x}")
            
            if not aw_done and self.awready.value == 1:
                aw_done = True
                self.awvalid.value = 0
                
            if not w_done and self.wready.value == 1:
                w_done = True
                self.wvalid.value = 0

        # Wait for B response
        self.bready.value = 1
        b_done = False
        while not b_done:
            await RisingEdge(self.clk)
            cycles += 1
            if cycles > timeout_cycles:
                raise TimeoutError(f"AXI Write response timed out on addr=0x{addr:08x}")
            if self.bvalid.value == 1:
                resp = int(self.bresp.value)
                b_done = True
                
        self.bready.value = 0
        return resp

    async def read(self, addr, prot=0, timeout_cycles=500):
        """Perform AXI4-Lite read transfer per Section 6."""
        self.araddr.value  = addr
        self.arprot.value  = prot
        self.arvalid.value = 1
        self.rready.value  = 1
        
        ar_done = False
        cycles = 0
        
        while not ar_done:
            await RisingEdge(self.clk)
            cycles += 1
            if cycles > timeout_cycles:
                raise TimeoutError(f"AXI Read AR handshake timed out on addr=0x{addr:08x}")
            if self.arready.value == 1:
                ar_done = True
                self.arvalid.value = 0

        # Wait for R response
        r_done = False
        while not r_done:
            await RisingEdge(self.clk)
            cycles += 1
            if cycles > timeout_cycles:
                raise TimeoutError(f"AXI Read R handshake timed out on addr=0x{addr:08x}")
            if self.rvalid.value == 1:
                data = int(self.rdata.value)
                resp = int(self.rresp.value)
                r_done = True
                
        self.rready.value = 0
        return data, resp
