#!/usr/bin/env python3
import os
import shutil

PROJ_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MUTANTS_DIR = os.path.join(PROJ_DIR, "audit/mutants")

# Mutant 1: rr_arbiter.v -> Fixed priority instead of round-robin
src1 = os.path.join(PROJ_DIR, "rtl/common/rr_arbiter.v")
dst1 = os.path.join(MUTANTS_DIR, "m1_rr_arbiter/rr_arbiter.v")
with open(src1, "r") as f:
    c1 = f.read()
# Mutate: In round robin loop, force fixed priority (master 0 always wins)
c1_mut = c1.replace(
    "if (!found && req[(i + j) % NUM_REQS]) begin",
    "if (!found && req[0]) begin // MUTANT: Fixed priority to req[0]"
)
with open(dst1, "w") as f:
    f.write(c1_mut)
print("Created m1_rr_arbiter")

# Mutant 2: axil_ram.v -> Drop write strobe byte 0
src2 = os.path.join(PROJ_DIR, "rtl/axil/axil_ram.v")
dst2 = os.path.join(MUTANTS_DIR, "m2_axil_ram/axil_ram.v")
with open(src2, "r") as f:
    c2 = f.read()
c2_mut = c2.replace(
    "if (write_strb_active[0]) mem[write_ram_addr][7:0]   <= write_data_active[7:0];",
    "// MUTANT: Dropped WSTRB[0]\n                    if (1'b0) mem[write_ram_addr][7:0]   <= write_data_active[7:0];"
)
with open(dst2, "w") as f:
    f.write(c2_mut)
print("Created m2_axil_ram")

# Mutant 3: async_fifo.v -> Binary pointer across CDC instead of Gray code
src3 = os.path.join(PROJ_DIR, "rtl/common/async_fifo.v")
dst3 = os.path.join(MUTANTS_DIR, "m3_async_fifo/async_fifo.v")
with open(src3, "r") as f:
    c3 = f.read()
c3_mut = c3.replace(
    "wire [PTR_WIDTH-1:0] wgray_next = (wbin_next >> 1) ^ wbin_next;",
    "wire [PTR_WIDTH-1:0] wgray_next = wbin_next; // MUTANT: Binary instead of Gray"
)
with open(dst3, "w") as f:
    f.write(c3_mut)
print("Created m3_async_fifo")

# Mutant 4: axil2apb_bridge.v -> PSLVERR masked, returns RESP_OKAY
src4 = os.path.join(PROJ_DIR, "rtl/apb/axil2apb_bridge.v")
dst4 = os.path.join(MUTANTS_DIR, "m4_axil2apb_bridge/axil2apb_bridge.v")
with open(src4, "r") as f:
    c4 = f.read()
c4_mut = c4.replace(
    "s_axil_bresp  <= m_apb_pslverr ? 2'b10 : 2'b00;",
    "s_axil_bresp  <= 2'b00; // MUTANT: Mask PSLVERR on write"
).replace(
    "s_axil_rresp  <= m_apb_pslverr ? 2'b10 : 2'b00;",
    "s_axil_rresp  <= 2'b00; // MUTANT: Mask PSLVERR on read"
)
with open(dst4, "w") as f:
    f.write(c4_mut)
print("Created m4_axil2apb_bridge")

# Mutant 5: apb_timer.v -> Off-by-one timer expiry (fires at 1 instead of 0)
src5 = os.path.join(PROJ_DIR, "rtl/apb/apb_timer.v")
dst5 = os.path.join(MUTANTS_DIR, "m5_apb_timer/apb_timer.v")
with open(src5, "r") as f:
    c5 = f.read()
c5_mut = c5.replace(
    "if (reg_value == 32'd0) begin",
    "if (reg_value == 32'd1) begin // MUTANT: Off-by-one expiry"
)
with open(dst5, "w") as f:
    f.write(c5_mut)
print("Created m5_apb_timer")
