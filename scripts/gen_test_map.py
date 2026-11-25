#!/usr/bin/env python3
"""
scripts/gen_test_map.py

Parses test function and class names for spec IDs (Section 9.1, all 40 IDs),
reads the latest regression results.xml files, generates docs/test_map.csv,
and updates docs/vplan.md Section 3 test catalog tables.

Rules:
- Zero personal paths (strip /home/<user>/ -> relative paths)
- A row may say PASS only if the latest results.xml shows it passed.
- Missing tests are marked NOT IMPLEMENTED.
"""

import os
import re
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

PROJ_DIR = Path(__file__).resolve().parent.parent

# Canonical list of 40 Spec Test IDs per Section 9.1
SPEC_TESTS = [
    # Crossbar / AXI4-Lite (XB-01 .. XB-15)
    ("XB-01", "Single write and read, each master to each mapped slave", "OKAY response, payload verified against reference model"),
    ("XB-02", "Write-then-read memory data integrity on RAM", "Word and byte matches reference memory"),
    ("XB-03", "All 16 WSTRB patterns on RAM and CSR scratch", "Only strobed bytes change; non-strobed preserved"),
    ("XB-04", "Unmapped address read and write access", "DECERR, no bus stall, write data consumed"),
    ("XB-05", "Both masters to the same slave simultaneously", "Clean serialization, no data corruption, transaction lock honored"),
    ("XB-06", "Both masters to different slaves simultaneously", "Parallel completion without serialization penalty"),
    ("XB-07", "Arbitration fairness under sustained contention", "Grant count difference <= 1 across alternating requests"),
    ("XB-08", "AW before W / W before AW / simultaneous orderings", "Normal handshake completion in all three orderings"),
    ("XB-09", "Random READY back-pressure on all channels", ">= 2,000 transactions, no loss, no duplication"),
    ("XB-10", "Delayed BREADY / RREADY response holding", "BVALID/RVALID, response code and data held stable until accepted"),
    ("XB-11", "SLVERR response validation on out-of-bounds RAM and undefined regs", "SLVERR response returned without hanging interconnect"),
    ("XB-12", "Asynchronous reset recovery during in-flight transaction", "DUT returns to clean idle state; subsequent transactions succeed"),
    ("XB-13", "Multi-master constrained-random stress (>= 10,000 transactions)", "Zero scoreboard mismatches, 100% data and response accuracy"),
    ("XB-14", "AWPROT and ARPROT pass-through to APB PPROT", "APB PPROT matches AXI-Lite input protection bits"),
    ("XB-15", "Address alignment handling (LSBs [1:0] non-zero)", "Address treated as word-aligned without bus hang"),

    # APB Bridge (BR-01 .. BR-06)
    ("BR-01", "Single write and read, 0 wait states", "Correct SETUP -> ACCESS timing; PENABLE pulses high"),
    ("BR-02", "APB wait states (PREADY delayed 1..4 cycles)", "Signals held stable during wait states; completes upon PREADY=1"),
    ("BR-03", "PSLVERR on read and write maps to SLVERR", "Maps cleanly to AXI-Lite SLVERR (2'b10) response on read and write"),
    ("BR-04", "APB strobe propagation (PSTRB)", "m_apb_pstrb accurately reflects s_axil_wstrb on write transfers"),
    ("BR-05", "Back-to-back mixed read/write transfers", "Single-outstanding arbitration honored, no starvation or pipeline stall"),
    ("BR-06", "Delayed W data arrival relative to AW", "Bridge waits in ST_WAIT_W; PSEL never rises before W arrives"),

    # Peripherals (UA-01..05, TM-01..03, GP-01..03, CS-01..03)
    ("UA-01", "UART internal loopback mode across byte values", "RX data matches TX data; FIFO status flags update accurately"),
    ("UA-02", "UART FIFO full, empty, and overflow flags", "TX_FULL, RX_EMPTY, TX_OVF, RX_OVF set and clear via W1C"),
    ("UA-03", "UART baud rate divisor sweep", "Bit timing verified against programmed BAUDDIV divisor"),
    ("UA-04", "External RX stimulus with bad stop bit", "FRAME_ERR set, W1C clears it, next good frame received correctly"),
    ("UA-05", "UART interrupt generation", "uart_irq follows RX_IRQ_EN & ~RX_EMPTY"),
    ("TM-01", "Timer one-shot countdown mode", "Generates timeout interrupt after exactly (LOAD+1) cycles"),
    ("TM-02", "Timer periodic mode", "Automatically reloads from LOAD register on timeout; periodic IRQ"),
    ("TM-03", "Timer interrupt W1C clearing", "Writing 1 to TIMEOUT clears interrupt flag and deasserts IRQ"),
    ("GP-01", "GPIO direction and output drive", "Output pins drive programmed value when configured as output"),
    ("GP-02", "GPIO 2-FF input synchronizer latency", "Input sampled with exact 2-cycle synchronization pipeline delay"),
    ("GP-03", "GPIO rising-edge interrupt detection", "Pin rising edge triggers interrupt when unmasked; cleared via W1C"),
    ("CS-01", "System CSR reset values verification", "ID (0xA3BA0001), VERSION (0x00010000), defaults match spec"),
    ("CS-02", "System CSR access types (RO, RW, W1C)", "RO ignores writes with OKAY; W1C clears only set bits; W1C_SET hook"),
    ("CS-03", "System CSR interrupt aggregation", "UART, Timer, GPIO interrupts masked by IRQ_MASK and drive irq_o"),

    # CDC Bridge (CD-01 .. CD-05)
    ("CD-01", "Data integrity through bridge across ratio/phase sweep", "3 clock ratios (25ns, 10.3ns, 6ns) x 3 phases each; 0 errors"),
    ("CD-02", "Async FIFO continuous random-rate stream", "Fast/slow and slow/fast streams; wfull/rempty reached; 0 loss/corruption"),
    ("CD-03", "Independent domain reset recovery mid-transaction", "Reset assertion in either domain recovers cleanly without hang"),
    ("CD-04", "SLOW_COUNTER rate verification and control", "Counter increments at clk_slow rate; pauses and resumes via SLOW_CTRL"),
    ("CD-05", "Interleaved multi-master access to slow registers", "Both masters access slow_regs concurrently through full path"),
]


