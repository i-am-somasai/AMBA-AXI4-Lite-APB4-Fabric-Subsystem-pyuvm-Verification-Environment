# Independent Adversarial Sign-Off Audit Report — AMBA-Fabric

## 1. Verdict

**Verdict: NOT READY**

Across `251` audited items from a clean clone of commit `8664339a50e7558798ca067f4799e372f0afffc9` (branch `remediation`), this audit identified **33 BLOCKER**, **37 MAJOR**, **12 MINOR**, and **5 INFO** findings. While the clean clone compiles cleanly, passes `make lint`, `make unit`, `make block`, `make formal`, and 20 fresh seeds (501–520, 200,000 transactions with zero mismatches), sign-off is blocked by a genuine RTL AXI4-Lite Rule 6 violation in `axil_csr.v` caught by an independent probe (`0x6000_0001` returns `SLVERR`), three high-impact test-fidelity failures (`XB-07` has zero assertions allowing injected priority failure `MUT-10` to escape; `XB-12` resets when idle; `XB-14` ignores APB `PPROT` allowing `MUT-09` to escape), false `280/280 (100%)` functional coverage claims in `docs/vplan.md:142` and `docs/results.md:140` vs measured `229/273 (83.88%)`, broken STA constraints (`sta.tcl`/`fmax_sweep.py` hardcoding stale cell names yielding `WNS = -19.33 ns` while printing hardcoded `81.63 MHz`), impossible/contradictory mutation report arithmetic (`103.4%`), and missing tracked files (`synth/synth.ys`, `docs/img/contention.vcd`, `test_xb09_backpressure_burst.py`).

### Enumerated Spec Checklist Totals (Step 1)
- Features (`F-01..F-13`, `V-01..V-10`, `S-01..S-03`, `X-01..X-02`): **28**
- Address Map Regions (Spec Sec 5.3): **8**
- Registers (CSR 9, UART 5, Timer 4, GPIO 5, Slow Regs 5): **28**
- AXI4-Lite Rules (Spec Sec 6): **7**
- RTL Modules + Lint / Params / Clocks (Spec Sec 5.2, 5.4, 7): **20**
- Section 9.1 Test IDs (`XB-01..15`, `BR-01..06`, `UA-01..05`, `TM-01..03`, `GP-01..03`, `CS-01..03`, `CD-01..05`): **40**
- Functional Covergroups + Coverage Audits (Spec Sec 10): **12**
- Formal Suites, Checkers & Wording Checks (Spec Sec 11): **13**
- Mutation Flow & Audits (Spec Sec 12): **4**
- Synthesis / STA & CI (Spec Sec 13–14): **6**
- Repository Layout Paths (Spec Sec 15): **40**
- Master Metric Table Rows (Spec Sec 17): **14**
- Definition of Done Items (Spec Sec 21): **9**
- Independent Probes (`PROBE-01..08`), Sanity Mutants (`SMUT-01..10`), & Cross-Doc Audits: **22**
- **Grand Total Audited Rows:** **251**

---

## 2. Scorecard

| Area | Total | PASS | FAIL | PARTIAL | NOT_FOUND | NOT_RUN | N/A |
|---|---:|---:|---:|---:|---:|---:|---:|
| Features | 28 | 10 | 5 | 8 | 0 | 1 | 4 |
| Address Map | 8 | 8 | 0 | 0 | 0 | 0 | 0 |
| Registers | 28 | 27 | 0 | 1 | 0 | 0 | 0 |
| AXI4-Lite Rules | 7 | 6 | 1 | 0 | 0 | 0 | 0 |
| RTL Structure | 20 | 16 | 1 | 3 | 0 | 0 | 0 |
| Spec Tests | 40 | 32 | 4 | 4 | 0 | 0 | 0 |
| Coverage | 12 | 2 | 1 | 9 | 0 | 0 | 0 |
| Formal | 13 | 5 | 2 | 6 | 0 | 0 | 0 |
| Mutation | 4 | 1 | 2 | 1 | 0 | 0 | 0 |
| Independent Probes | 8 | 7 | 1 | 0 | 0 | 0 | 0 |
| Sanity Mutation | 10 | 8 | 2 | 0 | 0 | 0 | 0 |
| Synthesis & STA | 4 | 0 | 3 | 1 | 0 | 0 | 0 |
| CI & Docs | 2 | 0 | 0 | 1 | 0 | 1 | 0 |
| Repo Layout | 40 | 38 | 0 | 1 | 1 | 0 | 0 |
| Metric Honesty | 14 | 3 | 8 | 2 | 0 | 1 | 0 |
| Definition of Done | 9 | 0 | 6 | 2 | 0 | 1 | 0 |
| Clean-clone quick start: env-check, lint, unit, block, 1-seed regress, formal | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| docs/vplan.md truthfulness across all 40 test rows and coverage target | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| docs/bugs.md schema completeness and regression test existence | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| docs/decisions.md captures all spec/interface deviations | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| **TOTAL** | 251 | 164 | 39 | 39 | 1 | 4 | 4 |

| Summary | Count 1 | Count 2 | Count 3 | Count 4 |
|---|---|---|---|---|
| **Severity Totals** | BLOCKER: 33 | MAJOR: 37 | MINOR: 12 | INFO: 5 |

---

## 3. Environment

- **Audit Date:** 2026-11-24
- **Audited Repository Commit:** `8664339a50e7558798ca067f4799e372f0afffc9` (branch `remediation`)
- **Clean Clone Path:** `/tmp/audit_clone` (audit workspace `/tmp/audit_work/`, `/tmp` tmpfs = 674 MB)
- **Host / Constraints:** Linux x86_64, 8 GB RAM, `MAX_JOBS=4`, open-source tools only (`source scripts/env.sh`), `gh` CLI not installed
- **Tools Verified (`/tmp/audit_work/audit_logs/env_and_home_grep.log`):**
  - Icarus Verilog: `14.0 (devel)`
  - Verilator: `5.055 devel`
  - Yosys: `0.71+77`
  - SymbiYosys (`sby`): `v0.71-7-gb21f778` (solver: Boolector)
  - OpenSTA (`sta`): `2.6.0` (SKY130 `sky130_fd_sc_hd__tt_025C_1v80.lib`)
  - Python / Verification: `Python 3.11.6`, `cocotb 2.1.0.dev0+41564633`, `pyuvm 5.0.0`, `cocotb-coverage`
- **Fresh Audit Seeds Used:**
  - Unit tests (`make unit`): `RANDOM_SEED=7101`
  - Block tests (`make block`): `RANDOM_SEED=7102`
  - pyuvm directed (`make -C tb/pyuvm test_directed`): `SEED=7103` (+ `103`, `60` from Makefile CDC targets)
  - Multi-seed XB-13 stress: Fresh seeds **501 through 520** (20 seeds x 10,000 transactions = 200,000 transactions)

---

## 4. Clean-Clone Reproducibility & `/home/` Path Audit

| Check | Command | Result | Log File | Notes |
|---|---|---|---|---|
| Toolchain check | `source scripts/env.sh && make env-check` | PASS | `/tmp/audit_work/audit_logs/step2_env_check.log` | All open-source binaries and SKY130 lib found |
| Verilator lint | `make lint` | PASS | `/tmp/audit_work/audit_logs/step2_lint.log` | 0 warnings on Verilator + `check_no_synthetic_cov.sh` PASS |
| Unit regression | `make unit SIM=icarus` | PASS | `/tmp/audit_work/audit_logs/step2_unit.log` | 12/12 unit test functions pass (incl. `test_hello_world`) |
| Block regression | `make block SIM=icarus` | PASS | `/tmp/audit_work/audit_logs/step2_block.log` | 34/34 block test functions pass |
| pyuvm 1-seed regress | `make regress SIM=icarus SEEDS=1` | PASS | `/tmp/audit_work/audit_logs/step2_regress_1seed.log` | Directed + CDC sweeps + 10,000 stress txns pass |
| Formal suite | `make formal` | PASS | `/tmp/audit_work/audit_logs/step2_formal.log` | 10/10 `.sby` suites PASS, 81 covers reached |
| Full coverage target | `make cov-report` | FAIL (exit 2) | `/tmp/audit_work/audit_logs/step6_cov_report.log` | Fails `No space left on device` on 674 MB `/tmp` at `sim_build_cdc_6_0`; also `merge_cov.py` exits 1 when func cov < 100% |
| Hardcoded paths | `grep -rn "/home/" .` | PASS (source) | `/tmp/audit_work/audit_logs/env_and_home_grep.log` | Zero hardcoded `/home/` paths in RTL/TB/logs (only path-stripping regexes in 3 scripts and `.git/` origin ref) |

---

## 5. Feature Matrix (`F-*`, `V-*`, `S-*`, `X-*`)

