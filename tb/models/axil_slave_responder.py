# tb/models/axil_slave_responder.py
"""
Reactive AXI4-Lite Slave Responder Model for L1 testing.
Handles AW, W, B, AR, and R channels with programmable response delays,
configurable ready delays (backpressure), and response codes (OKAY, SLVERR, DECERR).
"""
import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.handle import SimHandleBase
import random


class AxilSlaveResponder:
    def __init__(
        self,
        clk: SimHandleBase,
        rst_n: SimHandleBase,
        name: str = "axil_slave",
        addr_width: int = 32,
        data_width: int = 32,
        base_addr: int = 0x00000000,
        size_bytes: int = 0x1000,
        default_resp: int = 0b00, # 00=OKAY, 10=SLVERR, 11=DECERR
        awready_delay: int = 0,
        wready_delay: int = 0,
        arready_delay: int = 0,
        bvalid_delay: int = 0,
        rvalid_delay: int = 0,
        # Port signals
        awaddr=None, awprot=None, awvalid=None, awready=None,
        wdata=None, wstrb=None, wvalid=None, wready=None,
        bresp=None, bvalid=None, bready=None,
        araddr=None, arprot=None, arvalid=None, arready=None,
        rdata=None, rresp=None, rvalid=None, rready=None,
    ):
        self.clk = clk
        self.rst_n = rst_n
        self.name = name
        self.addr_width = addr_width
        self.data_width = data_width
        self.base_addr = base_addr
        self.size_bytes = size_bytes
        self.default_resp = default_resp

        self.awready_delay = awready_delay
        self.wready_delay = wready_delay
        self.arready_delay = arready_delay
        self.bvalid_delay = bvalid_delay
        self.rvalid_delay = rvalid_delay

        # Signals
        self.awaddr = awaddr
        self.awprot = awprot
        self.awvalid = awvalid
        self.awready = awready

        self.wdata = wdata
        self.wstrb = wstrb
        self.wvalid = wvalid
        self.wready = wready

        self.bresp = bresp
        self.bvalid = bvalid
        self.bready = bready

        self.araddr = araddr
        self.arprot = arprot
        self.arvalid = arvalid
        self.arready = arready

        self.rdata = rdata
        self.rresp = rresp
        self.rvalid = rvalid
        self.rready = rready

        # Internal backing memory
        self.memory = {}
        self.running = False
        self._write_task = None
        self._read_task = None

    def start(self):
        if not self.running:
            self.running = True
            self._write_task = cocotb.start_soon(self._write_worker())
            self._read_task = cocotb.start_soon(self._read_worker())

    def stop(self):
        self.running = False
        if self._write_task:
            self._write_task.cancel()
        if self._read_task:
            self._read_task.cancel()

    async def _write_worker(self):
        # Initialize default outputs
        self.awready.value = 0
        self.wready.value = 0
        self.bvalid.value = 0
        self.bresp.value = 0

        while self.running:
            await RisingEdge(self.clk)
            if int(self.rst_n.value) == 0:
                self.awready.value = 0
                self.wready.value = 0
                self.bvalid.value = 0
                continue

            # Accept AW and W (can arrive in any order)
            captured_aw = False
            captured_w = False
            aw_addr = 0
            w_val = 0
            w_strb = 0xF

            while not (captured_aw and captured_w):
                # Drive AWREADY if AWVALID and not yet captured
                if not captured_aw:
                    if int(self.awvalid.value) == 1:
                        if self.awready_delay > 0:
                            for _ in range(self.awready_delay):
                                self.awready.value = 0
                                await RisingEdge(self.clk)
                        self.awready.value = 1
                        aw_addr = int(self.awaddr.value)
                        captured_aw = True
                    else:
                        self.awready.value = 0

                # Drive WREADY if WVALID and not yet captured
                if not captured_w:
                    if int(self.wvalid.value) == 1:
                        if self.wready_delay > 0:
                            for _ in range(self.wready_delay):
                                self.wready.value = 0
                                await RisingEdge(self.clk)
                        self.wready.value = 1
                        w_val = int(self.wdata.value)
                        w_strb = int(self.wstrb.value) if self.wstrb is not None else 0xF
                        captured_w = True
                    else:
                        self.wready.value = 0

                await RisingEdge(self.clk)
                self.awready.value = 0
                self.wready.value = 0

            # Store in backing memory
            offset = aw_addr - self.base_addr
            old_val = self.memory.get(offset, 0)
            new_val = old_val
            for b in range(4):
                if (w_strb >> b) & 1:
                    mask = 0xFF << (8 * b)
                    new_val = (new_val & ~mask) | (w_val & mask)
            self.memory[offset] = new_val

            # B channel response
            if self.bvalid_delay > 0:
                for _ in range(self.bvalid_delay):
                    await RisingEdge(self.clk)

            self.bvalid.value = 1
            self.bresp.value = self.default_resp

            # Wait for BREADY
            while True:
                await RisingEdge(self.clk)
                if int(self.bready.value) == 1:
                    break
            self.bvalid.value = 0

    async def _read_worker(self):
        self.arready.value = 0
        self.rvalid.value = 0
        self.rdata.value = 0
        self.rresp.value = 0

        while self.running:
            await RisingEdge(self.clk)
            if int(self.rst_n.value) == 0:
                self.arready.value = 0
                self.rvalid.value = 0
                continue

            # Wait for ARVALID
            if int(self.arvalid.value) == 1:
                if self.arready_delay > 0:
                    for _ in range(self.arready_delay):
                        self.arready.value = 0
                        await RisingEdge(self.clk)
                self.arready.value = 1
                rd_addr = int(self.araddr.value)
                await RisingEdge(self.clk)
                self.arready.value = 0

                # Prepare R response
                offset = rd_addr - self.base_addr
                data = self.memory.get(offset, 0x00000000)

                if self.rvalid_delay > 0:
                    for _ in range(self.rvalid_delay):
                        await RisingEdge(self.clk)

                self.rvalid.value = 1
                self.rdata.value = data
                self.rresp.value = self.default_resp

                # Wait for RREADY
                while True:
                    await RisingEdge(self.clk)
                    if int(self.rready.value) == 1:
                        break
                self.rvalid.value = 0
            else:
                self.arready.value = 0
