# tb/pyuvm/monitors/fabric_monitors.py
# Passive monitors observing physical DUT signals and driving functional coverage sampling
import cocotb
from cocotb.triggers import RisingEdge
from cocotb.utils import get_sim_time
from func_cov.fabric_cov import (
    sample_txn, sample_wstrb, sample_order, sample_backpressure,
    sample_contention, sample_apb, sample_cdc, sample_uart, sample_reset,
    CoverageCollector
)

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


class AxilBusMonitor:
    """Passive AXI4-Lite bus monitor observing physical channel transactions."""
    def __init__(self, clk, rst_n, master_id=0, prefix="s0_axil_", dut=None):
        self.clk = clk
        self.rst_n = rst_n
        self.master_id = master_id
        self.prefix = prefix
        self.dut = dut if dut is not None else cocotb.top
        self.running = False
        self._task = None

        self.awaddr = getattr(self.dut, f"{prefix}awaddr")
        self.awvalid = getattr(self.dut, f"{prefix}awvalid")
        self.awready = getattr(self.dut, f"{prefix}awready")

        self.wdata = getattr(self.dut, f"{prefix}wdata")
        self.wstrb = getattr(self.dut, f"{prefix}wstrb")
        self.wvalid = getattr(self.dut, f"{prefix}wvalid")
        self.wready = getattr(self.dut, f"{prefix}wready")

        self.bresp = getattr(self.dut, f"{prefix}bresp")
        self.bvalid = getattr(self.dut, f"{prefix}bvalid")
        self.bready = getattr(self.dut, f"{prefix}bready")

        self.araddr = getattr(self.dut, f"{prefix}araddr")
        self.arvalid = getattr(self.dut, f"{prefix}arvalid")
        self.arready = getattr(self.dut, f"{prefix}arready")

        self.rdata = getattr(self.dut, f"{prefix}rdata")
        self.rresp = getattr(self.dut, f"{prefix}rresp")
        self.rvalid = getattr(self.dut, f"{prefix}rvalid")
        self.rready = getattr(self.dut, f"{prefix}rready")

    def start(self):
        if not self.running:
            self.running = True
            self._task = cocotb.start_soon(self._monitor_loop())

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()

    async def _monitor_loop(self):
        cycle = 0
        t_aw = None
        t_w = None
        t_aw_valid = None
        t_w_valid = None
        curr_awaddr = 0
        curr_wstrb = 0xF
        curr_araddr = 0

        aw_delay = 0
        w_delay = 0
        b_delay = 0
        ar_delay = 0
        r_delay = 0

        while self.running:
            await RisingEdge(self.clk)
            cycle += 1

            if safe_int(self.rst_n.value) == 0:
                t_aw = None
                t_w = None
                t_aw_valid = None
                t_w_valid = None
                aw_delay = 0
                w_delay = 0
                b_delay = 0
                ar_delay = 0
                r_delay = 0
                continue

            # --- AW Channel ---
            awv = safe_int(self.awvalid.value)
            awr = safe_int(self.awready.value)
            if awv:
                if t_aw_valid is None:
                    t_aw_valid = cycle
                if awr:
                    t_aw = cycle
                    curr_awaddr = safe_int(self.awaddr.value)
                    sample_backpressure("AW", CoverageCollector.delay_to_bucket(aw_delay))
                    aw_delay = 0
                else:
                    aw_delay += 1

            # --- W Channel ---
            wv = safe_int(self.wvalid.value)
            wr = safe_int(self.wready.value)
            if wv:
                if t_w_valid is None:
                    t_w_valid = cycle
                if wr:
                    t_w = cycle
                    curr_wstrb = safe_int(self.wstrb.value)
                    sample_backpressure("W", CoverageCollector.delay_to_bucket(w_delay))
                    w_delay = 0
                else:
                    w_delay += 1

            # --- B Channel ---
            bv = safe_int(self.bvalid.value)
            br = safe_int(self.bready.value)
            if bv:
                if br:
                    sample_backpressure("B", CoverageCollector.delay_to_bucket(b_delay))
                    b_delay = 0
                    # Write transaction completed
                    target = CoverageCollector.decode_target(curr_awaddr)
                    resp = CoverageCollector.decode_resp(safe_int(self.bresp.value))
                    sample_txn(self.master_id, target, "WR", resp)

                    # Handshake/arrival order: track earliest VALID assertion (w_first vs aw_first)
                    if t_aw is not None and t_w is not None:
                        if t_w_valid is not None and t_aw_valid is not None:
                            if t_w_valid < t_aw_valid:
                                order = "w_first"
                            elif t_aw_valid < t_w_valid or t_aw < t_w:
                                order = "aw_first"
                            else:
                                order = "simultaneous"
                        elif t_aw == t_w:
                            order = "simultaneous"
                        elif t_aw < t_w:
                            order = "aw_first"
                        else:
                            order = "w_first"
                        if target in ["RAM", "CSR", "CDC", "APB"]:
                            sample_wstrb(target, curr_wstrb & 0xF)
                            sample_order(target, order)
                    t_aw = None
                    t_w = None
                    t_aw_valid = None
                    t_w_valid = None
                else:
                    b_delay += 1

            # --- AR Channel ---
            arv = safe_int(self.arvalid.value)
            arr = safe_int(self.arready.value)
            if arv:
                if arr:
                    curr_araddr = safe_int(self.araddr.value)
                    sample_backpressure("AR", CoverageCollector.delay_to_bucket(ar_delay))
                    ar_delay = 0
                else:
                    ar_delay += 1

            # --- R Channel ---
            rv = safe_int(self.rvalid.value)
            rr = safe_int(self.rready.value)
            if rv:
                if rr:
                    sample_backpressure("R", CoverageCollector.delay_to_bucket(r_delay))
                    r_delay = 0
                    # Read transaction completed
                    target = CoverageCollector.decode_target(curr_araddr)
                    resp = CoverageCollector.decode_resp(safe_int(self.rresp.value))
                    sample_txn(self.master_id, target, "RD", resp)
                else:
                    r_delay += 1


