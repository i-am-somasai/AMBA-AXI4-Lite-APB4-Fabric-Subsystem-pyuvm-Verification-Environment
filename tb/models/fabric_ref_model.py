# tb/models/fabric_ref_model.py
# Unified reference model integrating Address Decode, RAM, CSR, CDC, and APB Peripherals
from models.addr_map import AddrMap
from models.ram_model import RamModel
from models.reg_model import CsrModel, SlowRegsModel
from models.peripheral_model import ApbUartModel, ApbTimerModel, ApbGpioModel

class FabricRefModel:
    """System-level reference model for AMBA fabric subsystem."""
    def __init__(self, ram_depth=256):
        self.ram = RamModel(depth_words=ram_depth)
        self.csr = CsrModel()
        self.slow_regs = SlowRegsModel()
        self.uart = ApbUartModel()
        self.timer = ApbTimerModel()
        self.gpio = ApbGpioModel()
        self.unknown_words = set()

    def reset(self, preserve_ram=False):
        if not preserve_ram:
            self.ram.reset()
        self.csr.reset()
        self.slow_regs.reset()
        self.uart.reset()
        self.timer.reset()
        self.gpio.reset()
        self.unknown_words.clear()

    def mark_write_unknown(self, addr):
        """Mark word address as UNKNOWN after reset interrupted an in-flight write."""
        self.unknown_words.add(addr & ~0x3)

    def predict_write(self, addr, data, strb=0xF, prot=0):
        """Predicts the write response for a transaction.
        Returns: expected_bresp (0: OKAY, 2: SLVERR, 3: DECERR)
        """
        slave_idx, target, is_mapped = AddrMap.decode(addr)
        word_addr = addr & ~0x3

        if slave_idx == AddrMap.SLAVE_DECERR:
            return AddrMap.RESP_DECERR

        elif slave_idx == AddrMap.SLAVE_RAM:
            resp = self.ram.write(addr, data, strb)
            if resp == AddrMap.RESP_OKAY and (strb & 0xF) == 0xF:
                self.unknown_words.discard(word_addr)
            return resp

        elif slave_idx == AddrMap.SLAVE_CSR:
            resp = self.csr.write(addr, data, strb)
            if resp == AddrMap.RESP_OKAY and (strb & 0xF) == 0xF:
                self.unknown_words.discard(word_addr)
            return resp

        elif slave_idx == AddrMap.SLAVE_CDC:
            resp = self.slow_regs.write(addr, data, strb)
            if resp == AddrMap.RESP_OKAY and (strb & 0xF) == 0xF:
                self.unknown_words.discard(word_addr)
            return resp

        elif slave_idx == AddrMap.SLAVE_APB:
            offset = addr & 0x0FFF_FFFF
            if target == "UART":
                resp = self.uart.write(offset, data)
            elif target == "TIMER":
                resp = self.timer.write(offset, data)
            elif target == "GPIO":
                resp = self.gpio.write(offset, data)
            else:
                return AddrMap.RESP_SLVERR
            if resp == AddrMap.RESP_OKAY and (strb & 0xF) == 0xF:
                self.unknown_words.discard(word_addr)
            return resp

        return AddrMap.RESP_DECERR

    def predict_read(self, addr, prot=0):
        """Predicts the read data and response for a transaction.
        Returns: (expected_rdata, expected_rresp, check_data)
        where check_data=True indicates exact data comparison.
        """
        slave_idx, target, is_mapped = AddrMap.decode(addr)
        is_unknown = (addr & ~0x3) in self.unknown_words

        if slave_idx == AddrMap.SLAVE_DECERR:
            # Default slave returns 0 with DECERR
            return 0, AddrMap.RESP_DECERR, False

        elif slave_idx == AddrMap.SLAVE_RAM:
            rdata, resp = self.ram.read(addr)
            if is_unknown:
                return None, resp, False
            return rdata, resp, (resp == AddrMap.RESP_OKAY)

        elif slave_idx == AddrMap.SLAVE_CSR:
            rdata, resp = self.csr.read(addr)
            if is_unknown:
                return None, resp, False
            # IRQ_RAW and IRQ_STATUS are dynamic if external interrupts occur,
            # but in pure crossbar stress without active IRQs they are exact
            return rdata, resp, (rdata is not None)

        elif slave_idx == AddrMap.SLAVE_CDC:
            rdata, resp = self.slow_regs.read(addr)
            if is_unknown:
                return None, resp, False
            return rdata, resp, (rdata is not None)

        elif slave_idx == AddrMap.SLAVE_APB:
            offset = addr & 0x0FFF_FFFF
            if target == "UART":
                rdata, resp = self.uart.read(offset)
            elif target == "TIMER":
                rdata, resp = self.timer.read(offset)
            elif target == "GPIO":
                rdata, resp = self.gpio.read(offset)
            else:
                return 0, AddrMap.RESP_SLVERR, False
            if is_unknown:
                return None, resp, False
            return rdata, resp, (rdata is not None)

        return 0, AddrMap.RESP_DECERR, False
