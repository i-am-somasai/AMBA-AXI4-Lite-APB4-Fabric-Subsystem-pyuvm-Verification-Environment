# AMBA-Fabric Audit Checklist

Generated from `docs/spec.md` as the authoritative verification contract.

## Checklist Item Summary by Spec Section

| Section | Item Count |
|---|---|
| Section 3 | 28 |
| Section 5.2 | 3 |
| Section 5.4 | 3 |
| Section 2 | 1 |
| Section 5.3 | 9 |
| Section 6 | 8 |
| Section 7.1 | 4 |
| Section 7.2 | 14 |
| Section 7.3 | 19 |
| Section 7.4 | 6 |
| Section 7.6 | 1 |
| Section 9.1 | 40 |
| Section 10 | 11 |
| Section 11.2 | 9 |
| Section 11.3 | 1 |
| Section 12 | 4 |
| Section 13.1 | 1 |
| Section 13.2 | 1 |
| Section 13.3 | 1 |
| Section 13.4 | 1 |
| Section 14 | 1 |
| Section 15 | 10 |
| Section 21 | 8 |
| Section 17 | 1 |
| **TOTAL** | **185** |

## Complete Requirement Checklist

| ID | Section | Requirement Description | Priority |
|---|---|---|---|
| F-01 | Section 3 | AXI4-Lite 2Mx4S crossbar with address decode | P0 |
| F-02 | Section 3 | Per-slave round-robin arbiter (separate read/write) with transaction lock | P0 |
| F-03 | Section 3 | Default slave returning DECERR for unmapped addresses (write data consumed, no hang) | P0 |
| F-04 | Section 3 | AXI4-Lite scratch RAM with WSTRB and SLVERR on out-of-range | P0 |
| F-05 | Section 3 | AXI4-Lite CSR block (RO / RW / W1C / WO-set register types, IRQ aggregation) | P0 |
| F-06 | Section 3 | AXI4-Lite -> APB4 bridge (wait states, PSLVERR, PSTRB, PPROT) | P0 |
| F-07 | Section 3 | APB decoder with PSLVERR on unmapped APB address | P0 |
| F-08 | Section 3 | APB UART (8N1, 16x oversampling, TX/RX FIFOs, loopback, framing-error detect) | P0 |
| F-09 | Section 3 | APB Timer (periodic/one-shot, IRQ, W1C status) | P0 |
| F-10 | Section 3 | APB GPIO (direction, 2-FF input sync, rising-edge IRQ, W1C) | P1 |
| F-11 | Section 3 | CDC bridge: request/response Gray-pointer async FIFOs to clk_slow register block | P0 |
| F-12 | Section 3 | Reset synchronizers per clock domain (async assert, sync deassert) | P0 |
| F-13 | Section 3 | Interrupt aggregation to a single irq_o | P1 |
| V-01 | Section 3 | pyuvm environment with 2 AXI-Lite master agents + AXI-Lite slave responder agents + APB responder agent | P0 |
| V-02 | Section 3 | Scoreboards with reference memory/register model | P0 |
| V-03 | Section 3 | Constrained-random + directed sequences (Section 9.4) | P0 |
| V-04 | Section 3 | Functional coverage model (Section 10) closed to 100% | P0 |
| V-05 | Section 3 | Code coverage via Verilator, reported | P0 |
| V-06 | Section 3 | SVA-style protocol checkers: simulation monitors in Python + formal-grade checkers in RTL (ifdef FORMAL) | P0 |
| V-07 | Section 3 | Formal proofs with SymbiYosys (Section 11) | P0 |
| V-08 | Section 3 | CDC ratio/phase sweep tests | P0 |
| V-09 | Section 3 | Mutation testing with Yosys mutate + survivor analysis | P1 |
| V-10 | Section 3 | GitHub Actions CI (regression + coverage artifacts) | P1 |
| S-01 | Section 3 | Yosys synthesis + OpenSTA on SKY130 with async clock groups | P0 |
| S-02 | Section 3 | Gate-level simulation of synthesized netlist (smoke subset) | P2 |
| S-03 | Section 3 | OpenLane run for a GDSII | P2 |
| X-01 | Section 3 | Attach Project 1 RISC-V core as a third master | P2 |
| X-02 | Section 3 | Multiple outstanding transactions with response FIFOs | P2 |
| ARCH-PARAM-01 | Section 5.2 | Top-level parameters: DATA_WIDTH=32, ADDR_WIDTH=32, NUM_MASTERS=2, NUM_SLAVES=4 | P0 |
| ARCH-PARAM-02 | Section 5.2 | RAM_DEPTH parameter: 256 words (1 KB) in simulation, 64 words for synthesis | P0 |
| ARCH-PARAM-03 | Section 5.2 | FIFO_DEPTH: 4 (CDC), 8 (UART); GPIO_WIDTH=16 | P0 |
| ARCH-CLK-01 | Section 5.4 | Two clock domains: clk_sys (100 MHz target) and clk_slow (async) | P0 |
| ARCH-RST-01 | Section 5.4 | Single external async active-low rst_n synchronized into each domain via rst_sync | P0 |
| ARCH-CDC-RULE | Section 5.4 | All CDC signals pass strictly through async FIFOs (data) or 2-FF syncs (status) | P0 |
| ARCH-PORT-RULE | Section 2 | No SV interfaces, classes, or packed structs on module ports | P0 |
| MAP-S0-BASE | Section 5.3 | Slave 0 APB subsystem Base: 0x4000_0000, Size: 64 KB | P0 |
| MAP-S0-UART | Section 5.3 | APB UART Region: 0x4000_0000, Size: 4 KB | P0 |
| MAP-S0-TIMER | Section 5.3 | APB TIMER Region: 0x4000_1000, Size: 4 KB | P0 |
| MAP-S0-GPIO | Section 5.3 | APB GPIO Region: 0x4000_2000, Size: 4 KB | P0 |
| MAP-S0-ERR | Section 5.3 | Unmapped APB addresses return PSLVERR | P0 |
| MAP-S1-RAM | Section 5.3 | Slave 1 Scratch RAM Base: 0x5000_0000, Size: 4 KB (first RAM_DEPTH*4 bytes backed, rest SLVERR) | P0 |
| MAP-S2-CSR | Section 5.3 | Slave 2 CSR Block Base: 0x6000_0000, Size: 256 B (undefined offsets SLVERR) | P0 |
| MAP-S3-CDC | Section 5.3 | Slave 3 CDC Bridge Base: 0x7000_0000, Size: 256 B (undefined offsets SLVERR) | P0 |
| MAP-DEFAULT | Section 5.3 | Default slave covers all unmapped addresses and returns DECERR | P0 |
| AXI-RULE-01 | Section 6 | Source holds VALID and payload stable until READY handshake | P0 |
| AXI-RULE-02 | Section 6 | Master does not wait for READY before VALID; Slave may wait for VALID before READY | P0 |
| AXI-RULE-03 | Section 6 | BVALID asserts only after both AW and W handshakes complete | P0 |
| AXI-RULE-04 | Section 6 | RVALID asserts only after AR handshake completes | P0 |
| AXI-RULE-05 | Section 6 | Exactly one response per transaction (one B per write, one R per read) | P0 |
| AXI-RULE-06 | Section 6 | Address LSBs [1:0] ignored (word-aligned access assumed) | P0 |
| AXI-RULE-07 | Section 6 | Reads and writes are independent channels with no ordering guarantee | P0 |
| AXI-RULE-08 | Section 6 | Responses restricted to OKAY (2'b00), SLVERR (2'b10), DECERR (2'b11); no EXOKAY | P0 |
| RTL-MOD-RSTSYNC | Section 7.1 | rst_sync.v: 2-FF reset synchronizer (async assert, sync deassert) | P0 |
| RTL-MOD-SYNCFIFO | Section 7.1 | sync_fifo.v: Parameterized FIFO with full, empty, count, overflow, underflow | P0 |
| RTL-MOD-ASYNCFIFO | Section 7.1 | async_fifo.v: Dual-clock Gray-pointer FIFO with 2-FF syncs | P0 |
| RTL-MOD-RRARB | Section 7.1 | rr_arbiter.v: Round-robin arbiter with lock and one-hot grant | P0 |
| RTL-MOD-AXILDEC | Section 7.2 | axil_decoder.v: Address decoder with decode_err flag | P0 |
| RTL-MOD-AXILXBAR | Section 7.2 | axil_xbar.v: 2Mx4S crossbar with independent R/W arbiters and transaction lock | P0 |
| RTL-MOD-AXILDEF | Section 7.2 | axil_default_slave.v: Default slave consuming AW/W->DECERR, AR->DECERR, never hangs | P0 |
| RTL-MOD-AXILRAM | Section 7.2 | axil_ram.v: RAM with byte-enable WSTRB, 1-cycle latency, out-of-range SLVERR | P0 |
| RTL-MOD-AXILCSR | Section 7.2 | axil_csr.v: CSR block with RO/RW/W1C/WO-set regs and IRQ aggregation | P0 |
| RTL-MOD-AXIL2APB | Section 7.3 | axil2apb_bridge.v: AXI-to-APB bridge, wait states, PSTRB, PPROT, PSLVERR->SLVERR | P0 |
| RTL-MOD-APBDEC | Section 7.3 | apb_decoder.v: One-hot PSEL from PADDR[15:12], unmapped PSLVERR | P0 |
| RTL-MOD-APBUART | Section 7.3 | apb_uart.v: 8N1 UART, 16x oversampling, TX/RX FIFOs, loopback, frame error, IRQ | P0 |
| RTL-MOD-APBTIMER | Section 7.3 | apb_timer.v: Down-counter, timeout LOAD+1 cycles, periodic/one-shot, W1C status, IRQ | P0 |
| RTL-MOD-APBGPIO | Section 7.3 | apb_gpio.v: Direction, 2-FF input sync, rising-edge IRQ, W1C status | P1 |
| RTL-MOD-AXILCDC | Section 7.4 | axil_cdc_bridge.v: CDC bridge with req/resp async FIFOs (depth 4) | P0 |
| RTL-MOD-SLOWREGS | Section 7.4 | slow_regs.v: clk_slow registers (ID, scratch, free-running counter, ctrl) | P0 |
| RTL-MOD-TOP | Section 7.6 | amba_fabric_top.v: Top-level integrating all modules, M0/M1 ports, clocks, rst_n, IRQ | P0 |
| REG-CSR-ID | Section 7.2 | CSR ID: offset 0x00, RO, reset 0xA3BA0001, writes ignored OKAY | P0 |
| REG-CSR-VERSION | Section 7.2 | CSR VERSION: offset 0x04, RO, reset 0x00010000 | P0 |
| REG-CSR-SCRATCH | Section 7.2 | CSR SCRATCH: offset 0x08, RW, reset 0x00000000, full-word RW | P0 |
| REG-CSR-SCRATCH2 | Section 7.2 | CSR SCRATCH2: offset 0x0C, RW, reset 0x00000000, byte-writable via WSTRB | P0 |
| REG-CSR-IRQRAW | Section 7.2 | CSR IRQ_RAW: offset 0x10, RO, reset 0x0, [0] UART, [1] TIMER, [2] GPIO | P0 |
| REG-CSR-IRQMASK | Section 7.2 | CSR IRQ_MASK: offset 0x14, RW, reset 0x0, per-source enable | P0 |
| REG-CSR-IRQSTATUS | Section 7.2 | CSR IRQ_STATUS: offset 0x18, RO, reset 0x0, IRQ_RAW & IRQ_MASK | P0 |
| REG-CSR-W1CTEST | Section 7.2 | CSR W1C_TEST: offset 0x1C, W1C, reset 0x0, write 1 clears bit | P0 |
| REG-CSR-W1CSET | Section 7.2 | CSR W1C_SET: offset 0x20, WO, writing 1 sets matching bit in W1C_TEST | P0 |
| REG-UART-TXDATA | Section 7.3 | UART TXDATA: offset 0x00, WO, [7:0] pushes TX FIFO, overflow sets TX_OVF | P0 |
| REG-UART-RXDATA | Section 7.3 | UART RXDATA: offset 0x04, RO, [7:0] pops RX FIFO, empty returns 0 | P0 |
| REG-UART-STATUS | Section 7.3 | UART STATUS: offset 0x08, RO/W1C, [0]TX_FULL [1]TX_EMPTY [2]RX_FULL [3]RX_EMPTY [4]FRAME_ERR(W1C) [5]RX_OVF(W1C) [6]TX_OVF(W1C) [7]TX_BUSY | P0 |
| REG-UART-CTRL | Section 7.3 | UART CTRL: offset 0x0C, RW, [0]TX_EN [1]RX_EN [2]LOOPBACK [3]RX_IRQ_EN | P0 |
| REG-UART-BAUDDIV | Section 7.3 | UART BAUDDIV: offset 0x10, RW, [15:0] divisor, tick = clk_sys/(BAUDDIV+1) | P0 |
| REG-TMR-CTRL | Section 7.3 | TIMER CTRL: offset 0x00, RW, [0]EN [1]PERIODIC [2]IRQ_EN | P0 |
| REG-TMR-LOAD | Section 7.3 | TIMER LOAD: offset 0x04, RW, reload value | P0 |
| REG-TMR-VALUE | Section 7.3 | TIMER VALUE: offset 0x08, RO, current count | P0 |
| REG-TMR-STATUS | Section 7.3 | TIMER STATUS: offset 0x0C, W1C, [0]TIMEOUT | P0 |
| REG-GPIO-DIR | Section 7.3 | GPIO DIR: offset 0x00, RW, 1=output | P1 |
| REG-GPIO-OUT | Section 7.3 | GPIO OUT: offset 0x04, RW, output value | P1 |
| REG-GPIO-IN | Section 7.3 | GPIO IN: offset 0x08, RO, 2-FF synchronized gpio_i | P1 |
| REG-GPIO-IRQEN | Section 7.3 | GPIO IRQ_EN: offset 0x0C, RW, per-pin enable | P1 |
| REG-GPIO-IRQSTATUS | Section 7.3 | GPIO IRQ_STATUS: offset 0x10, W1C, rising-edge detect on synchronized IN | P1 |
| REG-SLOW-ID | Section 7.4 | SLOW_ID: offset 0x00, RO, reset 0x510E0001 | P0 |
| REG-SLOW-SCRATCH | Section 7.4 | SLOW_SCRATCH: offset 0x04, RW, WSTRB-aware | P0 |
| REG-SLOW-COUNTER | Section 7.4 | SLOW_COUNTER: offset 0x08, RO, free-running counter in clk_slow | P0 |
| REG-SLOW-CTRL | Section 7.4 | SLOW_CTRL: offset 0x0C, RW, [0] counter enable | P0 |
| TEST-XB-01 | Section 9.1 | XB-01: Single write and read, each master to each mapped slave | P0 |
| TEST-XB-02 | Section 9.1 | XB-02: Write-then-read data integrity on RAM | P0 |
| TEST-XB-03 | Section 9.1 | XB-03: All 16 WSTRB patterns on RAM and CSR scratch | P0 |
| TEST-XB-04 | Section 9.1 | XB-04: Unmapped read and write (several regions + boundary) -> DECERR | P0 |
| TEST-XB-05 | Section 9.1 | XB-05: Both masters to the same slave simultaneously (contention/serialized) | P0 |
| TEST-XB-06 | Section 9.1 | XB-06: Both masters to different slaves simultaneously (parallel completion) | P0 |
| TEST-XB-07 | Section 9.1 | XB-07: Arbitration fairness under sustained contention (diff <= 1) | P0 |
| TEST-XB-08 | Section 9.1 | XB-08: AW before W / W before AW / simultaneous orderings | P0 |
| TEST-XB-09 | Section 9.1 | XB-09: Random READY back-pressure on all channels | P0 |
| TEST-XB-10 | Section 9.1 | XB-10: Delayed BREADY / RREADY response holding | P0 |
| TEST-XB-11 | Section 9.1 | XB-11: SLVERR propagation (RAM out-of-range, CSR undefined, APB error, CDC undefined) | P0 |
| TEST-XB-12 | Section 9.1 | XB-12: Reset during in-flight transaction, then clean recovery | P0 |
| TEST-XB-13 | Section 9.1 | XB-13: Random stress >= 10,000 transactions, 2 masters, 0 mismatches | P0 |
| TEST-XB-14 | Section 9.1 | XB-14: AWPROT/ARPROT pass-through to APB PPROT | P0 |
| TEST-XB-15 | Section 9.1 | XB-15: Unaligned address LSBs [1:0] behave as word-aligned | P0 |
| TEST-BR-01 | Section 9.1 | BR-01: Single write and read, 0 wait states, APB SETUP/ACCESS timing | P0 |
| TEST-BR-02 | Section 9.1 | BR-02: Wait states 1..N random, PENABLE stable, signals held | P0 |
| TEST-BR-03 | Section 9.1 | BR-03: PSLVERR on read and write maps to SLVERR | P0 |
| TEST-BR-04 | Section 9.1 | BR-04: PSTRB patterns match WSTRB | P0 |
| TEST-BR-05 | Section 9.1 | BR-05: Back-to-back mixed read/write from both masters, no starvation | P0 |
| TEST-BR-06 | Section 9.1 | BR-06: Write with W arriving long after AW, bridge waits | P0 |
| TEST-UA-01 | Section 9.1 | UA-01: Loopback: all 256 byte values, RX matches TX | P0 |
| TEST-UA-02 | Section 9.1 | UA-02: TX FIFO full / RX FIFO full / overflow flags and W1C clearing | P0 |
| TEST-UA-03 | Section 9.1 | UA-03: Sweep BAUDDIV, pin-level bit period matches | P0 |
| TEST-UA-04 | Section 9.1 | UA-04: External RX stimulus with bad stop bit sets FRAME_ERR | P0 |
| TEST-UA-05 | Section 9.1 | UA-05: RX IRQ enable/disable follows RX_IRQ_EN & ~RX_EMPTY | P0 |
| TEST-TM-01 | Section 9.1 | TM-01: One-shot countdown, timeout after exactly LOAD+1 cycles | P0 |
| TEST-TM-02 | Section 9.1 | TM-02: Periodic mode, exact LOAD+1 period each time | P0 |
| TEST-TM-03 | Section 9.1 | TM-03: W1C of TIMEOUT, IRQ clear | P0 |
| TEST-GP-01 | Section 9.1 | GP-01: Direction and output value (gpio_o) | P1 |
| TEST-GP-02 | Section 9.1 | GP-02: Input sync latency (2-cycle latency on IN) | P1 |
| TEST-GP-03 | Section 9.1 | GP-03: Rising-edge IRQ + W1C, no false edges | P1 |
| TEST-CS-01 | Section 9.1 | CS-01: Reset values of all CSRs match table | P0 |
| TEST-CS-02 | Section 9.1 | CS-02: RO ignores writes (OKAY), W1C semantics, W1C_SET hook | P0 |
| TEST-CS-03 | Section 9.1 | CS-03: IRQ mask and aggregation to irq_o | P0 |
| TEST-CD-01 | Section 9.1 | CD-01: Data integrity through bridge across ratio/phase sweep (slow < sys, approx, slow > sys) | P0 |
| TEST-CD-02 | Section 9.1 | CD-02: FIFO full/empty boundary behaviour (no overflow/underflow) | P0 |
| TEST-CD-03 | Section 9.1 | CD-03: Reset in either domain at random times, clean recovery | P0 |
| TEST-CD-04 | Section 9.1 | CD-04: SLOW_COUNTER reads increase at clk_slow rate | P0 |
| TEST-CD-05 | Section 9.1 | CD-05: Read/write interleave to slow regs from both masters | P0 |
| COV-CG-TXN | Section 10 | cg_txn covergroup: master (2) x target (5) x op (2) x resp (3) | P0 |
| COV-CG-WSTRB | Section 10 | cg_wstrb covergroup: 16 WSTRB patterns x target (RAM, CSR, slow regs, APB) | P0 |
| COV-CG-ORDER | Section 10 | cg_order covergroup: order (AW first, W first, same) x target | P0 |
| COV-CG-BACKPRESSURE | Section 10 | cg_backpressure covergroup: 5 channels x 4 ready-delay buckets {0, 1, 2-4, 5-16} | P0 |
| COV-CG-CONTENTION | Section 10 | cg_contention covergroup: contention (same slave, diff slave, one idle) x op combo | P0 |
| COV-CG-APB | Section 10 | cg_apb covergroup: wait bucket x PSLVERR x op; PSTRB x op | P0 |
| COV-CG-CDC | Section 10 | cg_cdc covergroup: clock ratio bucket x FIFO occupancy x op | P0 |
| COV-CG-UART | Section 10 | cg_uart covergroup: BAUDDIV bucket x FIFO state; error type | P0 |
| COV-CG-RESET | Section 10 | cg_reset covergroup: reset applied while idle / AW in flight / W in flight / B pending / R pending | P0 |
| COV-CLOSURE-100 | Section 10 | Functional coverage closure: 100% of defined bins hit (waivers documented) | P0 |
| COV-CODE-VERILATOR | Section 10 | Code coverage via Verilator (line + toggle reported) | P0 |
| FORMAL-AXIL-PROPS | Section 11.2 | AXI4-Lite protocol checker: stability, BVALID after AW&W, RVALID after AR, single response | P0 |
| FORMAL-RR-ARBITER | Section 11.2 | rr_arbiter.sby: one-hot grant, priority rotation, lock hold, bounded fairness | P0 |
| FORMAL-AXIL-XBAR | Section 11.2 | axil_xbar.sby: mutual exclusion, W routing to locked slave, response isolation, no deadlock | P0 |
| FORMAL-AXIL2APB | Section 11.2 | axil2apb_bridge.sby: SETUP->ACCESS timing, stability under wait, PSLVERR->SLVERR | P0 |
| FORMAL-ASYNC-FIFO | Section 11.2 | async_fifo.sby: full/empty safety, Gray 1-bit step, magic value data integrity, multiclock | P0 |
| FORMAL-SYNC-FIFO | Section 11.2 | sync_fifo.sby: count consistency, full/empty safety | P0 |
| FORMAL-APB-TIMER | Section 11.2 | apb_timer.sby: timeout after LOAD+1 cycles, reload, W1C status | P0 |
| FORMAL-AXIL-CSR | Section 11.2 | axil_csr.sby: RO constants, W1C status, IRQ aggregation | P0 |
| FORMAL-AXIL-RAM | Section 11.2 | axil_ram.sby: address bounds check, byte strobes, response stability | P0 |
| FORMAL-COVER-TRACES | Section 11.3 | All formal cover traces reachable (vacuity check) | P0 |
| MUT-FLOW-EXISTS | Section 12 | Mutation flow using Yosys mutate + Python driver exists and runs | P1 |
| MUT-SCORE-CALC | Section 12 | Mutation score arithmetic verified: killed / (total - confirmed equivalent) | P1 |
| MUT-SURVIVOR-TRIAGE | Section 12 | Survivor triage into equivalent vs test gap | P1 |
| MUT-IMPROVEMENTS | Section 12 | At least 2 documented survivor -> new test -> killed improvements verified in git | P1 |
| SYNTH-SCRIPT | Section 13.1 | synth/synth.ys synthesizes amba_fabric_top with SKY130 liberty and RAM_DEPTH=64 | P0 |
| SYNTH-SDC | Section 13.2 | synth/amba_fabric.sdc defines clk_sys (10ns), clk_slow (24ns), async clock groups, I/O delays | P0 |
| SYNTH-STA | Section 13.3 | synth/sta.tcl runs OpenSTA timing analysis (WNS, TNS, Fmax sweep) | P0 |
| SYNTH-QUALITY | Section 13.4 | Synthesis/STA quality: reports cell count, flops, area, Fmax, no latches/loops | P0 |
| CI-WORKFLOW | Section 14 | .github/workflows/ci.yml runs lint, unit, regress, formal, mutation-sample, uploads artifacts | P1 |
| REPO-LAYOUT-DOCS | Section 15 | docs/ directory contains spec.md, vplan.md, results.md, img/ | P0 |
| REPO-LAYOUT-RTL | Section 15 | rtl/ directory contains common/, axil/, apb/, cdc/, amba_fabric_top.v | P0 |
| REPO-LAYOUT-TB | Section 15 | tb/ directory contains unit/, pyuvm/, models/ | P0 |
| REPO-LAYOUT-FORMAL | Section 15 | formal/ directory contains *.sby and *_props.v | P0 |
| REPO-LAYOUT-MUTATION | Section 15 | mutation/ directory contains run_mutants.py | P1 |
| REPO-LAYOUT-SYNTH | Section 15 | synth/ directory contains synth.ys, amba_fabric.sdc, sta.tcl | P0 |
| REPO-LAYOUT-SCRIPTS | Section 15 | scripts/ directory contains env.sh, regression scripts | P0 |
| REPO-MAKE-TARGETS | Section 15 | Makefile contains: lint, unit, regress, regress-verilator, cov-report, formal, mutation, mutation-sample, synth, sta, clean | P0 |
| REPO-REQ-PINNED | Section 15 | requirements.txt has pinned package versions | P0 |
| REPO-GITIGNORE | Section 15 | .gitignore excludes build artifacts, .venv, VCDs | P0 |
| DOD-P0-COMPLETE | Section 21 | All P0 features implemented and passing tests | P0 |
| DOD-REGRESS-SEEDS | Section 21 | Multi-seed regression passes with documented seeds on Icarus and Verilator | P0 |
| DOD-COV-CLOSED | Section 21 | Functional coverage 100% of defined bins (waivers documented) and code coverage reported | P0 |
| DOD-FORMAL-PASS | Section 21 | All formal tasks pass with cover traces reachable | P0 |
| DOD-MUTATION-SCORE | Section 21 | Mutation score computed with survivor analysis and >=2 test improvements | P1 |
| DOD-SYNTH-STA | Section 21 | Synthesis + STA reports produced; Fmax stated | P0 |
| DOD-CI-GREEN | Section 21 | CI workflow green with badge in README | P1 |
| DOD-DOCS-COMPLETE | Section 21 | README, vplan, results, bugs complete with real numbers and waveform screenshots | P0 |
| DOD-METRICS-HONEST | Section 17 | All metrics in README, results.md and resume bullets match raw execution logs | P0 |
