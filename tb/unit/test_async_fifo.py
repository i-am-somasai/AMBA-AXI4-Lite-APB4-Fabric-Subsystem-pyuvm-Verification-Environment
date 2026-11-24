# L0 Unit Test for async_fifo (CD-02)
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def run_fifo_stream(dut, wclk_period, rclk_period, num_items=200):
    wclk_task = cocotb.start_soon(Clock(dut.wclk, wclk_period, unit="ns").start())
    rclk_task = cocotb.start_soon(Clock(dut.rclk, rclk_period, unit="ns").start())

    dut.wrst_n.value = 0
    dut.rrst_n.value = 0
    dut.winc.value = 0
    dut.rinc.value = 0
    dut.wdata.value = 0

    await Timer(50, unit="ns")
    dut.wrst_n.value = 1
    dut.rrst_n.value = 1
    for _ in range(5):
        await RisingEdge(dut.wclk)
    for _ in range(5):
        await RisingEdge(dut.rclk)

    sent_items = [random.randint(1, 0x7FFFFFFF) for _ in range(num_items)]
    received_items = []
    wfull_reached = False
    rempty_reached = False

    async def writer():
        nonlocal wfull_reached
        for val in sent_items:
            while True:
                await Timer(1, unit="ns")
                if int(dut.wfull.value) == 1:
                    wfull_reached = True
                    dut.winc.value = 0
                    await RisingEdge(dut.wclk)
                else:
                    break

            if random.random() < 0.2:
                dut.winc.value = 0
                await RisingEdge(dut.wclk)
                while True:
                    await Timer(1, unit="ns")
                    if int(dut.wfull.value) == 1:
                        wfull_reached = True
                        await RisingEdge(dut.wclk)
                    else:
                        break

            dut.wdata.value = val
            dut.winc.value = 1
            await RisingEdge(dut.wclk)
            dut.winc.value = 0
            await Timer(1, unit="ns")
            if int(dut.wfull.value) == 1:
                wfull_reached = True

        dut.winc.value = 0

    async def reader():
        nonlocal rempty_reached
        cycles = 0
        timeout = 50000
        while len(received_items) < num_items and cycles < timeout:
            cycles += 1
            while True:
                await Timer(1, unit="ns")
                if int(dut.rempty.value) == 1:
                    rempty_reached = True
                    dut.rinc.value = 0
                    await RisingEdge(dut.rclk)
                else:
                    break

            if random.random() < 0.2:
                dut.rinc.value = 0
                await RisingEdge(dut.rclk)
                while True:
                    await Timer(1, unit="ns")
                    if int(dut.rempty.value) == 1:
                        rempty_reached = True
                        await RisingEdge(dut.rclk)
                    else:
                        break

            # FWFT read: item is valid on rdata
            await Timer(1, unit="ns")
            received_items.append(int(dut.rdata.value))
            dut.rinc.value = 1
            await RisingEdge(dut.rclk)
            dut.rinc.value = 0

    t_w = cocotb.start_soon(writer())
    t_r = cocotb.start_soon(reader())

    await t_w
    await t_r

    for _ in range(10):
        await RisingEdge(dut.rclk)

    assert wfull_reached, "wfull was never reached during stream test!"
    assert rempty_reached, "rempty was never reached during stream test!"
    assert len(received_items) == num_items, f"Count mismatch: sent {num_items}, received {len(received_items)}"
    assert received_items == sent_items, "Data stream corruption / ordering mismatch!"

    wclk_task.cancel()
    rclk_task.cancel()
    await Timer(10, unit="ns")


@cocotb.test()
async def test_cd02_async_fifo_stream(dut):
    """CD-02: Async FIFO continuous random-rate stream (fast writer/slow reader and reverse)."""
    dut._log.info("Starting CD-02: Async FIFO continuous stream test")

    # Fast writer (10 ns) / Slow reader (25 ns)
    dut._log.info("Running fast writer (10 ns) / slow reader (25 ns)...")
    await run_fifo_stream(dut, wclk_period=10, rclk_period=25, num_items=200)

    # Slow writer (25 ns) / Fast reader (10 ns)
    dut._log.info("Running slow writer (25 ns) / fast reader (10 ns)...")
    await run_fifo_stream(dut, wclk_period=25, rclk_period=10, num_items=200)

    dut._log.info("CD-02 PASSED: 400 total items streamed with full/empty reached and 0 mismatches")


@cocotb.test()
async def test_async_fifo_dual_clock(dut):
    """Basic dual-clock async FIFO functionality check."""
    await run_fifo_stream(dut, wclk_period=10, rclk_period=17, num_items=50)
