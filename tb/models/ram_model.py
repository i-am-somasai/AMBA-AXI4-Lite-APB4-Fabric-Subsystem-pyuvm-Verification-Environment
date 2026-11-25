# tb/models/ram_model.py
# Independent reference model for 1 KB Scratchpad RAM based on docs/spec.md Section 7.2
from models.addr_map import AddrMap

class RamModel:
    """Byte-addressable 1 KB Scratchpad RAM model with byte strobe support."""
    def __init__(self, depth_words=256):
        self.depth_words = depth_words
        self.size_bytes = depth_words * 4
        self.mem = bytearray(self.size_bytes)

    def reset(self):
        self.mem = bytearray(self.size_bytes)

    def write(self, addr, data, strb=0xF):
        offset = addr & 0x0FFF_FFFF
        word_idx = offset >> 2
        if word_idx >= self.depth_words or offset < 0:
            return AddrMap.RESP_SLVERR

        # Word-aligned byte offset
        word_addr = word_idx << 2
        for i in range(4):
            if (strb >> i) & 1:
                byte_val = (data >> (i * 8)) & 0xFF
                self.mem[word_addr + i] = byte_val

        return AddrMap.RESP_OKAY

    def read(self, addr):
        offset = addr & 0x0FFF_FFFF
        word_idx = offset >> 2
        if word_idx >= self.depth_words or offset < 0:
            return 0, AddrMap.RESP_SLVERR

        word_addr = word_idx << 2
        rdata = 0
        for i in range(4):
            rdata |= (self.mem[word_addr + i] << (i * 8))

        return rdata, AddrMap.RESP_OKAY
