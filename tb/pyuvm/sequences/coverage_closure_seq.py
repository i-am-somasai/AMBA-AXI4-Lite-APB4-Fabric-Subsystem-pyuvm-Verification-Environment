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

        # 3b. Exercise explicit BREADY and RREADY backpressure delay buckets (0, 1, 2-4, 5-16)
        for dly in [0, 1, 3, 6]:
            w_addr = 0x50000100 + (0x100 if self.master_id == 1 else 0x0) + dly * 4
            resp = await self.write(w_addr, 0x5A5A0000 + dly, bready_delay=dly)
            assert resp == 0
            rval, rresp = await self.read(w_addr, rready_delay=dly)
            assert rresp == 0 and rval == (0x5A5A0000 + dly)

        # 4. Exercise UART registers (only Master 0 to avoid UART contention with M1)
        if self.master_id == 0:
            dut = cocotb.top
            # Configure BAUDDIV = 0, 1, 4 and fill TX FIFO before enabling TX_EN
            for b_div in [0, 1, 4]:
                await self.write(0x40000010, b_div)  # BAUDDIV
                await self.read(0x40000010)
                await self.write(0x4000000C, 0x00)   # CTRL: disable TX/RX while filling TX FIFO
                for b_val in range(8):
                    await self.write(0x40000000, 0x41 + b_val)  # Fill 8-entry TX FIFO
                await self.read(0x40000008)          # STATUS sees tx_fifo_full=1 at this BAUDDIV
                await self.write(0x4000000C, 0x07)   # CTRL: TX_EN | RX_EN | LOOPBACK

                # Poll STATUS until all 8 bytes finish TX & loopback RX transfer
                for _ in range(80):
                    for _ in range(120):
                        await RisingEdge(dut.clk_sys)
                    st, _ = await self.read(0x40000008)
                    # tx_empty (bit 1) == 1, rx_full (bit 2) == 1, tx_busy (bit 7) == 0
                    if ((st >> 1) & 1) == 1 and ((st >> 7) & 1) == 0:
                        break
                for _ in range(16 * (b_div + 2)):
                    await RisingEdge(dut.clk_sys)
                for _ in range(8):
                    await self.read(0x40000004)      # Pop RXDATA
                await self.read(0x40000008)          # STATUS

            # Trigger external UART RX bad stop bit (FRAME_ERR) on dut.uart_rx
            await self.write(0x40000010, 0)          # BAUDDIV = 0 (16 clk_sys ticks/bit)
            dut.uart_rx.value = 1
            await self.write(0x4000000C, 0x02)       # CTRL: RX_EN=1, LOOPBACK=0, TX_EN=0
            for _ in range(40):
                await RisingEdge(dut.clk_sys)
            # Start bit (0)
            dut.uart_rx.value = 0
            for _ in range(16):
                await RisingEdge(dut.clk_sys)
            # 8 data bits (0x55 = 0b01010101)
            for bit_idx in range(8):
                dut.uart_rx.value = (0x55 >> bit_idx) & 1
                for _ in range(16):
                    await RisingEdge(dut.clk_sys)
            # Bad stop bit (0 instead of 1) held across mid-stop sample tick 7..15
            dut.uart_rx.value = 0
            for _ in range(32):
                await RisingEdge(dut.clk_sys)
            dut.uart_rx.value = 1
            for _ in range(32):
                await RisingEdge(dut.clk_sys)

            # Read STATUS (must reflect FRAME_ERR bit 4) and clear via W1C
            st_val, st_resp = await self.read(0x40000008)
            assert st_resp == 0 and ((st_val >> 4) & 1) == 1, (
                f"Expected UART FRAME_ERR bit[4]=1 after bad stop bit, got STATUS=0x{st_val:08x}"
            )
            await self.write(0x40000008, 0x10)       # W1C clear FRAME_ERR
            st_clr, _ = await self.read(0x40000008)
            assert ((st_clr >> 4) & 1) == 0, f"FRAME_ERR failed W1C clear: 0x{st_clr:08x}"