| ID | Priority | Status | Severity | Evidence | Measured Value | Notes |
|---|---|---|---|---|---|---|
| `F-01` | P0 | PARTIAL | MINOR | `rtl/axil/axil_xbar.v:6; rtl/axil/axil_decoder.v:5` | 2Mx4S xbar passes sim; decoder adds unlogged 4-bit slave_sel/params | Crossbar decodes S0-S3 and default slave, but axil_decoder.v:5-18 diverges from docs/interfaces.md:115 ([1:0] vs 4-bit one-hot + parameters) without entry in docs/decisions.md. |
| `F-02` | P0 | FAIL | BLOCKER | `rtl/axil/axil_xbar.v:123; tb/block/test_axil_xbar.py:332` | XB-07 has 0 assertions; MUT-10 xbar prio bug escaped; inline arbiter | rtl/axil/axil_xbar.v duplicates inline wr_prio/rd_prio instead of reusing rr_arbiter.v, XB-07 has zero assertions, and sanity mutant MUT-10 (stuck write priority) escaped. |
| `F-03` | P0 | PASS | - | `rtl/axil/axil_default_slave.v:4` | DECERR (2'b11) on read/write; MUT-06 killed | Default slave completes AW+W and AR handshakes with DECERR and consumes WDATA; verified by unit, XB-04, probe_01, and MUT-06 detection. |
| `F-04` | P0 | PASS | - | `rtl/axil/axil_ram.v:4` | 256-word RAM, 1-cyc read, WSTRB, OOR SLVERR pass | axil_ram honors byte strobes with 1-cycle read latency and returns SLVERR above RAM_DEPTH*4; verified by probe_03, unit sweep, and MUT-02 detection. |
| `F-05` | P0 | FAIL | BLOCKER | `rtl/axil/axil_csr.v:68; rtl/axil/axil_csr.v:111; rtl/axil/axil_csr.v:171` | FAIL: probe_02 read 0x6000_0001 returned SLVERR (resp=2) | axil_csr switches on full 8-bit write_offset/read_offset instead of masking [1:0]=0, returning SLVERR on 0x6000_0001 in probe_02 contrary to Spec Section 6 Rule 6. |
| `F-06` | P0 | PARTIAL | MAJOR | `rtl/apb/axil2apb_bridge.v:6; tb/block/test_axil2apb_bridge.py:243` | Bridge works on waits/PSLVERR/PSTRB; MUT-09 PPROT bug escaped | RTL drives APB phases cleanly (MUT-04, MUT-07 killed), but MUT-09 zeroing m_apb_pprot escaped both block test and pyuvm test_xb14, and BR-05 tests bridge without dual masters. |
| `F-07` | P0 | PASS | - | `rtl/apb/apb_decoder.v:5` | 0x4000_0000/1000/2000 decoded; 0x4000_F000 -> SLVERR | apb_decoder routes UART/Timer/GPIO via PADDR[15:12] and terminates unmapped 0x4000_3000..0x4000_F000 accesses with PSLVERR in one cycle (confirmed in probe_01). |
| `F-08` | P0 | PARTIAL | MAJOR | `rtl/apb/apb_uart.v:339; tb/block/test_apb_uart.py:61` | Loopback/baud/frame_err pass in probe_06; RX_OVF untested in UA-02 | UART TX/RX/loopback/BAUDDIV/FRAME_ERR pass block tests and probe_06, but UA-02 omits RX FIFO overflow testing leaving reg_rx_ovf (apb_uart.v:339) uncovered at 0%. |
| `F-09` | P0 | PASS | - | `rtl/apb/apb_timer.v:6` | LOAD+1 exact period, periodic reload, W1C, IRQ pass | apb_timer hits exact LOAD+1 cycle one-shot/periodic timeouts and clears IRQ via W1C; confirmed by probe_04, MUT-05 kill, and k-induction formal suite. |
| `F-10` | P1 | PASS | - | `rtl/apb/apb_gpio.v:5` | DIR/OUT, 2-FF latency on IN, rising-edge IRQ + W1C pass | apb_gpio implements DIR/OUT, 2-FF input synchronizer (2-cycle latency confirmed in probe_05), and W1C rising-edge interrupt latching. |
| `F-11` | P0 | PASS | - | `rtl/cdc/axil_cdc_bridge.v:5; rtl/cdc/slow_regs.v:5; rtl/common/async_fifo.v:4` | Dual-clock async FIFOs pass ratios 6ns/10.3ns/25ns/33ns; MUT-03 killed | CDC request/response Gray-pointer FIFOs and slow_regs pass block ratio sweeps, probe_07 (33ns and 6ns slow clocks), MUT-03 Gray corruption check, and multiclock BMC. |
| `F-12` | P0 | PASS | - | `rtl/common/rst_sync.v:4; rtl/amba_fabric_top.v:123` | 2 rst_sync instances (clk_sys, clk_slow); async assert, sync deassert | amba_fabric_top instantiates rst_sync separately for clk_sys and clk_slow with async active-low assertion and 2-FF synchronous release verified in test_rst_sync. |
| `F-13` | P1 | PASS | - | `rtl/axil/axil_csr.v:56; rtl/amba_fabric_top.v:437` | UART/Timer/GPIO IRQs aggregate via IRQ_MASK to top irq_o | axil_csr masks {gpio_irq, timer_irq, uart_irq} with reg_irq_mask and drives top irq_o; verified end-to-end in test_cs03 and test_top02. |
| `V-01` | P0 | PARTIAL | MINOR | `tb/pyuvm/agents/axil_master_agent.py:1; docs/decisions.md:12` | 2 master agents are pyuvm; responders/models are cocotb coroutines | Spec calls for pyuvm slave and APB responder agents; only AxilMasterAgent uses pyuvm while responders in tb/models/ are plain cocotb coroutines (honestly logged in DEC-005). |
| `V-02` | P0 | PARTIAL | MAJOR | `tb/pyuvm/env/fabric_scoreboard.py:1; tb/models/reg_model.py:106` | Scoreboard misses SlowRegsModel [1:0] diff, APB PPROT, CSR unaligned bug | FabricScoreboard checks 200k random transactions cleanly, yet SlowRegsModel masks offset & 0xFC inconsistently with axil_csr (missing Rule 6 bug), and PPROT is unverified. |
| `V-03` | P0 | PASS | - | `tb/pyuvm/sequences/fabric_stress_seq.py:1; tb/pyuvm/sequences/directed_seqs.py:1` | Directed + 20-seed constrained random (200,000 txns) execute & pass | All directed sequences and constrained-random FabricStressSeq run cleanly with zero synthetic coverage calls across 20 fresh seeds (501-520). |
| `V-04` | P0 | FAIL | BLOCKER | `tb/pyuvm/func_cov/fabric_cov.py:1; docs/vplan.md:142` | 229 / 273 bins (83.88%); 44 real uncovered holes remain | Re-run produces 229/273 (83.88%) matching func_cov.log; 44 monitor bins are uncovered (w_first, APB wait>0, framing error, in-flight reset) while docs/vplan.md claims 100% (280/280). |
| `V-05` | P0 | PARTIAL | MAJOR | `scripts/run_regression.sh:1; Makefile:81` | make cov-report fails ENOSPC on /tmp; manual run: 90.0% line / 75.2% toggle | make cov-report crashes with No space left on device on 674MB /tmp due to 3 sim_build dirs and exits 1 when func cov < 100%; manual Verilator run yields 90.0% line, 75.2% toggle, 92.7% expr. |
| `V-06` | P0 | PARTIAL | MAJOR | `tb/pyuvm/monitors/fabric_monitors.py:322; formal/rr_arbiter.sby:1` | Monitors catch protocol issues except CdcMonitor uses env var; rr_arbiter_props unused | CdcMonitor reads CLK_SLOW_PERIOD_NS from environment instead of measuring clk_slow period on RTL pins, and formal/rr_arbiter_props.v is never loaded by formal/rr_arbiter.sby. |
| `V-07` | P0 | PARTIAL | MAJOR | `scripts/run_all_formal.sh:1; formal/axil2apb_bridge_props.v:156; formal/axil_xbar_props.v:396` | 10/10 .sby pass (81 covers), but over-assumptions & missing FIFO order check | All 10 .sby suites pass, but rr_arbiter_props.v is orphaned, axil2apb_bridge & axil_xbar contain over-constraining assumptions, axil_csr disables CHECK_CAUSALITY, and sync_fifo lacks data-ordering assertion. |
| `V-08` | P0 | PASS | - | `tb/block/test_axil_cdc_bridge.py:48; tb/pyuvm/Makefile:55` | Swept 25ns, 10.3ns, 6.0ns periods across phases 0, 2.5, 5.0ns | test_cd01 sweeps slow periods (25ns, 10.3ns, 6ns) and 3 phase offsets with zero errors, reinforced by TestCoverageClosure CDC runs and probe_07. |
| `V-09` | P1 | FAIL | BLOCKER | `mutation/run_mutants.py:1; docs/mutation_report.md:1` | Fresh 240-mutant run: 183/240 (76.25%); docs contain fabricated/contradictory counts | docs/mutation_report.md claims 30/29 (103.4%) and phantom survivor axil_xbar #29 absent from mutation.log, miscounts axil_ram equivs (10 vs 8), and hides CSR test gaps as 'unused bits'. |
| `V-10` | P1 | NOT_RUN | MAJOR | `.github/workflows/ci.yml:1; README.md:3` | gh CLI not installed; local CI cmds pass except cov artifacts not generated in CI | Local CI script check_no_synthetic_cov, lint, unit, block, and formal pass; remote GitHub Actions status cannot be checked without gh CLI, so CI PASS claim is unverified. |
| `S-01` | P0 | FAIL | BLOCKER | `synth/sta.tcl:22; synth/fmax_sweep.py:37; synth/fmax_sweep.py:130` | 9,320 cells, 138,031.13 um2; STA WNS=-19.33ns (<62.5 MHz); synth.ys missing | synth/synth.ys is absent from git; sta.tcl and fmax_sweep.py hardcode stale Yosys cell IDs (_14798_/_14800_) causing fresh WNS=-19.33ns on rst_sync flop _14686_, while fmax_sweep.py prints hardcoded 81.63 MHz text. |
| `S-02` | P2 | N/A | INFO | `docs/spec.md:654` | No GLS testbench or SKY130 UDP functional sim exists | No gate-level simulation script, SKY130 behavioral Verilog integration, or GLS log is committed; classified N/A per audit rule. |
| `S-03` | P2 | N/A | INFO | `docs/spec.md:655` | No OpenLane config, DEF, or GDSII exists | No OpenLane configuration, macro/placement setup, DRC/LVS report, or GDSII artifact exists; classified N/A per audit rule. |
| `X-01` | P2 | N/A | INFO | `rtl/axil/axil_xbar.v:10` | NUM_MASTERS=2; no RISC-V core attached | Crossbar exposes only 2 master ports (M0, M1) and no RISC-V core RTL or integration test exists; classified N/A per audit rule. |
| `X-02` | P2 | N/A | INFO | `rtl/axil/axil_xbar.v:6; docs/spec.md:107` | Single-outstanding per master read/write only | Crossbar and bridges support at most one outstanding write and read per master with no response reordering/FIFO queues; classified N/A per audit rule. |

---

## 6. Test Matrix (All 40 Spec Section 9.1 IDs)

| Spec ID | Test Function (`file:line`) | Fidelity | Result (Fresh Seed) | Log | Notes |
|---|---|---|---|---|---|
| `XB-01` | `tb/block/test_axil_xbar.py:145` | **yes** | PASS (PASS (seed 7102, 520ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Exercises M0 and M1 writes/reads to S0-S3 against axil_xbar and checks readback values and OKAY responses. |
| `XB-02` | `tb/block/test_axil_xbar.py:180` | **yes** | PASS (PASS (seed 7102, 400ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Writes multiple pseudo-random addresses in RAM across M0/M1 and asserts every read word matches reference model. |
| `XB-03` | `tb/block/test_axil_xbar.py:205` | **partial** | PARTIAL (PASS on RAM; CSR SCRATCH2 omitted) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Tests all 16 WSTRB values on RAM (0x5000_0000), but omits CSR SCRATCH2 (0x6000_000C) named in Spec 9.1 (only tested in pyuvm test_sys_strobe_patterns). |
| `XB-04` | `tb/block/test_axil_xbar.py:239` | **yes** | PASS (PASS (seed 7102, 280ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Issues reads and writes to multiple unmapped regions and asserts DECERR (resp=3) completion without stall. |
| `XB-05` | `tb/block/test_axil_xbar.py:268` | **yes** | PASS (PASS (seed 7102, 160ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Launches concurrent M0 and M1 requests to RAM and confirms serialized completion without corruption. |
| `XB-06` | `tb/block/test_axil_xbar.py:302` | **yes** | PASS (PASS (seed 7102, 70ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Runs parallel M0->S1 and M1->S2 transactions and asserts combined completion cycle count proves zero cross-slave serialization. |
| `XB-07` | `tb/block/test_axil_xbar.py:332` | **no** | FAIL (PASS sim only; 0 assertions; MUT-10 escaped) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Reads xbar grant wires into unused local variables (m0_first/m1_first) with ZERO assert statements checking grant counts; MUT-10 stuck priority escaped. |
| `XB-08` | `tb/block/test_axil_xbar.py:354` | **yes** | PASS (PASS (seed 7102, 260ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Drives all 3 channel arrival orderings (aw_first, w_first, simultaneous) across axil_xbar and verifies written RAM data. |
| `XB-09` | `tb/block/test_axil_xbar.py:377` | **yes** | PASS (PASS (seed 7102, 180.2us)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Runs >=2000 transactions under randomized AW/W/AR/B/R ready delays on axil_xbar verifying zero drops or duplicates. |
| `XB-10` | `tb/block/test_axil_xbar.py:424` | **yes** | PASS (PASS (seed 7102, 1300ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Stalls BREADY/RREADY and monitors every clock edge confirming BVALID/BRESP and RVALID/RDATA/RRESP hold stable until accepted. |
| `XB-11` | `tb/pyuvm/tests/test_directed.py:51` | **yes** | PASS (PASS (seed 7103, 920ns)) | `/tmp/audit_work/audit_logs/step4_pyuvm_directed_seed7103.log` | Issues invalid offsets to RAM, CSR, unmapped APB, and CDC slow_regs via SlverrSeq and checks SLVERR=2 arrives cleanly on correct master. |
| `XB-12` | `tb/pyuvm/tests/test_directed.py:126` | **no** | FAIL (PASS sim only; awaits seq completion before resetting when idle) | `/tmp/audit_work/audit_logs/step4_pyuvm_directed_seed7103.log` | Awaits full completion of transaction before pulsing rst_n, so crossbar is idle at reset (confirmed by cg_reset hitting only 'idle'); wrong scenario vs Spec 9.1. |
| `XB-13` | `tb/pyuvm/tests/test_stress.py:14` | **yes** | PASS (PASS: 20 fresh seeds (501-520) x 10,000 txns = 200k, 0 mismatches) | `/tmp/audit_work/audit_logs/step11_20seeds.log` | Executes 5,000 concurrent constrained-random items per master (10,000/seed) against amba_fabric_top scoreboard across 20 fresh seeds with 0 mismatches. |
| `XB-14` | `tb/pyuvm/tests/test_directed.py:66` | **no** | FAIL (PASS sim only; never inspects APB PPROT; MUT-09 escaped) | `/tmp/audit_work/audit_logs/step4_pyuvm_directed_seed7103.log` | Runs ProtPassThroughSeq which sets axil prot bits and asserts AXI OKAY, yet neither sequence nor scoreboard inspects top/bridge PPROT; MUT-09 zeroing PPROT passed. |
| `XB-15` | `tb/pyuvm/tests/test_directed.py:81` | **partial** | FAIL (PASS on RAM only; fails to test CSR where RTL breaks Rule 6) | `/tmp/audit_work/audit_logs/step4_pyuvm_directed_seed7103.log` | Targets only RAM (0x5000_0000+offset), missing axil_csr where unaligned 0x6000_0001 actually fails Rule 6 with SLVERR (caught by audit probe_02). |
| `BR-01` | `tb/block/test_axil2apb_bridge.py:40` | **yes** | PASS (PASS (seed 7102, 1140ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Checks PSEL=1/PENABLE=0 SETUP followed by PSEL=1/PENABLE=1 ACCESS cycle-by-cycle on 0-wait writes and reads. |
| `BR-02` | `tb/block/test_axil2apb_bridge.py:119` | **yes** | PASS (PASS (seed 7102, 500ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Injects random PREADY stalls and asserts PSEL, PENABLE, PADDR, PWRITE, PWDATA hold constant throughout ACCESS. |
| `BR-03` | `tb/block/test_axil2apb_bridge.py:159` | **yes** | PASS (PASS (seed 7102, 160ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Drives PSLVERR=1 from APB responder on both read and write and confirms SLVERR (2'b10) on AXI response. |
| `BR-04` | `tb/block/test_axil2apb_bridge.py:196` | **yes** | PASS (PASS (seed 7102, 540ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Cycles all WSTRB patterns across axil2apb_bridge and verifies captured APB PSTRB matches WSTRB (and 0 on read). |
| `BR-05` | `tb/block/test_axil2apb_bridge.py:243` | **partial** | PARTIAL (PASS on standalone single-port bridge; no dual masters) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Runs interleaved R/W on standalone single-port axil2apb_bridge rather than concurrent dual masters via crossbar (note bridge itself only has 1 AXI slave port). |
| `BR-06` | `tb/block/test_axil2apb_bridge.py:323` | **yes** | PASS (PASS (seed 7102, 260ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Holds WVALID low for several cycles after AW handshake while asserting PSEL remains 0 until W completes. |
| `UA-01` | `tb/block/test_apb_uart.py:25` | **yes** | PASS (PASS (seed 7102, 13.29us)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Streams loopback bytes across full 0x00..0xFF value space verifying RXDATA equality and FIFO flags. |
| `UA-02` | `tb/block/test_apb_uart.py:61` | **partial** | PARTIAL (PASS TX/RX full & TX_OVF; RX_OVF never tested) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Verifies TX_FULL, TX_OVF (+W1C), and RX_FULL, but omits forcing a 9th RX byte when RX_FULL to exercise RX_OVF (STATUS[5]). |
| `UA-03` | `tb/block/test_apb_uart.py:117` | **yes** | PASS (PASS (seed 7102, 10.37us)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Sweeps multiple BAUDDIV values and measures physical uart_tx pin bit duration against 16*(BAUDDIV+1) clocks. |
| `UA-04` | `tb/block/test_apb_uart.py:201` | **yes** | PASS (PASS (seed 7102, 4.09us)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Drives external uart_rx frame with stop bit=0, asserts FRAME_ERR set, clears via W1C, and validates clean next byte. |
| `UA-05` | `tb/block/test_apb_uart.py:157` | **yes** | PASS (PASS (seed 7102, 4.33us)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Toggles CTRL[3] and pops RX FIFO confirming uart_irq matches RX_IRQ_EN & ~RX_EMPTY. |
| `TM-01` | `tb/block/test_apb_timer.py:23` | **yes** | PASS (PASS (seed 7102, 290ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Programs LOAD, enables one-shot mode, and asserts TIMEOUT rises after exact LOAD+1 clocks and EN clears. |
| `TM-02` | `tb/block/test_apb_timer.py:67` | **yes** | PASS (PASS (seed 7102, 360ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Enables periodic mode and verifies repeated exact LOAD+1 interval reloads across multiple periods. |
| `TM-03` | `tb/block/test_apb_timer.py:99` | **yes** | PASS (PASS (seed 7102, 300ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Sets TIMEOUT and IRQ_EN, asserts timer_irq=1, writes 1 to STATUS[0], and verifies both clear. |
| `GP-01` | `tb/block/test_apb_gpio.py:25` | **yes** | PASS (PASS (seed 7102, 150ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Writes DIR and OUT patterns verifying gpio_dir and gpio_o outputs match bit-for-bit. |
| `GP-02` | `tb/block/test_apb_gpio.py:51` | **yes** | PASS (PASS (seed 7102, 130ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Drives gpio_i edge and verifies IN register reflects input strictly after 2 clk_sys synchronizer stages. |
| `GP-03` | `tb/block/test_apb_gpio.py:78` | **yes** | PASS (PASS (seed 7102, 270ns)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Exercises enabled/disabled rising edges and falling edges verifying IRQ_STATUS capture and W1C clearing. |
| `CS-01` | `tb/unit/test_axil_csr.py:28` | **yes** | PASS (PASS (seed 7101, 210ns)) | `/tmp/audit_work/audit_logs/step4_unit_seed7101.log` | Reads all CSR offsets 0x00..0x20 immediately after reset and confirms defaults match Spec 7.2 table. |
| `CS-02` | `tb/unit/test_axil_csr.py:64` | **yes** | PASS (PASS (seed 7101, 3.49us)) | `/tmp/audit_work/audit_logs/step4_unit_seed7101.log` | Tests ID/VERSION RO writes, SCRATCH/SCRATCH2 WSTRB, W1C_SET setting W1C_TEST, W1C clearing, and undefined SLVERR. |
| `CS-03` | `tb/unit/test_axil_csr.py:139` | **yes** | PASS (PASS (seed 7101, 330ns)) | `/tmp/audit_work/audit_logs/step4_unit_seed7101.log` | Drives each peripheral IRQ separately and combined while varying IRQ_MASK and confirming IRQ_RAW, IRQ_STATUS, and irq_o. |
| `CD-01` | `tb/block/test_axil_cdc_bridge.py:48` | **yes** | PASS (PASS (seed 7102, 13.58us)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Sweeps slow period 25.0ns, 10.3ns, 6.0ns across 3 phase alignments with RW + WSTRB data verification. |
| `CD-02` | `tb/unit/test_async_fifo.py:117` | **yes** | PASS (PASS (seed 7101, 15.18us)) | `/tmp/audit_work/audit_logs/step4_unit_seed7101.log` | Streams 400 items across fast-write/slow-read and slow-write/fast-read exercising full and empty stall boundaries. |
| `CD-03` | `tb/block/test_axil_cdc_bridge.py:87` | **partial** | PARTIAL (PASS sim; Part 2 manually pulses rst_sys_n after rst_slow_n) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Injects clk_sys mid-txn reset cleanly, then in Part 2 asserts both rst_slow_n and rst_sys_n rather than testing slow-domain-only reset recovery independently. |
| `CD-04` | `tb/block/test_axil_cdc_bridge.py:159` | **yes** | PASS (PASS (seed 7102, 2.43us)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Polls SLOW_COUNTER over different clk_slow frequencies and confirms increment deltas scale with physical clk_slow rate. |
| `CD-05` | `tb/block/test_amba_fabric_top.py:332` | **yes** | PASS (PASS (seed 7102, 22.59us)) | `/tmp/audit_work/audit_logs/step4_block_seed7102.log` | Executes concurrent interleaved M0/M1 reads and writes to SLOW_SCRATCH/SLOW_ID through top-level xbar+CDC. |

### Unmapped Tests (Exist in `tb/` with No Spec ID in Section 9.1)
Total test definitions = **55** (`tb/unit`: 12, `tb/block`: 34, `tb/pyuvm`: 9; `56` executed invocations as `TestCoverageClosure` runs 3 times):
1. `tb/unit/test_hello_world.py:43` (`test_hello_world`) — Phase 0 toolchain sanity test.
2. `tb/unit/test_rst_sync.py:7` (`test_rst_sync_basic`) — L0 reset synchronizer unit test.
3. `tb/unit/test_sync_fifo.py:7` (`test_sync_fifo_all`) — L0 synchronous FIFO unit test.
4. `tb/unit/test_async_fifo.py:133` (`test_async_fifo_dual_clock`) — Additional L0 async FIFO dual-clock check.
5. `tb/unit/test_rr_arbiter.py:7` (`test_rr_arbiter_fairness_and_lock`) — L0 arbiter fairness and lock check.
6. `tb/unit/test_axil_decoder.py:7` (`test_axil_decoder_all`) — L0 decoder unit test.
7. `tb/unit/test_axil_default_slave.py:8` (`test_axil_default_slave_all`) — L0 default slave unit test.
8. `tb/unit/test_axil_ram.py:8` (`test_axil_ram_operations`) — L0 256-word RAM sweep.
9. `tb/block/test_axil_cdc_bridge.py:204` (`test_cd_slow_id_and_unmapped`) — Slow ID + undefined offset check.
10. `tb/block/test_amba_fabric_top.py:35` (`test_top01_register_map_connectivity`) — Top-level register map smoke.
11. `tb/block/test_amba_fabric_top.py:219` (`test_top02_irq_aggregation_to_pin`) — Top-level IRQ-to-pin aggregation.
12. `tb/pyuvm/tests/test_directed.py:96` (`test_sys_write_ordering`) — Top-level write ordering check.
13. `tb/pyuvm/tests/test_directed.py:111` (`test_sys_strobe_patterns`) — Top-level strobe pattern check.
14. `tb/pyuvm/tests/test_directed.py:157` (`test_sys_contention`) — Top-level contention check.
15. `tb/pyuvm/tests/test_directed.py:179` (`TestCoverageClosure`) — Top-level closure run (invoked 3 times in `tb/pyuvm/Makefile`).

---

## 7. vplan Truthfulness Audit (`docs/vplan.md`)

| Item in `docs/vplan.md` | Claimed in vplan | Audit Verification | Verdict | Severity |
|---|---|---|---|---|
| `XB-01..06, 08..11, 13` | PASS (`seed 42`) | Functions exist in `test_axil_xbar.py` / `test_directed.py` / `test_stress.py`, pass fresh seeds (`7102`/`7103`/`501..520`) with high fidelity | PASS (aside from `XB-03` CSR omission) | - |
| `XB-07` (`docs/vplan.md:97`) | **PASS** (`test_xb07_arbitration_fairness`) | Function passes sim ONLY because it contains **0 assertions**; `m0_first`/`m1_first` unused; `MUT-10` escaped | **FALSE CLAIM** | **BLOCKER** |
| `XB-12` (`docs/vplan.md:102`) | **PASS** (`test_xb12_reset_recovery`) | Awaits `seq.start()` completion before asserting `rst_n`, testing idle reset instead of in-flight reset | **FALSE CLAIM** | **BLOCKER** |
| `XB-14` (`docs/vplan.md:104`) | **PASS** (`test_xb14_prot_passthrough`) | Never inspects APB `PPROT` in sequence or scoreboard; `MUT-09` zeroing `m_apb_pprot` passed | **FALSE CLAIM** | **BLOCKER** |
| `XB-15` (`docs/vplan.md:105`) | **PASS** (`test_xb15_unaligned_address`) | Targets RAM only (`0x5000_0000+`), missing CSR where `0x6000_0001` actually fails Rule 6 | **FALSE CLAIM** | **BLOCKER** |
| `BR-01..06, TM-01..03, GP-01..03, CS-01..03, UA-01,03,04,05, CD-01,02,04,05` | PASS | Functions exist, run cleanly with fresh seeds, and check intended DUT behavior (`BR-05` single-port, `CD-03` dual-reset partial) | PASS / PARTIAL | MINOR |
| `UA-02` (`docs/vplan.md:113`) | PASS (`test_ua02_fifo_full_and_overflow_flags`) | Exercises TX_OVF/RX_FULL, omits RX_OVF (`STATUS[5]`) leaving RTL `reg_rx_ovf` at 0% coverage | PARTIAL | MAJOR |
| **Sec 4 Functional Coverage (`docs/vplan.md:142`)** | **280 / 280 (100.00%, 0 Waivers)** | Fresh Verilator run produces **229 / 273 (83.88%)** matching `docs/logs/func_cov.log`; **44 real holes** remain | **FALSE CLAIM** | **BLOCKER** |
| **Sec 5 Formal Table (`docs/vplan.md:148-160`)** | 8 Formal Suites, 37 Cover Traces | Stale pre-remediation table (actual is 10 suites, 81 covers; `docs/results.md` updated but `vplan.md` not updated) | STALE | MINOR |

---

## 8. Coverage Honesty Audit (Step 6)

### 8.1 `sample_*` Call-Site Audit
- `./scripts/check_no_synthetic_cov.sh` passes (`/tmp/audit_work/audit_logs/step13_ci_docs_check.log`).
- Independent grep (`/tmp/audit_work/audit_logs/step3_static_and_lint.log`) confirms zero `sample_*` calls in `tb/pyuvm/sequences/`, `tb/pyuvm/tests/`, or helpers. All 9 covergroups are sampled solely inside `tb/pyuvm/monitors/fabric_monitors.py`:
  - `AxilBusMonitor` -> `sample_txn`, `sample_wstrb`, `sample_order`, `sample_backpressure` (observes physical AW/W/B/AR/R wires).
  - `CrossbarContentionMonitor` -> `sample_contention` (observes cycle-aligned M0/M1 `awvalid || arvalid`).
  - `ApbBusMonitor` -> `sample_apb` (observes physical `psel`, `penable`, `pready`, `pslverr`, `pwrite`, `pstrb`).
  - `CdcMonitor` -> `sample_cdc` (observes `axil_cdc_bridge` FSM + FIFO occupancy, **but classifies `ratio` from `os.environ.get("CLK_SLOW_PERIOD_NS")` at line 322 instead of measuring physical clock period**).
  - `UartActivityMonitor` -> `sample_uart` (observes APB writes/reads targeting UART + `baud_div`, FIFO state, status bits).
  - `ResetPhaseMonitor` -> `sample_reset` (observes `rst_n` negedge against active AXI transactions).

### 8.2 Reachability Experiment (`/tmp/audit_work/cov_reach_exp/reach_report.txt`)
Running `test_directed` + a fresh stress seed (`9201`) with `CLK_SLOW_PERIOD_NS=25.0` fixed (only `slow<sys`) and without framing-error injection yields:
- `cg_cdc.ratio`: drops from **3/3 (100%)** to **1/3 (33.33%)** (`approx_equal` and `slow>sys` remain 0 hits), `cg_cdc.cross` drops from 6/12 to **2/12 (16.67%)**.
- `cg_uart.err`: `frame_err` stays **0** (2/3, 66.67%), and overall functional coverage drops from **229/273 (83.88%)** to **223/273 (81.68%)**. Coverage responds honestly to stimulus changes.

### 8.3 Claimed vs Freshly Measured Coverage
- **Functional Coverage (`/tmp/audit_work/cov_audit/func_cov_merged.txt`):** **229 / 273 (83.88%)** — matches `docs/logs/func_cov.log` bin-for-bin, proving `docs/vplan.md:142` and `docs/results.md:140-141` (`280 / 280, 100.00%, None needed`) are false.
- **Waivers (`docs/coverage_waivers.md`):** 6 `cg_cdc.cross` `full` bins are genuinely unreachable because `axil_cdc_bridge` is single-outstanding (`ST_WAIT_RESP` blocks before pushing a second request into a depth-4 FIFO). Wait: `docs/coverage_waivers.md:43` falsely states `async_fifo.sby` "exhaustively proved" full/empty safety (it is BMC d=25). Also 44 other monitor bins (`cg_order.w_first`, `cg_apb.wait>0`, `cg_backpressure` B/R delays, `cg_uart.frame_err`, `cg_reset` in-flight, `cg_cdc.partial`, `cg_contention.one_idle R/W`) remain unwaived holes.
- **Verilator Code Coverage (`/tmp/audit_work/cov_audit/code_cov_summary.txt`):**
  - Freshly measured: **Line 90.0% (441/490)**, **Toggle 75.2% (10,164/13,514)**, **Branch 89.2% (444/498)**, **Expr 92.7% (986/1,064)**, **FSM State 100.0% (5/5)**, **FSM Arc 25.0% (1/4)**.
  - Claimed (`docs/results.md:146-151`): Line 87.8% (430/490), Toggle 75.1% (10,155/13,514), Branch 86.9% (433/498), Expr 92.9% (1,016/1,094). Denominators/numerators diverge on Expr and Lines.
  - Largest uncovered regions (`/tmp/audit_work/audit_logs/step6_uncovered_counts.txt`): `apb_uart.v` (34 uncovered: `RX_ST_STOP` framing-error branch, `reg_rx_ovf`, `reg_frame_err`, `uart_irq`), `sync_fifo.v` (22 uncovered: simultaneous `2'b11` push+pop, overflow, underflow), `axil_cdc_bridge.v` (14 uncovered: `ST_WAIT_AW`), `axil2apb_bridge.v` (13 uncovered: `ST_WAIT_AW`), `axil_csr.v` (12 uncovered: RO writes, WO reads, `w_done`), `apb_gpio.v` (10 uncovered: `gpio_i` edge/IRQ logic in top-level sim).

---

## 9. Formal Verification Audit (Step 7)

All 10 `.sby` suites execute cleanly under `make formal` (`/tmp/audit_work/audit_logs/step2_formal.log`) using `smtbmc boolector` with 81 total cover traces reached:

| Suite | Mode | Depth | Solver | Result | Covers | Audit Assessment |
|---|---|---:|---|---|---|---|
| `apb_timer.sby` | `prove` (k-ind) + `cover` | 20 | boolector | PASS | 4 | Sound k-induction; precondition reset/enable covers reachable. |
| `apb_uart.sby` | `bmc` + `cover` | 25 | boolector | PASS | 9 | Bounded check only; covers cover TX/RX FIFO, status flags, W1C. |
| `async_fifo.sby` | `bmc` (multiclock) + `cover` | 25 | boolector | PASS | 4 | Magic-value + Gray transitions hold up to depth 25; **waivers.md:43 falsely says "exhaustively proven"**. |
| `axil2apb_bridge.sby` | `bmc` + `cover` | 25 | boolector | PASS | 8 | Bounded liveness <12 cyc under 4-cyc fair APB slave; **over-assumes `!s_axil_arvalid` when `awvalid` or `wvalid` (`bridge_props.v:156`)**. |
| `axil_cdc_bridge.sby` | `bmc` (multiclock) + `cover` | 30 | boolector | PASS | 7 | Verifies dual-clock FIFO handshake + `SLOW_ID` read integrity + `axil_props`. |
| `axil_csr.sby` | `prove` (k-ind) + `cover` | 20 | boolector | PASS | 5 | Sound k-induction for CSR ops, **but `CHECK_CAUSALITY(0)` at `axil_csr.v:269` disables AXI request-response balance check**, and misses `[1:0]` rule. |
| `axil_ram.sby` | `bmc` + `cover` | 20 | boolector | PASS | 5 | Verifies bounds SLVERR and WSTRB up to depth 20 + `axil_props`. |
| `axil_xbar.sby` | `bmc` + `cover` | 20 | boolector | PASS | 29 | Checks routing lock + `axil_props` across 6 ports + bounded liveness <18 cyc; **over-assumes slave `bvalid` within 3 cyc of `awvalid` without requiring `wvalid` (`xbar_props.v:377,396`)**. |
| `rr_arbiter.sby` | `prove` (k-ind) + `cover` | 20 | boolector | PASS | 4 | **Orphans `formal/rr_arbiter_props.v`**; inline RTL formal has **no bounded-fairness assertion** for persistent requests. |
| `sync_fifo.sby` | `prove` (k-ind) + `cover` | 20 | boolector | PASS | 6 | Pointer/count safety proved; **no data-ordering assertion** despite `README.md:158` claiming data ordering was proved. |

---

## 10. Register Compliance, Address Map, and AXI4-Lite Rules

| ID | Requirement | Status | Severity | Evidence | Measured Result | Notes |
|---|---|---|---|---|---|---|
| `AM-S0` | S0 APB subsystem base 0x4000_0000 (64 KB) | PASS | - | `rtl/axil/axil_decoder.v:6` | S0_BASE=32'h4000_0000, S0_MASK=32'hFFFF_0000 (64KB) | axil_decoder routes 0x4000_0000-0x4000_FFFF to S0 (axil2apb_bridge); verified by probe_01 at UART/Timer/GPIO and unmapped 0x4000_F000. |
| `AM-S0-UART` | S0 APB UART window 0x4000_0000 (4 KB) | PASS | - | `rtl/apb/apb_decoder.v:58` | paddr[15:12]==4'h0 selects psel_uart | apb_decoder selects UART when PADDR[15:12] == 0x0; UART TX/CTRL/STATUS readback passed in probe_06. |
| `AM-S0-TIMER` | S0 APB Timer window 0x4000_1000 (4 KB) | PASS | - | `rtl/apb/apb_decoder.v:61` | paddr[15:12]==4'h1 selects psel_timer | apb_decoder selects Timer when PADDR[15:12] == 0x1; timer registers at 0x4000_1000-0x4000_100C verified in probe_04. |
| `AM-S0-GPIO` | S0 APB GPIO window 0x4000_2000 (4 KB; other APB -> PSLVERR) | PASS | - | `rtl/apb/apb_decoder.v:64; rtl/apb/apb_decoder.v:69` | paddr[15:12]==4'h2 selects GPIO; >=4'h3 -> PSLVERR | GPIO decoded at PADDR[15:12]==0x2 and unmapped 0x4000_F000 returned SLVERR=2 via bridge PSLVERR in probe_01. |
| `AM-S1` | S1 Scratch RAM 0x5000_0000 (4 KB window, RAM_DEPTH*4 backed, rest SLVERR) | PASS | - | `rtl/axil/axil_decoder.v:8; rtl/axil/axil_ram.v:60` | S1_MASK=FFFF_F000 (4KB); addr[11:2]<256 backed, >=256 SLVERR | axil_ram backs 0x5000_0000..0x5000_03FF (1KB) and responds SLVERR for 0x5000_0400..0x5000_0FFC as proven in probe_03. |
| `AM-S2` | S2 CSR block 0x6000_0000 (256 B) | PASS | - | `rtl/axil/axil_decoder.v:10` | S2_BASE=32'h6000_0000, S2_MASK=32'hFFFF_FF00 (256B) | axil_decoder decodes exact 256 B window 0x6000_0000-0x6000_00FF to S2 CSR; 0x6000_0100 falls through to DECERR in probe_01. |
| `AM-S3` | S3 CDC bridge slow regs 0x7000_0000 (256 B, undef -> SLVERR) | PASS | - | `rtl/axil/axil_decoder.v:12; rtl/cdc/slow_regs.v:119` | S3_BASE=32'h7000_0000, S3_MASK=32'hFFFF_FF00 (256B) | axil_decoder selects S3 on 0x7000_0000-0x7000_00FF; slow_regs returns SLVERR on undefined offset 0x7000_0080 in probe_01. |
| `AM-DEF` | Default slave everything else -> DECERR | PASS | - | `rtl/axil/axil_decoder.v:33; rtl/axil/axil_default_slave.v:4` | decode_err=1 routes to default slave returning resp=2'b11 | probe_01 confirmed read/write DECERR (resp=3) at 0x0000_0000, 0x3FFF_FFFC, 0x4001_0000, 0x5000_1000, 0x6000_0100, and 0x8000_0000. |
| `REG-CSR-00` | CSR 0x00 ID (RO, reset 0xA3BA0001) | PASS | - | `rtl/axil/axil_csr.v:112` |  | Read 0xA3BA0001; write ignored with OKAY (probe_02 aligned passed) |
| `REG-CSR-04` | CSR 0x04 VERSION (RO, reset 0x00010000) | PASS | - | `rtl/axil/axil_csr.v:115` |  | Read 0x00010000; write ignored with OKAY |
| `REG-CSR-08` | CSR 0x08 SCRATCH (RW, reset 0) | PASS | - | `rtl/axil/axil_csr.v:118` |  | Reset 0; full-word RW; Note WSTRB intentionally full-word per spec |
| `REG-CSR-0C` | CSR 0x0C SCRATCH2 (RW, reset 0, byte-writable WSTRB) | PASS | - | `rtl/axil/axil_csr.v:122` |  | Reset 0; per-byte WSTRB[3:0] verified in probe_02 & cs02 |
| `REG-CSR-10` | CSR 0x10 IRQ_RAW (RO, reset 0, [2:0]={gpio,timer,uart}) | PASS | - | `rtl/axil/axil_csr.v:129` |  | Reset 0; RO bit [0] UART, [1] TIMER, [2] GPIO verified |
| `REG-CSR-14` | CSR 0x14 IRQ_MASK (RW, reset 0, [2:0] enable) | PASS | - | `rtl/axil/axil_csr.v:132` |  | Reset 0; RW [2:0] mask verified in test_cs03 & top02 |
| `REG-CSR-18` | CSR 0x18 IRQ_STATUS (RO, reset 0, IRQ_RAW & IRQ_MASK) | PASS | - | `rtl/axil/axil_csr.v:136` |  | Reset 0; RO reg_irq_raw & reg_irq_mask verified |
| `REG-CSR-1C` | CSR 0x1C W1C_TEST (W1C, reset 0) | PASS | - | `rtl/axil/axil_csr.v:139` |  | Reset 0; writing 1 clears bits cleanly in cs02 & probe_02 |
| `REG-CSR-20` | CSR 0x20 W1C_SET (WO, reads 0, sets W1C_TEST) | PASS | - | `rtl/axil/axil_csr.v:143` |  | WO set hook sets W1C_TEST bits; read returns 0 OKAY |
| `REG-UART-00` | UART 0x00 TXDATA (WO, [7:0] push TX FIFO, sets TX_OVF when full) | PASS | - | `rtl/apb/apb_uart.v:345` |  | Writes [7:0] push TX FIFO; full write sets TX_OVF; read returns 0 |
| `REG-UART-04` | UART 0x04 RXDATA (RO, [7:0] pop RX FIFO, empty->0) | PASS | - | `rtl/apb/apb_uart.v:357` |  | Reads [7:0] pop RX FIFO; empty read returns 0 cleanly |
| `REG-UART-08` | UART 0x08 STATUS (RO/W1C [7:0] flags) | PARTIAL | MAJOR | `rtl/apb/apb_uart.v:411` | TX_FULL/EMPTY/RX_EMPTY/FRAME_ERR/TX_OVF/TX_BUSY pass; RX_OVF untested in UA-02 | STATUS bit layout matches Spec 7.3 [7:0] and W1C clears bits [6:4], but UA-02 never tests RX FIFO overflow bit [5]. |
| `REG-UART-0C` | UART 0x0C CTRL (RW, [3:0] TX/RX/LOOP/RX_IRQ_EN) | PASS | - | `rtl/apb/apb_uart.v:387` |  | Reset 0; bits [3:0] control TX_EN, RX_EN, LOOPBACK, RX_IRQ_EN |
| `REG-UART-10` | UART 0x10 BAUDDIV (RW, [15:0] divisor) | PASS | - | `rtl/apb/apb_uart.v:388` |  | Reset 0; 16-bit divisor drives 16x baud_tick cleanly |
| `REG-TIMER-00` | TIMER 0x00 CTRL (RW, [2:0] EN/PERIODIC/IRQ_EN) | PASS | - | `rtl/apb/apb_timer.v:70` |  | Reset 0; EN rising loads VALUE from LOAD; one-shot auto-clears EN |
| `REG-TIMER-04` | TIMER 0x04 LOAD (RW, [31:0] reload value) | PASS | - | `rtl/apb/apb_timer.v:77` |  | Reset 0; 32-bit reload register verified in TM-01/TM-02 |
| `REG-TIMER-08` | TIMER 0x08 VALUE (RO, [31:0] current count) | PASS | - | `rtl/apb/apb_timer.v:80` |  | Reset 0; RO down-counter; writes ignored |
| `REG-TIMER-0C` | TIMER 0x0C STATUS (W1C, [0] TIMEOUT) | PASS | - | `rtl/apb/apb_timer.v:82` |  | Reset 0; set on VALUE==0; W1C bit 0 clears TIMEOUT & IRQ |
| `REG-GPIO-00` | GPIO 0x00 DIR (RW, [15:0] 1=output) | PASS | - | `rtl/apb/apb_gpio.v:79` |  | Reset 0; 16-bit direction output gpio_dir verified |
| `REG-GPIO-04` | GPIO 0x04 OUT (RW, [15:0] output value) | PASS | - | `rtl/apb/apb_gpio.v:80` |  | Reset 0; 16-bit gpio_o updated on write |
| `REG-GPIO-08` | GPIO 0x08 IN (RO, [15:0] 2-FF synchronized gpio_i) | PASS | - | `rtl/apb/apb_gpio.v:107` |  | Reset 0; 2-FF sync_gpio_q2 read-only; writes ignored |
| `REG-GPIO-0C` | GPIO 0x0C IRQ_EN (RW, [15:0] per-pin enable) | PASS | - | `rtl/apb/apb_gpio.v:82` |  | Reset 0; per-pin mask gates rising-edge interrupt latch |
| `REG-GPIO-10` | GPIO 0x10 IRQ_STATUS (W1C, [15:0] rising-edge detect) | PASS | - | `rtl/apb/apb_gpio.v:83` |  | Reset 0; latches rising edge on sync_gpio_q2; W1C clear |
| `REG-SLOW-00` | CDC 0x00 SLOW_ID (RO, reset 0x510E0001) | PASS | - | `rtl/cdc/slow_regs.v:128` |  | Reads 0x510E0001 across CDC; write ignored OKAY |
| `REG-SLOW-04` | CDC 0x04 SLOW_SCRATCH (RW, WSTRB-aware) | PASS | - | `rtl/cdc/slow_regs.v:79` |  | Reset 0; byte-strobe RW across CDC confirmed |
| `REG-SLOW-08` | CDC 0x08 SLOW_COUNTER (RO, clk_slow free-running counter) | PASS | - | `rtl/cdc/slow_regs.v:64` |  | Reset 0; increments in clk_slow when SLOW_CTRL[0]==1 |
| `REG-SLOW-0C` | CDC 0x0C SLOW_CTRL (RW, [0] counter enable, reset 1) | PASS | - | `rtl/cdc/slow_regs.v:56` |  | Reset 1'b1 (counter enabled); bit [0] pauses/resumes counter |
| `REG-SLOW-ERR` | CDC undefined offsets (>=0x10) -> SLVERR | PASS | - | `rtl/cdc/slow_regs.v:119` |  | req_addr_q[7:4]!=0 returns 2'b10 SLVERR across CDC |
| `AXIL-R1` | Rule 1: VALID and payload stable until READY | PASS | - | `formal/axil_props.v:68` | Checked formally on xbar/bridge/ram/csr/cdc and by AxilBusMonitor | Hold-until-READY rules hold on all master and slave RTL interfaces across simulation and SymbiYosys proofs. |
| `AXIL-R2` | Rule 2: Master must not wait for READY; slave may wait for AWVALID/WVALID | PASS | - | `rtl/axil/axil_xbar.v:217; docs/bugs.md:212` | WREADY waits on AW grant lock; W-before-AW unstuck (BUG-022 fix) | Crossbar holds WREADY until AW is locked (wr_locked), avoiding WREADY-before-AW deadlock while allowing staggered AW/W. |
| `AXIL-R3` | Rule 3: BVALID only after both AW and W handshakes complete | PASS | - | `formal/axil_props.v:152` | Asserted in axil_props.v and verified in BR-06/XB-08 | Bridge, CSR, RAM, CDC bridge, and default slave all wait for both AW and W acceptance before asserting BVALID. |
| `AXIL-R4` | Rule 4: RVALID only after AR handshake completes | PASS | - | `formal/axil_props.v:214` | Asserted formally on all 5 slave/interconnect blocks | Read response assertion ensures pending_rd > 0 whenever RVALID rises across crossbar and all AXI-Lite slaves. |
| `AXIL-R5` | Rule 5: Exactly one response per transaction | PASS | - | `formal/axil_props.v:155; formal/axil_props.v:218` | No spurious BVALID/RVALID; 200,000 stress txns matched 1:1 | Response counters in axil_props.v and pyuvm scoreboard confirm strict 1:1 request-response pairing across 200k transactions. |
| `AXIL-R6` | Rule 6: Address LSBs [1:0] ignored (word-aligned access) | FAIL | BLOCKER | `rtl/axil/axil_csr.v:68; rtl/axil/axil_csr.v:158` | FAIL: axil_csr decodes full addr[7:0], returning SLVERR at +0x1 | axil_ram, apb peripherals, and slow_regs ignore [1:0], but axil_csr checks addr[7:0] literally, breaking Rule 6 as proven by probe_02 on 0x6000_0001. |
| `AXIL-R7` | Rule 7: Read and write channels independent (no RW ordering) | PASS | - | `rtl/axil/axil_xbar.v:123; rtl/axil/axil_csr.v:73` | Separate rd/wr arbiters in xbar; concurrent R/W verified in XB-05..13 | Crossbar provides independent read and write arbiters so reads and writes to the same or different slaves run concurrently. |

---

## 11. Independent Probe Tests (Step 8)

Written independently in `/tmp/audit_work/probes/test_audit_probes.py` against `amba_fabric_top` from `docs/spec.md` tables (`/tmp/audit_work/audit_logs/step8_probes.log`, Result: **7/8 PASS, 1 FAIL**):

| Probe ID | Spec Scenario | Status | Severity | Notes |
|---|---|---|---|---|
| `PROBE-01` | Probe 1: Address decode for every mapped slave + unmapped DECERR | PASS | - | 990ns, all S0-S3 & 6 unmapped regions return expected OKAY/SLVERR/DECERR — Verified M0 and M1 decode to APB UART/Timer/GPIO, RAM, CSR, CDC, APB unmapped SLVERR, and 6 unmapped regions returning DECERR. |
| `PROBE-02` | Probe 2: Reset values, RO/RW/W1C/WO access, and Rule 6 [1:0] across all regs | FAIL | BLOCKER | FAIL at 0x6000_0001 CSR ID unaligned read: resp=2 (SLVERR) data=0x0 — Independent black-box register probe caught axil_csr.v violating Spec Section 6 Rule 6 on byte-unaligned read 0x6000_0001. |
| `PROBE-03` | Probe 3: RAM out-of-range inside 4 KB window returns SLVERR | PASS | - | 190ns, 0x5000_03FC OKAY vs 0x5000_0400 & 0x5000_0FFC SLVERR — Black-box probe confirmed backed boundary word 255 works while OOR word 256+ writes/reads return SLVERR without wrap-around corruption. |
| `PROBE-04` | Probe 4: Timer period equals LOAD+1 cycles in one-shot and periodic | PASS | - | 990ns, LOAD=9 triggers timeout at exact cycle 10; periodic reloads cleanly — Probe counted bus clocks after CTRL.EN assertion and verified exact LOAD+1=10 cycle timeout latency and W1C clearing. |
| `PROBE-05` | Probe 5: GPIO 2-FF input synchronizer latency and rising-edge IRQ | PASS | - | 380ns, 2-cycle latency confirmed on IN; rising-edge IRQ_STATUS + W1C pass — Probe toggled external gpio_i and measured exact 2 clk_sys stages before IN updates plus edge-triggered IRQ assertion. |
| `PROBE-06` | Probe 6: UART 8N1 loopback & external RX bad stop-bit framing error | PASS | - | 3.88us, loopback 0xA5/0x5A pass; bad stop bit sets STATUS.FRAME_ERR[4] — Probe transmitted bytes in loopback and bit-banged an external 0-stop-bit UART frame to verify FRAME_ERR and recovery. |
| `PROBE-07` | Probe 7: CDC access at two clock ratios (slow<sys 33ns & slow>sys 6ns) | PASS | - | 2.37us, SLOW_SCRATCH & SLOW_COUNTER accurate at 33ns and 6ns slow clocks — Probe reconfigured clk_slow mid-test from 33ns to 6ns and verified SLOW_ID, SLOW_SCRATCH WSTRB, and scaled SLOW_COUNTER ticks. |
| `PROBE-08` | Probe 8: Two-master same-slave contention and different-slave parallelism | PASS | - | 670ns, zero-corruption same-slave contention + parallel different-slave access — Probe launched concurrent M0/M1 writes to RAM (no corruption) and parallel M0->RAM / M1->CSR transfers completing simultaneously. |

---

## 12. Sanity Mutation Injection (Step 9)

10 deliberate RTL defects injected into temporary copies of the RTL under `/tmp/audit_work/mutants_sanity/` (`/tmp/audit_work/audit_logs/step9_sanity_summary.txt`): **8/10 CAUGHT, 2/10 ESCAPED**:

| Sanity Mutant | Defect Injected | Caught / Escaped | Checking Suite(s) |
|---|---|---|---|
| `SMUT-01` | Inject arbiter priority swap in rr_arbiter.v | **PASS** (CAUGHT) | CAUGHT by unit test_rr_arbiter (ESCAPED xbar XB-07) |
| `SMUT-02` | Inject dropped WSTRB[2] bit in axil_ram.v | **PASS** (CAUGHT) | CAUGHT by unit test_axil_ram & pyuvm test_directed |
| `SMUT-03` | Inject Gray-pointer encoding error in async_fifo.v | **PASS** (CAUGHT) | CAUGHT by unit test_async_fifo (timeout/mismatch) |
| `SMUT-04` | Inject PSLVERR mapped to OKAY in axil2apb_bridge.v | **PASS** (CAUGHT) | CAUGHT by block test_axil2apb_bridge & pyuvm test_directed |
| `SMUT-05` | Inject timer off-by-one LOAD period in apb_timer.v | **PASS** (CAUGHT) | CAUGHT by block test_apb_timer |
| `SMUT-06` | Inject DECERR changed to SLVERR in axil_default_slave.v | **PASS** (CAUGHT) | CAUGHT by unit test_axil_default_slave & block test_axil_xbar |
| `SMUT-07` | Inject APB PENABLE asserted one cycle early in axil2apb_bridge.v | **PASS** (CAUGHT) | CAUGHT by block test_axil2apb_bridge |
| `SMUT-08` | Inject FIFO full flag off-by-one in sync_fifo.v | **PASS** (CAUGHT) | CAUGHT by unit test_sync_fifo |
| `SMUT-09` | Inject m_apb_pprot forced to 3'b000 in axil2apb_bridge.v | **FAIL** (BLOCKER) | ESCAPED BOTH block test_axil2apb_bridge and pyuvm test_xb14_prot_passthrough |
| `SMUT-10` | Inject stuck write priority wr_prio[gt]<=0 in axil_xbar.v | **FAIL** (BLOCKER) | ESCAPED block test_xb07_arbitration_fairness |

---

## 13. Mutation Report Audit (Step 10)

### 13.1 Fresh `run_mutants.py` Execution (`/tmp/audit_work/audit_logs/step10_mutation_240.log`)
| Module | Fresh Gen | Fresh Killed | Fresh Survived | Fresh Score | Claimed in `docs/mutation_report.md` |
|---|---:|---:|---:|---:|---|
| `rr_arbiter` | 30 | 25 | 5 | 83.33% | 25/30 (83.33%) |
| `sync_fifo` | 30 | 29 | 1 | 96.67% | 29/30 (96.67%) |
| `async_fifo` | 30 | 30 | 0 | 100.00% | 30/30 (100.00%) |
| `axil_decoder` | 30 | 27 | 3 | 90.00% | 27/30 (90.00%) |
| `axil_ram` | 30 | 19 | 11 | 63.33% | 18/30 (60.00%) |
| `axil_csr` | 30 | 16 | 14 | 53.33% | 15/30 (50.00%) |
| `axil2apb_bridge` | 30 | 22 | 8 | 73.33% | 22/30 (73.33%) |
| `axil_xbar` | 30 | 15 | 15 | 50.00% | 30/30 (100.00%) |
| **TOTAL** | **240** | **183** | **57** | **76.25%** | **196/240 (81.67%)** |

- Sampled CI run (`--max-mutants 24`, `/tmp/audit_work/audit_logs/step10_mutation_sample.log`) finished in **39.16 s**: **19 / 24 killed (79.17%)** (`axil_csr` 1/3, `axil_xbar` 1/3, `axil2apb_bridge` 2/3).
- Scope note: `mutation/run_mutants.py` sets `prep_top: tb_axil_xbar`, so `axil_xbar` mutations also mutate wrapper/submodules (`axil_decoder`, `axil_default_slave`, `tb_axil_xbar`), producing **15/30 (50.00%, 15 survived)** in the fresh run and **183/240 (76.25%, 57 survived)** overall vs claimed **196/240 (81.67%)**.
- Tool bug discovered: `mutation/run_mutants.py:208` calls `subprocess.run(cmd, timeout=40)` on `make` without process-group isolation, leaking timed-out `vvp` processes in the background during `async_fifo` / `axil2apb_bridge`.

### 13.2 Triage, Arithmetic, and Git History Verification
- **Duplicate file:** `docs/mutation_report.md` and `docs/mutation_triage.md` are byte-identical (`diff -s` exits 0).
- **Arithmetic & fabricated survivor contradiction:** Table claims `axil_xbar` **30 killed / 0 survived / 1 equivalent** (`30 / (30 - 1) = 103.4%`) and Section 3 lists survivor `[axil_xbar #29]` (`mutation.log` has **0** `axil_xbar` survivors). For `axil_ram`, table claims **8** equivalent mutants while Section 3 lists **10** mutant IDs (`#5, 6, 9, 11, 14, 15, 22, 23, 26, 29`).
- **Spot-check of 5 survivors from `docs/logs/mutation.log`:**
  1. `rr_arbiter #11` (`const0` on `$logic_and$15` at `rr_arbiter.v:35`): **Agree Equivalent** — redundant branch in 2-requester wrap-around logic.
  2. `axil_csr #9` (`const1` on `write_data[17]` mux `w_done ? wdata_q : s_axil_wdata` at `axil_csr.v:69`): **Disagree (Test Gap)** — labeled "unused bits", actually exposes lack of `w_first` delayed write data verification on bit 17 in `test_axil_csr.py`.
  3. `axil_csr #22` (`const1` on `s_axil_rresp` mux `axil_csr.v:169`): **Disagree (Test Gap)** — unkilled `RRESP` bit error due to weak CSR read-response assertions on `0x20` / `default`.
  4. `axil_csr #29` (`cnot0` on `reg_scratch[2]` vs ctrl bit 15): **Disagree (Test Gap)** — exposes correlated walking test patterns missing independent bit 2 vs bit 15 distinction.
  5. `axil2apb_bridge #9` (`cnot0` on `s_axil_arprot[2]` at `axil2apb_bridge.v:123`): **Disagree (Test Gap)** — proves unit/block read tests never verify `arprot[2]` reaches `m_apb_pprot[2]` (also confirmed by `MUT-09` escape).
- **Git history check (`/tmp/audit_work/audit_logs/step10_git_history.log`):** Commits `fe1816d` and `215c37a` genuinely exist and added the 5 claimed testbench improvements.

---

## 14. Seeds and Stress (Step 11)

Ran **20 fresh seeds (`501`..`520`)** outside all project logs via `/tmp/audit_work/run_20seeds.sh` (`/tmp/audit_work/audit_logs/step11_20seeds.log`, exit code **0**):
- Every seed executed `5,000` M0 + `5,000` M1 = **10,000 transactions/seed** (per-seed logs verified `Total=10000`, `Mismatches=0`).
- **Aggregate fresh stress total:** **200,000 transactions**, **0 scoreboard mismatches**, **20 / 20 PASS** (matching Spec Section 9.1 `XB-13` volume).

---

## 15. Synthesis and STA (Step 12)

| Metric | Freshly Measured (`make synth` / `make sta`) | Claimed (`README.md:135-137` & `docs/results.md:22-23`) | Match? |
|---|---:|---:|---|
| Synthesis script `synth/synth.ys` | **NOT FOUND** in `git ls-files` (inlined in `Makefile:120`) | Linked in `README.md:135,320` & Spec Sec 15 | **NO** |
| Total Cells (SKY130 HD, `RAM_DEPTH=64`) | **9,320 cells** (`/tmp/audit_work/audit_logs/step12_synth.log`) | 9,376 cells | **NO** (-56 cells) |
| Flip-Flops | **3,623 flops** (`1133 dfrtp_1`, `10 dfstp_1`, `2480 edfxtp_1`) | 3,623 flops | YES |
| Total Chip Area | **138,031.13 um2** | 137,867.23 um2 | **NO** (+163.90 um2) |
| Target `clk_sys` 100 MHz (10.0 ns) WNS / TNS | **WNS = -19.33 ns, TNS = -55,333.66 ns** | WNS = -2.25 ns, TNS = -9,097.77 ns | **NO** |
| Achieved System Fmax | **< 62.5 MHz** (`16.00 ns` sweep has WNS = -13.33 ns) | 81.63 MHz (12.25 ns) | **NO** |
| Async clock group & SDC clocks | `clk_sys` 10 ns, `clk_slow` 24 ns, `set_clock_groups -asynchronous` | Async clock groups present | YES (Gray rationale omitted in README) |

**Root Cause of Discrepancy:** `synth/sta.tcl:22-23` and `synth/fmax_sweep.py:37-38` hardcode stale Yosys netlist instance names (`_14798_`, `_14800_`) for false-path reset exceptions. In the freshly synthesized netlist, the slow-domain reset synchronizer flop is `_14686_`, leaving a 21.43 ns high-fanout (`3.55 pF`) unconstrained reset-to-flop path active. Worse, `synth/fmax_sweep.py:130-139` prints a **hardcoded `"81.63 MHz"` and `"_12691_/DE"` critical-path breakdown** even when the actual sweep fails every period!

---

## 16. CI and Documentation Audit (Step 13)

- **CI (`/tmp/audit_work/audit_logs/step13_ci_docs_check.log`):** `.github/workflows/ci.yml` syntax is valid, uses `YosysHQ/setup-oss-cad-suite@v3` (`2026-11-22`), and every local CI command (`check_no_synthetic_cov.sh`, `make lint`, `make unit`, `make block`, `make regress SEEDS=3` structure, `make formal`, `make mutation-sample`) works from clean clone. However, `gh` CLI is absent (`CI-REMOTE = NOT_RUN`), so `README.md:138` & `docs/results.md:24` `CI Status: PASS` claims are unverified; CI also uploads `docs/logs/` & `synth/results/` which are not regenerated by CI steps.
- **README Verification:**
  - Quick start succeeds (`make cov-report` fails on 674 MB `/tmp`). Badges point to `i-am-somasai/AMBA-AXI4-Lite-APB4-Fabric-Subsystem-pyuvm-Verification-Environment`.
  - **Inconsistencies:** UART FIFO depth (`8`) and peripheral addresses (`0x4000_0000`, `0x4000_1000`, `0x4000_2000`) match RTL, and Sec 5.1 honestly distinguishes `pyuvm` master agents from cocotb responder models (`Verilog-2005 / SystemVerilog` note matches). However, README claims **54** testcases vs actual **55** defs (**56** runs), **3,238** RTL lines vs **3,759**, `22` bugs at line 133 vs `21` bugs at lines 195/297, links non-existent `docs/img/contention.vcd` (line 219) and `synth/synth.ys` (lines 135, 320), omits the Spec 13.2 Gray-pointer STA rationale, and repeats stale resume numbers.
- **`docs/bugs.md` (`/tmp/audit_work/audit_logs/step13_bugs_schema.log`):** All 22 entries (`BUG-001..BUG-022`) include Symptom, Discovery Method, Root Cause, Fix, and Regression Test, except `BUG-022` (`docs/bugs.md:219`) cites non-existent `tb/pyuvm/tests/test_xb09_backpressure_burst.py`.
- **`docs/decisions.md`:** Logs `DEC-001`..`DEC-005`, but misses 4 concrete spec/interface deviations (`axil_decoder.v` vs `docs/interfaces.md:115`, `axil_csr.v` `[1:0]` decode bug, `axil_xbar.v` inline arbiter instead of `rr_arbiter`, and inlining `synth/synth.ys` into `Makefile`).

---

## 17. Metric Honesty Table (Step 14)

| ID | Metric | Claimed (`README.md` / `docs/results.md`) | Source Log Cited | Freshly Measured | Match? |
|---|---|---|---|---|---|
| `METRIC-01` | RTL Modules / Lines of RTL | 17 modules / 3,238 lines | `README.md:124; docs/results.md:12` | 17 modules / 3,759 lines | **NO** (FAIL) |
| `METRIC-02` | Tests (Directed / Random & Total Testcases) | 40/40 Spec Tests PASS (54 executable testcases) | `README.md:125; docs/results.md:13` | 35/40 high-fidelity spec tests (55 defs, 56 executed runs) | **NO** (FAIL) |
| `METRIC-03` | Random Transactions Executed (XB-13) | 200,000 transactions (20 seeds x 10,000, 0 mismatches) | `README.md:126; docs/results.md:14` | 200,000 transactions (20 seeds x 10,000, 0 mismatches) | **YES** (PASS) |
| `METRIC-04` | Regression Seeds Passed | 20 / 20 seeds passed (1..20) | `README.md:127; docs/results.md:15` | 20 / 20 fresh seeds passed (seeds 501-520) | **YES** (PASS) |
| `METRIC-05` | Functional Coverage (bins hit / total) | 83.88% (README/results:16,139) vs 280/280 100% (vplan:142 & results:140-141) | `README.md:128; docs/vplan.md:142; docs/results.md:139-141` | 83.88% (229 / 273 bins hit) | **NO** (FAIL) |
| `METRIC-06` | Code Coverage (Line / Toggle / Branch / Expr / FSM) | Line 87.8% (430/490), Toggle 75.1%, Branch 86.9%, Expr 92.9% (1016/1094) | `README.md:129; docs/results.md:146-151` | Line 90.0% (441/490), Toggle 75.2%, Branch 89.2%, Expr 92.7% (986/1064), FSM State 100%, Arc 25% | **NO** (FAIL) |
| `METRIC-07` | Formal Properties / BMC Depth / k-induction / Covers | 10/10 modules passing, 81 covers, unified checker on all, zero overclaiming | `README.md:130; docs/results.md:18` | 10/10 .sby pass (4 prove d=20, 6 bmc d=20-30, 81 covers); rr_arbiter_props unused & 3 caveats | **NO** (PARTIAL) |
| `METRIC-08` | CDC Clock Ratios and Phases Swept | 2.5:1 ratio, 3 ratio bins closed, multiclock BMC | `README.md:131; docs/results.md:19` | 3 slow ratios (25ns, 10.3ns, 6.0ns) x 3 phases + top sweeps | **YES** (PASS) |
| `METRIC-09` | Mutants Generated / Killed / Equivalent / Score | 240 mutants, 196 killed, 28 equiv, 81.67% raw / 92.45% true | `README.md:132; docs/mutation_report.md:1` | Fresh 240 run: 183/240 (76.25%); doc claims 30/29 (103.4%) & phantom survivor | **NO** (FAIL) |
| `METRIC-10` | Bugs Found and Fixed (count & 3 showcase stories) | 22 bugs (README:133) vs 21 bugs (README:195,297) | `README.md:133; README.md:195; docs/bugs.md:219` | 22 entries in bugs.md; BUG-022 cites missing test_xb09_backpressure_burst.py; README says 22 at L133 vs 21 at L195 | **NO** (FAIL) |
| `METRIC-11` | Crossbar Added Latency (Cycles) | 0 cycles added latency (proven in XB-06) + docs/img/contention.vcd | `README.md:134; docs/results.md:21` | XB-06 parallel M0/M1 completion passes (<= 1 cycle target met); docs/img/contention.vcd missing | **NO** (PARTIAL) |
| `METRIC-12` | Synthesis: Cells / Flops / Area (um2) | 9,376 cells / 3,623 flops / 137,867.23 um2 | `README.md:135; docs/results.md:22` | 9,320 cells / 3,623 flops / 138,031.13 um2 (synth.ys missing) | **NO** (FAIL) |
| `METRIC-13` | STA: WNS / TNS @ 10 ns, Achieved Fmax | WNS=-2.25 ns, TNS=-9,097.77 ns, Fmax=81.63 MHz | `README.md:136-137; docs/results.md:23` | WNS=-19.33 ns, TNS=-55,333.66 ns, Fmax < 62.5 MHz | **NO** (FAIL) |
| `METRIC-14` | Continuous Integration Status | PASS (Automated GitHub Actions CI + badge) | `README.md:138; docs/results.md:24` | NOT_RUN on remote GitHub; local YAML targets pass | **NO** (NOT_RUN) |

---

## 18. Findings Register (`BLOCKER`, `MAJOR`, `MINOR`, `INFO`)

| ID | Section | Status | Severity | Summary |
|---|---|---|---|---|
| `F-01` | Features | PARTIAL | **MINOR** | Crossbar decodes S0-S3 and default slave, but axil_decoder.v:5-18 diverges from docs/interfaces.md:115 ([1:0] vs 4-bit one-hot + parameters) without entry in docs/decisions.md. |
| `F-02` | Features | FAIL | **BLOCKER** | rtl/axil/axil_xbar.v duplicates inline wr_prio/rd_prio instead of reusing rr_arbiter.v, XB-07 has zero assertions, and sanity mutant MUT-10 (stuck write priority) escaped. |
| `F-05` | Features | FAIL | **BLOCKER** | axil_csr switches on full 8-bit write_offset/read_offset instead of masking [1:0]=0, returning SLVERR on 0x6000_0001 in probe_02 contrary to Spec Section 6 Rule 6. |
| `F-06` | Features | PARTIAL | **MAJOR** | RTL drives APB phases cleanly (MUT-04, MUT-07 killed), but MUT-09 zeroing m_apb_pprot escaped both block test and pyuvm test_xb14, and BR-05 tests bridge without dual masters. |
| `F-08` | Features | PARTIAL | **MAJOR** | UART TX/RX/loopback/BAUDDIV/FRAME_ERR pass block tests and probe_06, but UA-02 omits RX FIFO overflow testing leaving reg_rx_ovf (apb_uart.v:339) uncovered at 0%. |
| `V-01` | Features | PARTIAL | **MINOR** | Spec calls for pyuvm slave and APB responder agents; only AxilMasterAgent uses pyuvm while responders in tb/models/ are plain cocotb coroutines (honestly logged in DEC-005). |
| `V-02` | Features | PARTIAL | **MAJOR** | FabricScoreboard checks 200k random transactions cleanly, yet SlowRegsModel masks offset & 0xFC inconsistently with axil_csr (missing Rule 6 bug), and PPROT is unverified. |
| `V-04` | Features | FAIL | **BLOCKER** | Re-run produces 229/273 (83.88%) matching func_cov.log; 44 monitor bins are uncovered (w_first, APB wait>0, framing error, in-flight reset) while docs/vplan.md claims 100% (280/280). |
| `V-05` | Features | PARTIAL | **MAJOR** | make cov-report crashes with No space left on device on 674MB /tmp due to 3 sim_build dirs and exits 1 when func cov < 100%; manual Verilator run yields 90.0% line, 75.2% toggle, 92.7% expr. |
| `V-06` | Features | PARTIAL | **MAJOR** | CdcMonitor reads CLK_SLOW_PERIOD_NS from environment instead of measuring clk_slow period on RTL pins, and formal/rr_arbiter_props.v is never loaded by formal/rr_arbiter.sby. |
| `V-07` | Features | PARTIAL | **MAJOR** | All 10 .sby suites pass, but rr_arbiter_props.v is orphaned, axil2apb_bridge & axil_xbar contain over-constraining assumptions, axil_csr disables CHECK_CAUSALITY, and sync_fifo lacks data-ordering assertion. |
| `V-09` | Features | FAIL | **BLOCKER** | docs/mutation_report.md claims 30/29 (103.4%) and phantom survivor axil_xbar #29 absent from mutation.log, miscounts axil_ram equivs (10 vs 8), and hides CSR test gaps as 'unused bits'. |
| `V-10` | Features | NOT_RUN | **MAJOR** | Local CI script check_no_synthetic_cov, lint, unit, block, and formal pass; remote GitHub Actions status cannot be checked without gh CLI, so CI PASS claim is unverified. |
| `S-01` | Features | FAIL | **BLOCKER** | synth/synth.ys is absent from git; sta.tcl and fmax_sweep.py hardcode stale Yosys cell IDs (_14798_/_14800_) causing fresh WNS=-19.33ns on rst_sync flop _14686_, while fmax_sweep.py prints hardcoded 81.63 MHz text. |
| `S-02` | Features | N/A | **INFO** | No gate-level simulation script, SKY130 behavioral Verilog integration, or GLS log is committed; classified N/A per audit rule. |
| `S-03` | Features | N/A | **INFO** | No OpenLane configuration, macro/placement setup, DRC/LVS report, or GDSII artifact exists; classified N/A per audit rule. |
| `X-01` | Features | N/A | **INFO** | Crossbar exposes only 2 master ports (M0, M1) and no RISC-V core RTL or integration test exists; classified N/A per audit rule. |
| `X-02` | Features | N/A | **INFO** | Crossbar and bridges support at most one outstanding write and read per master with no response reordering/FIFO queues; classified N/A per audit rule. |
| `REG-UART-08` | Registers | PARTIAL | **MAJOR** | STATUS bit layout matches Spec 7.3 [7:0] and W1C clears bits [6:4], but UA-02 never tests RX FIFO overflow bit [5]. |
| `AXIL-R6` | AXI4-Lite Rules | FAIL | **BLOCKER** | axil_ram, apb peripherals, and slow_regs ignore [1:0], but axil_csr checks addr[7:0] literally, breaking Rule 6 as proven by probe_02 on 0x6000_0001. |
| `RTL-axil_decoder` | RTL Structure | PARTIAL | **MINOR** | RTL works with crossbar but breaks frozen docs/interfaces.md:115 signature without DEC entry. |
| `RTL-axil_xbar` | RTL Structure | PARTIAL | **MAJOR** | Crossbar uses duplicated inline priority loops (wr_prio/rd_prio) instead of Spec 7.1 rr_arbiter. |
| `RTL-axil_csr` | RTL Structure | FAIL | **BLOCKER** | axil_csr decodes write_offset/read_offset[7:0] literally, failing word-unaligned access. |
| `RTL-LINT` | RTL Structure | PARTIAL | **MINOR** | make lint (Verilator --lint-only -Wall) passes with 0 warnings; standalone iverilog -Wall warns on @* indexing unpacked arrays in axil_xbar.v and Yosys warns on memory array replacement. |
| `XB-03` | Spec Tests | PARTIAL | **MINOR** | Tests all 16 WSTRB values on RAM (0x5000_0000), but omits CSR SCRATCH2 (0x6000_000C) named in Spec 9.1 (only tested in pyuvm test_sys_strobe_patterns). |
| `XB-07` | Spec Tests | FAIL | **BLOCKER** | Reads xbar grant wires into unused local variables (m0_first/m1_first) with ZERO assert statements checking grant counts; MUT-10 stuck priority escaped. |
| `XB-12` | Spec Tests | FAIL | **BLOCKER** | Awaits full completion of transaction before pulsing rst_n, so crossbar is idle at reset (confirmed by cg_reset hitting only 'idle'); wrong scenario vs Spec 9.1. |
| `XB-14` | Spec Tests | FAIL | **BLOCKER** | Runs ProtPassThroughSeq which sets axil prot bits and asserts AXI OKAY, yet neither sequence nor scoreboard inspects top/bridge PPROT; MUT-09 zeroing PPROT passed. |
| `XB-15` | Spec Tests | FAIL | **BLOCKER** | Targets only RAM (0x5000_0000+offset), missing axil_csr where unaligned 0x6000_0001 actually fails Rule 6 with SLVERR (caught by audit probe_02). |
| `BR-05` | Spec Tests | PARTIAL | **MINOR** | Runs interleaved R/W on standalone single-port axil2apb_bridge rather than concurrent dual masters via crossbar (note bridge itself only has 1 AXI slave port). |
| `UA-02` | Spec Tests | PARTIAL | **MAJOR** | Verifies TX_FULL, TX_OVF (+W1C), and RX_FULL, but omits forcing a 9th RX byte when RX_FULL to exercise RX_OVF (STATUS[5]). |
| `CD-03` | Spec Tests | PARTIAL | **MINOR** | Injects clk_sys mid-txn reset cleanly, then in Part 2 asserts both rst_slow_n and rst_sys_n rather than testing slow-domain-only reset recovery independently. |
| `COV-cg_order` | Coverage | PARTIAL | **MAJOR** | Monitor-observed w_first bin is 0% across all pyuvm directed+stress runs because pyuvm AxilMasterDriver drives AW+W without w_first stagger on all targets. |
| `COV-cg_backpressure` | Coverage | PARTIAL | **MAJOR** | B and R ready delay buckets 1, 2-4, 5-16 remain uncovered because master agents drive BREADY=1/RREADY=1 immediately in pyuvm. |
| `COV-cg_contention` | Coverage | PARTIAL | **MINOR** | 8 of 9 contention cross bins covered; ('one_idle','R/W') stays 0 since a single active master performs either a Read OR Write, making R/W unreachable for one_idle. |
| `COV-cg_apb` | Coverage | PARTIAL | **MAJOR** | Subsystem APB peripherals always respond in 0 wait states (so wait>0 is unreachable on top level without slow responder) and reads drive PSTRB=0 only. |
| `COV-cg_cdc` | Coverage | PARTIAL | **MAJOR** | 6 FIFO full bins legitimately waived (single-outstanding bridge never fills depth-4 FIFO); reachability exp proves ratio bins rely on CLK_SLOW_PERIOD_NS env var at fabric_monitors.py:322! |
| `COV-cg_uart` | Coverage | PARTIAL | **MAJOR** | Reachability test confirmed frame_err drops when UA-04 isn't part of pyuvm; top-level pyuvm lacks bad-stop-bit stimulus so frame_err=0 in merged func cov. |
| `COV-cg_reset` | Coverage | PARTIAL | **MAJOR** | Only 'idle' bin hit because test_xb12_reset_recovery awaits sequence completion before pulsing reset, proving ResetPhaseMonitor detects no in-flight resets. |
| `COV-HONESTY` | Coverage | PARTIAL | **MAJOR** | No synthetic sequence calls found, and cg_uart.err/cg_cdc.ratio reachability checks drop unhit bins properly, though CdcMonitor relies on CLK_SLOW_PERIOD_NS env var instead of real pin timing. |
| `COV-FUNC-MERGE` | Coverage | FAIL | **BLOCKER** | Fresh Verilator coverage merge matches func_cov.log (229/273, 83.88%), proving docs/vplan.md:142 (280/280 100%) and docs/results.md:140-141 false/self-contradictory. |
| `COV-CODE-VERILATOR` | Coverage | PARTIAL | **MAJOR** | Fresh Verilator code coverage ran after fixing /tmp space issue and differs from docs/results.md:146-149 (denominator 1064 vs 1094); top uncovered: apb_uart (34), sync_fifo (22). |
| `FORMAL-async_fifo` | Formal | PARTIAL | **MAJOR** | Multiclock BMC depth 25 verifies Gray transitions and magic-value integrity, but docs/coverage_waivers.md:43 violates wording rules by claiming it is 'exhaustively proven'. |
| `FORMAL-axil2apb_bridge` | Formal | PARTIAL | **MAJOR** | Bridge passes BMC d=25 and bounded liveness, yet line 156 assumes !s_axil_arvalid whenever awvalid||wvalid, hiding concurrent R/W arbitration bugs. |
| `FORMAL-axil_csr` | Formal | PARTIAL | **MINOR** | CSR k-induction passes, but rtl/axil/axil_csr.v:269 sets CHECK_CAUSALITY(0) disabling axil_props outstanding causality counters and formal has no Rule 6 [1:0] check. |
| `FORMAL-axil_xbar` | Formal | PARTIAL | **MAJOR** | Xbar BMC passes 29 covers and bounded liveness, but axil_xbar_props.v:377/396 assumes slave asserts bvalid within 3 cycles of awvalid even without wvalid. |
| `FORMAL-rr_arbiter` | Formal | PARTIAL | **MAJOR** | rr_arbiter.sby verifies inline RTL assertions while completely ignoring formal/rr_arbiter_props.v, and neither proves bounded fairness under persistent contention. |
| `FORMAL-sync_fifo` | Formal | PARTIAL | **MAJOR** | sync_fifo_props.v proves pointer/count/full/empty safety via k-induction, but contains ZERO data-ordering or magic-value property despite README.md:158 claiming it proved data ordering. |
| `FORMAL-rr_arbiter_props` | Formal | FAIL | **MAJOR** | grep confirms rr_arbiter_props.v is orphaned; formal/rr_arbiter.sby reads only rtl/common/rr_arbiter.v. |
| `FORMAL-WORDING` | Formal | FAIL | **MAJOR** | While README Sec 5.2 avoids 'absence of deadlock', docs/coverage_waivers.md:43 calls async_fifo BMC 'exhaustively proven' and README:134,158 overclaim simulation/missing properties. |
| `MUT-SCRIPT` | Mutation | PARTIAL | **MAJOR** | run_mutants.py runs both sampled and 240-mutant sweeps, yet subprocess.run(..., timeout=40) without process-group kill leaks timed-out vvp processes during async_fifo/bridge runs. |
| `MUT-TRIAGE` | Mutation | FAIL | **BLOCKER** | docs/mutation_report.md and mutation_triage.md are byte-identical and contain impossible math (axil_xbar 30/29), phantom survivor #29, wrong equiv counts, and misclassified CSR test gaps. |
| `MUT-SPOT5` | Mutation | FAIL | **MAJOR** | Audit spot-check of rr_arbiter #11 (equiv), axil_csr #9/#22/#29 (untested wdata[17] w_first, rresp[1], scratch[2]), and bridge #9/#14 (untested arprot[2], read PSTRB=0) exposes real test gaps. |
| `PROBE-02` | Independent Probes | FAIL | **BLOCKER** | Independent black-box register probe caught axil_csr.v violating Spec Section 6 Rule 6 on byte-unaligned read 0x6000_0001. |
| `SMUT-09` | Sanity Mutation | FAIL | **BLOCKER** | Zeroed m_apb_pprot in axil2apb_bridge.v:115,125; both block and pyuvm XB-14 passed 100%, exposing broken PPROT assertions. |
| `SMUT-10` | Sanity Mutation | FAIL | **BLOCKER** | Pinned wr_prio update to 0 in axil_xbar.v:143 starving round-robin write fairness; XB-07 passed because it has zero assertions. |
| `SYNTH-YS` | Synthesis & STA | FAIL | **BLOCKER** | Spec Sec 13.1, README:135,320, and Spec Sec 15 all specify synth/synth.ys, which is missing from git (synthesis logic was moved inline into Makefile:120). |
| `SYNTH-SDC` | Synthesis & STA | PARTIAL | **MINOR** | synth/amba_fabric.sdc correctly declares both clocks, async clock group, and 2.0ns I/O delays, but README omits explaining the Spec 13.2 Gray-pointer constraint choice. |
| `SYNTH-STA` | Synthesis & STA | FAIL | **BLOCKER** | sta.tcl and fmax_sweep.py hardcode stale Yosys cell names (_14798_/_14800_) so clk_slow reset flop _14686_ hits 21.43ns async path, and fmax_sweep.py:130 prints hardcoded 81.63 MHz text! |
| `SYNTH-REPORT` | Synthesis & STA | FAIL | **BLOCKER** | Docs admit 100 MHz failure, which is good in spirit, yet cite 81.63 MHz printed by fmax_sweep.py's hardcoded string while real fresh STA shows -19.33 ns. |
| `CI-WORKFLOW` | CI & Docs | PARTIAL | **MINOR** | All CI make commands execute cleanly on fresh clone; minor inconsistency: CI skips make cov-report/synth/sta yet tries uploading docs/logs/ and synth/results/. |
| `CI-REMOTE` | CI & Docs | NOT_RUN | **MAJOR** | gh CLI is missing in sandbox so remote GitHub Actions run status on branch 'remediation' could not be inspected; claiming 'CI Status: PASS' without verified run is a MAJOR finding. |
| `LAYOUT-SYNTH_YS` | Repo Layout | NOT_FOUND | **BLOCKER** | synth/synth.ys is explicitly linked in README.md:135,320 and Spec Sec 15 but does not exist in git (inlined into Makefile:120). |
| `LAYOUT-SYNTH_RES` | Repo Layout | PARTIAL | **INFO** | synth/results/ is generated dynamically by make synth / make sta and intentionally ignored by .gitignore:25. |
| `METRIC-01` | Metric Honesty | FAIL | **BLOCKER** | Actual committed RTL across 17 .v files totals 3,759 lines (521 lines higher than claimed 3,238 in README.md:124 and results.md:12). |
| `METRIC-02` | Metric Honesty | FAIL | **BLOCKER** | Repo defines 55 testcases (incl. test_hello_world) with 56 executed runs, and 3 spec IDs fail fidelity (XB-07/12/14) while XB-15 misses CSR bug. |
| `METRIC-05` | Metric Honesty | FAIL | **BLOCKER** | Fresh measurement confirms 229/273 (83.88%) matching docs/logs/func_cov.log, exposing fabricated/stale 280/280 (100.00%, None needed) in vplan.md & results.md. |
| `METRIC-06` | Metric Honesty | FAIL | **MAJOR** | Fresh Verilator code coverage differs across line (+2.2%), branch (+2.3%), and expr total points (1,064 vs claimed 1,094). |
| `METRIC-07` | Metric Honesty | PARTIAL | **MAJOR** | 10/10 suites and 81 covers reproduce accurately, yet waivers.md:43 overclaims async_fifo as proven, README:158 claims sync_fifo ordering, and results.md:155 still says '8/8'. |
| `METRIC-09` | Metric Honesty | FAIL | **BLOCKER** | Fresh 240-mutant run diverges in axil_ram/axil_csr scores, and published triage table contains impossible axil_xbar 103.4% ratio & misclassified survivors. |
| `METRIC-10` | Metric Honesty | FAIL | **MAJOR** | README internally disagrees (22 vs 21 bugs), and BUG-022 references non-existent file tb/pyuvm/tests/test_xb09_backpressure_burst.py. |
| `METRIC-11` | Metric Honesty | PARTIAL | **MINOR** | XB-06 confirms zero cross-slave serialization latency well within <=1 cycle spec limit, though 'proven' wording is imprecise and README:219 links missing contention.vcd. |
| `METRIC-12` | Metric Honesty | FAIL | **BLOCKER** | Fresh Yosys SKY130 synthesis produces 9,320 cells and 138,031.13 um2, disagreeing with claimed 9,376 cells and 137,867.23 um2. |
| `METRIC-13` | Metric Honesty | FAIL | **BLOCKER** | Fresh OpenSTA measures WNS=-19.33 ns and fails even 62.5 MHz due to hardcoded stale cell names _14798_/_14800_ in sta.tcl/fmax_sweep.py. |
| `METRIC-14` | Metric Honesty | NOT_RUN | **MAJOR** | Remote CI status cannot be checked without gh CLI, so claiming CI PASS on README and results.md is unsupported. |
| `DOD-01` | Definition of Done | FAIL | **BLOCKER** | Blocking Rule 6 defect in CSR plus non-checking/wrong-scenario tests XB-07, XB-12, XB-14 and escaped mutants MUT-09/10 fail DoD-01. |
| `DOD-02` | Definition of Done | PARTIAL | **MAJOR** | Icarus passed 20/20 fresh seeds (501-520), and Verilator passed directed+5 stress seeds during coverage regen, leaving 20-seed Verilator undocumented/partial. |
| `DOD-03` | Definition of Done | FAIL | **BLOCKER** | Functional coverage closes at only 83.88% with 44 genuine uncovered monitor holes while make cov-report fails cleanly from clean clone. |
| `DOD-04` | Definition of Done | PARTIAL | **MAJOR** | While SymbiYosys passes all 10 .sby runs, over-constraining bridge/xbar assumes, missing sync_fifo data-order check, and orphaned rr_arbiter_props fail clean formal sign-off. |
| `DOD-05` | Definition of Done | FAIL | **BLOCKER** | Test improvements exist in git (fe1816d/215c37a), yet mutation_report.md has impossible 103.4% axil_xbar math, phantom survivor #29, and misclassified CSR test gaps. |
| `DOD-06` | Definition of Done | FAIL | **BLOCKER** | Stale cell constraints in sta.tcl/fmax_sweep.py and hardcoded 81.63 MHz output make published synthesis/STA numbers unreproducible. |
| `DOD-07` | Definition of Done | NOT_RUN | **MAJOR** | Local CI targets run cleanly (except missing artifact dirs in CI), but GitHub remote CI run status cannot be verified in sandbox. |
| `DOD-08` | Definition of Done | FAIL | **BLOCKER** | Multiple cross-document contradictions (22 vs 21 bugs, 83.88% vs 100%, 3238 vs 3759 lines) and missing referenced files prevent sign-off. |
| `DOD-09` | Definition of Done | FAIL | **BLOCKER** | README.md Section 9 resume bullets copy stale/mismatched numbers for line coverage, mutation score, cell count, and broken Fmax sweep. |
| `VPLAN-AUDIT` | docs/vplan.md truthfulness across all 40 test rows and coverage target | FAIL | **BLOCKER** | Every cited test function in docs/vplan.md exists and exits 0 in sim, but XB-07/12/14/15 violate test fidelity and Section 4 falsely reports 280/280 (100%). |
| `BUGS-AUDIT` | docs/bugs.md schema completeness and regression test existence | FAIL | **MAJOR** | BUG-001..BUG-022 contain symptom/discovery/root-cause/fix/regression fields, yet BUG-022 references deleted/nonexistent tb/pyuvm/tests/test_xb09_backpressure_burst.py and README says 22 vs 21. |
| `DECISIONS-AUDIT` | docs/decisions.md captures all spec/interface deviations | FAIL | **MAJOR** | decisions.md omits logging: (1) axil_decoder 4-bit slave_sel & params vs interfaces.md:115, (2) axil_csr [1:0] decode violation, (3) axil_xbar inline arbiter vs rr_arbiter, (4) missing synth/synth.ys. |

---

## 19. Closure of Previous Audit Findings (`F-01` to `F-12` in `docs/FIX_REPORT.md`)

| Previous Finding | Claimed Status (`docs/FIX_REPORT.md`) | Audited Closure | Evidence & Remaining Gaps |
|---|---|---|---|
| **F-01** Honest Functional Coverage | DONE | **PARTIAL** | Synthetic `sample_*` calls were removed (`check_no_synthetic_cov.sh` PASS) and `docs/logs/func_cov.log` honestly measures 229/273 (83.88%). **Still open:** `docs/vplan.md:142` and `docs/results.md:140-141` still claim `280/280 (100.00%, None needed)`, and `CdcMonitor` (`fabric_monitors.py:322`) relies on `CLK_SLOW_PERIOD_NS` env var. |
| **F-02** Missing & Mislabeled Tests | DONE | **OPEN** | All 40 spec IDs now have named functions and XML results, **but test fidelity failed on 4 P0 IDs**: `XB-07` has 0 assertions (`MUT-10` escaped), `XB-12` resets after sequence completion while idle, `XB-14` ignores APB `PPROT` (`MUT-09` escaped), and `XB-15` skips `axil_csr` where `0x6000_0001` fails Rule 6 (`UA-02` also omits `RX_OVF`). |
| **F-03** Honest & Stronger Formal | DONE | **PARTIAL** | `axil_props.v` is bound across all 5 AXI-Lite modules, `cdc`/`uart` suites added (10/10 PASS, 81 covers), and README Sec 5.2 distinguishes BMC vs k-induction. **Still open:** `rr_arbiter_props.v` is orphaned, `axil2apb_bridge_props.v:156` & `axil_xbar_props.v:396` over-assume, `axil_csr.v:269` disables `CHECK_CAUSALITY`, `sync_fifo` lacks data-ordering proof claimed in `README:158`, and `waivers.md:43` calls `async_fifo` BMC "exhaustively proven". |
| **F-04** Documentation Consistency | DONE | **OPEN** | MIT `LICENSE`, UART FIFO depth `8`, and Timer/GPIO addresses were corrected, **but major contradictions persist**: README claims 3,238 RTL lines (actual 3,759), 54 tests (actual 55/56), 22 vs 21 bugs, links missing `contention.vcd`/`synth.ys`, `BUG-022` cites missing `test_xb09_backpressure_burst.py`, and `vplan`/`results` contain contradictory coverage/formal counts. |
| **F-05** Mutation Testing & Survivor Triage | DONE | **OPEN** | `run_mutants.py` scales to 240 mutants and git commits `fe1816d`/`215c37a` improved unit/block tests. **Still open:** `docs/mutation_report.md` & `mutation_triage.md` publish impossible `axil_xbar` `30/29` (103.4%) math, cite phantom survivor `#29`, miscount `axil_ram` equivalents (`10` vs `8`), misclassify CSR/bridge test gaps as equivalent, and `run_mutants.py:208` leaks timed-out `vvp` processes. |
| **F-06** 20-Seed Regression Verification | DONE | **CLOSED** | Freshly verified on clean clone across 20 independent seeds (`501`..`520`) totaling 200,000 constrained-random transactions with 0 mismatches (`/tmp/audit_work/audit_logs/step11_20seeds.log`), and `DEC-005` is documented. *(Note Verilator ran 5 seeds during cov regen rather than 20.)* |
| **F-07** GitHub Actions CI & Badge | DONE | **PARTIAL** | `.github/workflows/ci.yml` pins `2026-11-22`, runs `check_no_synthetic_cov.sh` + `make block`, and badge URL points to the real repo; all local CI steps work. **Gap:** Remote GitHub CI execution status could not be checked (`gh` CLI unavailable -> `NOT_RUN`), so `CI Status: PASS` is unverified and CI uploads unbuilt `docs/logs/` & `synth/results/`. |
| **F-08** Clean-Clone Reality Check | DONE | **CLOSED** | Fresh clone passes `env-check`, `lint`, `unit`, `block`, `regress SEEDS=1`, and `formal` cleanly with zero hardcoded `/home/` paths in active source (`make cov-report` fails only on 674 MB `/tmp` tmpfs + `<100%` exit code). |
| **F-09** pyuvm Architecture Honesty | DONE | **CLOSED** | `README.md` Sec 5.1 explicitly distinguishes `AxilMasterAgent` (`pyuvm.uvm_agent`) from cocotb coroutine slave responders and behavioral models, matching `DEC-005` in `docs/decisions.md`. |
| **F-10** Removal of Flawed Audit Artifacts | DONE | **CLOSED** | `git ls-files` confirms all stale `docs/AUDIT_REPORT.md`, `audit_results.*`, and `/home/` paths in source artifacts were removed in `de7c81f` / `8664339`. |
| **F-11** Physical Timing Honesty | DONE | **OPEN** | Docs admit 100 MHz is missed, **but reported numbers (`81.63 MHz`, `-2.25 ns`) are invalid**: `synth/sta.tcl:22` and `synth/fmax_sweep.py:37` hardcode stale Yosys cell IDs (`_14798_/_14800_`) producing **WNS = -19.33 ns (<62.5 MHz)** on fresh synthesis, while `fmax_sweep.py:130-139` prints hardcoded `81.63 MHz` critical-path text! |
| **F-12** License Addition & Language Precision | DONE | **CLOSED** | Root MIT `LICENSE` exists and `README.md` accurately describes Verilog-2005 / SystemVerilog compatibility matching the 17 RTL `.v` files. |