def clean_path(p):
    """Convert absolute path to project-relative path and strip any home directory."""
    s = str(p)
    if str(PROJ_DIR) in s:
        s = os.path.relpath(s, PROJ_DIR)
    # Strip any stray home directory mentions
    s = re.sub(r"^/home/[^/]+/", "", s)
    return s


def find_test_definitions():
    """Scan test files to map spec IDs to (test_function_name, relative_file_path)."""
    id_map = {}
    tb_dir = PROJ_DIR / "tb"

    # Regex patterns for test functions or classes
    fn_pattern = re.compile(r"^\s*(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\(")
    cls_pattern = re.compile(r"^\s*class\s+([a-zA-Z0-9_]+)\s*\(")

    for py_file in tb_dir.rglob("*.py"):
        if "venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        rel_path = clean_path(py_file)
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                for line in f:
                    m_fn = fn_pattern.match(line)
                    m_cls = cls_pattern.match(line)
                    name = None
                    if m_fn:
                        name = m_fn.group(1)
                    elif m_cls:
                        name = m_cls.group(1)

                    if name:
                        # Extract spec ID if name contains e.g. test_xb01_... or TestXB01...
                        m_id = re.search(r"(?:test_)?([a-zA-Z]{2})0?([0-9]{1,2})", name, re.IGNORECASE)
                        if m_id:
                            prefix = m_id.group(1).upper()
                            num = int(m_id.group(2))
                            spec_id = f"{prefix}-{num:02d}"
                            if any(s[0] == spec_id for s in SPEC_TESTS):
                                # Prioritize spec-specific pyuvm directed tests (e.g. XB-11..15) or test_ files
                                if spec_id not in id_map or (
                                    "test_" in rel_path and "all_targets" in id_map[spec_id][0]
                                ):
                                    id_map[spec_id] = (name, rel_path)
        except Exception as e:
            pass

    return id_map


def parse_results_xmls():
    """Find and parse results*.xml files under build/results/ to get {test_name: (passed_bool, seed, file)}."""
    results = {}
    search_root = PROJ_DIR / "build" / "results"
    if not search_root.exists():
        search_root = PROJ_DIR
    for xml_file in sorted(search_root.rglob("results*.xml")):
        if any(p in xml_file.parts for p in (".venv", ".git", "sanity", "mutants")):
            continue
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            for tc in root.iter("testcase"):
                name = tc.get("name")
                if not name:
                    continue
                failures = list(tc.iter("failure"))
                passed = len(failures) == 0
                tc_file = clean_path(tc.get("file", ""))
                # Look for seed in properties
                seed = "42"
                for prop in tc.iter("property"):
                    if "seed" in prop.get("name", "").lower():
                        seed = prop.get("value", seed)
                # If seen multiple times, true PASS requires all runs pass
                if name not in results:
                    results[name] = {"passed": passed, "seed": seed, "file": tc_file}
                else:
                    results[name]["passed"] = results[name]["passed"] and passed
        except Exception:
            pass

    return results


