# tb/pyuvm/sequences/coverage_closure_seq.py
# Comprehensive stimulus sequence exercising Section 10 functional coverage scenarios
# NOTE: All coverage sampling is performed passively by bus monitors observing real signals.
import cocotb
from cocotb.triggers import RisingEdge, Timer
from sequences.axil_base_seq import AxilBaseSeq
from sequences.axil_seq_item import AxilSeqItem

class CoverageClosureSeq(AxilBaseSeq):
    """Stimulus sequence exercising transactions, strobes, orders, errors, and peripherals."""
    def __init__(self, name="CoverageClosureSeq", master_id=0):
        super().__init__(name)
        self.master_id = master_id

    async def body(self):
        targets = {
            "RAM": 0x50000000,
            "CSR": 0x60000008,     # SCRATCH
            "CDC": 0x70000004,     # SLOW_SCRATCH
            "APB": 0x40001004      # Timer LOAD
        }

        # 1. Exercise all 16 WSTRB patterns across all 4 mapped targets
        for t_name, base_addr in targets.items():
            for strb_val in range(16):
                await self.write(base_addr, 0x11223344, strb=strb_val, order="simultaneous")

        # 2. Exercise all 3 write orders across all 4 mapped targets
        for t_name, base_addr in targets.items():
            for ord_val in ["simultaneous", "aw_first", "w_first"]:
                await self.write(base_addr, 0xA5A5A5A5, strb=0xF, order=ord_val)

        # 3. Exercise all legal transaction combinations on DUT:
        # RAM: OKAY
        await self.write(0x50000010, 0x12345678)
        await self.read(0x50000010)
        # RAM: SLVERR (out of bounds >= 0x400)
        await self.write(0x50000400, 0x12345678)
        await self.read(0x50000400)

        # CSR: OKAY
        await self.write(0x60000008, 0x87654321)
        await self.read(0x60000008)
        # CSR: SLVERR (undefined offset 0x30)
        await self.write(0x60000030, 0x87654321)
        await self.read(0x60000030)

        # CDC: OKAY
        await self.write(0x70000004, 0xCAFEBABE)
        await self.read(0x70000004)
        # CDC: SLVERR (undefined offset 0x20)
        await self.write(0x70000020, 0xCAFEBABE)
        await self.read(0x70000020)

        # APB: OKAY (Timer LOAD)
        await self.write(0x40001004, 0x00000050)
        await self.read(0x40001004)
        # APB: SLVERR (unmapped peripheral 0x4000_3000)
        await self.write(0x40003000, 0xDEADBEEF)
        await self.read(0x40003000)

        # UNMAPPED: DECERR
        await self.write(0x10000000, 0x00000000)
        await self.read(0x10000000)

        # 4. Exercise UART registers (bauddiv, TX/RX)
        # Configure BAUDDIV = 0, 1, 4
        for b_div in [0, 1, 4]:
            await self.write(0x40000010, b_div) # BAUDDIV
            await self.read(0x40000010)
        # Enable TX/RX/Loopback
        await self.write(0x4000000C, 0x07) # CTRL: TX_EN, RX_EN, LOOPBACK
        # Push 8 bytes to exercise FIFO fill
        for b_val in range(8):
            await self.write(0x40000000, 0x41 + b_val) # TXDATA
        # Read STATUS
        await self.read(0x40000008) # STATUS
        # Pop RX bytes
        for _ in range(8):
            await self.read(0x40000004) # RXDATA
        await self.read(0x40000008) # STATUS empty

