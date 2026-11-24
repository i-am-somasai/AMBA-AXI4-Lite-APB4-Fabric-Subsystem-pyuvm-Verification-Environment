# tb/unit/test_axil_decoder.py
# Unit test for axil_decoder address decode and error generation
import cocotb
from cocotb.triggers import Timer

@cocotb.test()
async def test_axil_decoder_all(dut):
    """Test full decode map and unmapped detection for axil_decoder."""
    # Test cases: (addr, expected_sel, expected_err)
    test_vectors = [
        # S0: APB Subsystem 64 KB (0x4000_0000 - 0x4000_FFFF)
        (0x4000_0000, 0b0001, 0),
        (0x4000_1000, 0b0001, 0),
        (0x4000_2000, 0b0001, 0),
        (0x4000_FFFF, 0b0001, 0),

        # S1: Scratchpad RAM 4 KB (0x5000_0000 - 0x5000_0FFF)
        (0x5000_0000, 0b0010, 0),
        (0x5000_0100, 0b0010, 0),
        (0x5000_03FC, 0b0010, 0),
        (0x5000_0FFF, 0b0010, 0),

        # S2: System CSR 256 B (0x6000_0000 - 0x6000_00FF)
        (0x6000_0000, 0b0100, 0),
        (0x6000_0020, 0b0100, 0),
        (0x6000_00FC, 0b0100, 0),

        # S3: CDC Slow Regs 256 B (0x7000_0000 - 0x7000_00FF)
        (0x7000_0000, 0b1000, 0),
        (0x7000_0008, 0b1000, 0),
        (0x7000_00FC, 0b1000, 0),

        # Unmapped Spaces -> decode_err = 1, slave_sel = 0
        (0x0000_0000, 0b0000, 1),
        (0x1000_0000, 0b0000, 1),
        (0x3FFF_FFFF, 0b0000, 1),
        (0x4001_0000, 0b0000, 1),
        (0x5000_1000, 0b0000, 1),
        (0x6000_0100, 0b0000, 1),
        (0x7000_0100, 0b0000, 1),
        (0x8000_0000, 0b0000, 1),
        (0xDEAD_BEEF, 0b0000, 1),
        (0xFFFF_FFFC, 0b0000, 1),
    ]

    for addr, exp_sel, exp_err in test_vectors:
        dut.addr.value = addr
        await Timer(1, unit="ns")
        sel = int(dut.slave_sel.value)
        err = int(dut.decode_err.value)
        assert sel == exp_sel, f"Addr 0x{addr:08X}: expected sel=0x{exp_sel:X}, got 0x{sel:X}"
        assert err == exp_err, f"Addr 0x{addr:08X}: expected err={exp_err}, got {err}"

    dut._log.info("test_axil_decoder_all PASSED across all mapped and unmapped vectors")