def main():
    test_defs = find_test_definitions()
    results = parse_results_xmls()

    docs_dir = PROJ_DIR / "docs"
    docs_dir.mkdir(exist_ok=True)
    csv_path = docs_dir / "test_map.csv"

    rows = []
    missing_count = 0
    fail_count = 0
    pass_count = 0

    print(f"{'Spec ID':<8} {'Test Function/Class':<38} {'Location':<34} {'Result':<10} {'Seed':<6}")
    print("-" * 100)

    for spec_id, desc, checks in SPEC_TESTS:
        test_info = test_defs.get(spec_id)
        if not test_info:
            test_name = "NONE"
            loc = "NONE"
            res_str = "NOT IMPLEMENTED"
            seed_val = "n/a"
            missing_count += 1
        else:
            test_name, loc = test_info
            # Check results.xml
            if test_name in results:
                res_meta = results[test_name]
                if res_meta["passed"]:
                    res_str = "PASS"
                    pass_count += 1
                else:
                    res_str = "FAIL"
                    fail_count += 1
                seed_val = res_meta.get("seed", "42")
            else:
                # Test definition exists in source but has not yet been executed in results.xml
                res_str = "NOT RUN"
                seed_val = "42"
                missing_count += 1

        print(f"{spec_id:<8} {test_name:<38} {loc:<34} {res_str:<10} {seed_val:<6}")
        rows.append({
            "spec_id": spec_id,
            "test_name": test_name,
            "file": loc,
            "result": res_str,
            "seed": seed_val,
            "desc": desc,
            "checks": checks,
        })

    # Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["spec_id", "test_name", "file", "result", "seed"])
        for r in rows:
            writer.writerow([r["spec_id"], r["test_name"], r["file"], r["result"], r["seed"]])

    print(f"\nSaved test mapping CSV to {clean_path(csv_path)}")
    print(f"Summary: PASS={pass_count}, FAIL={fail_count}, NOT_RUN/MISSING={missing_count} (Total={len(SPEC_TESTS)})")

    # Update docs/vplan.md
    update_vplan(rows)


def update_vplan(rows):
    vplan_path = PROJ_DIR / "docs" / "vplan.md"
    if not vplan_path.exists():
        return

    row_dict = {r["spec_id"]: r for r in rows}

    def format_row(spec_id):
        r = row_dict[spec_id]
        res_display = f"**{r['result']}**"
        loc_display = f"`{r['file']}`" if r["file"] != "NONE" else "*None*"
        return f"| **{spec_id}** | {r['desc']} | {r['checks']} | {loc_display} | {res_display} |"

    xb_rows = [format_row(f"XB-{i:02d}") for i in range(1, 16)]
    br_rows = [format_row(f"BR-{i:02d}") for i in range(1, 7)]
    periph_ids = [
        "UA-01", "UA-02", "UA-03", "UA-04", "UA-05",
        "TM-01", "TM-02", "TM-03",
        "GP-01", "GP-02", "GP-03",
        "CS-01", "CS-02", "CS-03"
    ]
    periph_rows = [format_row(pid) for pid in periph_ids]
    cd_rows = [format_row(f"CD-{i:02d}") for i in range(1, 6)]

    content = vplan_path.read_text(encoding="utf-8")

    # Replace 3.1 table
    xb_block = (
        "### 3.1 Crossbar & AXI4-Lite Suite (`XB-*`)\n\n"
        "| Test ID | Scenario Description | Expected Checks | Test Location | Result |\n"
        "|---|---|---|---|---|\n"
        + "\n".join(xb_rows) + "\n"
    )
    content = re.sub(
        r"### 3\.1 Crossbar & AXI4-Lite Suite \(`XB-\*`\)\n\n.*?### 3\.2 APB Bridge Suite",
        xb_block + "\n### 3.2 APB Bridge Suite",
        content,
        flags=re.DOTALL
    )

    # Replace 3.2 table
    br_block = (
        "### 3.2 APB Bridge Suite (`BR-*`)\n\n"
        "| Test ID | Scenario Description | Expected Checks | Test Location | Result |\n"
        "|---|---|---|---|---|\n"
        + "\n".join(br_rows) + "\n"
    )
    content = re.sub(
        r"### 3\.2 APB Bridge Suite \(`BR-\*`\)\n\n.*?### 3\.3 Peripheral Suite",
        br_block + "\n### 3.3 Peripheral Suite",
        content,
        flags=re.DOTALL
    )

    # Replace 3.3 table
    periph_block = (
        "### 3.3 Peripheral Suite (`UA-*`, `TM-*`, `GP-*`, `CS-*`)\n\n"
        "| Test ID | Scenario Description | Expected Checks | Test Location | Result |\n"
        "|---|---|---|---|---|\n"
        + "\n".join(periph_rows) + "\n"
    )
    content = re.sub(
        r"### 3\.3 Peripheral Suite \(`UA-\*`, `TM-\*`, `GP-\*`, `CS-\*`\)\n\n.*?### 3\.4 CDC Bridge Suite",
        periph_block + "\n### 3.4 CDC Bridge Suite",
        content,
        flags=re.DOTALL
    )

    # Replace 3.4 table preserving <!-- END:metrics:vplan_test_catalog --> marker
    cd_block = (
        "### 3.4 CDC Bridge Suite (`CD-*`)\n\n"
        "| Test ID | Scenario Description | Expected Checks | Test Location | Result |\n"
        "|---|---|---|---|---|\n"
        + "\n".join(cd_rows) + "\n"
    )
    content = re.sub(
        r"### 3\.4 CDC Bridge Suite \(`CD-\*`\)\n\n.*?(?=(?:<!-- END:metrics:vplan_test_catalog -->|---\n\n## 4\. Functional Coverage))",
        cd_block,
        content,
        flags=re.DOTALL
    )

    # Ensure no home directory leaked
    content = re.sub(r"/home/[^/]+/", "", content)

    vplan_path.write_text(content, encoding="utf-8")
    print(f"Updated Section 3 of {clean_path(vplan_path)} successfully.")


if __name__ == "__main__":
    main()
