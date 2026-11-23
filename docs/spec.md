# AMBA-Fabric: AXI4-Lite Interconnect + APB Peripheral Subsystem with a Reusable pyuvm Verification Environment

**Project type:** Original design + verification project (100% simulation/open-source, zero hardware cost)
**Target roles:** RTL Design / Design Verification fresher and entry-level roles
**Host machine:** HP 15, Ryzen 5 5500U, 8 GB RAM, Ubuntu
**One-line pitch:** *"I designed a small AMBA SoC fabric and then verified it the way a DV team would: plan, constrained-random pyuvm environment, functional coverage closure, formal proofs, CDC checks, mutation-tested testbench, CI, and synthesis/STA on SKY130."*

---

## 0. How to use this document

This is the single source of truth for the project. It contains:

1. What the project is and why it is worth building (Sections 1–3)
2. Tools and installation (Section 4)
3. Complete architecture, address map, registers and RTL behaviour (Sections 5–7)
4. The verification strategy, test plan, coverage model, assertions, formal and mutation testing (Sections 8–12)
5. Synthesis/STA, CI, repository layout (Sections 13–15)
6. A phased schedule with checklists (Section 16)
7. Deliverables, resume bullets, interview prep, risks, definition of done (Sections 17–21)

Feature priority tags: **P0** = must have, **P1** = should have, **P2** = stretch.

---

## 1. Project overview

### 1.1 What is being built

A small but complete **bus fabric subsystem** built around the two most commonly asked-about AMBA protocols:

- An **AXI4-Lite 2-master × 4-slave crossbar** (address decode, per-slave round-robin arbitration, default error slave)
- An **AXI4-Lite → APB4 bridge** feeding three APB peripherals (**UART, Timer, GPIO**)
- An **AXI4-Lite scratch RAM** (byte-strobe writes, SLVERR on out-of-range)
- An **AXI4-Lite CSR block** (RO, RW, W1C register types and interrupt aggregation)
- A **clock-domain-crossing (CDC) bridge** to a second, asynchronous clock domain using Gray-pointer asynchronous FIFOs

The second half of the project, which carries most of the weight for hiring, is **how it is verified**:

- A **pyuvm** (UVM methodology in Python on top of cocotb) environment: agents, drivers, monitors, sequencers, scoreboards, register model, sequences
- **Functional coverage** with defined bins and crosses, closed to 100% (with documented waivers)
- **Code coverage** with Verilator
- **Formal verification** with SymbiYosys (BMC + k-induction) for protocol checkers, arbiter, FIFO, bridge
- **CDC verification** (simulation across clock ratios and phases, plus formal on the FIFO)
- **Mutation testing** with Yosys `mutate` to *measure the quality of the testbench itself*
- **CI** on GitHub Actions
- **Synthesis + STA** on SKY130 with Yosys + OpenSTA, including an asynchronous clock-group constraint

### 1.2 Why this project (what it fixes on the resume)

| Gap in current resume | How this project fixes it |
|---|---|
| No UVM-style environment | pyuvm agents/scoreboard/sequences/coverage |
| No memory-mapped bus protocols (APB/AXI4-Lite) | Full AXI4-Lite crossbar + APB bridge |
| No CDC | Async FIFO bridge, two clock domains, ratio sweeps, formal |
| No formal | SymbiYosys proofs on 4+ modules |
| Results not quantified | Coverage %, assertion counts, mutation score, Fmax, area |
| No CI | GitHub Actions regression with coverage artifacts |

### 1.3 Goals

- G1. Working, parameterized RTL for every block in Section 5.
- G2. A written verification plan (`docs/vplan.md`) mapping every feature to tests, coverage and checks.
- G3. 100% of defined functional coverage bins hit (waivers documented) and a reported code coverage number.
- G4. Formal proofs (no counterexamples) for the property sets in Section 11.
- G5. A measured mutation score with an analysis of surviving mutants and test improvements.
- G6. Synthesis + STA report on SKY130 at a stated clock target.
- G7. A public GitHub repo with a clear README, waveform screenshots, results table and CI badge.

### 1.4 Non-goals (explicitly out of scope)

- No FPGA, no board, no hardware of any kind
- No AXI4 full (bursts, IDs, outstanding, out-of-order), AXI4-Lite only
- No commercial tools, no SystemVerilog class-based UVM (not runnable on open-source simulators; pyuvm is used instead)
- No full P&R requirement (optional stretch; see Section 13)
- No CPU in the base project (optional stretch: attach your RISC-V core from Project 1 as a master)

---

## 2. Constraints

| Constraint | Decision |
|---|---|
| RAM 8 GB | Design is tiny (a few thousand cells). Synthesis configuration reduces RAM depth (Section 7.4). Avoid giant memories as flops. |
| Open-source only | Icarus Verilog, Verilator, Yosys, SymbiYosys, OpenSTA, cocotb, pyuvm, GTKWave |
| Ubuntu | All tools install on Ubuntu (Section 4) |
| Tool compatibility | RTL style = Verilog-2005 + minimal SystemVerilog (`logic`, `always_ff`, `always_comb`, parameters, generate). **No interfaces, no classes, no packed structs on ports** so the same RTL works in Icarus, Verilator and Yosys |

---

## 3. Feature list

