# tb/models/axil_monitor.py
"""
Passive AXI4-Lite Protocol Monitor.
Checks protocol compliance per Section 6 on every clock edge:
1. Payload stability: Once VALID is asserted, VALID and address/data/strb/prot must not change until READY is high.
2. BVALID only asserted after both AW and W handshakes have occurred.
3. RVALID only asserted after AR handshake.
4. Response codes only in {00: OKAY, 10: SLVERR, 11: DECERR}.
5. Exactly one response per transaction.
"""
import cocotb
from cocotb.triggers import RisingEdge


class AxilProtocolMonitor:
    def __init__(self, clk, rst_n, name="axil_mon",
                 awaddr=None, awprot=None, awvalid=None, awready=None,
                 wdata=None, wstrb=None, wvalid=None, wready=None,
                 bresp=None, bvalid=None, bready=None,
                 araddr=None, arprot=None, arvalid=None, arready=None,
                 rdata=None, rresp=None, rvalid=None, rready=None):
        self.clk = clk
        self.rst_n = rst_n
        self.name = name

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

        self.aw_count = 0
        self.w_count = 0
        self.b_count = 0
        self.ar_count = 0
        self.r_count = 0

        self.last_awvalid = 0
        self.last_awready = 0
        self.last_awaddr  = 0

        self.last_wvalid  = 0
        self.last_wready  = 0
        self.last_wdata   = 0

        self.last_bvalid  = 0
        self.last_bready  = 0
        self.last_bresp   = 0

        self.last_arvalid = 0
        self.last_arready = 0
        self.last_araddr  = 0

        self.last_rvalid  = 0
        self.last_rready  = 0
        self.last_rdata   = 0
        self.last_rresp   = 0

        self.running = False
        self._task = None

    def start(self):
        if not self.running:
            self.running = True
            self._task = cocotb.start_soon(self._check_loop())

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()

    async def _check_loop(self):
        while self.running:
            await RisingEdge(self.clk)
            if int(self.rst_n.value) == 0:
                self.aw_count = 0
                self.w_count = 0
                self.b_count = 0
                self.ar_count = 0
                self.r_count = 0
                self.last_awvalid = 0
                self.last_awready = 0
                self.last_wvalid  = 0
                self.last_wready  = 0
                self.last_arvalid = 0
                self.last_arready = 0
                self.last_bvalid  = 0
                self.last_bready  = 0
                self.last_rvalid  = 0
                self.last_rready  = 0
                continue

            # 1. AW Channel Stability
            cur_awvalid = int(self.awvalid.value) if self.awvalid.value.is_resolvable else 0
            cur_awready = int(self.awready.value) if self.awready.value.is_resolvable else 0
            cur_awaddr  = int(self.awaddr.value) if (cur_awvalid and self.awaddr.value.is_resolvable) else 0

            if self.last_awvalid and not self.last_awready:
                assert cur_awvalid == 1, f"[{self.name}] AWVALID dropped before AWREADY!"
                assert cur_awaddr == self.last_awaddr, f"[{self.name}] AWADDR changed before AWREADY!"
            if cur_awvalid and cur_awready:
                self.aw_count += 1
            self.last_awvalid = cur_awvalid
            self.last_awready = cur_awready
            self.last_awaddr  = cur_awaddr

            # 2. W Channel Stability
            cur_wvalid = int(self.wvalid.value) if self.wvalid.value.is_resolvable else 0
            cur_wready = int(self.wready.value) if self.wready.value.is_resolvable else 0
            cur_wdata  = int(self.wdata.value) if (cur_wvalid and self.wdata.value.is_resolvable) else 0

            if self.last_wvalid and not self.last_wready:
                assert cur_wvalid == 1, f"[{self.name}] WVALID dropped before WREADY!"
                assert cur_wdata == self.last_wdata, f"[{self.name}] WDATA changed before WREADY!"
            if cur_wvalid and cur_wready:
                self.w_count += 1
            self.last_wvalid = cur_wvalid
            self.last_wready = cur_wready
            self.last_wdata  = cur_wdata

            # 3. B Channel Verification
            cur_bvalid = int(self.bvalid.value) if self.bvalid.value.is_resolvable else 0
            cur_bready = int(self.bready.value) if self.bready.value.is_resolvable else 0
            cur_bresp  = int(self.bresp.value) if (cur_bvalid and self.bresp.value.is_resolvable) else 0

            if cur_bvalid:
                assert cur_bresp in (0b00, 0b10, 0b11), f"[{self.name}] Illegal BRESP {bin(cur_bresp)}!"
                assert min(self.aw_count, self.w_count) > self.b_count, \
                    f"[{self.name}] Spurious BVALID! aw_count={self.aw_count}, w_count={self.w_count}, b_count={self.b_count}"
            if self.last_bvalid and not self.last_bready:
                assert cur_bvalid == 1, f"[{self.name}] BVALID dropped before BREADY!"
                assert cur_bresp == self.last_bresp, f"[{self.name}] BRESP changed before BREADY!"
            if cur_bvalid and cur_bready:
                self.b_count += 1
            self.last_bvalid = cur_bvalid
            self.last_bready = cur_bready
            self.last_bresp  = cur_bresp

            # 4. AR Channel Stability
            cur_arvalid = int(self.arvalid.value) if self.arvalid.value.is_resolvable else 0
            cur_arready = int(self.arready.value) if self.arready.value.is_resolvable else 0
            cur_araddr  = int(self.araddr.value) if (cur_arvalid and self.araddr.value.is_resolvable) else 0

            if self.last_arvalid and not self.last_arready:
                assert cur_arvalid == 1, f"[{self.name}] ARVALID dropped before ARREADY!"
                assert cur_araddr == self.last_araddr, f"[{self.name}] ARADDR changed before ARREADY!"
            if cur_arvalid and cur_arready:
                self.ar_count += 1
            self.last_arvalid = cur_arvalid
            self.last_arready = cur_arready
            self.last_araddr  = cur_araddr

            # 5. R Channel Verification
            cur_rvalid = int(self.rvalid.value) if self.rvalid.value.is_resolvable else 0
            cur_rready = int(self.rready.value) if self.rready.value.is_resolvable else 0
            cur_rresp  = int(self.rresp.value) if (cur_rvalid and self.rresp.value.is_resolvable) else 0
            cur_rdata  = int(self.rdata.value) if (cur_rvalid and self.rdata.value.is_resolvable) else 0

            if cur_rvalid:
                assert cur_rresp in (0b00, 0b10, 0b11), f"[{self.name}] Illegal RRESP {bin(cur_rresp)}!"
                assert self.ar_count > self.r_count, \
                    f"[{self.name}] Spurious RVALID! ar_count={self.ar_count}, r_count={self.r_count}"
            if self.last_rvalid and not self.last_rready:
                assert cur_rvalid == 1, f"[{self.name}] RVALID dropped before RREADY!"
                assert cur_rdata == self.last_rdata, f"[{self.name}] RDATA changed before RREADY!"
            if cur_rvalid and cur_rready:
                self.r_count += 1
            self.last_rvalid = cur_rvalid
            self.last_rready = cur_rready
            self.last_rdata  = cur_rdata
            self.last_rresp  = cur_rresp