class CrossbarContentionMonitor:
    """Cycle-aligned observer monitoring multi-master concurrent activity and contention."""
    def __init__(self, clk, rst_n, dut=None):
        self.clk = clk
        self.rst_n = rst_n
        self.dut = dut if dut is not None else cocotb.top
        self.running = False
        self._task = None

    def start(self):
        if not self.running:
            self.running = True
            self._task = cocotb.start_soon(self._monitor_loop())

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()

    async def _monitor_loop(self):
        while self.running:
            await RisingEdge(self.clk)
            if safe_int(self.rst_n.value) == 0:
                continue

            m0_aw = safe_int(self.dut.s0_axil_awvalid.value) == 1
            m0_ar = safe_int(self.dut.s0_axil_arvalid.value) == 1
            m1_aw = safe_int(self.dut.s1_axil_awvalid.value) == 1
            m1_ar = safe_int(self.dut.s1_axil_arvalid.value) == 1

            m0_active = m0_aw or m0_ar
            m1_active = m1_aw or m1_ar

            if m0_active and m1_active:
                addr0 = safe_int(self.dut.s0_axil_awaddr.value) if m0_aw else safe_int(self.dut.s0_axil_araddr.value)
                addr1 = safe_int(self.dut.s1_axil_awaddr.value) if m1_aw else safe_int(self.dut.s1_axil_araddr.value)
                t0 = CoverageCollector.decode_target(addr0)
                t1 = CoverageCollector.decode_target(addr1)

                c_type = "same_slave" if t0 == t1 else "diff_slaves"
                op0 = "WR" if m0_aw else "RD"
                op1 = "WR" if m1_aw else "RD"

                if op0 == "RD" and op1 == "RD":
                    combo = "R/R"
                elif op0 == "WR" and op1 == "WR":
                    combo = "W/W"
                else:
                    combo = "R/W"
                sample_contention(c_type, combo)
            elif m0_active or m1_active:
                is_wr = (m0_aw if m0_active else m1_aw)
                combo = "W/W" if is_wr else "R/R"
                sample_contention("one_idle", combo)


