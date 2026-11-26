# Independent Adversarial Audit Report — AMBA-Fabric

> Local file paths were replaced with <WORK_DIR> for publication; findings are unchanged.


## 1. Verdict and Rationale

**Verdict:** `NOT READY`

Across 200 independently checked requirements from `docs/spec.md` executed on a clean clone of commit `338fd189f39404a8b220993308e7a93be965b5e4` (`remediation-r2`), the RTL, clean-clone build flow, 400,000-transaction multi-simulator stress runs (20 fresh Icarus seeds `701..720` + 20 Verilator seeds `1..20`), independent black-box probes (`5/5 PASS`), honest functional coverage (`267/267 = 100.00%`), mutation runner, and SKY130 synthesis/OpenSTA reproduction are substantially solid with **0 BLOCKER** findings. However, the computed verdict is **`NOT READY`** due to **16 MAJOR** findings: (1) an unverified remote GitHub Actions CI claim (`CI-REMOTE`/`V-10`/`METRIC-14`/`DOD-07`, `NOT_RUN` because `gh` CLI is absent and claimed run `45602303543` targeted `c46cc77`), (2) `MUT-10` escaping in sanity mutation because `GP-02` (`tb/block/test_apb_gpio.py:51-75`) never asserts `IN==0` after 1 cycle, (3) bounded formal coverage (`bmc` d=20/25/30 rather than unbounded `prove`) on `axil_xbar`, `axil2apb_bridge`, and `axil_cdc_bridge` plus calling 15 depth-10 `EQUIV_BMC10` miters 'proven equivalent' (`FORMAL-WORDING`/`MUT-EQUIV-CLAIM`), and (4) an inaccurate published S0 APB address range in `README.md:108` (`0x4000_0000 - 0x4FFF_FFFF` vs RTL 64 KB `0x4000_0000 - 0x4000_FFFF`).

## 2. Scorecard

| Audit Area | Total | PASS | FAIL | PARTIAL | NOT_FOUND | NOT_RUN | N/A |
|---|---:|---:|---:|---:|---:|---:|---:|
| RTL, Address Map & Registers | 75 | 67 | 0 | 3 | 0 | 1 | 4 |
| Test Fidelity (Sec 9.1) | 40 | 33 | 0 | 7 | 0 | 0 | 0 |
| Coverage Honesty | 14 | 12 | 0 | 2 | 0 | 0 | 0 |
| Formal Verification | 12 | 4 | 1 | 7 | 0 | 0 | 0 |
| Mutation & Sanity | 15 | 12 | 1 | 1 | 1 | 0 | 0 |
| Seeds & Stress | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| Synthesis & STA | 4 | 4 | 0 | 0 | 0 | 0 | 0 |
| CI & Clean Clone & Layout | 16 | 9 | 2 | 4 | 0 | 1 | 0 |
| Metric Honesty & DoD | 23 | 16 | 0 | 5 | 0 | 2 | 0 |
| **Overall** | 200 | 158 | 4 | 29 | 1 | 4 | 4 |

- **Checklist totals (Step 1):** 28 Feature IDs (`F-01..13`, `V-01..10`, `S-01..03`, `X-01..02`), 8 Address Map entries, 27 Registers, 7 AXI4-Lite Rules, 40 Spec Tests, 9 Covergroups + Code Cov, 10 SBY Formal Suites + 11 Property Sets, 14 Metric Rows, 9 DoD Items (plus independent probes, sanity mutations, and documentation checks = 200 rows).

## 3. Environment

- **Audit Date:** 2026-11-25
- **Audited Commit / Branch:** `338fd189f39404a8b220993308e7a93be965b5e4` (`remediation-r2`)
- **Clone Location:** `<WORK_DIR>/audit_clone` (`208` committed files via `git ls-files`); heavy build artifacts isolated under `<WORK_DIR>/audit_build`
- **Host Machine:** Linux, 6.6 GiB RAM + 4.0 GiB swap (max 4 parallel jobs enforced, no `sudo`)
- **Toolchain (`scripts/env.sh` + `make env-check`):**
  - `iverilog`: Icarus Verilog `14.0 (devel) (s20260301-1260-gfd4a65b20-dirty)`
  - `verilator`: Verilator `5.055 devel rev v5.054-354-g005ee501b`
  - `yosys`: `Yosys 0.71+77` (`clang++ 21.1.8`)
  - `sby`: `SBY v0.71-7-gb21f778` with Boolector
  - `sta`: OpenSTA `2.6.0` with SKY130 HD `sky130_fd_sc_hd__tt_025C_1v80.lib`
  - `python3`: Python `3.11.6`, `cocotb 2.1.0.dev0+41564633`, `pyuvm 5.0.0`, `cocotb_coverage 2.0`; `gh` CLI **not installed**
- **Fresh Seeds Used (not in repo logs):** `901` (unit/block), `902` (reachability exp), `701..720` (20 fresh Icarus stress seeds = 200,000 txns), plus clean `1..20` Verilator `make cov-report` run

## 4. Clean-Clone Reproducibility

- `make lint`: **PASS** (`EXIT=0`, log `<WORK_DIR>/audit_work/audit_logs/step2_lint.log`)
- `make unit SIM=icarus`: **PASS** (`14/14` across 9 modules, `EXIT=0`, log `<WORK_DIR>/audit_work/audit_logs/step2_unit.log`)
- `make block SIM=icarus`: **PASS** (`38/38` across 7 suites, `EXIT=0`, log `<WORK_DIR>/audit_work/audit_logs/step2_block.log`)
- `make regress SIM=icarus SEEDS=1`: **PASS** (`77/77` XML testcases total with unit+block, `EXIT=0`, log `<WORK_DIR>/audit_work/audit_logs/step2_regress_s1.log`). Note: top-level `Makefile:78` does not quote `SEEDS=$(SEEDS)`, so passing space-separated multi-seed lists fails at top level (`make -C tb/pyuvm SEEDS='701..720' regress` succeeds).
- `make formal`: **PASS** (`10/10` SBY tasks, `84` covers in `160s`, `EXIT=0`, log `<WORK_DIR>/audit_work/audit_logs/step2_formal.log`)
- `git grep -n "<WORK_DIR>/"`: **PASS** (0 hardcoded personal paths in active RTL/TB/synth/scripts; `<WORK_DIR>/audit_work/audit_logs/step2_home_grep.log`)

## 5. Feature Matrix (F-, V-, S-, X-)

