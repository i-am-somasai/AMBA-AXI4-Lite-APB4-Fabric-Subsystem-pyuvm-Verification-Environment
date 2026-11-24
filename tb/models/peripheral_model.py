# tb/models/peripheral_model.py
# Independent reference models for APB UART, Timer, and GPIO
from models.addr_map import AddrMap

class ApbUartModel:
    def __init__(self):
        self.reset()

    def reset(self):
        self.ctrl = 0
        self.bauddiv = 0
        self.tx_fifo = []
        self.rx_fifo = []
        self.frame_err = 0
        self.rx_ovf = 0
        self.tx_ovf = 0

    def write(self, offset, data):
        reg = offset & 0xFF
        if reg == 0x00:
            # TXDATA: pushes to TX FIFO
            byte_val = data & 0xFF
            if len(self.tx_fifo) < 8:
                self.tx_fifo.append(byte_val)
            else:
                self.tx_ovf = 1
            return AddrMap.RESP_OKAY
        elif reg == 0x08:
            # STATUS: W1C on bits 4, 5, 6
            if (data >> 4) & 1: self.frame_err = 0
            if (data >> 5) & 1: self.rx_ovf = 0
            if (data >> 6) & 1: self.tx_ovf = 0
            return AddrMap.RESP_OKAY
        elif reg == 0x0C:
            self.ctrl = data & 0xF
            return AddrMap.RESP_OKAY
        elif reg == 0x10:
            self.bauddiv = data & 0xFFFF
            return AddrMap.RESP_OKAY
        else:
            return AddrMap.RESP_OKAY # Undefined peripheral register writes ignored

    def read(self, offset):
        reg = offset & 0xFF
        if reg == 0x00:
            return 0, AddrMap.RESP_OKAY
        elif reg == 0x04:
            # RXDATA: returns dynamic or popped byte
            return None, AddrMap.RESP_OKAY
        elif reg == 0x08:
            # STATUS is dynamic based on hardware FIFO states
            return None, AddrMap.RESP_OKAY
        elif reg == 0x0C:
            return self.ctrl, AddrMap.RESP_OKAY
        elif reg == 0x10:
            return self.bauddiv, AddrMap.RESP_OKAY
        else:
            return 0, AddrMap.RESP_OKAY # Undefined peripheral register reads return 0


class ApbTimerModel:
    def __init__(self):
        self.reset()

    def reset(self):
        self.ctrl = 0
        self.load = 0
        self.timeout = 0

    def write(self, offset, data):
        reg = offset & 0xFF
        if reg == 0x00:
            self.ctrl = data & 0x7
            return AddrMap.RESP_OKAY
        elif reg == 0x04:
            self.load = data & 0xFFFF_FFFF
            return AddrMap.RESP_OKAY
        elif reg == 0x08:
            return AddrMap.RESP_OKAY # VALUE is RO
        elif reg == 0x0C:
            if data & 1: self.timeout = 0
            return AddrMap.RESP_OKAY
        else:
            return AddrMap.RESP_OKAY

    def read(self, offset):
        reg = offset & 0xFF
        if reg == 0x00:
            # CTRL is dynamic because bit 0 (EN) is automatically cleared on timeout
            return None, AddrMap.RESP_OKAY
        elif reg == 0x04:
            return self.load, AddrMap.RESP_OKAY
        elif reg == 0x08:
            return None, AddrMap.RESP_OKAY # Counter is dynamic
        elif reg == 0x0C:
            return None, AddrMap.RESP_OKAY # Status is dynamic
        else:
            return 0, AddrMap.RESP_OKAY


class ApbGpioModel:
    def __init__(self):
        self.reset()

    def reset(self):
        self.dir = 0
        self.out = 0
        self.irq_en = 0
        self.irq_status = 0

    def write(self, offset, data):
        reg = offset & 0xFF
        if reg == 0x00:
            self.dir = data & 0xFFFF
            return AddrMap.RESP_OKAY
        elif reg == 0x04:
            self.out = data & 0xFFFF
            return AddrMap.RESP_OKAY
        elif reg == 0x08:
            return AddrMap.RESP_OKAY # IN is RO
        elif reg == 0x0C:
            self.irq_en = data & 0xFFFF
            return AddrMap.RESP_OKAY
        elif reg == 0x10:
            self.irq_status &= ~(data & 0xFFFF)
            return AddrMap.RESP_OKAY
        else:
            return AddrMap.RESP_OKAY

    def read(self, offset):
        reg = offset & 0xFF
        if reg == 0x00:
            return self.dir, AddrMap.RESP_OKAY
        elif reg == 0x04:
            return self.out, AddrMap.RESP_OKAY
        elif reg == 0x08:
            return None, AddrMap.RESP_OKAY # External input is dynamic
        elif reg == 0x0C:
            return self.irq_en, AddrMap.RESP_OKAY
        elif reg == 0x10:
            return None, AddrMap.RESP_OKAY # Dynamic edge status
        else:
            return 0, AddrMap.RESP_OKAY