| ID | Feature | Priority |
|---|---|---|
| F-01 | AXI4-Lite 2M×4S crossbar with address decode | P0 |
| F-02 | Per-slave round-robin arbiter (separate read and write) with transaction lock | P0 |
| F-03 | Default slave returning DECERR for unmapped addresses (write data consumed, no hang) | P0 |
| F-04 | AXI4-Lite scratch RAM with WSTRB and SLVERR on out-of-range | P0 |
| F-05 | AXI4-Lite CSR block (RO / RW / W1C / WO-set register types, IRQ aggregation) | P0 |
| F-06 | AXI4-Lite → APB4 bridge (wait states, PSLVERR, PSTRB, PPROT) | P0 |
| F-07 | APB decoder with PSLVERR on unmapped APB address | P0 |
| F-08 | APB UART (8N1, 16× oversampling, TX/RX FIFOs, loopback, framing-error detect) | P0 |
| F-09 | APB Timer (periodic/one-shot, IRQ, W1C status) | P0 |
| F-10 | APB GPIO (direction, 2-FF input sync, rising-edge IRQ, W1C) | P1 |
| F-11 | CDC bridge: request/response Gray-pointer async FIFOs to `clk_slow` register block | P0 |
| F-12 | Reset synchronizers per clock domain (async assert, sync deassert) | P0 |
| F-13 | Interrupt aggregation to a single `irq_o` | P1 |
| V-01 | pyuvm environment with 2 AXI-Lite master agents + AXI-Lite slave responder agents + APB responder agent | P0 |
| V-02 | Scoreboards with reference memory/register model | P0 |
| V-03 | Constrained-random + directed sequences (Section 9.4) | P0 |
| V-04 | Functional coverage model (Section 10) closed to 100% | P0 |
| V-05 | Code coverage via Verilator, reported | P0 |
| V-06 | SVA-style protocol checkers: simulation monitors in Python + formal-grade checkers in RTL (`ifdef FORMAL`) | P0 |
| V-07 | Formal proofs with SymbiYosys (Section 11) | P0 |
| V-08 | CDC ratio/phase sweep tests | P0 |
| V-09 | Mutation testing with Yosys `mutate` + survivor analysis | P1 |
| V-10 | GitHub Actions CI (regression + coverage artifacts) | P1 |
| S-01 | Yosys synthesis + OpenSTA on SKY130 with async clock groups | P0 |
| S-02 | Gate-level simulation of synthesized netlist (smoke subset) | P2 |
| S-03 | OpenLane run for a GDSII | P2 |
| X-01 | Attach Project 1 RISC-V core as a third master | P2 |
| X-02 | Multiple outstanding transactions with response FIFOs | P2 |

---

## 4. Toolchain

### 4.1 Tool list

| Purpose | Tool | Notes |
|---|---|---|
| RTL simulation (primary) | **Icarus Verilog** (`iverilog`, `vvp`) | Most stable with cocotb |
| Fast sim + code coverage | **Verilator 5.x** | `--coverage`, `--assert`, `--trace` |
| Waveforms | **GTKWave** | |
| Testbench framework | **cocotb** | Python testbench driving the simulator |
| UVM methodology | **pyuvm** | UVM architecture in Python on cocotb |
| Functional coverage | **cocotb-coverage** | Cover points/crosses, export to XML/YAML |
| Formal | **SymbiYosys (`sby`)** + Yosys + Boolector/Yices/Z3 | BMC, k-induction, cover |
| Synthesis | **Yosys** + ABC | |
| STA | **OpenSTA** | |
| PDK libraries | **SKY130** (`sky130_fd_sc_hd` Liberty) | Obtain via open_pdks / volare (the tool has been renamed; check the current name) / the copy bundled with OpenLane |
| Mutation | **Yosys `mutate`** + Python driver | |
| Reports | `lcov`/`genhtml`, `verilator_coverage`, matplotlib | |
| CI | GitHub Actions | Free for public repos |
| Version control | Git | |

### 4.2 Recommended installation (Ubuntu)

**Step 1: base packages**

```bash
sudo apt update
sudo apt install -y build-essential git make python3 python3-venv python3-pip \
     gtkwave iverilog lcov cmake tcl-dev swig bison flex libeigen3-dev
```

**Step 2: OSS CAD Suite (recommended).** Download the free prebuilt bundle from the YosysHQ `oss-cad-suite-build` GitHub releases. It includes Yosys, SymbiYosys, Boolector/Yices/Z3, a recent Verilator, Icarus and GTKWave. Source its `environment` script in your shell. This avoids the old Verilator that Ubuntu's apt provides (cocotb needs Verilator 5.x).

**Step 3: OpenSTA.** Build from source (`github.com/The-OpenROAD-Project/OpenSTA`) using cmake. Needs the packages from Step 1. Use `make -j2` to stay inside 8 GB.

**Step 4: Python environment**

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install cocotb pyuvm cocotb-coverage pytest numpy matplotlib
pip freeze > requirements.txt
```

> **Version note:** pyuvm, cocotb and cocotb-coverage must be mutually compatible. Check the pyuvm README for the supported cocotb version, install a combination that works, and **pin the exact versions** in `requirements.txt` so CI is reproducible.

**Step 5: SKY130 Liberty files.** Obtain `sky130_fd_sc_hd__tt_025C_1v80.lib` (and ss/ff corner files for the stretch goal).

### 4.3 Simulator strategy

- **Day-to-day and mutation testing:** Icarus Verilog (stable cocotb support).
- **Coverage and fast random regressions:** Verilator (code coverage, speed).
- Keep a `SIM=icarus|verilator` Makefile switch so the same tests run on both. Passing on both is itself a good README line.

---

## 5. Architecture

### 5.1 Block diagram

```
                    clk_sys domain                                          clk_slow domain
 ┌─────────────┐    ┌──────────────────────────────┐
 │ Master 0    │───▶│                              │──▶ S0: axil2apb_bridge ─▶ apb_decoder ─┬▶ UART
 │ (TB agent)  │    │   AXI4-Lite 2×4 Crossbar     │                                        ├▶ TIMER
 ├─────────────┤    │  - address decoder           │                                        └▶ GPIO
 │ Master 1    │───▶│  - per-slave RR arbiters     │──▶ S1: axil_ram (scratch RAM)
 │ (TB agent)  │    │  - default DECERR slave      │──▶ S2: axil_csr (ID, SCRATCH, IRQ, W1C)
 └─────────────┘    │                              │──▶ S3: axil_cdc_bridge ═▶ req async FIFO ═▶ slow_regs
                    └──────────────────────────────┘                           resp async FIFO ◀═
                         irq_o ◀── irq aggregation (UART, TIMER, GPIO)
