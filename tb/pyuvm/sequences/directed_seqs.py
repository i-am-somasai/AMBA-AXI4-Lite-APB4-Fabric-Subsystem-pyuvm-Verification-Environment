# tb/pyuvm/sequences/directed_seqs.py
# Directed test sequences for AXI4-Lite Crossbar & APB Bridge (spec Section 9)
import cocotb
from cocotb.triggers import RisingEdge
from sequences.axil_base_seq import AxilBaseSeq
from sequences.axil_seq_item import AxilSeqItem

class SlverrPropagationSeq(AxilBaseSeq):
    """XB-11: Verify SLVERR propagation from all slaves to master."""
    async def body(self):
        # 1. RAM out-of-range write & read (offset >= 0x400 = 1024 bytes)
        resp = await self.write(0x50000400, 0x11223344)
        assert resp == 2, f"Expected SLVERR (2) on out-of-range RAM write, got {resp}"
        rdata, resp = await self.read(0x50000400)
        assert resp == 2, f"Expected SLVERR (2) on out-of-range RAM read, got {resp}"

        # 2. CSR undefined register write & read (offset > 0x20)
        resp = await self.write(0x60000030, 0xAABBCCDD)
        assert resp == 2, f"Expected SLVERR (2) on undefined CSR write, got {resp}"
        rdata, resp = await self.read(0x60000030)
        assert resp == 2, f"Expected SLVERR (2) on undefined CSR read, got {resp}"

        # 3. APB unmapped peripheral (peripheral index 3: 0x4000_3000)
        resp = await self.write(0x40003000, 0x12345678)
        assert resp == 2, f"Expected SLVERR (2) on unmapped APB write, got {resp}"
        rdata, resp = await self.read(0x40003000)
        assert resp == 2, f"Expected SLVERR (2) on unmapped APB read, got {resp}"

        # 4. CDC undefined register write & read (offset > 0x0C)
        resp = await self.write(0x70000020, 0x99887766)
        assert resp == 2, f"Expected SLVERR (2) on undefined CDC write, got {resp}"
        rdata, resp = await self.read(0x70000020)
        assert resp == 2, f"Expected SLVERR (2) on undefined CDC read, got {resp}"


class ProtPassThroughSeq(AxilBaseSeq):
    """XB-14: AWPROT and ARPROT pass-through verification."""
    async def body(self):
        for prot_val in [0, 1, 2, 4, 7]:
            # Write to APB Timer LOAD with specific prot
            resp = await self.write(0x40001004, 0x1000 + prot_val, prot=prot_val)
            assert resp == 0, f"Timer LOAD write failed with prot={prot_val}"
            rdata, resp = await self.read(0x40001004, prot=prot_val)
            assert resp == 0 and rdata == 0x1000 + prot_val, f"Timer LOAD read mismatch with prot={prot_val}"


class UnalignedAddressSeq(AxilBaseSeq):
    """XB-15: Unaligned address LSBs behave as word-aligned."""
    async def body(self):
        # Write to unaligned RAM addresses: 0x5000_0011, 0x5000_0012, 0x5000_0013
        # In hardware, address bits [1:0] are ignored and word 0x5000_0010 is updated
        await self.write(0x50000010, 0x11111111)
        rdata, resp = await self.read(0x50000010)
        assert resp == 0 and rdata == 0x11111111

        await self.write(0x50000011, 0x22222222)
        rdata, resp = await self.read(0x50000010)
        assert resp == 0 and rdata == 0x22222222, f"Unaligned address did not update word: {hex(rdata)}"

        rdata_unaligned, resp = await self.read(0x50000012)
        assert resp == 0 and rdata_unaligned == 0x22222222, f"Unaligned read did not return word: {hex(rdata_unaligned)}"


class WriteOrderSeq(AxilBaseSeq):
    """BR-06 & XB write channel ordering test (simultaneous, aw_first, w_first)."""
    async def body(self):
        # 1. Simultaneous
        resp = await self.write(0x50000020, 0xAAAAAAAA, order="simultaneous")
        assert resp == 0
        # 2. AW first, W later
        resp = await self.write(0x50000024, 0xBBBBBBBB, order="aw_first")
        assert resp == 0
        # 3. W first, AW later
        resp = await self.write(0x50000028, 0xCCCCCCCC, order="w_first")
        assert resp == 0

        # Read back all three
        r0, _ = await self.read(0x50000020)
        r1, _ = await self.read(0x50000024)
        r2, _ = await self.read(0x50000028)
        assert r0 == 0xAAAAAAAA and r1 == 0xBBBBBBBB and r2 == 0xCCCCCCCC


class StrobePatternSeq(AxilBaseSeq):
    """BR-04: Test all PSTRB / WSTRB byte permutations on RAM and CSR."""
    async def body(self):
        # Zero out RAM word
        await self.write(0x50000030, 0x00000000, strb=0xF)

        # Write byte 0
        await self.write(0x50000030, 0x000000AA, strb=0x1)
        rdata, _ = await self.read(0x50000030)
        assert rdata == 0x000000AA, f"Byte 0 write failed: {hex(rdata)}"

        # Write byte 2
        await self.write(0x50000030, 0x00CC0000, strb=0x4)
        rdata, _ = await self.read(0x50000030)
        assert rdata == 0x00CC00AA, f"Byte 2 write failed: {hex(rdata)}"

        # Write bytes 1 and 3
        await self.write(0x50000030, 0xDD00BB00, strb=0xA)
        rdata, _ = await self.read(0x50000030)
        assert rdata == 0xDDCCBBAA, f"Bytes 1,3 write failed: {hex(rdata)}"


class ResetRecoverySeq(AxilBaseSeq):
    """XB-12: Post-reset recovery sequence."""
    async def body(self):
        resp = await self.write(0x50000054, 0x87654321)
        assert resp == 0, "Post-reset write failed"
        rdata, resp = await self.read(0x50000054)
        assert resp == 0 and rdata == 0x87654321, f"Post-reset readback failed: {hex(rdata)}"


class ContentionM0Seq(AxilBaseSeq):
    """BR-05: Master 0 sequence for contention testing."""
    async def body(self):
        await self.write(0x50000060, 0xAAAA5555)
        # Read back word written by M1 after small delay
        for _ in range(5):
            await RisingEdge(cocotb.top.clk_sys)
        r1, resp1 = await self.read(0x50000064)
        assert resp1 == 0 and r1 == 0x5555AAAA, f"M0 read of M1 write failed: {hex(r1)}"


class ContentionM1Seq(AxilBaseSeq):
    """BR-05: Master 1 sequence for contention testing."""
    async def body(self):
        await self.write(0x50000064, 0x5555AAAA)
        # Read back word written by M0 after small delay
        for _ in range(5):
            await RisingEdge(cocotb.top.clk_sys)
        r0, resp0 = await self.read(0x50000060)
        assert resp0 == 0 and r0 == 0xAAAA5555, f"M1 read of M0 write failed: {hex(r0)}"