class ApbBusMonitor:
    """Monitors the APB4 bus on the bridge peripheral side."""
    def __init__(self, clk, rst_n, psel=None, penable=None, pwrite=None, pready=None,
                 pslverr=None, pstrb=None, paddr=None, dut=None):
        self.clk = clk
        self.rst_n = rst_n
        self.dut = dut if dut is not None else cocotb.top
        self.psel = psel if psel is not None else getattr(self.dut, "apb_psel", None)
        self.penable = penable if penable is not None else getattr(self.dut, "apb_penable", None)
        self.pwrite = pwrite if pwrite is not None else getattr(self.dut, "apb_pwrite", None)
        self.pready = pready if pready is not None else getattr(self.dut, "apb_pready", None)
        self.pslverr = pslverr if pslverr is not None else getattr(self.dut, "apb_pslverr", None)
        self.pstrb = pstrb if pstrb is not None else getattr(self.dut, "apb_pstrb", None)
        self.paddr = paddr if paddr is not None else getattr(self.dut, "apb_paddr", None)

        self.running = False
        self._task = None

    def start(self):
        if not self.running and self.psel is not None:
            self.running = True
            self._task = cocotb.start_soon(self._monitor_loop())

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()

    async def _monitor_loop(self):
        wait_count = 0
        curr_write = 0
        curr_strb = 0xF

        while self.running:
            await RisingEdge(self.clk)
            if safe_int(self.rst_n.value) == 0:
                wait_count = 0
                continue

            psel_val = safe_int(self.psel.value)
            penable_val = safe_int(self.penable.value)

            if psel_val == 1 and penable_val == 0:
                # SETUP phase
                wait_count = 0
                curr_write = safe_int(self.pwrite.value)
                curr_strb = safe_int(self.pstrb.value) if self.pstrb is not None else 0xF
            elif psel_val == 1 and penable_val == 1:
                # ACCESS phase
                pready_val = safe_int(self.pready.value)
                if pready_val == 0:
                    wait_count += 1
                else:
                    # Transfer complete
                    if wait_count == 0:
                        wait_b = "0"
                    elif wait_count == 1:
                        wait_b = "1"
                    elif 2 <= wait_count <= 4:
                        wait_b = "2-4"
                    else:
                        wait_b = "5+"

                    err = "err" if (safe_int(self.pslverr.value) == 1) else "no_err"
                    op = "WR" if (curr_write == 1) else "RD"
                    s_class = CoverageCollector.strb_to_class(curr_strb)

                    sample_apb(wait_b, err, op, s_class)
                    wait_count = 0