| ID | Priority | Requirement | Status | Severity | Measured / Notes |
|---|---|---|---|---|---|
| F-01 | P0 | AXI4-Lite 2Mx4S crossbar with address decode | PASS | NONE | 2x4 crossbar + default slave decode verified (XB-01..15 + BMC depth 20) |
| F-02 | P0 | Per-slave round-robin arbiter (separate R/W) with transaction lock | PARTIAL | MINOR | Inline wr_prio/rd_prio pass fairness; rr_arbiter standalone proved d=20 (DEC-007) |
| F-03 | P0 | Default slave returning DECERR for unmapped addresses (W consumed, no hang) | PASS | NONE | DECERR (2'b11) returned on AW/W/AR unmapped without hang |
| F-04 | P0 | AXI4-Lite scratch RAM with WSTRB and SLVERR on out-of-range | PASS | NONE | WSTRB byte masking and out-of-range SLVERR verified (unit, BMC d=20, probe) |
| F-05 | P0 | AXI4-Lite CSR block (RO/RW/W1C/WO-set, IRQ aggregation) | PASS | NONE | All 9 CSR offsets (ID..W1C_SET) verified in CS-01..04, prv+bmc, probe |
| F-06 | P0 | AXI4-Lite -> APB4 bridge (wait states, PSLVERR, PSTRB, PPROT) | PASS | NONE | BR-01..08 and BMC d=25 pass across wait states, PSLVERR, PSTRB, PPROT |
| F-07 | P0 | APB decoder with PSLVERR on unmapped APB address | PASS | NONE | One-hot PSEL (paddr[15:12]==0/1/2) and unmapped PSLVERR verified |
| F-08 | P0 | APB UART (8N1, 16x oversampling, TX/RX FIFOs, loopback, frame error) | PASS | NONE | 8-entry TX/RX sync_fifo loopback, baud sweep, framing error, overflow verified |
| F-09 | P0 | APB Timer (periodic/one-shot, IRQ, W1C status) | PASS | NONE | LOAD+1 timeout proved unboundedly via apb_timer prove d=20 and verified in TM-01..03 |
| F-10 | P1 | APB GPIO (direction, 2-FF input sync, rising-edge IRQ, W1C) | PASS | NONE | RTL 2-FF sync verified by probe PROBE-04 (0 after 1 cycle, value after 2) |
| F-11 | P0 | CDC bridge: request/response Gray-pointer async FIFOs to clk_slow regs | PASS | NONE | Dual-clock CDC verified across 25ns/10.3ns/6.0ns ratios, async reset, BMC d=25/30 |
| F-12 | P0 | Reset synchronizers per clock domain (async assert, sync deassert) | PASS | NONE | 2-FF async assert/sync deassert works functionally in sim; pre-layout reset net unbuffered in STA |
| F-13 | P1 | Interrupt aggregation to a single irq_o | PASS | NONE | irq_o = |(irq_sources & reg_irq_mask) verified in CS-03 and test_top02 |
| V-01 | P0 | pyuvm env with 2 AXI-Lite master agents + slave/APB responder agents | PARTIAL | MINOR | Only 2 AXI-Lite masters are uvm_agent classes; slave/peripheral models are plain Python |
| V-02 | P0 | Scoreboards with reference memory/register model | PASS | NONE | 0 mismatches across directed, 20 Icarus seeds (701..720), and 20 Verilator seeds |
| V-03 | P0 | Constrained-random + directed sequences (Section 9.4) | PASS | NONE | Directed + coverage-closure + 10k-txn random stress pass across all 20 fresh seeds |
| V-04 | P0 | Functional coverage model (Section 10) closed to 100% | PASS | NONE | 267/267 reachable bins hit (100.00%, 36 waived), zero synthetic sample_* calls |
| V-05 | P0 | Code coverage via Verilator, reported | PASS | NONE | Line 92.4% (496/537), Branch 91.6% (501/547), Expr 93.8%, Toggle 76.2% |
| V-06 | P0 | SVA-style protocol checkers: Python monitors + RTL ifdef FORMAL | PASS | NONE | Python AXI4-Lite monitor + formal immediate assertions active across all key blocks |
| V-07 | P0 | Formal proofs with SymbiYosys (Section 11) | PARTIAL | MAJOR | 10/10 suites pass (84 covers, 160s), but 6 suites (incl. xbar/bridge/cdc) are BMC only |
| V-08 | P0 | CDC ratio/phase sweep tests | PASS | NONE | Sweeps slow periods 25.0ns, 10.3ns, 6.0ns across multiple phases (CD-01 + pyuvm) |
| V-09 | P1 | Mutation testing with Yosys mutate + survivor analysis | PASS | NONE | 205/240 raw killed (85.42%) reproduced cleanly |
| V-10 | P1 | GitHub Actions CI (regression + coverage artifacts) | NOT_RUN | MAJOR | gh CLI absent; remote run 45602303543 (on c46cc77, before HEAD 338fd18) unverified |
| S-01 | P0 | Yosys synthesis + OpenSTA on SKY130 with async clock groups | PASS | NONE | Reproduced 9237 cells, 3630 flops, 138086.19 um^2, full WNS -18.60ns (34.97 MHz) |
| S-02 | P2 | Gate-level simulation of synthesized netlist (smoke subset) | N/A | NONE | Not implemented (out-of-scope P2 stretch) |
| S-03 | P2 | OpenLane run for a GDSII | N/A | NONE | Not implemented (out-of-scope P2 stretch) |
| X-01 | P2 | Attach Project 1 RISC-V core as a third master | N/A | NONE | Not implemented (out-of-scope P2 stretch) |
| X-02 | P2 | Multiple outstanding transactions with response FIFOs | N/A | NONE | Not implemented (out-of-scope P2 stretch) |

## 6. Test Matrix (All 40 Spec 9.1 IDs)

| Spec ID | Function | File:Line | Fidelity | Result | Seed | Log File | Fidelity Rationale |
|---|---|---|---|---|---|---|---|
| XB-01 | `test_xb01_single_rw_each_master_to_each_slave` | `tb/block/test_axil_xbar.py:145` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Exercises M0 and M1 single reads/writes to all 4 mapped slaves on axil_xbar with per-slave address/data checks. |
| XB-02 | `test_xb02_ram_data_integrity` | `tb/block/test_axil_xbar.py:180` | partial | PARTIAL | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Verifies S1 data integrity on axil_xbar against Python AxilSlaveResponder rather than axil_ram RTL (RTL covered in L0/L2). |
| XB-03 | `test_xb03_wstrb_patterns` | `tb/block/test_axil_xbar.py:205` | partial | PARTIAL | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Drives all 16 WSTRB values across S1/S2 against AxilSlaveResponder in L1; real axil_ram/axil_csr RTL strobes tested in test_sys_strobe_patterns. |
| XB-04 | `test_xb04_unmapped_decerr` | `tb/block/test_axil_xbar.py:248` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Tests unmapped boundary addresses across 0x0000_0000..0xFFFF_FFFC confirming DECERR (0b11) and write-data consumption. |
| XB-05 | `test_xb05_contention_same_slave` | `tb/block/test_axil_xbar.py:277` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Launches M0 and M1 concurrently targeting S1, verifying serialization without corruption and full completion. |
| XB-06 | `test_xb06_parallel_different_slaves` | `tb/block/test_axil_xbar.py:311` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Launches M0->S0 and M1->S1 simultaneously and checks parallel cycle latency without cross-slave serialization. |
| XB-07 | `test_xb07_arbitration_fairness` | `tb/block/test_axil_xbar.py:341` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Holds sustained M0+M1 contention on read and write channels and checks running grant imbalance <= 1 (catches MUT-01 & SMUT-10). |
| XB-08 | `test_xb08_write_orderings` | `tb/block/test_axil_xbar.py:507` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Exercises aw_first, w_first, and simultaneous write arrival orders across masters with full data/response checking. |
| XB-09 | `test_xb09_random_ready_backpressure` | `tb/block/test_axil_xbar.py:530` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Injects randomized slave AWREADY/WREADY/ARREADY stalls and verifies zero dropped or duplicated transactions. |
| XB-10 | `test_xb10_delayed_bready_rready_stability` | `tb/block/test_axil_xbar.py:577` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Holds BREADY=0 / RREADY=0 for multi-cycle delays and monitors bus stability until master handshake. |
| XB-11 | `test_xb11_slverr_propagation` | `tb/pyuvm/tests/test_directed.py:51` | yes | PASS | SEED=1 | `<WORK_DIR>/audit_work/audit_logs/step2_regress_s1.log` | Top-level pyuvm test drives RAM out-of-range, CSR undefined, APB unmapped, and CDC undefined confirming SLVERR routing. |
| XB-12 | `test_xb12_reset_recovery` | `tb/pyuvm/tests/test_directed.py:126` | yes | PASS | SEED=1 | `<WORK_DIR>/audit_work/audit_logs/step2_regress_s1.log` | Asserts reset mid-flight across AW/W/B/R phases on amba_fabric_top, recovers cleanly, and passes post-reset transactions (kills SMUT-14). |
| XB-13 | `test_xb13_stress` | `tb/pyuvm/tests/test_stress.py:14` | yes | PASS | SEEDS=701..720 | `<WORK_DIR>/audit_work/audit_logs/step11_regress_20seeds.log` | Executes 10,000 randomized concurrent 2-master transactions per seed on amba_fabric_top with 0 scoreboard mismatches across 20 fresh seeds. |
| XB-14 | `test_xb14_prot_passthrough` | `tb/pyuvm/tests/test_directed.py:66` | yes | PASS | SEED=1 | `<WORK_DIR>/audit_work/audit_logs/step2_regress_s1.log` | Verifies AWPROT/ARPROT propagation to APB PPROT across combinations (kills SMUT-09). |
| XB-15 | `test_xb15_unaligned_address` | `tb/pyuvm/tests/test_directed.py:81` | yes | PASS | SEED=1 | `<WORK_DIR>/audit_work/audit_logs/step2_regress_s1.log` | Verifies Rule 6 [1:0] word-alignment on RAM, CSR (BUG-023), APB, and CDC (kills SMUT-11). |
| BR-01 | `test_br01_single_rw_zero_wait` | `tb/block/test_axil2apb_bridge.py:43` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Tests 0-wait APB write and read on axil2apb_bridge checking PPROT/PSTRB/data and zero-wait protocol completion (kills MUT-07 & SMUT-07). |
| BR-02 | `test_br02_wait_states` | `tb/block/test_axil2apb_bridge.py:137` | partial | PARTIAL | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Sweeps wait states ws=[1,2,4] checking data integrity, while cycle-by-cycle PENABLE/control hold is verified in formal props rather than Python test body. |
| BR-03 | `test_br03_pslverr_propagation` | `tb/block/test_axil2apb_bridge.py:177` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Injects PSLVERR=1 on APB read and write and asserts AXI SLVERR (2'b10) (kills MUT-04 & SMUT-04). |
| BR-04 | `test_br04_pstrb_patterns` | `tb/block/test_axil2apb_bridge.py:214` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Tests all 16 WSTRB values on writes (PSTRB==WSTRB) and verifies PSTRB==0 on reads. |
| BR-05 | `test_br05_back_to_back_mixed_rw` | `tb/block/test_axil2apb_bridge.py:261` | partial | PARTIAL | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | vplan cites only single-master axil2apb_bridge back-to-back mixed R/W; dual-master (M0+M1) APB mixed R/W exists separately at test_amba_fabric_top.py:370. |
| BR-06 | `test_br06_delayed_w_no_early_psel` | `tb/block/test_axil2apb_bridge.py:341` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Stalls WVALID for 6 cycles after AW handshake and explicitly asserts PSEL stays 0 until W completes. |
| UA-01 | `test_ua01_loopback_bytes` | `tb/block/test_apb_uart.py:25` | partial | PARTIAL | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Spec Sec 9.1 specifies all 256 byte values, whereas test_ua01 loops only 8 bytes [0x55,0xAA,0x00,0xFF,0x3C,0xC3,0x12,0x89] (all 8 bit positions hit). |
| UA-02 | `test_ua02_fifo_full_and_overflow_flags` | `tb/block/test_apb_uart.py:61` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Fills 8-entry TX and RX FIFOs, triggers TX_OVF/RX_OVF, and checks W1C flag clearing (kills SMUT-12). |
| UA-03 | `test_ua03_bauddiv_sweep` | `tb/block/test_apb_uart.py:136` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Sweeps BAUDDIV=[1,3] and measures pin-level uart_tx bit period against 16*(BAUDDIV+1) cycles. |
| UA-04 | `test_ua04_framing_error` | `tb/block/test_apb_uart.py:220` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Drives external uart_rx frame with stop_bit=0, checks FRAME_ERR=1 and W1C clearing. |
| UA-05 | `test_ua05_rx_irq` | `tb/block/test_apb_uart.py:176` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Verifies uart_irq tracks RX_IRQ_EN & ~RX_EMPTY across enable, empty, and pop transitions. |
| TM-01 | `test_tm01_oneshot_countdown` | `tb/block/test_apb_timer.py:23` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Loads LOAD=10, enables one-shot, and asserts exact 11-cycle (LOAD+1) timeout and EN self-clear (kills MUT-05 & SMUT-05). |
| TM-02 | `test_tm02_periodic_countdown` | `tb/block/test_apb_timer.py:67` | partial | PARTIAL | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Runs 3 periodic iterations checking timer_irq==1 within <20 cycles, never asserting exact LOAD+1 period each cycle. |
| TM-03 | `test_tm03_w1c_timeout_and_irq_clear` | `tb/block/test_apb_timer.py:99` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Checks W1C write to STATUS clears TIMEOUT and deasserts timer_irq. |
| GP-01 | `test_gp01_direction_and_out` | `tb/block/test_apb_gpio.py:25` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Programs DIR and OUT across alternating patterns and verifies gpio_dir and gpio_o pins. |
| GP-02 | `test_gp02_input_sync_latency` | `tb/block/test_apb_gpio.py:51` | partial | PARTIAL | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Drives gpio_i=0xBEEF and reads IN after 2 cycles, never asserting IN==0 after 1 cycle; allowed our 1-FF bug MUT-10 to survive. |
| GP-03 | `test_gp03_rising_edge_irq_and_w1c` | `tb/block/test_apb_gpio.py:78` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Triggers masked/unmasked rising edges, tests IRQ_STATUS W1C clear, and verifies falling edges do not re-trigger. |
| CS-01 | `test_cs01_reset_values` | `tb/unit/test_axil_csr.py:28` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_unit_s901.log` | Reads all CSR offsets after reset confirming ID=0xA3BA0001, VERSION=0x00010000, RW regs=0, undefined=SLVERR. |
| CS-02 | `test_cs02_access_types_w1c` | `tb/unit/test_axil_csr.py:71` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_unit_s901.log` | Checks RO writes ignored with OKAY, WSTRB on SCRATCH2, W1C_SET->W1C_TEST set/clear semantics (kills MUT-09). |
| CS-03 | `test_cs03_irq_aggregation` | `tb/unit/test_axil_csr.py:152` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_unit_s901.log` | Drives irq_sources[2:0] and IRQ_MASK combinations verifying IRQ_RAW, IRQ_STATUS, and irq_o. |
| CD-01 | `test_cd01_ratio_phase_sweep` | `tb/block/test_axil_cdc_bridge.py:48` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Sweeps slow/sys ratios (~1/1.3, 1/3, 1/7, 5/3) and phases on axil_cdc_bridge verifying R/W integrity and SLVERR. |
| CD-02 | `test_cd02_async_fifo_stream` | `tb/unit/test_async_fifo.py:129` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_unit_s901.log` | Streams dual-clock patterns through async_fifo checking full/empty/overflow/underflow boundaries (paired with unit overflow test & BMC). |
| CD-03 | `test_cd03_reset_recovery` | `tb/block/test_axil_cdc_bridge.py:87` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Applies independent rst_sys_n and rst_slow_n resets mid-transaction per DEC-008 and verifies clean post-reset R/W recovery (kills SMUT-15). |
| CD-04 | `test_cd04_free_running_counter` | `tb/block/test_axil_cdc_bridge.py:192` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | Reads SLOW_COUNTER at controlled intervals verifying increment rate tracks clk_slow frequency and SLOW_CTRL[0] gating. |
| CD-05 | `test_cd05_dual_master_slow_regs` | `tb/block/test_amba_fabric_top.py:332` | yes | PASS | SEED=901 | `<WORK_DIR>/audit_work/audit_logs/step4_block_s901.log` | M0 and M1 interleave reads/writes to S3 slow_regs through full top-level crossbar + CDC bridge. |

- **Unmapped tests present (21 additional decorated tests beyond the 40 Spec IDs):** `test_hello_world`, `test_rst_sync_basic`, `test_sync_fifo_all`, `test_axil_decoder_all`, `test_axil_default_slave_all`, `test_axil_ram_operations`, `test_rr_arbiter_fairness_and_lock`, `test_async_fifo_dual_clock`, `test_async_fifo_overflow_preserve`, `test_cs04_ooo_w1c32_ro_wo_and_backpressure`, `test_xb11_all_targets_contention_and_backpressure`, `test_br07_apb_wait_err_cov`, `test_br08_addr_walk_and_ooo_backpressure`, `test_cd_slow_id_and_unmapped`, `test_top01_register_map_connectivity`, `test_top02_irq_aggregation_to_pin`, `test_br05_dual_master_apb_mixed_rw`, `test_sys_write_ordering`, `test_sys_strobe_patterns`, `test_sys_contention`, `TestCoverageClosure`.

## 7. vplan Truthfulness Table

- Verified all **40/40** Spec test rows and **13/13** feature rows in `docs/vplan.md`: every cited Python file and function exists via AST parse (`0` broken citations, `docs/test_map.csv` `40/40` aligned), and all `40` functions passed on fresh seeds `901` / `1` / `701..720` (`0` outright false PASS claims / `0` BLOCKERs). However, `7` vplan PASS rows have **partial** scenario fidelity (`GP-02` `MAJOR`; `UA-01`, `TM-02`, `BR-02`, `BR-05`, `XB-02`, `XB-03` `MINOR`).

## 8. Coverage Honesty

- **Sample-call audit:** `grep -rn 'sample_' tb/` confirms ZERO calls outside `tb/pyuvm/func_cov/fabric_cov.py` and `tb/pyuvm/monitors/fabric_monitors.py` (`make lint` `check_no_synthetic_cov.sh` PASS).

- **Monitor signal provenance:** `cg_txn`, `cg_wstrb`, `cg_order`, `cg_backpressure`, `cg_contention` are fed by live AXI4-Lite signal sampling in `FabricMonitor`; `cg_apb` by APB interface monitor (`ApbMonitor` / block collector); `cg_cdc` by `CdcMonitor` observing `clk_slow`/`clk_sys` periods and FIFO full/empty signals; `cg_uart` by UART monitor; `cg_reset` by `ResetMonitor`.

- **Reachability experiments:**

  1. Fixed single clock ratio `CLK_SLOW_PERIOD_NS=25.0` (`SEED=901`, `<WORK_DIR>/audit_work/audit_logs/step6_reach_ratio.log`): `cg_cdc.ratio = {'approx_equal': 0, 'slow<sys': 3024, 'slow>sys': 0}` -> unhit bins stayed 0.

  2. Disabled UART bad stop-bit stimulus in isolated copy (`SEED=902`, `<WORK_DIR>/audit_work/audit_logs/step6_reach_no_ferr.log`): `cg_uart.err = {'frame_err': 0, 'none': 172, 'overflow': 0}` -> `frame_err` stayed 0.

- **Claimed vs Measured Functional & Code Coverage:**

  - Functional: **267/267 (100.00%)** reproduced cleanly (`<WORK_DIR>/audit_work/audit_logs/step6_func_cov.log`; note `docs/coverage_waivers.md:10-20` summary table lists `224`/`188` cross-only bins instead of `303`/`267`). All `36` waivers are architecturally unreachable/illegal.

  - Verilator Code Coverage (`<WORK_DIR>/audit_work/audit_logs/step6_code_cov_summary.txt`): Measured **Line 92.4% (496/537)**, **Branch 91.6% (501/547)**, **Expr 93.8% (1036/1105)**, **Toggle 76.2% (10821/14202)**, **FSM State 100.0% (5/5)**, **FSM Arc 25.0% (1/4)** (vs `docs/logs/code_cov_summary.txt`: `92.0%` line / `74.8%` toggle due to unseeded `test_directed` & `test_axil2apb_bridge` runs). Largest uncovered Verilator regions: `axil_csr.v` (19 points: RO writes/WO read/below-10-hit lines), `apb_uart.v` (15 points: `reg_frame_err`, `reg_rx_ovf`, 3 mid-TX->IDLE FSM arcs), `apb_gpio.v` (10 points: `gpio_i`/2-FF sync in top-level stress), `slow_regs.v` (9 points), `axil_ram.v` (8 points).

## 9. Formal Verification

| Suite | Mode | Depth | Solver | Result | Covers | Runtime | Notes |
|---|---|---:|---|---|---:|---:|---|
| `apb_timer.sby` | `prove` | 20 | boolector | PASS | 4 | 1s | Unbounded k-induction; LOAD+1 and W1C proved |
| `sync_fifo.sby` | `prove` | 20 | boolector | PASS | 8 | 3s | Unbounded k-induction; (* anyconst *) magic data order proved |
| `rr_arbiter.sby` | `prove` | 20 | boolector | PASS | 3 | 1s | Unbounded k-induction; standalone per DEC-007 |
| `axil_csr.sby` | `prv+bmc` | 20 | boolector | PASS | 5 | 3s | CHECK_CAUSALITY=0 in prove, 1 in BMC (DEC-006) |
| `axil_ram.sby` | `bmc` | 20 | boolector | PASS | 5 | 3s | Bounded d=20, RAM_DEPTH=16 |
| `axil_xbar.sby` | `bmc` | 20 | boolector | PASS | 31 | 45s | Bounded d=20; routing, lock, and bounded liveness |
| `apb_uart.sby` | `bmc` | 25 | boolector | PASS | 9 | 5s | Bounded d=25 |
| `async_fifo.sby` | `bmc` | 25 | boolector | PASS | 4 | 8s | Multiclock bounded d=25; Gray + magic value |
| `axil2apb_bridge.sby` | `bmc` | 25 | boolector | PASS | 10 | 6s | Bounded d=25; SETUP/ACCESS/PSLVERR/bounded liveness |
| `axil_cdc_bridge.sby` | `bmc` | 30 | boolector | PASS | 5 | 85s | Multiclock bounded d=30; dual reset behavior |

- **Vacuity & Covers:** Every `.sby` is run by `make formal` and every `*_props.v` is instantiated (`axil_props`, `axil_xbar_props`, `axil2apb_bridge_props`, `rr_arbiter_props`, `sync_fifo_props`). All 84 cover traces (including all response types, multi-master contention, bounded fairness wait limits) were reached.
- **Assumptions review:** AXI4-Lite VALID/payload stability and 1-outstanding count limits in `axil_props.v`, well-behaved environment handshake release (`f_*_wait >= 4`) for bounded liveness, reset sequencing (`!f_past_valid => !rst_n`), and `async_fifo` full/empty guard assumptions match spec contracts; `axil_xbar_props.v:222-226` assumes valid signals are 0 while `!rst_n`.
- **Bounded liveness:** Bounded request completion is checked in `axil_xbar_props.v:507-571` and `axil2apb_bridge_props.v:243-302` under bounded ready-wait assumptions, only up to BMC depth 20/25.
- **Wording check:** `README.md` formal section accurately distinguishes `prove` vs `bmc`, **HOWEVER** `README.md:173` and `docs/mutation_report.md:24,46` claim `21 are proven equivalent` when `15` use bounded `EQUIV_BMC10` (`d=10`) (**MAJOR** `FORMAL-WORDING`).

## 10. Register Comparison & Protocol/Structure Compliance

| Block | Offset | Register | Access | Reset Value | RTL Evidence | Match Spec? |
|---|---|---|---|---|---|---|
| `axil_csr` | `0x00` | `ID` | RO | `0xA3BA0001` | `rtl/axil/axil_csr.v:44,112,172` | **YES** |
| `axil_csr` | `0x04` | `VERSION` | RO | `0x00010000` | `rtl/axil/axil_csr.v:45,115,176` | **YES** |
| `axil_csr` | `0x08` | `SCRATCH` | RW | `0x00000000` | `rtl/axil/axil_csr.v:51,85,118,180` | **YES** |
| `axil_csr` | `0x0C` | `SCRATCH2` | RW (WSTRB) | `0x00000000` | `rtl/axil/axil_csr.v:52,86,122,184` | **YES** |
| `axil_csr` | `0x10` | `IRQ_RAW` | RO | `0x00000000` | `rtl/axil/axil_csr.v:56,129,188` | **YES** |
| `axil_csr` | `0x14` | `IRQ_MASK` | RW | `0x00000000` | `rtl/axil/axil_csr.v:53,87,132,192` | **YES** |
| `axil_csr` | `0x18` | `IRQ_STATUS` | RO | `0x00000000` | `rtl/axil/axil_csr.v:57,136,196` | **YES** |
| `axil_csr` | `0x1C` | `W1C_TEST` | W1C | `0x00000000` | `rtl/axil/axil_csr.v:54,88,139,200` | **YES** |
| `axil_csr` | `0x20` | `W1C_SET` | WO (reads 0) | `n/a` | `rtl/axil/axil_csr.v:143,204` | **YES** |
| `apb_uart` | `0x00` | `TXDATA` | WO | `n/a (reads 0)` | `rtl/apb/apb_uart.v:345,374,423` | **YES** |
| `apb_uart` | `0x04` | `RXDATA` | RO | `0x00000000` | `rtl/apb/apb_uart.v:357,363,424` | **YES** |
| `apb_uart` | `0x08` | `STATUS` | RO/W1C [6:4] | `0x0A (TX/RX empty)` | `rtl/apb/apb_uart.v:265,410,425` | **YES** |
| `apb_uart` | `0x0C` | `CTRL` | RW [3:0] | `0x0` | `rtl/apb/apb_uart.v:387,426` | **YES** |
| `apb_uart` | `0x10` | `BAUDDIV` | RW [15:0] | `16'h0000` | `rtl/apb/apb_uart.v:383,388,427` | **YES** |
| `apb_timer` | `0x00` | `CTRL` | RW [2:0] | `0x0` | `rtl/apb/apb_timer.v:70,104` | **YES** |
| `apb_timer` | `0x04` | `LOAD` | RW | `0x00000000` | `rtl/apb/apb_timer.v:77,105` | **YES** |
| `apb_timer` | `0x08` | `VALUE` | RO | `0x00000000` | `rtl/apb/apb_timer.v:80,106` | **YES** |
| `apb_timer` | `0x0C` | `STATUS` | W1C [0] | `0x0` | `rtl/apb/apb_timer.v:82,107` | **YES** |
| `apb_gpio` | `0x00` | `DIR` | RW [15:0] | `0x0000` | `rtl/apb/apb_gpio.v:79,105` | **YES** |
| `apb_gpio` | `0x04` | `OUT` | RW [15:0] | `0x0000` | `rtl/apb/apb_gpio.v:80,106` | **YES** |
| `apb_gpio` | `0x08` | `IN` | RO [15:0] | `2-FF sync` | `rtl/apb/apb_gpio.v:81,107` | **YES** |
| `apb_gpio` | `0x0C` | `IRQ_EN` | RW [15:0] | `0x0000` | `rtl/apb/apb_gpio.v:82,108` | **YES** |
| `apb_gpio` | `0x10` | `IRQ_STATUS` | W1C [15:0] | `0x0000` | `rtl/apb/apb_gpio.v:83,109` | **YES** |
| `slow_regs` | `0x00` | `SLOW_ID` | RO | `0x510E0001` | `rtl/cdc/slow_regs.v:31,78,128` | **YES** |
| `slow_regs` | `0x04` | `SLOW_SCRATCH` | RW (WSTRB) | `0x00000000` | `rtl/cdc/slow_regs.v:79,129` | **YES** |
| `slow_regs` | `0x08` | `SLOW_COUNTER` | RO | `0x00000000` | `rtl/cdc/slow_regs.v:85,130` | **YES** |
| `slow_regs` | `0x0C` | `SLOW_CTRL` | RW [0] | `0x1 (Default enabled)` | `rtl/cdc/slow_regs.v:56,86,131` | **YES** |

- All **8** Section 5.3 address regions and **7** Section 6 AXI4-Lite rules match `docs/spec.md` in RTL (`ADDR-*`, `AXIL-RULE-*` in `audit_results.csv`). Minor structural deviations: `axil_default_slave` and `axil_decoder` sit inside `axil_xbar` rather than `amba_fabric_top`, and `axil_xbar` uses inline round-robin logic (`DEC-007`).

## 11. Independent Probe Tests (Step 8)

- Executed `<WORK_DIR>/audit_work/probes/test_probes.py` against `amba_fabric_top` (`<WORK_DIR>/audit_work/audit_logs/step8_probes.log`): **5/5 PASS**:

  1. `test_probe_address_decode_and_default_slave`: Verified S0 (`0x4000_0000`+UART/Timer/GPIO), `0x4000_3000` APB unmapped (`SLVERR`), `0x4001_0000` (`DECERR`, disproving `README:108`), S1, S2, S3, and unmapped regions (`DECERR`).

  2. `test_probe_all_registers_reset_and_access`: Verified reset values & RO/RW/W1C/WO behaviors for CSR (`ID=0xA3BA0001`, `VERSION=0x00010000`), UART, Timer, GPIO, and Slow Regs (`SLOW_ID=0x510E0001`).

  3. `test_probe_ram_oob_and_timer_period`: Verified RAM word `0x5000_0400` returns `SLVERR` and Timer `LOAD=4` asserts `irq_o` at exactly `LOAD+1 = 5` cycles.

  4. `test_probe_gpio_sync_latency_and_uart_loopback_frame_err`: Confirmed GPIO `IN==0` at +1 cycle and `0xA55A` at +2 cycles, plus UART loopback `0x5A` and external bad-stop `FRAME_ERR`.

  5. `test_probe_cdc_ratios_and_contention`: Confirmed CDC R/W integrity at two clock ratios (`10ns/25ns` and `10ns/6ns`) and concurrent M0+M1 contention.

## 12. Sanity Mutation Results (Step 9)

- **Independent 10-bug injection (`<WORK_DIR>/audit_work/audit_logs/step9_sanity_mut.log`):** **9/10 KILLED, 1 SURVIVED**:

  - **KILLED (9):** `MUT-01` xbar WR priority M0 (`XB-07`), `MUT-02` RAM `WSTRB[1]` drop (`test_axil_ram`), `MUT-03` `async_fifo` Gray error (`test_async_fifo`), `MUT-04` bridge `PSLVERR->OKAY` (`BR-03`), `MUT-05` Timer off-by-one (`TM-01`), `MUT-06` `DECERR->SLVERR` (`test_axil_default_slave`), `MUT-07` APB early `PENABLE` (`BR-01`), `MUT-08` `sync_fifo` full off-by-one (`test_sync_fifo`), `MUT-09` CSR `W1C_TEST` (`CS-02`).

  - **SURVIVED (`MAJOR`):** `MUT-10` (GPIO 2-FF sync reduced to 1-FF in `rtl/apb/apb_gpio.v`) **SURVIVED** `test_gp02_input_sync_latency` (`TESTS=1 PASS=1 FAIL=0`) because `GP-02` never checks `IN == 0` on cycle 1!

- **Project 16-mutant gate (`<WORK_DIR>/audit_work/audit_logs/step9_proj_sanity.log`):** **16/16 KILLED (`SMUT-01..16`)**.

## 13. Mutation Report Audit (Step 10)

- **Reproduced Frozen 240-Mutant Run (`<WORK_DIR>/audit_work/audit_logs/step10_mutation_full.log`):** **205/240 KILLED (85.42% raw)**, **35 SURVIVED**, **0 timeouts**, **0 build errors** in `318.96 seconds` — matching `docs/mutation_report.md` and `docs/logs/mutation.log` identically! Sampled run (`<WORK_DIR>/audit_work/audit_logs/step10_mutation_sample.log`): `19/24 (79.17%)`.

- **Score arithmetic & doc note:** `205/240 = 85.42%` raw, `205/(240-21) = 205/219 = 93.61%` adjusted; all 8 per-module rows verify identically. Note: `docs/mutation_triage.md` does not exist in `git ls-files` (deleted in `52bf157`; triage moved to `docs/mutation_report.md`).

- **Git history check:** Commits `fe1816d` and `52bf157` genuinely document survivor-to-new-test additions (`test_rr_arbiter.py`, `test_axil_ram.py`, `test_axil2apb_bridge.py`, etc.).

- **Spot-check of 6 survivors from `docs/mutation_report.md`:**

  1. `axil_decoder #1` (`EQUIV_YOSYS`): Equivalent — `equiv_induct` proves bit 22 comparison redundancy.

  2. `axil_xbar #5` (`SIGNAL_PROOF`): Equivalent — `def_araddr[2]` feeds only `u_default_slave._unused_inputs`.

  3. `axil2apb_bridge #13` (`NON_EQUIV_CEX`): **Real test gap** — `const0` on `m_apb_paddr[27]` during `ST_WAIT_AW`; bridge tests omit high-bit address checks under W-before-AW.

  4. `axil_csr #19` (`NON_EQUIV_CEX`): **Real test gap** — `s_axil_bvalid` clear condition under `bvalid && bready` (`rtl/axil/axil_csr.v:151`) has an observable CEX unhit by unit tests.

  5. `rr_arbiter #22` (`NON_EQUIV_CEX`): **Real test gap** — `if (!found && req[(i+j)%NUM_REQS])` (`rtl/common/rr_arbiter.v:35`) forced `const1` exposes missing arbitration contention coverage.

  6. `axil_ram #0` (`SIGNAL_TRIAGE`): **Residual survivor/gap** — `$procmux$52855` on `aw_done`/`w_done`/`bvalid` condition (`rtl/axil/axil_ram.v:95-97`), not formally proved equivalent.

## 14. Seed and Stress Results (Step 11)

- **20 Fresh Icarus Seeds (`701..720`, `<WORK_DIR>/audit_work/audit_logs/step11_regress_20seeds.log`):** **20/20 PASS**, **10,000 transactions/seed** (**200,000 total**), **0 scoreboard mismatches**.

- **20 Verilator Seeds (`1..20` via `make cov-report`, `<WORK_DIR>/audit_work/audit_logs/step6_cov_report.log`):** **20/20 PASS**, **10,000 transactions/seed** (**200,000 total**), **0 mismatches**.

## 15. Synthesis and STA Comparison (Step 12)

| Metric | Claimed (`docs/results.md` / `README`) | Fresh Measured (`step12_*`) | Match? |
|---|---|---|---|
| Total Cells / Sequential Flops (SKY130, `RAM_DEPTH=64`) | `9,237` / `3,630` (`2,048` RAM) | `9,237` / `3,630` (`1,140 dfrtp_1 + 10 dfstp_1 + 2,480 edfxtp_1`) | **YES** |
| Total Area / Sequential % | `138,086.19 um^2` / `74.78%` | `138,086.19 um^2` / `74.78%` | **YES** |
| Clocks & CDC SDC | `10ns clk_sys`, `24ns clk_slow`, `-asynchronous` | Verified in `synth/amba_fabric.sdc` | **YES** |
| 100 MHz Target (`10ns`) Full Netlist WNS / TNS | `-18.60 ns` / `-54046.39 ns` (`VIOLATED`) | `-18.60 ns` / `-54046.39 ns` (`VIOLATED`) | **YES** |
| Achieved Full Netlist Fmax / Core+IO Ref Fmax | `34.97 MHz` (`28.60 ns`) / `62.89 MHz` (`15.90 ns`) | `34.97 MHz` (`28.60 ns`) / `62.89 MHz` (`15.90 ns`) | **YES** |

- Docs honestly state 100 MHz timing is **VIOLATED** pre-layout due to unbuffered `rst_sys_n` (`fanout=958`, `cap=3.46 pF`, `slew=29.27 ns`) and use measured Fmax (`34.97 MHz` full / `62.89 MHz` ref) in README resume bullets.

## 16. CI and Documentation Audit (Step 13)

- **CI Remote (`CI-REMOTE`, `NOT_RUN`, `MAJOR`):** `gh` CLI unavailable; `.github/workflows/ci.yml` commands all exist and pass locally, while remote green claim (`run 45602303543` on `c46cc77`, predating audited `338fd18`) could not be independently queried. Request verified GitHub Actions run URL from user.

- **README:** Quick start commands work; badges target repo branch `remediation-r2`; UART `FIFO_DEPTH=8` and `Verilog-2005` / `pyuvm vs cocotb models` disclosures are accurate. **Defects:** `README.md:108` incorrectly states S0 range `0x4000_0000 - 0x4FFF_FFFF` instead of `0x4000_FFFF` (`MAJOR`); `README.md:309` lists 5 non-existent agents under `tb/pyuvm/agents/` (`MINOR`).

- **`docs/bugs.md` & `docs/decisions.md`:** All 24 bugs have Symptom, Detection Method, Root Cause, Fix Applied, and valid Regression Test (`check_bug_refs.py` `24/24 PASS`). `docs/decisions.md` logs `DEC-001..013`, omitting internal `axil_default_slave` nesting (`axil_xbar.v` vs Spec 7.6) and fixed top-level `NUM_MASTERS`/`FIFO_DEPTH` params (`MINOR`).

## 17. Metric Honesty Table (Step 14)

| Metric ID | Metric | Claimed Value | Source Log in Repo | Fresh Measured Value | Match? |
|---|---|---|---|---|---|
| METRIC-01 | RTL modules / lines of RTL | 17 / 3,200 (docs/metrics.json) | `docs/results.md:15-26` | 17 modules / 3,200 non-blank non-comment lines | YES |
| METRIC-02 | Test definitions / XML runs / Spec map | 61 defs / 77 XML / 40/40 (docs/results.md:16) | `docs/results.md:15-26` | 61 Python defs / 77 XML (SEEDS=1) / 40 Spec IDs | YES |
| METRIC-03 | Random transactions executed | 200k Verilator + 200k Icarus | `docs/results.md:15-26` | 200,000 Icarus (701..720) + 200,000 Verilator (1..20), 0 mismatches | YES |
| METRIC-04 | Seeds passed | 20 + 20 seeds | `docs/results.md:15-26` | 20/20 fresh Icarus seeds (701..720) + 20/20 Verilator seeds (1..20) | YES |
| METRIC-05 | Functional coverage (bins hit / total) | 267/267 (100.00%, 24 YAMLs) | `docs/results.md:15-26` | 267/267 (100.00%), 36 waived (docs/logs/func_cov.log) | YES |
| METRIC-06 | Verilator code coverage (line / toggle / branch) | Line 92.0% (494/537), Toggle 74.8% | `docs/results.md:15-26` | Line 92.4% (496/537), Branch 91.6%, Toggle 76.2% | PARTIAL (detail in Notes) |
| METRIC-07 | Formal verification suites / covers / runtime | 10/10 PASS, 84 covers, 150s | `docs/results.md:15-26` | 10/10 PASS, 84 covers, 160s runtime (3 prove, 1 prv+bmc, 6 bmc) | YES |
| METRIC-08 | CDC clock ratios and phases swept | 3 periods x 3 phases, formal d=25/30 | `docs/results.md:15-26` | 3 slow periods (25.0, 10.3, 6.0 ns) x phases + CD-01 ratios | YES |
| METRIC-09 | Mutation score (before -> after / equiv) | 165/240 -> 205/240 (85.42% / 93.61% adj) | `docs/results.md:15-26` | Baseline 165/240 (68.75%); Final 205/240 (85.42%); 21 equiv (15 BMC10) | PARTIAL (detail in Notes) |
| METRIC-10 | Bugs found and fixed | 24 bugs (15 RTL + 9 TB/formal/tooling) | `docs/results.md:15-26` | 24 bugs (BUG-001..BUG-024), 24/24 refs valid | YES |
| METRIC-11 | Crossbar added latency (cycles) | 0 cycles added latency | `docs/results.md:15-26` | 0 cycles added latency (verified in XB-06) | YES |
| METRIC-12 | Synthesis cells / flops / area (RAM_DEPTH=64) | 9,237 cells / 3,630 flops / 138,086.19 um^2 | `docs/results.md:15-26` | 9,237 cells / 3,630 flops / 138,086.19 um^2 | YES |
| METRIC-13 | STA WNS/TNS at 10 ns and achieved Fmax | VIOLATED -18.60ns / 34.97 MHz (62.89 ref) | `docs/results.md:15-26` | Full WNS -18.60ns TNS -54046.39ns (34.97 MHz); Core+IO -5.89ns (62.89 MHz) | YES |
| METRIC-14 | CI status metric in README & results.md | PASS (run 45602303543) | `docs/results.md:15-26` | NOT_RUN locally (gh absent; claimed run 45602303543 on c46cc77) | NOT_RUN |

## 18. Prioritized Remediation List

- **BLOCKER (0):** None.

- **MAJOR (16):**
  - **V-07** (`scripts/run_all_formal.sh:1; formal/axil_xbar.sby:1`): V-07 all 10 suites pass clean, but crossbar, APB bridge, CDC bridge, UART, and RAM only run bounded bmc (d=20..30), not unbounded prove.
  - **V-10** (`.github/workflows/ci.yml:1; docs/logs/ci_remote_verified.json:1`): V-10 ci.yml commands pass locally, but remote GitHub Actions green badge cannot be verified without gh CLI; ask user for verified run URL on audited commit.
  - **GP-02** (`tb/block/test_apb_gpio.py:51`): Drives gpio_i=0xBEEF and reads IN after 2 cycles, never asserting IN==0 after 1 cycle; allowed our 1-FF bug MUT-10 to survive.
  - **FORMAL-XBAR** (`formal/axil_xbar.sby:1; formal/axil_xbar_props.v:1`): FORMAL-XBAR runs cleanly via make formal and reaches all cover traces; status reflects unbounded prove vs bounded bmc depth limits.
  - **FORMAL-BRIDGE** (`formal/axil2apb_bridge.sby:1; formal/axil2apb_bridge_props.v:1`): FORMAL-BRIDGE runs cleanly via make formal and reaches all cover traces; status reflects unbounded prove vs bounded bmc depth limits.
  - **FORMAL-CDC** (`formal/axil_cdc_bridge.sby:1; rtl/cdc/axil_cdc_bridge.v:380`): FORMAL-CDC runs cleanly via make formal and reaches all cover traces; status reflects unbounded prove vs bounded bmc depth limits.
  - **FORMAL-WORDING** (`README.md:173; docs/mutation_report.md:24,46`): README.md:173 and docs/mutation_report.md:24,46 label all 21 survivors 'proven equivalent', though 15 rely on 10-cycle bounded BMC (EQUIV_BMC10).
  - **SANITY-10** (`<WORK_DIR>/audit_work/sanity_mut.py:1; rtl/`): SANITY-10: SURVIVED (3.0s, TESTS=1 PASS=1 FAIL=0) because test_gp02 never asserts IN==0 at +1 cycle!
  - **MUT-EQUIV-CLAIM** (`docs/mutation_report.md:46-70; docs/logs/mutation_equiv.log:1`): 3 axil_decoder mutants use unbounded equiv_induct and 3 xbar _unused_inputs are trivially dead, but 15 EQUIV_BMC10 are bounded d=10 checks labeled 'proven equivalent'.
  - **CI-REMOTE** (`.github/workflows/ci.yml:1; docs/logs/ci_remote_verified.json:1`): gh CLI unavailable in audit environment so remote CI status is unverified (MAJOR per Step 13); ask user to confirm run URL on 338fd18.
  - **DOC-README-ADDR** (`README.md:108; rtl/axil/axil_decoder.v:6-7; docs/spec.md:214`): Published README.md:108 memory map incorrectly expands S0 APB subsystem across 0x4001_0000..0x4FFF_FFFF, which actually returns DECERR per axil_decoder.v.
  - **METRIC-09** (`docs/results.md:15-26; README.md:128-142`): 205/240 raw kill count and score math match exactly, but '21 proven equivalent' includes 15 depth-10 BMC checks.
  - **METRIC-14** (`docs/results.md:15-26; README.md:128-142`): Published CI green status could not be checked without gh CLI/network and predates audited HEAD 338fd18.
  - **DOD-04** (`docs/spec.md:834-842; README.md:270-276`): All 10 .sby tasks pass with 84 covers, but xbar/bridge/cdc remain bounded BMC rather than unbounded prove.
  - **DOD-07** (`docs/spec.md:834-842; README.md:270-276`): Cannot verify GitHub Actions remote green status without gh CLI; ask user for verified run URL on audited commit.
  - **DOD-08** (`docs/spec.md:834-842; README.md:270-276`): docs/img/*.png screenshots and logs exist, but README:108 gives wrong S0 end address (0x4FFF_FFFF vs 0x4000_FFFF).
- **MINOR (22):**
  - **F-02** (`rtl/axil/axil_xbar.v:277-495; rtl/common/rr_arbiter.v:4`): F-02 functional behavior passes, but axil_xbar implements inline priority registers rather than instantiating rr_arbiter.v (documented in DEC-007).
  - **V-01** (`tb/pyuvm/agents/axil_master_agent.py:1; tb/models/axil_slave_responder.py:1`): V-01 master agents use pyuvm.uvm_agent, while slave/APB/peripheral responders are plain cocotb models in tb/models/ (disclosed in README prose, not README:309 tree).
  - **XB-02** (`tb/block/test_axil_xbar.py:180`): Verifies S1 data integrity on axil_xbar against Python AxilSlaveResponder rather than axil_ram RTL (RTL covered in L0/L2).
  - **XB-03** (`tb/block/test_axil_xbar.py:205`): Drives all 16 WSTRB values across S1/S2 against AxilSlaveResponder in L1; real axil_ram/axil_csr RTL strobes tested in test_sys_strobe_patterns.
  - **BR-02** (`tb/block/test_axil2apb_bridge.py:137`): Sweeps wait states ws=[1,2,4] checking data integrity, while cycle-by-cycle PENABLE/control hold is verified in formal props rather than Python test body.
  - **BR-05** (`tb/block/test_axil2apb_bridge.py:261`): vplan cites only single-master axil2apb_bridge back-to-back mixed R/W; dual-master (M0+M1) APB mixed R/W exists separately at test_amba_fabric_top.py:370.
  - **UA-01** (`tb/block/test_apb_uart.py:25`): Spec Sec 9.1 specifies all 256 byte values, whereas test_ua01 loops only 8 bytes [0x55,0xAA,0x00,0xFF,0x3C,0xC3,0x12,0x89] (all 8 bit positions hit).
  - **TM-02** (`tb/block/test_apb_timer.py:67`): Runs 3 periodic iterations checking timer_irq==1 within <20 cycles, never asserting exact LOAD+1 period each cycle.
  - **COV-CODE** (`scripts/run_regression.sh:1; docs/logs/code_cov_summary.txt:1`): Reproduced code coverage exceeds docs/results.md slightly (+2 lines, +205 toggle bits) because test_directed & test_axil2apb_bridge lack fixed SEED in Makefile.
  - **COV-WAIVERS-DOC** (`docs/coverage_waivers.md:10-20; docs/results.md:83-94`): All 4 waiver justifications (24 illegal DECERR, 6 CDC full, 3 one_idle, 3 APB read PSTRB) are sound, but docs/coverage_waivers.md omits leaf bins (224 vs 303).
  - **FORMAL-ASYNC-FIFO** (`formal/async_fifo.sby:1; rtl/common/async_fifo.v:115`): FORMAL-ASYNC-FIFO runs cleanly via make formal and reaches all cover traces; status reflects unbounded prove vs bounded bmc depth limits.
  - **FORMAL-CSR** (`formal/axil_csr.sby:1; rtl/axil/axil_csr.v:220`): FORMAL-CSR runs cleanly via make formal and reaches all cover traces; status reflects unbounded prove vs bounded bmc depth limits.
  - **FORMAL-RAM** (`formal/axil_ram.sby:1; rtl/axil/axil_ram.v:150`): FORMAL-RAM runs cleanly via make formal and reaches all cover traces; status reflects unbounded prove vs bounded bmc depth limits.
  - **FORMAL-UART** (`formal/apb_uart.sby:1; rtl/apb/apb_uart.v:450`): FORMAL-UART runs cleanly via make formal and reaches all cover traces; status reflects unbounded prove vs bounded bmc depth limits.
  - **DOC-MUT-TRIAGE** (`docs/mutation_report.md:1; docs/audit_r2_tracking.csv:40`): docs/mutation_triage.md was deleted in commit 52bf157 as duplicate of docs/mutation_report.md, which consolidates all 35 survivors.
  - **CLONE-REGRESS** (`Makefile:75-81`): SEEDS=1 passes in clean clone, but Makefile:78 lacks quotes around $(SEEDS) when forwarding a multi-seed list (tb/pyuvm/Makefile direct works).
  - **LINT-ICARUS** (`rtl/axil/axil_xbar.v:203-213,370-513`): Icarus Verilog elaboration succeeds (EXIT=0) but prints @* array sensitivity warnings in axil_xbar.v lines 203-213 and 370-513.
  - **LAYOUT-PORTS** (`rtl/amba_fabric_top.v:6-12; rtl/axil/axil_xbar.v:6`): All 17 RTL modules match functionally, with minor structural deviations (default slave & decoder inside axil_xbar rather than top; fixed master/FIFO params on top).
  - **DOC-README-TREE** (`README.md:309; tb/pyuvm/agents/axil_master_agent.py:1`): Although README:151-152 honestly distinguishes pyuvm agents from tb/models/, README:309 still carries stale spec directory comments.
  - **DOC-DECISIONS** (`docs/decisions.md:1`): docs/decisions.md thoroughly logs DEC-001..013, though structural placement of default_slave inside axil_xbar and omitted top params are unlogged.
  - **METRIC-06** (`docs/results.md:15-26; README.md:128-142`): Source log code_cov_summary.txt matches docs/results.md, while fresh run scored +0.4% line / +1.4% toggle due to unseeded directed/bridge runs.
  - **DOD-01** (`docs/spec.md:834-842; README.md:270-276`): All P0 RTL features pass tests & probes; minor fidelity gaps in UA-01, TM-02, BR-02, BR-05, XB-02/03.
