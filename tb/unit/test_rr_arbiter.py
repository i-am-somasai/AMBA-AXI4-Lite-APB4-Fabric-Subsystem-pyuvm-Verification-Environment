# L0 Unit Test for rr_arbiter
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_rr_arbiter_fairness_and_lock(dut):
    """Test single request, round-robin fairness, and transaction lock behavior."""
    dut._log.info("Starting test_rr_arbiter_fairness_and_lock")
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.rst_n.value = 0
    dut.req.value   = 0
    dut.lock.value  = 0
    await Timer(25, unit="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # 1. Zero requests -> zero grant
    assert dut.grant.value == 0
    assert dut.grant_valid.value == 0

    # 2. Single request 0
    dut.req.value = 0b01
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert dut.grant.value == 0b01, f"Expected grant=0b01, got {dut.grant.value}"
    assert dut.grant_valid.value == 1

    # 3. Single request 1
    dut.req.value = 0b10
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert dut.grant.value == 0b10, f"Expected grant=0b10, got {dut.grant.value}"

    # 4. Sustained contention: both requesting (req=0b11), lock=0
    # Should alternate 0 -> 1 -> 0 -> 1
    grants = []
    dut.req.value = 0b11
    dut.lock.value = 0
    for _ in range(6):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        grants.append(int(dut.grant.value))

    # Check alternating sequence
    for i in range(len(grants) - 1):
        assert grants[i] != grants[i+1], f"Arbiter did not alternate under contention: {grants}"

    # 5. Lock behavior: grant requester 0, assert lock
    dut.req.value = 0b01
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert dut.grant.value == 0b01

    # Assert lock and request from both
    dut.lock.value = 1
    dut.req.value  = 0b11
    for _ in range(4):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert dut.grant.value == 0b01, f"Lock violated! Expected 0b01, got {dut.grant.value}"

    # Release lock: should immediately grant requester 1
    dut.lock.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert dut.grant.value == 0b10, f"Expected grant to switch to 0b10 after lock release, got {dut.grant.value}"

    # 6. Deassert requests: verify grant drops to 0 immediately
    dut.req.value = 0b00
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert dut.grant.value == 0b00, f"Expected grant=0b00 after deasserting req, got {dut.grant.value}"
    assert dut.grant_valid.value == 0, f"Expected grant_valid=0, got {dut.grant_valid.value}"

    # 7. Contention priority rollover: last granted was 1, so with req=0b11, master 0 should have priority
    dut.req.value = 0b11
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert dut.grant.value == 0b01, f"Expected grant=0b01 (rollover from 1), got {dut.grant.value}"

    dut._log.info("test_rr_arbiter_fairness_and_lock PASSED")
