# tb/pyuvm/sequences/axil_seq_item.py
# AXI4-Lite UVM sequence item
from pyuvm import uvm_sequence_item
import random

class AxilSeqItem(uvm_sequence_item):
    """AXI4-Lite transaction sequence item supporting read/write transfers."""
    def __init__(self, name="AxilSeqItem"):
        super().__init__(name)
        self.is_write = False
        self.addr = 0
        self.data = 0
        self.strb = 0xF
        self.prot = 0
        self.order = "simultaneous" # "simultaneous", "aw_first", "w_first"
        self.bready_delay = 0
        self.rready_delay = 0
        self.master_id = 0

        # Response fields (filled by driver)
        self.rdata = 0
        self.resp = 0

    def randomize(self, master_id=0, addr_range=None, is_write_p=0.5):
        """Constrained randomizer for AXI-Lite transfers."""
        self.master_id = master_id
        self.is_write = (random.random() < is_write_p)

        if addr_range:
            self.addr = random.choice(addr_range)
        else:
            # Weighted target selection:
            # 40% RAM, 20% CSR, 15% CDC, 15% APB, 10% Unmapped
            r = random.random()
            if r < 0.40:
                # RAM: 0x5000_0000 to 0x5000_03FC
                # Partition RAM write/read ranges per master to ensure zero race hazards
                # M0: words 0..127 (0x5000_0000 .. 0x5000_01FC)
                # M1: words 128..255 (0x5000_0200 .. 0x5000_03FC)
                base = 0x50000000 if master_id == 0 else 0x50000200
                self.addr = base + (random.randint(0, 127) << 2)

            elif r < 0.60:
                # CSR: 0x6000_0000 to 0x6000_0020
                if self.is_write:
                    # M0 writes SCRATCH (0x08) or W1C_SET (0x20)
                    # M1 writes SCRATCH2 (0x0C) or IRQ_MASK (0x14)
                    if master_id == 0:
                        self.addr = random.choice([0x60000008, 0x60000020, 0x6000001C])
                    else:
                        self.addr = random.choice([0x6000000C, 0x60000014])
                else:
                    if master_id == 0:
                        self.addr = random.choice([0x60000000, 0x60000004, 0x60000008, 0x60000010, 0x6000001C])
                    else:
                        self.addr = random.choice([0x60000000, 0x60000004, 0x6000000C, 0x60000014, 0x60000018])

            elif r < 0.75:
                # CDC: 0x7000_0000 to 0x7000_000C
                if self.is_write:
                    # M0 writes SLOW_SCRATCH (0x04), M1 writes SLOW_CTRL (0x0C)
                    self.addr = 0x70000004 if master_id == 0 else 0x7000000C
                else:
                    # Both can read SLOW_ID (0x00) and SLOW_COUNTER (0x08)
                    if master_id == 0:
                        self.addr = random.choice([0x70000000, 0x70000004, 0x70000008])
                    else:
                        self.addr = random.choice([0x70000000, 0x70000008, 0x7000000C])

            elif r < 0.90:
                # APB:
                # M0 exercises UART (0x4000_0000) and Timer (0x4000_1000)
                # M1 exercises GPIO (0x4000_2000) and APB unmapped (0x4000_3000)
                if master_id == 0:
                    periph = random.choice([0x0000, 0x1000])
                    offset = (random.randint(0, 3) << 2) if periph == 0x1000 else (random.randint(0, 4) << 2)
                    self.addr = 0x40000000 + periph + offset
                else:
                    periph = random.choice([0x2000, 0x3000])
                    offset = 0 if periph == 0x3000 else (random.randint(0, 4) << 2)
                    self.addr = 0x40000000 + periph + offset

            else:
                # Unmapped (triggers DECERR)
                if master_id == 0:
                    self.addr = random.choice([0x10000000, 0x20000000, 0x30000000])
                else:
                    self.addr = random.choice([0x80000000, 0x90000000, 0xA0000000])

        self.data = random.randint(0, 0xFFFF_FFFF)
        self.strb = random.choice([0xF, 0x1, 0x2, 0x4, 0x8, 0x3, 0xC, 0x5, 0xA])
        self.prot = random.randint(0, 7)
        self.order = random.choice(["simultaneous", "aw_first", "w_first"])
        self.bready_delay = random.choice([0, 0, 0, 1, 2, 3, 6])
        self.rready_delay = random.choice([0, 0, 0, 1, 2, 3, 6])

    def __str__(self):
        op = "WR" if self.is_write else "RD"
        return f"{self.get_name()}[M{self.master_id} {op} addr=0x{self.addr:08x} data=0x{self.data:08x} strb=0x{self.strb:x} resp={self.resp} rdata=0x{self.rdata:08x}]"