```

### 5.2 Parameters (top level)

| Parameter | Default | Meaning |
|---|---|---|
| `DATA_WIDTH` | 32 | AXI-Lite data width (fixed at 32 for the base project) |
| `ADDR_WIDTH` | 32 | Address width |
| `NUM_MASTERS` | 2 | Masters |
| `NUM_SLAVES` | 4 | Slaves (excluding default slave) |
| `RAM_DEPTH` | 256 words (1 KB) in simulation, 64 words for synthesis | See Section 7.4 |
| `FIFO_DEPTH` | 4 (CDC), 8 (UART) | Powers of two |
| `GPIO_WIDTH` | 16 | |

### 5.3 Address map

| Slave | Region | Base | Size | Notes |
|---|---|---|---|---|
| S0 | APB subsystem | `0x4000_0000` | 64 KB | Behind AXI4-Lite→APB bridge |
|  – UART | | `0x4000_0000` | 4 KB | |
|  – TIMER | | `0x4000_1000` | 4 KB | |
|  – GPIO | | `0x4000_2000` | 4 KB | Other APB addresses → PSLVERR |
| S1 | Scratch RAM | `0x5000_0000` | 4 KB | Only the first `RAM_DEPTH*4` bytes are backed; rest → SLVERR |
| S2 | CSR block | `0x6000_0000` | 256 B | |
| S3 | CDC bridge (slow domain regs) | `0x7000_0000` | 256 B | Undefined offsets → SLVERR |
| Default | everything else | n/a | n/a | DECERR |

### 5.4 Clocks and resets

- `clk_sys` (target 100 MHz) and `clk_slow` (asynchronous to `clk_sys`; testbench sweeps ratios and phases).
- A single external active-low asynchronous `rst_n` is synchronized into each domain by `rst_sync` (assert async, deassert sync).
- **Rule:** every signal crossing clock domains goes only through the async FIFOs (data) or 2-FF synchronizers (single-bit status). No other crossings. Document this in the README.

---

## 6. AXI4-Lite protocol reference (what the RTL must follow)

**Channels and signals** (32-bit data, 32-bit address):

- Write address: `AWADDR, AWPROT, AWVALID, AWREADY`
- Write data: `WDATA, WSTRB[3:0], WVALID, WREADY`
- Write response: `BRESP[1:0], BVALID, BREADY`
- Read address: `ARADDR, ARPROT, ARVALID, ARREADY`
- Read data: `RDATA, RRESP[1:0], RVALID, RREADY`

**Responses:** `00 OKAY`, `10 SLVERR`, `11 DECERR` (EXOKAY not supported in AXI4-Lite).

**Rules the design and checkers enforce:**

1. A source must hold `VALID` and its payload stable until `READY` is seen (once VALID is asserted it cannot be dropped).
2. A master must not wait for `AWREADY`/`WREADY` before asserting `AWVALID`/`WVALID`. A slave/interconnect *may* wait for `AWVALID` and/or `WVALID` before asserting `READY`.
3. `BVALID` may only assert after both the AW and W handshakes have completed.
4. `RVALID` may only assert after the AR handshake.
5. Exactly one response per transaction (one `B` per write, one `R` per read).
6. Address LSBs `[1:0]` are ignored (word-aligned access is assumed; document this).
7. Reads and writes are independent channels with no ordering guarantee between them.

---

## 7. RTL specification

All files go in `rtl/`. Reuse the same naming and port conventions everywhere (`clk`, `rst_n`, then channel signals).

### 7.1 Common blocks (`rtl/common/`)

#### `rst_sync.v` (F-12)
2-FF reset synchronizer: asynchronous assertion, synchronous de-assertion, one instance per domain.

#### `sync_fifo.v`
Parameterized (`WIDTH`, `DEPTH`) synchronous FIFO with `full`, `empty`, `count`; used for UART TX/RX. Simultaneous push/pop supported; push-when-full and pop-when-empty are ignored and flagged on `overflow`/`underflow` outputs.

#### `async_fifo.v` (F-11)
Dual-clock FIFO per Cummings' classic design:

- Binary pointer for addressing, **Gray-coded pointer** sent across the domain
- 2-FF synchronizer on each Gray pointer (`wptr→rclk`, `rptr→wclk`)
- `full` generated in the write domain (compare with extra pointer bit), `empty` in the read domain
- Parameters: `WIDTH`, `DEPTH` (power of 2), `ASYNC_STAGES` (default 2)
- Mark synchronizer flops with a naming convention (`sync_*_q1/q2`) so STA/CDC constraints can target them

#### `rr_arbiter.v` (F-02)
N-requester round-robin arbiter:

- Inputs: `req[N-1:0]`, `lock` (when high, holds current grant)
- Outputs: one-hot `grant[N-1:0]`, `grant_valid`
- Properties: grant is one-hot or zero; a requester that keeps requesting is granted within N−1 other grants (bounded fairness)

### 7.2 AXI4-Lite interconnect (`rtl/axil/`)

#### `axil_decoder.v`
Combinational address-to-slave-index decode using localparam base/mask pairs. Output includes a `decode_err` flag when no region matches (routes to the default slave).

#### `axil_xbar.v` (F-01, F-02)
2 masters × (4 slaves + default). Behaviour:

**Write path**
1. Each master's AW address is decoded to a target (slave or default).
2. Each target has a **write arbiter** over the masters requesting it.
3. When a master wins, the crossbar **locks** that target to the master from the AW handshake until the **B handshake** completes.
4. The W channel is forwarded only to the locked target (the crossbar holds `WREADY` low until the AW is granted, which is allowed by the protocol).
5. B response from the locked target is routed back to the owning master.

**Read path**: same structure with independent read arbiters (reads and writes to the same slave can proceed concurrently if the slave supports it).

**Limits (document in README):**
- One outstanding write and one outstanding read per master (AXI-Lite has no IDs; this keeps ordering trivially correct). Multiple outstanding is stretch X-02.
- Different masters targeting *different* slaves proceed in parallel (verified by cycle count).
- Added latency target: ≤ 1 cycle on the request path and ≤ 1 cycle on the response path (state your measured number).

#### `axil_default_slave.v` (F-03)
- Accepts AW and W, returns `BRESP = DECERR`
- Accepts AR, returns `RRESP = DECERR`, `RDATA = 0`
- Must never hang and must always consume write data

#### `axil_ram.v` (F-04)
- `RAM_DEPTH` 32-bit words, byte-enable writes using `WSTRB`
- Read latency: 1 cycle
- Address ≥ `RAM_DEPTH*4` (inside the 4 KB window) → `SLVERR` on both read and write (write data discarded)
- Behavioral array (inferred memory) in simulation

#### `axil_csr.v` (F-05, F-13)

| Offset | Name | Type | Reset | Description |
|---|---|---|---|---|
| 0x00 | `ID` | RO | `0xA3BA0001` | Constant ID; writes ignored (OKAY) |
| 0x04 | `VERSION` | RO | `0x00010000` | |
| 0x08 | `SCRATCH` | RW | 0 | Full-word RW |
| 0x0C | `SCRATCH2` | RW | 0 | Byte-writable via `WSTRB` |
| 0x10 | `IRQ_RAW` | RO | 0 | `[0]` UART, `[1]` TIMER, `[2]` GPIO |
| 0x14 | `IRQ_MASK` | RW | 0 | Per-source enable |
| 0x18 | `IRQ_STATUS` | RO | 0 | `IRQ_RAW & IRQ_MASK` |
| 0x1C | `W1C_TEST` | W1C | 0 | Writing 1 clears the bit |
| 0x20 | `W1C_SET` | WO | n/a | Writing 1 **sets** the matching bit in `W1C_TEST` (test hook) |

`irq_o = |IRQ_STATUS`. Undefined offsets → `SLVERR`.

### 7.3 APB subsystem (`rtl/apb/`)

#### `axil2apb_bridge.v` (F-06)
- Converts one AXI4-Lite transaction at a time to APB4.
- Round-robin arbitration between a pending write and a pending read.
- Write starts only when **both** AW and W have been received.
- APB sequence: **IDLE → SETUP (PSEL=1, PENABLE=0) → ACCESS (PSEL=1, PENABLE=1, wait while PREADY=0) → response**.
- `PSTRB` from `WSTRB` (reads drive `PSTRB=0`), `PPROT` from `AWPROT/ARPROT`.
- `PSLVERR=1` at the end of ACCESS → `SLVERR` on `BRESP`/`RRESP`.
- APB signals held stable while waiting for `PREADY` (checked by formal).

#### `apb_decoder.v` (F-07)
- One-hot `PSEL` per peripheral from `PADDR[15:12]`; muxes `PRDATA/PREADY/PSLVERR`.
- Unmapped APB address: `PREADY=1`, `PSLVERR=1`, `PRDATA=0` after one access cycle.

#### `apb_uart.v` (F-08)

| Offset | Name | Access | Fields |
|---|---|---|---|
| 0x00 | `TXDATA` | WO | `[7:0]` pushes into TX FIFO; write when full is dropped and sets `TX_OVF` |
| 0x04 | `RXDATA` | RO | `[7:0]` pops RX FIFO (empty → returns 0) |
| 0x08 | `STATUS` | RO/W1C | `[0]` TX_FULL, `[1]` TX_EMPTY, `[2]` RX_FULL, `[3]` RX_EMPTY, `[4]` FRAME_ERR (W1C), `[5]` RX_OVF (W1C), `[6]` TX_OVF (W1C), `[7]` TX_BUSY |
| 0x0C | `CTRL` | RW | `[0]` TX_EN, `[1]` RX_EN, `[2]` LOOPBACK, `[3]` RX_IRQ_EN |
| 0x10 | `BAUDDIV` | RW | `[15:0]` divisor; tick = `clk_sys / (BAUDDIV+1)`, 16× oversampling |

- Format 8N1, LSB first. 8-entry TX and RX FIFOs (`sync_fifo`).
- `LOOPBACK=1` connects TX internally to RX (lets the testbench verify without an external model).
- RX: start-bit detect, mid-bit sampling, stop-bit check → `FRAME_ERR` on a bad stop bit.
- `irq = RX_IRQ_EN & ~RX_EMPTY`.

#### `apb_timer.v` (F-09)

| Offset | Name | Access | Fields |
|---|---|---|---|
| 0x00 | `CTRL` | RW | `[0]` EN, `[1]` PERIODIC, `[2]` IRQ_EN |
| 0x04 | `LOAD` | RW | Reload value |
| 0x08 | `VALUE` | RO | Current count |
| 0x0C | `STATUS` | W1C | `[0]` TIMEOUT |

- Down-counter at `clk_sys`. When EN is set, VALUE loads from LOAD; timeout period is `LOAD + 1` cycles.
- On reaching 0: set `TIMEOUT`; if PERIODIC reload, else clear EN.
- `irq = IRQ_EN & TIMEOUT`.

#### `apb_gpio.v` (F-10)

| Offset | Name | Access | Fields |
|---|---|---|---|
| 0x00 | `DIR` | RW | 1 = output |
| 0x04 | `OUT` | RW | Output value |
| 0x08 | `IN` | RO | 2-FF synchronized `gpio_i` |
| 0x0C | `IRQ_EN` | RW | Per-pin enable |
| 0x10 | `IRQ_STATUS` | W1C | Rising-edge detect on synchronized `IN` |

### 7.4 CDC subsystem (`rtl/cdc/`)

#### `axil_cdc_bridge.v` (F-11)
- AXI-Lite slave in `clk_sys`; accepts one transaction at a time.
- **Request FIFO** (`clk_sys → clk_slow`): `{is_write, addr[7:0], wdata[31:0], wstrb[3:0]}`, depth 4.
- **Response FIFO** (`clk_slow → clk_sys`): `{rdata[31:0], resp[1:0]}`, depth 4.
- Bridge holds `BVALID/RVALID` until the response FIFO returns data.

#### `slow_regs.v` (`clk_slow` domain)

| Offset | Name | Access | Description |
|---|---|---|---|
| 0x00 | `SLOW_ID` | RO | Constant `0x510E0001` |
| 0x04 | `SLOW_SCRATCH` | RW | WSTRB-aware |
| 0x08 | `SLOW_COUNTER` | RO | Free-running counter in `clk_slow` (proves it really lives in the other domain) |
| 0x0C | `SLOW_CTRL` | RW | `[0]` counter enable |
| other | n/a | n/a | `SLVERR` |

### 7.5 Synthesis configuration note
A 4 KB RAM built from flops is ~32k flops and will bloat synthesis. Use `RAM_DEPTH=256` for simulation and `RAM_DEPTH=64` for the synthesis run (or treat the RAM as a blackbox and report it separately). State which one you used in the results table.

### 7.6 Top level: `amba_fabric_top.v`
Instantiates: `rst_sync` ×2, `axil_xbar`, `axil_default_slave`, `axil_ram`, `axil_csr`, `axil2apb_bridge` + `apb_decoder` + UART/TIMER/GPIO, `axil_cdc_bridge` + `slow_regs`. Exposes two AXI-Lite master ports, `clk_sys`, `clk_slow`, `rst_n`, `gpio_i/gpio_o`, `uart_rx/uart_tx`, `irq_o`.

---

## 8. Verification strategy

### 8.1 Philosophy
Verify at three levels so failures are easy to localize, and so every block has evidence:

| Level | DUT | Environment |
|---|---|---|
| **L0 Unit** | `rr_arbiter`, `sync_fifo`, `async_fifo`, `axil_decoder`, `rst_sync` | Small cocotb tests + formal |
| **L1 Block** | `axil_xbar` (with slave responder agents), `axil2apb_bridge` (with APB responder agent), `axil_cdc_bridge` | pyuvm env with agents and scoreboards |
| **L2 Subsystem** | `amba_fabric_top` | Full pyuvm env, register model scoreboard, coverage closure |

### 8.2 Verification components (pyuvm)

| Component | Role |
|---|---|
| `AxilMasterAgent` ×2 | Sequencer + driver (drives AW/W/B/AR/R with configurable per-channel delays and ordering) + monitor |
| `AxilSlaveResponderAgent` ×4 | For L1: reactive slave with configurable latency, random `READY` back-pressure, error injection (`SLVERR`) |
| `ApbResponderAgent` | For bridge L1: configurable wait states (0–N), error injection, PSTRB capture |
| `UartRxStimAgent` / `UartTxMonitor` | Drives and samples the UART pins at a given baud (bad-stop-bit injection) |
| `GpioAgent` | Drives `gpio_i`, samples `gpio_o` |
| `ClockResetAgent` | Generates `clk_sys`/`clk_slow` with configurable ratio and phase offset; applies resets (including mid-transaction) |
| `AxilProtocolMonitor` | Passive checker, implements the rules of Section 6 in Python on every channel |
| `FabricScoreboard` | Predicts the expected result of every transaction (reference memory, register model, peripheral models, address decode model) and compares |
| `CoverageCollector` | Samples the covergroups in Section 10 from monitor transactions |
| `FabricEnv` / tests | Configures agents, runs sequences |

**Reference models in Python (`tb/models/`):**
- `addr_map.py`: expected decode (same table as Section 5.3, written independently from the RTL)
- `ram_model.py`: byte-enable memory with out-of-range behaviour
- `reg_model.py`: per-register access types (RO/RW/W1C/WO-set) with reset values
- `uart_model.py`, `timer_model.py`, `gpio_model.py`: cycle-aware behavioural predictions

### 8.3 Directed vs constrained-random
- **Directed** tests first (bring-up and corner cases), then **constrained-random** to fill coverage.
- Random constraints: address (mix of mapped / unmapped / boundary), `WSTRB`, data patterns (0, all-ones, walking-1/0, random), master ordering (AW-first, W-first, simultaneous), back-pressure delay distributions, contention between masters.
- All tests take a `SEED`; the seed is printed on failure so every failure is reproducible.

### 8.4 Checking strategy (three layers)
1. **Scoreboards** compare data and responses against reference models.
2. **Protocol monitors** check handshake rules on every cycle (Section 6).
3. **Formal checkers in RTL** (`ifdef FORMAL`) prove the same rules exhaustively for the key blocks.

Every test also has a **watchdog timeout** (e.g. 2000 cycles per transaction) so a hang is a failure, not a stuck simulation.

---

## 9. Verification plan (feature → test mapping)

### 9.1 Test list

**Crossbar / AXI4-Lite (L1 + L2)**

| ID | Scenario | Checks |
|---|---|---|
| XB-01 | Single write and read, each master to each mapped slave | Data/response correct, correct slave selected |
| XB-02 | Write-then-read data integrity on RAM | Reference memory match |
| XB-03 | All 16 `WSTRB` patterns on RAM and CSR scratch | Only strobed bytes change |
| XB-04 | Unmapped read and write (several regions + boundary addresses) | `DECERR`, no hang, write data consumed |
| XB-05 | Both masters to the same slave simultaneously | Serialized, no corruption, both complete |
| XB-06 | Both masters to different slaves simultaneously | Parallel completion (cycle count shows no serialization) |
| XB-07 | Arbitration fairness under sustained contention | Grant counts differ by ≤ 1 |
| XB-08 | AW before W / W before AW / simultaneous | Correct completion in all orders |
| XB-09 | Random `READY` back-pressure on all channels | No loss, no duplication |
| XB-10 | Delayed `BREADY` / `RREADY` | Response held stable until accepted |
| XB-11 | `SLVERR` propagation (RAM out-of-range, CSR undefined, APB error, CDC undefined) | Correct master receives correct code |
| XB-12 | Reset during an in-flight transaction, then recovery | Clean state, next transaction OK |
| XB-13 | Random stress, ≥ 10,000 transactions, 2 masters | Zero scoreboard mismatches |
| XB-14 | `AWPROT/ARPROT` pass-through to APB `PPROT` | Matches |
| XB-15 | Unaligned address LSBs | Behaves as word-aligned (documented) |

**APB bridge (L1)**

| ID | Scenario | Checks |
|---|---|---|
| BR-01 | Single write and read, 0 wait states | APB SETUP/ACCESS timing correct |
| BR-02 | Wait states 1…N random | `PENABLE` stable, signals held |
| BR-03 | `PSLVERR` on read and on write | Maps to `SLVERR` |
| BR-04 | `PSTRB` patterns | Match `WSTRB` |
| BR-05 | Back-to-back mixed read/write from both masters | Single-outstanding behaviour correct, no starvation |
| BR-06 | Write with W arriving long after AW | Bridge waits, no early APB start |

**Peripherals (L2)**

| ID | Scenario | Checks |
|---|---|---|
| UA-01 | Loopback: all 256 byte values | RX data = TX data, flags correct |
| UA-02 | TX FIFO full / RX FIFO full / overflow flags | Flag behaviour and W1C clearing |
| UA-03 | Sweep `BAUDDIV` | Pin-level bit period matches |
| UA-04 | External RX stimulus with bad stop bit | `FRAME_ERR` set |
| UA-05 | RX IRQ enable/disable | `irq` follows `RX_IRQ_EN & ~RX_EMPTY` |
| TM-01 | One-shot countdown | Timeout after exactly `LOAD+1` cycles |
| TM-02 | Periodic mode, several periods | Exact period each time |
| TM-03 | W1C of `TIMEOUT`, IRQ clear | Correct |
| GP-01 | Direction and output value | `gpio_o` as expected |
| GP-02 | Input sync latency | 2-cycle latency on `IN` |
| GP-03 | Rising-edge IRQ + W1C | Correct, no false edges |
| CS-01 | Reset values of all CSRs | Match table |
| CS-02 | RO ignores writes (returns OKAY), W1C semantics, `W1C_SET` hook | Match reg model |
| CS-03 | IRQ mask and aggregation | `irq_o` behaviour |

**CDC (L1 + L2)**

| ID | Scenario | Checks |
|---|---|---|
| CD-01 | Data integrity through the bridge across ratio/phase sweep (e.g. `clk_slow` = 1/1.3, 1/3, 1/7, 5/3 of `clk_sys`, random phase) | All transactions correct |
| CD-02 | FIFO full/empty boundary behaviour | No overflow/underflow |
| CD-03 | Reset in either domain at random times | Recovers cleanly |
| CD-04 | `SLOW_COUNTER` reads increase at `clk_slow` rate | Proves real second domain |
| CD-05 | Read/write interleave to slow regs from both masters | Correct |

### 9.2 Closure criteria
- All tests pass with ≥ 20 different random seeds.
- Functional coverage 100% of defined bins (waivers listed with justification).
- Code coverage (line/toggle) reported; unexplained holes investigated and either covered or waived.
- All formal proofs pass, all cover traces reachable.
- Mutation score reported with survivor analysis.

---

## 10. Functional coverage model (cocotb-coverage)

| Covergroup | Coverpoints | Crosses |
|---|---|---|
| `cg_txn` | master (2), target (S0–S3, default), op (R/W), resp (OKAY/SLVERR/DECERR) | master × target × op × resp (legal combos only; illegal combos explicitly excluded) |
| `cg_wstrb` | 16 `WSTRB` patterns | `WSTRB` × target (RAM, CSR, slow regs, APB) |
| `cg_order` | write ordering: AW first, W first, same cycle | order × target |
| `cg_backpressure` | per channel ready-delay bucket {0, 1, 2–4, 5–16} | channel × bucket |
| `cg_contention` | both masters to same slave / different slaves / one idle | contention × op combination (R/R, R/W, W/W) |
| `cg_apb` | wait-state bucket {0, 1, 2–4, 5+}, `PSLVERR` yes/no, `PSTRB` pattern class | wait bucket × error × op |
| `cg_cdc` | clock ratio bucket (slow<sys, ≈equal, slow>sys), FIFO occupancy {empty, partial, full} | ratio × occupancy × op |
| `cg_uart` | `BAUDDIV` bucket, TX/RX FIFO state, error type | divisor × FIFO state |
| `cg_reset` | reset applied while idle / AW in flight / W in flight / B pending / R pending | n/a |

Export coverage to XML/YAML at the end of every run and merge across seeds in `scripts/merge_cov.py`. Produce a table (bin, hits, goal) in `docs/results.md`.

**Code coverage:** run Verilator with `--coverage` (line + toggle), post-process with `verilator_coverage --annotate` and `lcov/genhtml` for an HTML report.

---

## 11. Assertions and formal verification (SymbiYosys)

### 11.1 Style
Yosys' native frontend handles immediate assertions well. Write checkers in `formal/` as modules using `assert/assume/cover` inside `always @(posedge clk)` blocks with an `f_past_valid` register, wrapped in `ifdef FORMAL`. This is portable across Yosys and Verilator. (Using `yosys-slang` for fuller SVA is optional.)

### 11.2 Property sets

**AXI4-Lite protocol checker (`axil_props.v`, bound to xbar ports, bridge input, RAM, CSR, CDC bridge)**
- `AWVALID && !AWREADY` ⇒ next cycle `AWVALID` and `AWADDR/AWPROT` stable (same for W, AR, B, R channels)
- `BVALID` only after AW *and* W handshakes (count-based reasoning)
- `RVALID` only after an AR handshake
- No `BVALID/RVALID` without a pending request; at most one response per request
- Response codes only in {OKAY, SLVERR, DECERR}
- **Cover:** each response type reachable; contention scenario reachable

**`rr_arbiter`**
- `grant` is zero or one-hot; grant only to requesters; no grant when no request
- Lock holds the grant stable
- Bounded fairness: a persistent requester is granted within N−1 other grants (with an assumption that the lock eventually releases)

**`axil_xbar`**
- A slave never sees AW/W from two masters at once; W is only routed to the slave locked by the same master
- B/R responses are routed back only to the owning master
- No deadlock: under assumed well-behaved masters/slaves, every request eventually completes (bounded-liveness check)

**`axil2apb_bridge`**
- `PENABLE` is only high the cycle after `PSEL`; APB address/write/data/strobe stable while `PENABLE && !PREADY`
- `PSEL` drops after completion; exactly one AXI response per APB transfer
- `PSLVERR` always yields `SLVERR`

**`async_fifo` (multiclock)**
- Never writes when full, never reads when empty
- Gray pointers change by one bit at a time
- **Data integrity:** the "magic value" method: an arbitrary tracked value written at an arbitrary point must appear in the correct order at the read side
- Use `multiclock on` and `async2sync` in the `.sby` file as needed

**`sync_fifo`, `apb_timer`**
- FIFO `count` consistent with push/pop, full/empty correct
- Timer: timeout exactly `LOAD+1` cycles after enable; W1C clears

### 11.3 `.sby` files
One per module: `bmc` (depth ≥ 20–30) and `prove` (k-induction) modes plus a `cover` task. Commit them, plus a script that runs all and prints a PASS/FAIL table. Report the **number of properties proven** and the **BMC depth / induction result** on the resume and in the README.

---

## 12. Mutation testing (Yosys `mutate`)

**Purpose:** answer the question "how good is my testbench?" with a number instead of just coverage.

**Flow (`mutation/`):**
1. Choose the RTL scope: `axil_xbar`, `axil_decoder`, `rr_arbiter`, `axil2apb_bridge`, `async_fifo`, `axil_ram`, `axil_csr`.
2. Use Yosys `mutate -list N` to generate a list of N mutations (run `help mutate` for the exact options of your Yosys version); apply each mutation to produce a mutant netlist/RTL.
3. Python driver (`run_mutants.py`): for each mutant, run a **fast regression subset** (smoke + key directed + short random, ~10–30 s) and record `KILLED` (some check failed) or `SURVIVED`.
4. **Mutation score = killed / (total − confirmed equivalent mutants).**
5. **Triage survivors:** classify each as (a) equivalent mutant (no observable behaviour change) or (b) test gap. For every gap, add a test/check and re-run.
6. Report: score before and after improving tests, plus 2–3 concrete examples of "mutant X survived → added test Y → now killed". This is exactly what interviewers love to hear.

Budget: ~200–300 mutants × ~20 s ≈ 1–2 hours per full run on your laptop. Run overnight, not in CI (CI runs a small sampled subset).

---

## 13. Synthesis and STA (Yosys + OpenSTA, SKY130)

### 13.1 Synthesis (`synth/synth.ys`)
Outline:
```
read_verilog -sv <all rtl files>
hierarchy -top amba_fabric_top -chparam RAM_DEPTH 64
synth -top amba_fabric_top -flatten
dfflibmap -liberty sky130_fd_sc_hd__tt_025C_1v80.lib
abc -liberty sky130_fd_sc_hd__tt_025C_1v80.lib -D 10000   # 10 ns target
opt_clean -purge
stat -liberty sky130_fd_sc_hd__tt_025C_1v80.lib
write_verilog -noattr results/amba_fabric_netlist.v
```

### 13.2 Constraints (`synth/amba_fabric.sdc`)
```
create_clock -name clk_sys  -period 10.0 [get_ports clk_sys]
create_clock -name clk_slow -period 24.0 [get_ports clk_slow]
set_clock_groups -asynchronous -group {clk_sys} -group {clk_slow}
set_input_delay  2.0 -clock clk_sys [all_inputs]   ;# exclude clocks/reset as needed
set_output_delay 2.0 -clock clk_sys [all_outputs]
```
Also constrain the Gray-pointer synchronizer paths (e.g. `set_max_delay -datapath_only` or rely on the asynchronous clock groups) and explain this choice in the README.

### 13.3 STA (`synth/sta.tcl`)
```
read_liberty sky130_fd_sc_hd__tt_025C_1v80.lib
read_verilog results/amba_fabric_netlist.v
link_design amba_fabric_top
read_sdc amba_fabric.sdc
report_checks -path_delay max -group_path_count 5
report_checks -path_delay min -group_path_count 5
report_tns
report_wns
report_clock_skew
```
Stretch: repeat at ss (setup) and ff (hold) corners.

### 13.4 Results to report
Cell count, area (µm²), flop count, WNS/TNS at the target period, achieved Fmax (sweep the period until it fails), critical path description (which block and why).

### 13.5 Optional stretch
- **S-02:** gate-level simulation of the netlist on a smoke subset (needs SKY130 functional cell models; use zero-delay).
- **S-03:** OpenLane run (RAM kept small or blackboxed) to produce a DRC/LVS-clean GDSII and a KLayout screenshot.

---

## 14. Continuous integration

`.github/workflows/ci.yml`:
1. Checkout, install OSS CAD Suite (or use cached install), Python venv with `requirements.txt`
2. `make lint` (Verilator `--lint-only -Wall`)
3. `make unit` (L0 tests)
4. `make regress SIM=icarus SEEDS=3` (L1/L2 with a few seeds)
5. `make formal` (all `.sby` tasks)
6. `make mutation-sample` (≈20 mutants as a sanity check)
7. Upload coverage reports and logs as artifacts
8. README badge for the CI status

---

## 15. Repository layout

```
amba-fabric/
├── README.md                    # overview, diagram, how to run, results table, CI badge
├── docs/
│   ├── spec.md                  # this document (trimmed)
│   ├── vplan.md                 # verification plan: feature → test → coverage → check
│   ├── results.md               # coverage tables, formal summary, mutation score, PPA
│   └── img/                     # waveforms, block diagram, coverage screenshots
├── rtl/
│   ├── common/    rst_sync.v  sync_fifo.v  async_fifo.v  rr_arbiter.v
│   ├── axil/      axil_decoder.v  axil_xbar.v  axil_default_slave.v  axil_ram.v  axil_csr.v
│   ├── apb/       axil2apb_bridge.v  apb_decoder.v  apb_uart.v  apb_timer.v  apb_gpio.v
│   ├── cdc/       axil_cdc_bridge.v  slow_regs.v
│   └── amba_fabric_top.v
├── tb/
│   ├── unit/                    # cocotb L0 tests
│   ├── pyuvm/
│   │   ├── agents/              # axil_master, axil_slave, apb_responder, uart, gpio, clk_rst
│   │   ├── env/                 # env, scoreboard, coverage collector, protocol monitor
│   │   ├── sequences/           # directed + random sequences
│   │   └── tests/               # test classes (XB-*, BR-*, UA-*, ...)
│   └── models/                  # addr_map, ram_model, reg_model, peripheral models
├── formal/                      # *_props.v checkers and *.sby files
├── mutation/                    # run_mutants.py, mutant lists, reports
├── synth/                       # synth.ys, amba_fabric.sdc, sta.tcl, results/
├── scripts/                     # merge_cov.py, run_all_formal.sh, report generators
├── Makefile
├── requirements.txt
└── .github/workflows/ci.yml
```

**Makefile targets:** `lint`, `unit`, `regress`, `regress-verilator`, `cov-report`, `formal`, `mutation`, `mutation-sample`, `synth`, `sta`, `clean`.

---

## 16. Phased schedule (about 6 weeks at 10–15 hours/week)

Rule: **write the unit test the same day you write the module.** Do not leave verification to the end.

### Phase 0: Setup (2–3 days)
- [ ] Install toolchain (Section 4), confirm `iverilog`, `verilator`, `yosys`, `sby`, `sta`
- [ ] Hello-world cocotb test + hello-world pyuvm test running together; pin versions
- [ ] Create repo skeleton and Makefile

### Phase 1: Common blocks + AXI-Lite basics (Week 1)
- [ ] `rr_arbiter`, `sync_fifo`, `async_fifo`, `rst_sync` + L0 tests
- [ ] First formal proofs on `rr_arbiter` and `async_fifo`
- [ ] `axil_ram`, `axil_csr`, `axil_default_slave` + simple cocotb read/write driver
- [ ] **Milestone:** write/read RAM and CSR through a single master directly

### Phase 2: Crossbar and APB bridge (Week 2)
- [ ] `axil_decoder`, `axil_xbar`
- [ ] `axil2apb_bridge`, `apb_decoder`, a minimal APB register slave
- [ ] Directed tests XB-01…XB-08, BR-01…BR-03
- [ ] Formal on xbar routing and bridge APB protocol
- [ ] **Milestone:** both masters reach all slaves; waveforms of contention captured

### Phase 3: Peripherals and CDC (Week 3)
- [ ] `apb_uart`, `apb_timer`, `apb_gpio`, IRQ aggregation
- [ ] `axil_cdc_bridge`, `slow_regs`, `amba_fabric_top`
- [ ] Directed tests UA/TM/GP/CS/CD basics
- [ ] **Milestone:** full top-level connectivity test passes

### Phase 4: pyuvm environment (Weeks 3–4)
- [ ] Agents (master, slave responder, APB responder, UART, GPIO, clk/reset)
- [ ] Protocol monitor, scoreboard + reference models
- [ ] Sequences: directed + constrained-random, seed management, watchdogs
- [ ] **Milestone:** XB-13 random stress passes with zero mismatches

### Phase 5: Coverage + formal closure (Week 5)
- [ ] Implement all covergroups, run multi-seed regressions, merge coverage
- [ ] Add tests/constraints for uncovered bins until 100% (document waivers)
- [ ] Verilator code coverage report; investigate holes
- [ ] Complete all `.sby` property sets; record proven-property counts
- [ ] **Milestone:** coverage and formal tables filled in `docs/results.md`

### Phase 6: Mutation, synthesis, CI (Week 6)
- [ ] Mutation flow, score, survivor triage, new tests, re-score
- [ ] Yosys synthesis + OpenSTA, Fmax sweep, report
- [ ] GitHub Actions CI + badge

### Phase 7: Polish (a few days)
- [ ] README with diagram, quick-start (`make regress` in one command), waveform screenshots, results table
- [ ] `vplan.md` and `results.md` finalized
- [ ] Record a 2–3 minute screen capture or add annotated screenshots
- [ ] Resume bullets and interview prep (Sections 18–19)

---

## 17. Deliverables and metrics to showcase

Fill this table in with your **real measured numbers** (do not publish placeholders):

| Metric | Result |
|---|---|
| RTL modules / lines of RTL | |
| Tests (directed / random) | |
| Random transactions executed (total, across seeds) | |
| Seeds passed | |
| Functional coverage (bins hit / total) | |
| Code coverage (line / toggle) | |
| Formal properties proven / BMC depth / k-induction | |
| CDC clock ratios and phases swept | |
| Mutants generated / killed / equivalent / score (before → after) | |
| Bugs found and fixed (list the 3 best with root cause) | |
| Crossbar added latency (cycles) | |
| Synthesis: cells / flops / area (µm²) | |
| STA: WNS/TNS at 10 ns, achieved Fmax | |
| CI status | |

**Bugs found log:** keep `docs/bugs.md` with every real bug (symptom, how it was found: scoreboard / protocol monitor / formal / mutation, root cause, fix). Real bug stories are the most convincing interview material, and a design this size will realistically hit several (W-before-AW handling, lock release timing, FIFO pointer edge cases, reset recovery).

---

## 18. Resume bullets (templates: replace brackets with real results)

**Title line:** *AMBA AXI4-Lite/APB Fabric with pyuvm Verification Environment | SystemVerilog, Python, cocotb, pyuvm, SymbiYosys, Yosys, OpenSTA*

- Designed a parameterized AXI4-Lite 2×4 crossbar with round-robin arbitration, default-error slave, AXI-to-APB bridge, and UART/Timer/GPIO peripherals plus an async-FIFO CDC bridge across two clock domains.
- Built a pyuvm environment (agents, protocol monitor, reference-model scoreboard) with constrained-random sequences; closed [100]% of [N] functional coverage bins and [X]% line coverage across [N] seeds / [N] random transactions.
- Proved [N] protocol, arbiter, bridge, and FIFO-integrity properties with SymbiYosys (BMC + k-induction); found [N] bugs through formal/random testing.
- Measured testbench quality with Yosys-based mutation testing: raised mutation score from [X]% to [Y]% after closing test gaps; automated regression in GitHub Actions.
- Synthesized on SKY130 with Yosys/OpenSTA: [N] cells, [X] µm², timing met at [X] MHz with asynchronous clock-group constraints.

---

## 19. Interview preparation (be able to answer these cold)

1. Walk me through an AXI4-Lite write. Which channels are independent? Why can AW and W arrive in either order?
2. What does your crossbar do if a master sends W before AW? Why is stalling `WREADY` legal?
3. How does your arbiter avoid starvation? How do you prove it?
4. Why Gray-code pointers? Why 2 flops? What can go wrong with multi-bit CDC?
5. How did you constrain the Gray pointer paths in STA, and why are they false paths / max-delay paths?
6. Why pyuvm instead of SystemVerilog UVM, and how do the concepts map (agent, driver, monitor, sequencer, scoreboard, factory/config DB)?
7. What is the difference between code coverage and functional coverage, and why is 100% of either not proof of correctness?
8. What did mutation testing teach you about your own testbench? Give a survivor example.
9. What did formal catch that simulation did not (or the reverse)?
10. Name your best bug: how was it found and what was the root cause?
11. How would you extend this to multiple outstanding transactions or AXI4 full?

---

## 20. Risks and mitigations

| Risk | Mitigation |
|---|---|
| pyuvm/cocotb/Verilator version incompatibility | Use Icarus as the primary simulator, Verilator for coverage; pin versions early (Phase 0) |
| Python-based simulation is slow for huge random runs | Keep random runs ≤ tens of thousands of transactions per test; parallelize seeds across 4–6 threads; use Verilator for long runs |
| Mutation runs too long | Fast regression subset per mutant, run overnight, cap at 200–300 mutants |
| Formal engine blow-up | Prove modules separately, small data widths for formal builds (parameter `DATA_WIDTH=8` in formal config), abstract the RAM |
| SVA support limits in open-source tools | Use immediate-assertion style with `f_past_valid`; keep property count manageable |
| RAM as flops bloats synthesis | `RAM_DEPTH=64` for synthesis or blackbox |
| Scope creep | Ship P0 first; P1/P2 only after the P0 checklist is complete |
| Overselling on resume | Report only numbers you measured; state honestly that it is pyuvm (UVM methodology), not SystemVerilog class UVM |

---

## 21. Definition of Done

- [ ] All P0 features implemented and passing their tests (Section 9)
- [ ] ≥ 20 seeds pass on the full regression with both simulators (or documented reason)
- [ ] Functional coverage 100% of defined bins (waivers documented); code coverage report generated
- [ ] All formal tasks pass; cover traces reachable
- [ ] Mutation score computed with survivor analysis; at least 2 test improvements documented
- [ ] Synthesis + STA reports produced; Fmax stated
- [ ] CI green with badge
- [ ] `README.md`, `vplan.md`, `results.md`, `bugs.md` complete with real numbers and waveform screenshots
- [ ] Resume bullets updated with measured results; repo link on resume

---

## 22. References and learning resources

- **ARM AMBA AXI and ACE Protocol Specification** (AXI4-Lite section) and **AMBA APB Protocol Specification**: free to download from Arm (registration required)
- **Clifford Cummings, "Simulation and Synthesis Techniques for Asynchronous FIFO Design"** (SNUG): the reference async FIFO design
- **ZipCPU blog** (zipcpu.com): practical formal verification of AXI-Lite and other bus designs with SymbiYosys
- **SymbiYosys documentation** (yosyshq.readthedocs.io): `.sby` syntax, multiclock, k-induction, cover
- **cocotb docs** (docs.cocotb.org), **pyuvm** (GitHub: pyuvm/pyuvm), **cocotb-coverage** docs
- **Yosys manual**: `help mutate`, `synth`, `abc`, `stat`
- **OpenSTA documentation**: Tcl commands for `report_checks`, `set_clock_groups`, `read_sdc`
