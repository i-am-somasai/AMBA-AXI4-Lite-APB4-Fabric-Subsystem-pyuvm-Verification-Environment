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

    def reset(self):
        self.ram.reset()
        self.csr.reset()
        self.slow_regs.reset()
        self.uart.reset()
        self.timer.reset()
        self.gpio.reset()

    def predict_write(self, addr, data, strb=0xF, prot=0):
        """Predicts the write response for a transaction.
        Returns: expected_bresp (0: OKAY, 2: SLVERR, 3: DECERR)
        """
        slave_idx, target, is_mapped = AddrMap.decode(addr)

        if slave_idx == AddrMap.SLAVE_DECERR:
            return AddrMap.RESP_DECERR

        elif slave_idx == AddrMap.SLAVE_RAM:
            return self.ram.write(addr, data, strb)

        elif slave_idx == AddrMap.SLAVE_CSR:
            return self.csr.write(addr, data, strb)

        elif slave_idx == AddrMap.SLAVE_CDC:
            return self.slow_regs.write(addr, data, strb)

        elif slave_idx == AddrMap.SLAVE_APB:
            offset = addr & 0x0FFF_FFFF
            if target == "UART":
                return self.uart.write(offset, data)
            elif target == "TIMER":
                return self.timer.write(offset, data)
            elif target == "GPIO":
                return self.gpio.write(offset, data)
            else:
                return AddrMap.RESP_SLVERR

        return AddrMap.RESP_DECERR

    def predict_read(self, addr, prot=0):
        """Predicts the read data and response for a transaction.
        Returns: (expected_rdata, expected_rresp, check_data)
        where check_data=True indicates exact data comparison.
        """
        slave_idx, target, is_mapped = AddrMap.decode(addr)

        if slave_idx == AddrMap.SLAVE_DECERR:
            # Default slave returns 0 with DECERR
            return 0, AddrMap.RESP_DECERR, False

        elif slave_idx == AddrMap.SLAVE_RAM:
            rdata, resp = self.ram.read(addr)
            return rdata, resp, (resp == AddrMap.RESP_OKAY)

        elif slave_idx == AddrMap.SLAVE_CSR:
            rdata, resp = self.csr.read(addr)
            # IRQ_RAW and IRQ_STATUS are dynamic if external interrupts occur,
            # but in pure crossbar stress without active IRQs they are exact
            return rdata, resp, (rdata is not None)

        elif slave_idx == AddrMap.SLAVE_CDC:
            rdata, resp = self.slow_regs.read(addr)
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

            return rdata, resp, (rdata is not None)

        return 0, AddrMap.RESP_DECERR, False
