# tb/pyuvm/sequences/axil_base_seq.py
# Base sequence with convenient write and read helper methods
from pyuvm import uvm_sequence
from sequences.axil_seq_item import AxilSeqItem

class AxilBaseSeq(uvm_sequence):
    def __init__(self, name="AxilBaseSeq"):
        super().__init__(name)

    async def write(self, addr, data, strb=0xF, prot=0, order="simultaneous"):
        item = AxilSeqItem(f"{self.get_name()}_wr")
        item.is_write = True
        item.addr = addr
        item.data = data
        item.strb = strb
        item.prot = prot
        item.order = order

        await self.start_item(item)
        await self.finish_item(item)
        return item.resp

    async def read(self, addr, prot=0):
        item = AxilSeqItem(f"{self.get_name()}_rd")
        item.is_write = False
        item.addr = addr
        item.prot = prot

        await self.start_item(item)
        await self.finish_item(item)
        return item.rdata, item.resp
