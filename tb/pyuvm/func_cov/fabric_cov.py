# tb/pyuvm/coverage/fabric_cov.py
# Functional coverage model for AMBA Fabric subsystem (spec Section 10)
import os
from cocotb_coverage.coverage import CoverPoint, CoverCross, coverage_db

# -----------------------------------------------------------------------------
# 1. cg_txn: Transaction coverage
# Master (0, 1) x Target (RAM, CSR, CDC, APB, UNMAPPED) x Op (RD, WR) x Resp (OKAY, SLVERR, DECERR)
# Illegal combinations (excluded via ign_bins):
# - UNMAPPED can only return DECERR (OKAY and SLVERR are illegal)
# - Mapped slaves (RAM, CSR, CDC, APB) can only return OKAY or SLVERR (DECERR is illegal)
# Total legal cross bins = 2 * (4 * 2 * 2 + 1 * 2 * 1) = 36 bins.
# -----------------------------------------------------------------------------
ign_bins_txn = []
for m in [0, 1]:
    for op in ["RD", "WR"]:
        ign_bins_txn.append((m, "UNMAPPED", op, "OKAY"))
        ign_bins_txn.append((m, "UNMAPPED", op, "SLVERR"))
        for t in ["RAM", "CSR", "CDC", "APB"]:
            ign_bins_txn.append((m, t, op, "DECERR"))

@CoverPoint("cg_txn.master", xf=lambda m, t, o, r: m, bins=[0, 1])
@CoverPoint("cg_txn.target", xf=lambda m, t, o, r: t, bins=["RAM", "CSR", "CDC", "APB", "UNMAPPED"])
@CoverPoint("cg_txn.op", xf=lambda m, t, o, r: o, bins=["RD", "WR"])
@CoverPoint("cg_txn.resp", xf=lambda m, t, o, r: r, bins=["OKAY", "SLVERR", "DECERR"])
@CoverCross("cg_txn.cross", items=["cg_txn.master", "cg_txn.target", "cg_txn.op", "cg_txn.resp"], ign_bins=ign_bins_txn)
def sample_txn(m, t, o, r):
    pass

# -----------------------------------------------------------------------------
# 2. cg_wstrb: Strobe coverage
# 16 WSTRB patterns x target (RAM, CSR, CDC, APB) = 64 bins
# -----------------------------------------------------------------------------
@CoverPoint("cg_wstrb.target", xf=lambda t, s: t, bins=["RAM", "CSR", "CDC", "APB"])
@CoverPoint("cg_wstrb.strb", xf=lambda t, s: s, bins=list(range(16)))
@CoverCross("cg_wstrb.cross", items=["cg_wstrb.target", "cg_wstrb.strb"])
def sample_wstrb(t, s):
    pass

# -----------------------------------------------------------------------------
# 3. cg_order: Write handshake ordering
# Order (simultaneous, aw_first, w_first) x target (RAM, CSR, CDC, APB) = 12 bins
# -----------------------------------------------------------------------------
@CoverPoint("cg_order.target", xf=lambda t, ord: t, bins=["RAM", "CSR", "CDC", "APB"])
@CoverPoint("cg_order.order", xf=lambda t, ord: ord, bins=["simultaneous", "aw_first", "w_first"])
@CoverCross("cg_order.cross", items=["cg_order.target", "cg_order.order"])
def sample_order(t, ord):
    pass

# -----------------------------------------------------------------------------
# 4. cg_backpressure: Channel ready-delay backpressure
# Channel (AW, W, B, AR, R) x delay bucket {0, 1, 2-4, 5-16} = 20 bins
# -----------------------------------------------------------------------------
@CoverPoint("cg_backpressure.channel", xf=lambda ch, b: ch, bins=["AW", "W", "B", "AR", "R"])
@CoverPoint("cg_backpressure.bucket", xf=lambda ch, b: b, bins=["0", "1", "2-4", "5-16"])
@CoverCross("cg_backpressure.cross", items=["cg_backpressure.channel", "cg_backpressure.bucket"])
def sample_backpressure(ch, b):
    pass

