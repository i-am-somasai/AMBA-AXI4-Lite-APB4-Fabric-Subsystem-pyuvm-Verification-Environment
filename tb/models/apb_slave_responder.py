# tb/models/apb_slave_responder.py
"""
Reactive APB4 Slave Responder Model for L1 testing.
Synchronous per-cycle model adhering strictly to AMBA APB4 protocol:
- SETUP phase: PSEL=1, PENABLE=0
- ACCESS phase: PSEL=1, PENABLE=1 (wait-states via PREADY delay)
- Byte-strobe handling and PSLVERR injection
"""
import cocotb
from cocotb.triggers import RisingEdge


class ApbSlaveResponder:
    def __init__(
        self,
        clk,
        rst_n,
        name: str = "apb_slave",
        wait_states: int = 0,
        inject_pslverr: bool = False,
        base_addr: int = 0x40000000,
        paddr=None, psel=None, penable=None, pwrite=None,
        pwdata=None, pstrb=None, pready=None, prdata=None, pslverr=None,
    ):
        self.clk = clk
        self.rst_n = rst_n
        self.name = name
        self.wait_states = wait_states
        self.inject_pslverr = inject_pslverr
        self.base_addr = base_addr

        self.paddr = paddr
        self.psel = psel
        self.penable = penable
        self.pwrite = pwrite
        self.pwdata = pwdata
        self.pstrb = pstrb
        self.pready = pready
        self.prdata = prdata
        self.pslverr = pslverr

        self.memory = {}
        self.running = False
        self._worker_task = None

    def start(self):
        if not self.running:
            self.running = True
            self._worker_task = cocotb.start_soon(self._worker())

    def stop(self):
        self.running = False
        if self._worker_task:
            self._worker_task.cancel()

    async def _worker(self):
        self.pready.value = 1
        self.prdata.value = 0
        self.pslverr.value = 0
        wait_count = 0

        while self.running:
            await RisingEdge(self.clk)
            if int(self.rst_n.value) == 0:
                self.pready.value = 1
                self.prdata.value = 0
                self.pslverr.value = 0
                wait_count = 0
                continue

            psel_val = int(self.psel.value) if self.psel.value.is_resolvable else 0
            penable_val = int(self.penable.value) if self.penable.value.is_resolvable else 0

            if psel_val == 1:
                addr = int(self.paddr.value) if self.paddr.value.is_resolvable else 0
                offset = addr - self.base_addr
                is_write = int(self.pwrite.value) if self.pwrite.value.is_resolvable else 0

                # SETUP phase: PSEL=1, PENABLE=0
                if penable_val == 0:
                    if self.wait_states > 0:
                        self.pready.value = 0
                        wait_count = self.wait_states
                    else:
                        self.pready.value = 1
                        wait_count = 0
                        if not is_write:
                            self.prdata.value = self.memory.get(offset, 0x00000000)
                        self.pslverr.value = 1 if self.inject_pslverr else 0

                # ACCESS phase: PSEL=1, PENABLE=1
                else:
                    if wait_count > 0:
                        wait_count -= 1
                        if wait_count == 0:
                            self.pready.value = 1
                            if not is_write:
                                self.prdata.value = self.memory.get(offset, 0x00000000)
                            self.pslverr.value = 1 if self.inject_pslverr else 0
                        else:
                            self.pready.value = 0
                    else:
                        # Transfer completes on this edge
                        if is_write:
                            wdata = int(self.pwdata.value)
                            pstrb = int(self.pstrb.value) if self.pstrb is not None else 0xF
                            old_val = self.memory.get(offset, 0)
                            new_val = old_val
                            for b in range(4):
                                if (pstrb >> b) & 1:
                                    mask = 0xFF << (8 * b)
                                    new_val = (new_val & ~mask) | (wdata & mask)
                            self.memory[offset] = new_val

            else:
                self.pready.value = 1
                self.pslverr.value = 0
                wait_count = 0