class CdcMonitor:
    """Monitors asynchronous CDC bridge crossings and measures physical clock periods."""
    def __init__(self, clk_sys, clk_slow, rst_n, dut=None):
        self.clk_sys = clk_sys
        self.clk_slow = clk_slow
        self.rst_n = rst_n
        self.dut = dut if dut is not None else cocotb.top
        self.running = False
        self._task = None
        self._sys_clk_task = None
        self._slow_clk_task = None
        self._sys_period_ns = None
        self._slow_period_ns = None

    def start(self):
        if not self.running:
            self.running = True
            self._sys_clk_task = cocotb.start_soon(self._measure_sys_clk())
            self._slow_clk_task = cocotb.start_soon(self._measure_slow_clk())
            self._task = cocotb.start_soon(self._monitor_loop())

    def stop(self):
        self.running = False
        for t in (self._task, self._sys_clk_task, self._slow_clk_task):
            if t:
                t.cancel()

    async def _measure_sys_clk(self):
        last_t = None
        while self.running:
            await RisingEdge(self.clk_sys)
            now = get_sim_time("ns")
            if last_t is not None and now > last_t:
                self._sys_period_ns = now - last_t
            last_t = now

    async def _measure_slow_clk(self):
        last_t = None
        while self.running:
            await RisingEdge(self.clk_slow)
            now = get_sim_time("ns")
            if last_t is not None and now > last_t:
                self._slow_period_ns = now - last_t
            last_t = now

    def _classify_ratio(self):
        if self._slow_period_ns is None or self._sys_period_ns is None:
            return None
        if self._slow_period_ns > self._sys_period_ns * 1.1:
            return "slow<sys"
        elif self._slow_period_ns < self._sys_period_ns * 0.9:
            return "slow>sys"
        return "approx_equal"

    async def _monitor_loop(self):
        u_cdc = getattr(self.dut, "u_cdc_bridge", None)
        if u_cdc is None:
            return

        sampled_partial = False
        curr_ratio = None
        curr_op = None

        while self.running:
            await RisingEdge(self.clk_sys)
            if safe_int(self.rst_n.value) == 0:
                sampled_partial = False
                curr_ratio = None
                curr_op = None
                continue

            state = safe_int(u_cdc.state.value)
            # Detect CDC transaction initiation (ST_PUSH_REQ state = 3)
            if state == 3:  # ST_PUSH_REQ
                ratio = self._classify_ratio()
                if ratio is not None:
                    is_wr = safe_int(u_cdc.reg_is_write.value) == 1
                    op = "WR" if is_wr else "RD"
                    req_rempty = safe_int(u_cdc.u_req_fifo.rempty.value)
                    rsp_rempty = safe_int(u_cdc.u_resp_fifo.rempty.value)
                    occ = "empty" if (req_rempty == 1 and rsp_rempty == 1) else "partial"
                    sample_cdc(ratio, occ, op)
                    curr_ratio = ratio
                    curr_op = op
                    sampled_partial = (occ == "partial")
            elif state == 4 and not sampled_partial and curr_ratio is not None:  # ST_WAIT_RESP
                req_rempty = safe_int(u_cdc.u_req_fifo.rempty.value)
                rsp_rempty = safe_int(u_cdc.u_resp_fifo.rempty.value)
                if req_rempty == 0 or rsp_rempty == 0:
                    sample_cdc(curr_ratio, "partial", curr_op)
                    sampled_partial = True


class UartActivityMonitor:
    """Monitors UART peripheral registers, status flags, and errors."""
    def __init__(self, clk, rst_n, dut=None):
        self.clk = clk
        self.rst_n = rst_n
        self.dut = dut if dut is not None else cocotb.top
        self.running = False
        self._task = None

    def start(self):
        if not self.running:
            self.running = True
            self._task = cocotb.start_soon(self._monitor_loop())

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()

    async def _monitor_loop(self):
        u_uart = getattr(self.dut, "u_uart", None)
        if u_uart is None:
            return

        last_status = 0
        while self.running:
            await RisingEdge(self.clk)
            if safe_int(self.rst_n.value) == 0:
                continue

            psel = safe_int(u_uart.psel.value)
            penable = safe_int(u_uart.penable.value)
            pready = safe_int(u_uart.pready.value)

            # Sample on UART access completion or status change
            status_val = safe_int(getattr(u_uart, "status_word", None).value) if hasattr(u_uart, "status_word") else 0
            if (psel and penable and pready) or (status_val != last_status):
                last_status = status_val
                baud_val = safe_int(getattr(u_uart, "reg_bauddiv", None).value) if hasattr(u_uart, "reg_bauddiv") else 0
                if baud_val == 0:
                    b_bucket = "0"
                elif baud_val == 1:
                    b_bucket = "1"
                else:
                    b_bucket = "2+"

                tx_empty = safe_int(getattr(u_uart, "tx_fifo_empty", None).value) if hasattr(u_uart, "tx_fifo_empty") else 1
                tx_full = safe_int(getattr(u_uart, "tx_fifo_full", None).value) if hasattr(u_uart, "tx_fifo_full") else 0
                rx_empty = safe_int(getattr(u_uart, "rx_fifo_empty", None).value) if hasattr(u_uart, "rx_fifo_empty") else 1
                rx_full = safe_int(getattr(u_uart, "rx_fifo_full", None).value) if hasattr(u_uart, "rx_fifo_full") else 0

                if tx_empty and rx_empty:
                    f_state = "empty"
                elif tx_full or rx_full:
                    f_state = "full"
                else:
                    f_state = "partial"

                # Check error flags: bit 4 = FRAME_ERR, bit 5 = RX_OVF, bit 6 = TX_OVF
                if status_val & (1 << 4):
                    err = "frame_err"
                elif status_val & ((1 << 5) | (1 << 6)):
                    err = "overflow"
                else:
                    err = "none"

                sample_uart(b_bucket, f_state, err)