# -----------------------------------------------------------------------------
# 5. cg_contention: Multi-master crossbar contention
# Legal dual-master cross bins: (same_slave, diff_slaves) x (R/R, R/W, W/W) = 6 bins
# Combining "one_idle" with a 2-master op pair is contradictory -> ign_bins (DEC-009)
# -----------------------------------------------------------------------------
ign_bins_contention = [
    ("one_idle", "R/R"),
    ("one_idle", "R/W"),
    ("one_idle", "W/W"),
]

@CoverPoint("cg_contention.type", xf=lambda c, op: c, bins=["same_slave", "diff_slaves", "one_idle"])
@CoverPoint("cg_contention.combo", xf=lambda c, op: op, bins=["R/R", "R/W", "W/W"])
@CoverCross("cg_contention.cross", items=["cg_contention.type", "cg_contention.combo"], ign_bins=ign_bins_contention)
def sample_contention(c, op):
    pass

# -----------------------------------------------------------------------------
# 6. cg_apb: APB bridge characteristics
# Wait-state bucket {0, 1, 2-4, 5+} x PSLVERR (no_err, err) x op (RD, WR) = 16 bins
# PSTRB pattern class x op: APB4 spec Sec 2.1 requires PSTRB=0 on reads ->
# ("byte"/"halfword"/"word", "RD") are illegal via ign_bins (DEC-010) -> 5 legal bins
# -----------------------------------------------------------------------------
ign_bins_apb_strb = [
    ("byte", "RD"),
    ("halfword", "RD"),
    ("word", "RD"),
]

@CoverPoint("cg_apb.wait", xf=lambda w, err, op, s: w, bins=["0", "1", "2-4", "5+"])
@CoverPoint("cg_apb.err", xf=lambda w, err, op, s: err, bins=["no_err", "err"])
@CoverPoint("cg_apb.op", xf=lambda w, err, op, s: op, bins=["RD", "WR"])
@CoverCross("cg_apb.wait_cross", items=["cg_apb.wait", "cg_apb.err", "cg_apb.op"])
@CoverPoint("cg_apb.strb_class", xf=lambda w, err, op, s: s, bins=["byte", "halfword", "word", "sparse"])
@CoverCross("cg_apb.strb_cross", items=["cg_apb.strb_class", "cg_apb.op"], ign_bins=ign_bins_apb_strb)
def sample_apb(w, err, op, s):
    pass

# -----------------------------------------------------------------------------
# 7. cg_cdc: Asynchronous CDC bridge characteristics
# Clock ratio (slow<sys, approx_equal, slow>sys) x FIFO occupancy (empty, partial) x op = 12 bins
# NOTE: FIFO occupancy "full" is physically unreachable under normal bridge operation
# because the bridge allows at most 1 outstanding transaction (FIFO depth = 4).
# "full" bins are excluded via ign_bins and documented in docs/coverage_waivers.md.
# -----------------------------------------------------------------------------
ign_bins_cdc = []
for r in ["slow<sys", "approx_equal", "slow>sys"]:
    for op in ["RD", "WR"]:
        ign_bins_cdc.append((r, "full", op))

@CoverPoint("cg_cdc.ratio", xf=lambda r, occ, op: r, bins=["slow<sys", "approx_equal", "slow>sys"])
@CoverPoint("cg_cdc.occupancy", xf=lambda r, occ, op: occ, bins=["empty", "partial"])
@CoverPoint("cg_cdc.op", xf=lambda r, occ, op: op, bins=["RD", "WR"])
@CoverCross("cg_cdc.cross", items=["cg_cdc.ratio", "cg_cdc.occupancy", "cg_cdc.op"], ign_bins=ign_bins_cdc)
def sample_cdc(r, occ, op):
    pass

