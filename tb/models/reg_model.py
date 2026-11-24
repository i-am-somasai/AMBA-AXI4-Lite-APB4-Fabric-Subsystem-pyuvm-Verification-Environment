# tb/models/reg_model.py
# Independent reference model for CSR block, CDC Slow Regs, and Peripherals
from models.addr_map import AddrMap

class CsrModel:
    CONST_ID      = 0xA3BA_0001
    CONST_VERSION = 0x0001_0000

    def __init__(self):
        self.reset()

    def reset(self):
        self.scratch = 0
        self.scratch2 = 0
        self.irq_raw = 0
        self.irq_mask = 0
        self.w1c_test = 0

    def write(self, addr, data, strb=0xF):
        offset = addr & 0xFF
        if offset % 4 != 0 or offset > 0x20:
            return AddrMap.RESP_SLVERR

        if offset == 0x00:
            # ID is RO: write ignored with OKAY
            return AddrMap.RESP_OKAY
        elif offset == 0x04:
            # VERSION is RO: write ignored with OKAY
            return AddrMap.RESP_OKAY
        elif offset == 0x08:
            # SCRATCH: full 32-bit RW
            self.scratch = data & 0xFFFF_FFFF
            return AddrMap.RESP_OKAY
        elif offset == 0x0C:
            # SCRATCH2: byte-writable via strb
            new_val = self.scratch2
            for i in range(4):
                if (strb >> i) & 1:
                    mask = 0xFF << (i * 8)
                    new_val = (new_val & ~mask) | (data & mask)
            self.scratch2 = new_val & 0xFFFF_FFFF
            return AddrMap.RESP_OKAY
        elif offset == 0x10:
            # IRQ_RAW is RO
            return AddrMap.RESP_OKAY
        elif offset == 0x14:
            # IRQ_MASK
            self.irq_mask = data & 0x7
            return AddrMap.RESP_OKAY
        elif offset == 0x18:
            # IRQ_STATUS is RO
            return AddrMap.RESP_OKAY
        elif offset == 0x1C:
            # W1C_TEST: writing 1 clears bit
            self.w1c_test &= ~(data & 0xFFFF_FFFF)
            return AddrMap.RESP_OKAY
        elif offset == 0x20:
            # W1C_SET: writing 1 sets bit in W1C_TEST
            self.w1c_test |= (data & 0xFFFF_FFFF)
            return AddrMap.RESP_OKAY
        else:
            return AddrMap.RESP_SLVERR

    def read(self, addr):
        offset = addr & 0xFF
        if offset % 4 != 0 or offset > 0x20:
            return 0, AddrMap.RESP_SLVERR

        if offset == 0x00:
            return self.CONST_ID, AddrMap.RESP_OKAY
        elif offset == 0x04:
            return self.CONST_VERSION, AddrMap.RESP_OKAY
        elif offset == 0x08:
            return self.scratch, AddrMap.RESP_OKAY
        elif offset == 0x0C:
            return self.scratch2, AddrMap.RESP_OKAY
        elif offset == 0x10:
            # IRQ_RAW reflects external dynamic peripheral interrupts
            return None, AddrMap.RESP_OKAY
        elif offset == 0x14:
            return self.irq_mask & 0x7, AddrMap.RESP_OKAY
        elif offset == 0x18:
            # IRQ_STATUS reflects masked dynamic peripheral interrupts
            return None, AddrMap.RESP_OKAY
        elif offset == 0x1C:
            return self.w1c_test, AddrMap.RESP_OKAY
        elif offset == 0x20:
            return 0, AddrMap.RESP_OKAY
        else:
            return 0, AddrMap.RESP_SLVERR


class SlowRegsModel:
    CONST_SLOW_ID = 0x510E_0001

    def __init__(self):
        self.reset()

    def reset(self):
        self.scratch = 0
        self.ctrl = 1
        self.counter_estimate = 0

    def write(self, addr, data, strb=0xF):
        offset = addr & 0xFF
        if offset > 0x0C or offset % 4 != 0:
            return AddrMap.RESP_SLVERR

        if offset == 0x00:
            return AddrMap.RESP_OKAY # SLOW_ID RO
        elif offset == 0x04:
            new_val = self.scratch
            for i in range(4):
                if (strb >> i) & 1:
                    mask = 0xFF << (i * 8)
                    new_val = (new_val & ~mask) | (data & mask)
            self.scratch = new_val & 0xFFFF_FFFF
            return AddrMap.RESP_OKAY
        elif offset == 0x08:
            return AddrMap.RESP_OKAY # SLOW_COUNTER RO
        elif offset == 0x0C:
            self.ctrl = data & 0x1
            return AddrMap.RESP_OKAY
        else:
            return AddrMap.RESP_SLVERR

    def read(self, addr):
        offset = addr & 0xFF
        if offset > 0x0C or offset % 4 != 0:
            return 0, AddrMap.RESP_SLVERR

        if offset == 0x00:
            return self.CONST_SLOW_ID, AddrMap.RESP_OKAY
        elif offset == 0x04:
            return self.scratch, AddrMap.RESP_OKAY
        elif offset == 0x08:
            # Free-running counter: response is OKAY, value is dynamic
            return None, AddrMap.RESP_OKAY
        elif offset == 0x0C:
            return self.ctrl, AddrMap.RESP_OKAY
        else:
            return 0, AddrMap.RESP_SLVERR
