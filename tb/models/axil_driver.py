# Reusable AXI4-Lite Master Driver for cocotb testbenches
import cocotb
from cocotb.triggers import RisingEdge, Timer


def safe_int(val, default=0):
    try:
        if hasattr(val, "is_resolvable"):
            if val.is_resolvable:
                return int(val)
            s = str(val).lower().replace("x", "0").replace("z", "0").replace("u", "0").replace("w", "0").replace("-", "0")
            return int(s, 2)
        return int(val)
    except Exception:
        return default

class AxilMasterDriver:
    """Simple single-master AXI4-Lite driver for L0/L1 tests."""
    def __init__(self, dut=None, clk=None, prefix="s_axil_", **kwargs):
        self.dut = dut
        self.clk = clk
        self.prefix = prefix
        self.timeout_cycles = 2000

        self.awaddr  = kwargs.get("awaddr") if "awaddr" in kwargs else getattr(dut, f"{prefix}awaddr")
        self.awprot  = kwargs.get("awprot") if "awprot" in kwargs else getattr(dut, f"{prefix}awprot", None)
        self.awvalid = kwargs.get("awvalid") if "awvalid" in kwargs else getattr(dut, f"{prefix}awvalid")
        self.awready = kwargs.get("awready") if "awready" in kwargs else getattr(dut, f"{prefix}awready")

        self.wdata   = kwargs.get("wdata") if "wdata" in kwargs else getattr(dut, f"{prefix}wdata")
        self.wstrb   = kwargs.get("wstrb") if "wstrb" in kwargs else getattr(dut, f"{prefix}wstrb")
        self.wvalid  = kwargs.get("wvalid") if "wvalid" in kwargs else getattr(dut, f"{prefix}wvalid")
        self.wready  = kwargs.get("wready") if "wready" in kwargs else getattr(dut, f"{prefix}wready")

        self.bresp   = kwargs.get("bresp") if "bresp" in kwargs else getattr(dut, f"{prefix}bresp")
        self.bvalid  = kwargs.get("bvalid") if "bvalid" in kwargs else getattr(dut, f"{prefix}bvalid")
        self.bready  = kwargs.get("bready") if "bready" in kwargs else getattr(dut, f"{prefix}bready")

        self.araddr  = kwargs.get("araddr") if "araddr" in kwargs else getattr(dut, f"{prefix}araddr")
        self.arprot  = kwargs.get("arprot") if "arprot" in kwargs else getattr(dut, f"{prefix}arprot", None)
        self.arvalid = kwargs.get("arvalid") if "arvalid" in kwargs else getattr(dut, f"{prefix}arvalid")
        self.arready = kwargs.get("arready") if "arready" in kwargs else getattr(dut, f"{prefix}arready")

        self.rdata   = kwargs.get("rdata") if "rdata" in kwargs else getattr(dut, f"{prefix}rdata")
        self.rresp   = kwargs.get("rresp") if "rresp" in kwargs else getattr(dut, f"{prefix}rresp")
        self.rvalid  = kwargs.get("rvalid") if "rvalid" in kwargs else getattr(dut, f"{prefix}rvalid")
        self.rready  = kwargs.get("rready") if "rready" in kwargs else getattr(dut, f"{prefix}rready")

        self.init_signals()

    def init_signals(self):
        self.awvalid.value = 0
        self.wvalid.value  = 0
        self.bready.value  = 0
        self.arvalid.value = 0
        self.rready.value  = 0

    async def write(self, addr, data, strb=0xF, prot=0, order="simultaneous", bready_delay=0):
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
        aw_delay = 0
        w_delay = 0
        b_delay = 0
        aw_asserted = False
        w_asserted = False

        if order == "simultaneous":
            self.awvalid.value = 1
            self.wvalid.value = 1
            aw_asserted = True
            w_asserted = True
        elif order == "aw_first":
            self.awvalid.value = 1
            self.wvalid.value = 0
            aw_asserted = True
        elif order == "w_first":
            self.awvalid.value = 0
            self.wvalid.value = 1
            w_asserted = True

        cycles = 0
        w_first_stagger = 2 if order == "w_first" else 0

        while not (aw_done and w_done):
            await RisingEdge(self.clk)
            cycles += 1
            if cycles > self.timeout_cycles:
                raise TimeoutError(f"AXI-Lite write handshake timeout on addr 0x{addr:08x}")

            if not aw_done:
                if self.awvalid.value and self.awready.value:
                    aw_done = True
                    self.awvalid.value = 0
                elif aw_asserted:
                    aw_delay += 1

            if not w_done:
                if self.wvalid.value and self.wready.value:
                    w_done = True
                    self.wvalid.value = 0
                elif w_asserted:
                    w_delay += 1

            # Advance second channel if staggered
            if order == "aw_first" and aw_done and not w_done and not self.wvalid.value:
                self.wvalid.value = 1
                w_asserted = True
            elif order == "w_first" and not aw_done and not self.awvalid.value:
                w_first_stagger -= 1
                if w_first_stagger <= 0:
                    self.awvalid.value = 1
                    aw_asserted = True

        # Wait for B response
        if bready_delay == 0:
            self.bready.value = 1
        else:
            self.bready.value = 0

        cycles = 0
        while True:
            await RisingEdge(self.clk)
            cycles += 1
            if cycles > self.timeout_cycles:
                raise TimeoutError(f"AXI-Lite write response timeout on addr 0x{addr:08x}")
            if self.bvalid.value:
                if bready_delay > 0:
                    for _ in range(max(0, bready_delay - 1)):
                        self.bready.value = 0
                        await RisingEdge(self.clk)
                    self.bready.value = 1
                    await RisingEdge(self.clk)
                    resp = safe_int(self.bresp.value)
                    self.bready.value = 0
                    break
                else:
                    resp = safe_int(self.bresp.value)
                    break
            b_delay += 1

        self.bready.value = 0
        return resp

    async def read(self, addr, prot=0, rready_delay=0):
        """Performs an AXI-Lite read transaction."""
        ar_delay = 0
        r_delay = 0
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
            ar_delay += 1
        self.arvalid.value = 0

        # Wait for R response
        if rready_delay == 0:
            self.rready.value = 1
        else:
            self.rready.value = 0

        cycles = 0
        while True:
            await RisingEdge(self.clk)
            cycles += 1
            if cycles > self.timeout_cycles:
                raise TimeoutError(f"AXI-Lite read response timeout on addr 0x{addr:08x}")
            if self.rvalid.value:
                if rready_delay > 0:
                    for _ in range(max(0, rready_delay - 1)):
                        self.rready.value = 0
                        await RisingEdge(self.clk)
                    self.rready.value = 1
                    await RisingEdge(self.clk)
                    rdata = safe_int(self.rdata.value)
                    rresp = safe_int(self.rresp.value)
                    self.rready.value = 0
                    break
                else:
                    rdata = safe_int(self.rdata.value)
                    rresp = safe_int(self.rresp.value)
                    break
            r_delay += 1

        self.rready.value = 0
        return rdata, rresp


# Alias for backwards compatibility
AxilDriver = AxilMasterDriver