class ResetPhaseMonitor:
    """Monitors system reset transitions and identifies in-flight transaction phases."""
    def __init__(self, clk, rst_n, dut=None):
        self.clk = clk
        self.rst_n = rst_n
        self.dut = dut if dut is not None else cocotb.top
        self.running = False
        self._task = None

    def start(self):
        if not self.running:
            self.running = True
            self._task = cocotb.start_soon(self._monitor_loop())

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()

    def _classify_phase(self):
        m0_awv = safe_int(getattr(self.dut, "s0_axil_awvalid", 0).value)
        m0_awr = safe_int(getattr(self.dut, "s0_axil_awready", 0).value)
        m1_awv = safe_int(getattr(self.dut, "s1_axil_awvalid", 0).value)
        m1_awr = safe_int(getattr(self.dut, "s1_axil_awready", 0).value)

        m0_wv = safe_int(getattr(self.dut, "s0_axil_wvalid", 0).value)
        m0_wr = safe_int(getattr(self.dut, "s0_axil_wready", 0).value)
        m1_wv = safe_int(getattr(self.dut, "s1_axil_wvalid", 0).value)
        m1_wr = safe_int(getattr(self.dut, "s1_axil_wready", 0).value)

        m0_bv = safe_int(getattr(self.dut, "s0_axil_bvalid", 0).value)
        m1_bv = safe_int(getattr(self.dut, "s1_axil_bvalid", 0).value)

        m0_arv = safe_int(getattr(self.dut, "s0_axil_arvalid", 0).value)
        m1_arv = safe_int(getattr(self.dut, "s1_axil_arvalid", 0).value)
        m0_rv = safe_int(getattr(self.dut, "s0_axil_rvalid", 0).value)
        m1_rv = safe_int(getattr(self.dut, "s1_axil_rvalid", 0).value)

        if (m0_awv and not m0_awr) or (m1_awv and not m1_awr):
            return "aw_in_flight"
        elif (m0_wv and not m0_wr) or (m1_wv and not m1_wr):
            return "w_in_flight"
        elif m0_bv or m1_bv:
            return "b_pending"
        elif m0_arv or m1_arv or m0_rv or m1_rv:
            return "r_pending"
        return "idle"

    async def _monitor_loop(self):
        last_rst = safe_int(self.rst_n.value)
        last_active_phase = "idle"
        while self.running:
            await RisingEdge(self.clk)
            curr_rst = safe_int(self.rst_n.value)
            if last_rst == 1 and curr_rst == 0:
                live_phase = self._classify_phase()
                # Asynchronous negedge rst_n clears registered BVALID/RVALID immediately;
                # fall back to the preceding active clock-edge phase when live signals cleared.
                phase = live_phase if live_phase != "idle" else last_active_phase
                sample_reset(phase)
            if curr_rst == 1:
                last_active_phase = self._classify_phase()
            last_rst = curr_rst
