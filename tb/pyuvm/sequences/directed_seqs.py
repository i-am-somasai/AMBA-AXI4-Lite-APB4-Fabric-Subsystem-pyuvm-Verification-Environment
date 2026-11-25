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
    """XB-14: AWPROT and ARPROT pass-through to APB PPROT across all 8 encodings 0..7."""
    async def body(self):
        dut = cocotb.top
        captured_pprot = []

        async def watch_apb_pprot():
            while True:
                await RisingEdge(dut.clk_sys)
                if int(dut.apb_psel.value) == 1 and int(dut.apb_penable.value) == 0:
                    captured_pprot.append((int(dut.apb_pwrite.value), int(dut.apb_pprot.value)))

        watch_task = cocotb.start_soon(watch_apb_pprot())
        try:
            for prot_val in range(8):
                # Write to APB Timer LOAD with specific AWPROT
                resp = await self.write(0x40001004, 0x1000 + prot_val, prot=prot_val)
                assert resp == 0, f"Timer LOAD write failed with prot={prot_val}"
                assert captured_pprot and captured_pprot[-1] == (1, prot_val), (
                    f"XB-14 AWPROT->PPROT mismatch: expected (1, {prot_val}), "
                    f"observed {captured_pprot[-1] if captured_pprot else None}"
                )

                # Read from APB Timer LOAD with specific ARPROT
                rdata, resp = await self.read(0x40001004, prot=prot_val)
                assert resp == 0 and rdata == 0x1000 + prot_val, (
                    f"Timer LOAD read mismatch with prot={prot_val}: resp={resp}, rdata={rdata:#x}"
                )
                assert captured_pprot and captured_pprot[-1] == (0, prot_val), (
                    f"XB-14 ARPROT->PPROT mismatch: expected (0, {prot_val}), "
                    f"observed {captured_pprot[-1] if captured_pprot else None}"
                )
        finally:
            watch_task.cancel()


class UnalignedAddressSeq(AxilBaseSeq):
    """XB-15: Unaligned address LSBs [1:0] ignored across RAM, CSR, APB, and CDC."""
    async def body(self):
        # 1. RAM (0x5000_0010..13)
        await self.write(0x50000010, 0x11111111)
        rdata, resp = await self.read(0x50000010)
        assert resp == 0 and rdata == 0x11111111
        await self.write(0x50000011, 0x22222222)
        for off in (0, 1, 2, 3):
            rdata, resp = await self.read(0x50000010 + off)
            assert resp == 0 and rdata == 0x22222222, (
                f"RAM unaligned +{off} mismatch: resp={resp}, data={hex(rdata)}"
            )

        # 2. CSR (0x6000_0000 ID +1/+2/+3 and 0x6000_000C SCRATCH2 +1/+2/+3) - AXIL-R6
        for off in (1, 2, 3):
            rdata, resp = await self.read(0x60000000 + off)
            assert resp == 0 and rdata == 0xA3BA0001, (
                f"CSR ID unaligned +{off} failed Rule 6: resp={resp}, rdata={hex(rdata)}"
            )
        resp = await self.write(0x6000000D, 0xDEADBEEF)
        assert resp == 0, f"CSR SCRATCH2 unaligned +1 write failed: resp={resp}"
        for off in (0, 2, 3):
            rdata, resp = await self.read(0x6000000C + off)
            assert resp == 0 and rdata == 0xDEADBEEF, (
                f"CSR SCRATCH2 unaligned +{off} read failed: resp={resp}, rdata={hex(rdata)}"
            )

        # 3. APB Timer LOAD (0x4000_1004..07)
        resp = await self.write(0x40001005, 0x00001234)
        assert resp == 0, f"APB unaligned +1 write failed: resp={resp}"
        for off in (0, 2, 3):
            rdata, resp = await self.read(0x40001004 + off)
            assert resp == 0 and rdata == 0x00001234, (
                f"APB unaligned +{off} read failed: resp={resp}, rdata={hex(rdata)}"
            )

        # 4. CDC slow_regs (0x7000_0000 SLOW_ID +1..3 and 0x7000_0004 SLOW_SCRATCH +1..3)
        for off in (1, 2, 3):
            rdata, resp = await self.read(0x70000000 + off)
            assert resp == 0 and rdata == 0x510E0001, (
                f"CDC SLOW_ID unaligned +{off} failed: resp={resp}, rdata={hex(rdata)}"
            )
        resp = await self.write(0x70000006, 0xCAFEBABE)
        assert resp == 0, f"CDC unaligned +2 write failed: resp={resp}"
        for off in (0, 1, 3):
            rdata, resp = await self.read(0x70000004 + off)
            assert resp == 0 and rdata == 0xCAFEBABE, (
                f"CDC unaligned +{off} read failed: resp={resp}, rdata={hex(rdata)}"
            )


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
    """XB-03 / BR-04: Test all 16 WSTRB byte permutations on RAM and CSR SCRATCH2."""
    async def body(self):
        for label, addr in [("RAM", 0x50000030), ("CSR_SCRATCH2", 0x6000000C)]:
            for strb in range(16):
                # Initialize word to non-zero baseline so strb=0 and unstrobed bytes are verified
                resp = await self.write(addr, 0xA5A55A5A, strb=0xF)
                assert resp == 0, f"{label} init write failed"

                wval = 0x13572468 ^ (strb * 0x01010101)
                resp = await self.write(addr, wval, strb=strb)
                assert resp == 0, f"{label} strb={strb:#x} write failed"

                expected = 0
                for b in range(4):
                    mask = 0xFF << (8 * b)
                    if (strb >> b) & 1:
                        expected |= (wval & mask)
                    else:
                        expected |= (0xA5A55A5A & mask)

                rdata, rresp = await self.read(addr)
                assert rresp == 0, f"{label} strb={strb:#x} read failed"
                assert rdata == expected, (
                    f"{label} WSTRB {strb:#x} mismatch: expected {expected:#x}, got {rdata:#x}"
                )


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
