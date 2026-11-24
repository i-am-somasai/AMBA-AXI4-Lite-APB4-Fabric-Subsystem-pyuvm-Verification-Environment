# tb/pyuvm/sequences/fabric_stress_seq.py
# Constrained-random stress sequence for XB-13 (>= 10,000 transactions across 2 masters)
from pyuvm import uvm_sequence
import cocotb
from sequences.axil_base_seq import AxilBaseSeq
from sequences.axil_seq_item import AxilSeqItem

class AxilRandomSeq(AxilBaseSeq):
    """Generates a stream of constrained-random AXI-Lite transactions."""
    def __init__(self, name="AxilRandomSeq", master_id=0, num_trans=5000):
        super().__init__(name)
        self.master_id = master_id
        self.num_trans = num_trans

    async def body(self):
        for i in range(self.num_trans):
            item = AxilSeqItem(f"item_m{self.master_id}_{i}")
            item.randomize(master_id=self.master_id)
            await self.start_item(item)
            await self.finish_item(item)


class FabricStressSeq(uvm_sequence):
    """Top-level stress sequence orchestrating concurrent streams from Master 0 and Master 1."""
    def __init__(self, name="FabricStressSeq", num_trans_per_master=5000):
        super().__init__(name)
        self.num_trans_per_master = num_trans_per_master
        self.m0_sequencer = None
        self.m1_sequencer = None

    async def body(self):
        seq0 = AxilRandomSeq("seq0", master_id=0, num_trans=self.num_trans_per_master)
        seq1 = AxilRandomSeq("seq1", master_id=1, num_trans=self.num_trans_per_master)

        task0 = cocotb.start_soon(seq0.start(self.m0_sequencer))
        task1 = cocotb.start_soon(seq1.start(self.m1_sequencer))

        await task0
        await task1
