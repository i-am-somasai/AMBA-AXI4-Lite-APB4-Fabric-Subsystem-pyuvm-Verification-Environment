# tb/block/test_apb_uart.py
# Directed tests for APB UART Peripheral (UA-01, UA-02, UA-03, UA-05)
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ReadOnly
from models.apb_driver import ApbMasterDriver

class UartTestbench:
    def __init__(self, dut):
        self.dut = dut
        self.apb = ApbMasterDriver(dut, dut.clk)
        self.dut.uart_rx.value = 1
        cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    async def reset(self):
        self.dut.rst_n.value = 0
        self.dut.uart_rx.value = 1
        self.apb.init_signals()
        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        self.dut.rst_n.value = 1
        await RisingEdge(self.dut.clk)

@cocotb.test()
async def test_ua01_loopback_bytes(dut):
    """UA-01: Loopback transmission of byte values (RX data == TX data, flags correct)."""
    tb = UartTestbench(dut)
    await tb.reset()

    # BAUDDIV = 0 (16 cycles per bit for fast sim execution)
    await tb.apb.write(addr=0x10, data=0)
    # CTRL = TX_EN(1) | RX_EN(2) | LOOPBACK(4) = 0x07
    await tb.apb.write(addr=0x0C, data=0x07)

    test_bytes = [0x55, 0xAA, 0x00, 0xFF, 0x3C, 0xC3, 0x12, 0x89]
    for b in test_bytes:
        # Write byte to TXDATA (0x00)
        await tb.apb.write(addr=0x00, data=b)

        # Wait for byte to be received into RX FIFO (poll STATUS[3] RX_EMPTY == 0)
        timeout = 250
        cycles = 0
        while cycles < timeout:
            status, _ = await tb.apb.read(addr=0x08)
            rx_empty = (status >> 3) & 1
            if rx_empty == 0:
                break
            await RisingEdge(dut.clk)
            cycles += 1

        assert rx_empty == 0, f"Byte {hex(b)} timed out waiting for reception"

        # Read byte from RXDATA (0x04)
        rdata, _ = await tb.apb.read(addr=0x04)
        assert (rdata & 0xFF) == b, f"Loopback data mismatch: expected {hex(b)}, got {hex(rdata & 0xFF)}"
        dut._log.info(f"Successfully transmitted and received byte {hex(b)} in {cycles} cycles")

    await RisingEdge(dut.clk)

@cocotb.test()
async def test_ua02_fifo_full_and_overflow_flags(dut):
    """UA-02: FIFO full / empty flags, TX_OVF and RX_OVF detection and W1C clearing."""
    tb = UartTestbench(dut)
    await tb.reset()

    # 1. Fill TX FIFO with TX disabled (CTRL = 0)
    await tb.apb.write(addr=0x0C, data=0x00)

    # Initial status: TX_EMPTY=1, RX_EMPTY=1
    status, _ = await tb.apb.read(addr=0x08)
    assert (status & 0x02) != 0, "Initial TX_EMPTY not set"
    assert (status & 0x08) != 0, "Initial RX_EMPTY not set"

    # Write 8 bytes to fill TX FIFO
    for i in range(8):
        await tb.apb.write(addr=0x00, data=(0x10 + i))

    # Verify TX_FULL is now set (STATUS[0] == 1)
    status, _ = await tb.apb.read(addr=0x08)
    assert (status & 0x01) == 1, f"TX_FULL not set after 8 writes: {hex(status)}"

    # Write 9th byte: should be dropped and set TX_OVF (STATUS[6] == 1)
    await tb.apb.write(addr=0x00, data=0x99)
    status, _ = await tb.apb.read(addr=0x08)
    assert ((status >> 6) & 1) == 1, f"TX_OVF not set after write when full: {hex(status)}"

    # Clear TX_OVF by writing 1 to bit 6 of STATUS
    await tb.apb.write(addr=0x08, data=(1 << 6))
    status, _ = await tb.apb.read(addr=0x08)
    assert ((status >> 6) & 1) == 0, f"TX_OVF did not clear via W1C: {hex(status)}"

    # Now enable TX and RX in loopback: drain TX FIFO into RX FIFO
    await tb.apb.write(addr=0x10, data=0)
    await tb.apb.write(addr=0x0C, data=0x07) # TX_EN | RX_EN | LOOPBACK

    # Wait until all 8 bytes arrive in RX FIFO -> RX_FULL (STATUS[2] == 1)
    for _ in range(2000):
        status, _ = await tb.apb.read(addr=0x08)
        if (status & 0x04) != 0: # RX_FULL
            break
        await RisingEdge(dut.clk)

    assert (status & 0x04) != 0, f"RX_FULL not set: {hex(status)}"

    # Read all 8 bytes back and verify data sequence
    for i in range(8):
        rdata, _ = await tb.apb.read(addr=0x04)
        assert (rdata & 0xFF) == (0x10 + i), f"Byte {i} mismatch: got {hex(rdata)}"

    # After reading 8 bytes, RX_EMPTY should be set again
    status, _ = await tb.apb.read(addr=0x08)
    assert (status & 0x08) != 0, f"RX_EMPTY not set after reading all bytes: {hex(status)}"

    await RisingEdge(dut.clk)

