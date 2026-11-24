# tb/pyuvm/env/fabric_scoreboard.py
# pyuvm Scoreboard comparing DUT transactions against independent reference model
from pyuvm import uvm_scoreboard, uvm_subscriber
from models.fabric_ref_model import FabricRefModel

class FabricMasterSubscriber(uvm_subscriber):
    """Subscriber that receives completed transactions from an AxilMasterAgent."""
    def __init__(self, name, parent, master_id):
        super().__init__(name, parent)
        self.master_id = master_id
        self.scoreboard = parent

    def write(self, item):
        self.scoreboard.check_transaction(item)


class FabricScoreboard(uvm_scoreboard):
    """Scoreboard checking all AXI-Lite read and write transfers against FabricRefModel."""
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.ref_model = FabricRefModel(ram_depth=256)
        self.m0_sub = None
        self.m1_sub = None

        # Statistics
        self.total_transactions = 0
        self.writes_verified = 0
        self.reads_verified = 0
        self.mismatches = 0

    def build_phase(self):
        super().build_phase()
        self.m0_sub = FabricMasterSubscriber("m0_sub", self, master_id=0)
        self.m1_sub = FabricMasterSubscriber("m1_sub", self, master_id=1)

    def check_transaction(self, item):
        """Validates a single completed transaction against the reference model."""
        self.total_transactions += 1

        if item.is_write:
            exp_resp = self.ref_model.predict_write(
                addr=item.addr,
                data=item.data,
                strb=item.strb,
                prot=item.prot
            )
            if item.resp != exp_resp:
                self.logger.error(
                    f"[MISMATCH M{item.master_id} WRITE] Addr=0x{item.addr:08x} Data=0x{item.data:08x} "
                    f"Expected BRESP={exp_resp}, Actual BRESP={item.resp}"
                )
                self.mismatches += 1
            else:
                self.writes_verified += 1
        else:
            exp_data, exp_resp, check_data = self.ref_model.predict_read(
                addr=item.addr,
                prot=item.prot
            )
            resp_mismatch = (item.resp != exp_resp)
            data_mismatch = check_data and (item.rdata != exp_data)

            if resp_mismatch or data_mismatch:
                self.logger.error(
                    f"[MISMATCH M{item.master_id} READ] Addr=0x{item.addr:08x} "
                    f"Expected RRESP={exp_resp} RDATA={'0x%08x' % exp_data if exp_data is not None else 'ANY'}, "
                    f"Actual RRESP={item.resp} RDATA=0x{item.rdata:08x}"
                )
                self.mismatches += 1
            else:
                self.reads_verified += 1

    def check_phase(self):
        super().check_phase()
        self.logger.info(
            f"--- Scoreboard Summary: Total={self.total_transactions} "
            f"Writes={self.writes_verified} Reads={self.reads_verified} "
            f"Mismatches={self.mismatches} ---"
        )
        assert self.mismatches == 0, f"Scoreboard detected {self.mismatches} mismatches!"