# -----------------------------------------------------------------------------
# 8. cg_uart: UART peripheral features
# BAUDDIV bucket (0, 1, 2+) x FIFO state (empty, partial, full) = 9 bins
# Error type (none, frame_err, overflow) = 3 bins
# -----------------------------------------------------------------------------
@CoverPoint("cg_uart.baud", xf=lambda b, f, e: b, bins=["0", "1", "2+"])
@CoverPoint("cg_uart.fifo", xf=lambda b, f, e: f, bins=["empty", "partial", "full"])
@CoverCross("cg_uart.cross", items=["cg_uart.baud", "cg_uart.fifo"])
@CoverPoint("cg_uart.err", xf=lambda b, f, e: e, bins=["none", "frame_err", "overflow"])
def sample_uart(b, f, e):
    pass

# -----------------------------------------------------------------------------
# 9. cg_reset: System reset states
# Phase (idle, aw_in_flight, w_in_flight, b_pending, r_pending) = 5 bins
# -----------------------------------------------------------------------------
@CoverPoint("cg_reset.phase", xf=lambda p: p, bins=["idle", "aw_in_flight", "w_in_flight", "b_pending", "r_pending"])
def sample_reset(p):
    pass


class CoverageCollector:
    """Singleton Coverage Collector managing sampling, source tagging, and reporting."""
    _instance = None

    def __init__(self):
        self.source = "top_level"
        self.allowed_groups = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def configure(self, source="top_level", allowed_groups=None):
        """Tag exported coverage with its origin ('top_level' or 'block') and filter groups."""
        self.source = source
        self.allowed_groups = list(allowed_groups) if allowed_groups is not None else None

    @staticmethod
    def decode_target(addr):
        if 0x40000000 <= addr <= 0x40003FFF:
            return "APB"
        elif 0x50000000 <= addr <= 0x50000FFF:
            return "RAM"
        elif 0x60000000 <= addr <= 0x60000FFF:
            return "CSR"
        elif 0x70000000 <= addr <= 0x70000FFF:
            return "CDC"
        else:
            return "UNMAPPED"

    @staticmethod
    def decode_resp(resp):
        if resp == 0:
            return "OKAY"
        elif resp == 2:
            return "SLVERR"
        elif resp == 3:
            return "DECERR"
        return "UNKNOWN"

    @staticmethod
    def delay_to_bucket(delay):
        if delay == 0:
            return "0"
        elif delay == 1:
            return "1"
        elif 2 <= delay <= 4:
            return "2-4"
        else:
            return "5-16"

    @staticmethod
    def strb_to_class(strb):
        s = strb & 0xF
        if s in [0x1, 0x2, 0x4, 0x8]:
            return "byte"
        elif s in [0x3, 0xC]:
            return "halfword"
        elif s == 0xF:
            return "word"
        else:
            return "sparse"

    def sample_transaction(self, item):
        target = self.decode_target(item.addr)
        op = "WR" if item.is_write else "RD"
        resp = self.decode_resp(item.resp)
        sample_txn(item.master_id, target, op, resp)

        if item.is_write and target in ["RAM", "CSR", "CDC", "APB"]:
            sample_wstrb(target, item.strb & 0xF)
            sample_order(target, item.order if hasattr(item, "order") and item.order else "simultaneous")

    def export(self, filepath, source=None, allowed_groups=None):
        import yaml
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        coverage_db.export_to_yaml(filepath)
        src = source if source is not None else self.source
        allowed = list(allowed_groups) if allowed_groups is not None else self.allowed_groups
        with open(filepath, "r") as fp:
            data = yaml.safe_load(fp) or {}
        if allowed is not None:
            data = {
                k: v for k, v in data.items()
                if any(k == p or k.startswith(p + ".") for p in allowed)
            }
        data["_meta"] = {
            "source": src,
            "allowed_groups": allowed if allowed is not None else ["all"],
        }
        with open(filepath, "w") as fp:
            yaml.safe_dump(data, fp, sort_keys=False)