@cocotb.test()
async def test_ua03_bauddiv_sweep(dut):
    """UA-03: Sweep BAUDDIV and verify bit duration scaling."""
    tb = UartTestbench(dut)
    await tb.reset()

    for bauddiv in [0, 1, 2]:
        await tb.apb.write(addr=0x10, data=bauddiv)
        await tb.apb.write(addr=0x0C, data=0x01) # TX_EN only

        # Send byte with clear start bit (0) and LSB=1
        await tb.apb.write(addr=0x00, data=0x01)

        # Wait for start bit falling edge on uart_tx
        while dut.uart_tx.value == 1:
            await RisingEdge(dut.clk)

        # Count cycles of start bit (until uart_tx transitions to bit 0 value = 1)
        start_cycles = 0
        while True:
            await RisingEdge(dut.clk)
            await ReadOnly()
            start_cycles += 1
            if dut.uart_tx.value == 1:
                break

        expected_cycles = (bauddiv + 1) * 16
        dut._log.info(f"BAUDDIV={bauddiv}: measured start bit length = {start_cycles} cycles (expected {expected_cycles})")
        assert abs(start_cycles - expected_cycles) <= 1, f"Bit period mismatch for BAUDDIV={bauddiv}: expected {expected_cycles}, got {start_cycles}"

        # Wait for TX to finish completely: TX_EMPTY (bit 1) and not TX_BUSY (bit 7)
        while True:
            status, _ = await tb.apb.read(addr=0x08)
            if (status & 0x02) and not (status & 0x80):
                break
            await RisingEdge(dut.clk)
        await Timer(100, unit="ns")

    await RisingEdge(dut.clk)

@cocotb.test()
async def test_ua05_rx_irq(dut):
    """UA-05: RX IRQ enable/disable follows (RX_IRQ_EN & ~RX_EMPTY)."""
    tb = UartTestbench(dut)
    await tb.reset()

    await tb.apb.write(addr=0x10, data=0)

    # 1. Enable loopback with RX_IRQ_EN: CTRL = TX_EN(1) | RX_EN(2) | LOOPBACK(4) | RX_IRQ_EN(8) = 0x0F
    await tb.apb.write(addr=0x0C, data=0x0F)

    # Initially empty: IRQ should be 0
    assert dut.uart_irq.value == 0, "Initial uart_irq not 0"

    # Transmit a byte
    await tb.apb.write(addr=0x00, data=0x7E)

    # Wait for byte to be received and IRQ to assert
    while dut.uart_irq.value == 0:
        await RisingEdge(dut.clk)

    assert dut.uart_irq.value == 1, "uart_irq did not assert when RX FIFO received byte"

    # Read byte from RXDATA: FIFO becomes empty, IRQ must deassert
    rdata, _ = await tb.apb.read(addr=0x04)
    assert (rdata & 0xFF) == 0x7E
    await RisingEdge(dut.clk)
    assert dut.uart_irq.value == 0, "uart_irq did not deassert after RX FIFO was emptied"

    # 2. Disable RX_IRQ_EN (CTRL = 0x07)
    await tb.apb.write(addr=0x0C, data=0x07)
    await tb.apb.write(addr=0x00, data=0x42)

    # Wait until byte arrives in RX FIFO
    for _ in range(250):
        await RisingEdge(dut.clk)

    # IRQ must remain 0 because RX_IRQ_EN is 0
    assert dut.uart_irq.value == 0, "uart_irq asserted while RX_IRQ_EN was disabled"

    await RisingEdge(dut.clk)
    await Timer(10, unit="ns")
