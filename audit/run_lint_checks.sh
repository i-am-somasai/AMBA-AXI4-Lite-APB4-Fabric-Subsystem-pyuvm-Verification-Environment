#!/usr/bin/env bash
# run_lint_checks.sh - Step C: Tool-compatibility and lint audit
set -e
source scripts/env.sh

LOG_DIR="audit/logs"
mkdir -p "$LOG_DIR"

echo "=== Running Step C Lint and Compatibility Checks ==="

RTL_FILES=(
    "rtl/common/rst_sync.v"
    "rtl/common/sync_fifo.v"
    "rtl/common/async_fifo.v"
    "rtl/common/rr_arbiter.v"
    "rtl/axil/axil_decoder.v"
    "rtl/axil/axil_default_slave.v"
    "rtl/axil/axil_ram.v"
    "rtl/axil/axil_csr.v"
    "rtl/axil/axil_xbar.v"
    "rtl/apb/axil2apb_bridge.v"
    "rtl/apb/apb_decoder.v"
    "rtl/apb/apb_uart.v"
    "rtl/apb/apb_timer.v"
    "rtl/apb/apb_gpio.v"
    "rtl/cdc/slow_regs.v"
    "rtl/cdc/axil_cdc_bridge.v"
    "rtl/amba_fabric_top.v"
)

INC_DIRS="-Irtl/common -Irtl/axil -Irtl/apb -Irtl/cdc"
LIB_DIRS="-y rtl/common -y rtl/axil -y rtl/apb -y rtl/cdc -Y .v"

echo "1. Verilator lint per file and top-level..."
> "$LOG_DIR/lint_verilator.log"
for f in "${RTL_FILES[@]}"; do
    echo "--- Verilating $f ---" >> "$LOG_DIR/lint_verilator.log"
    verilator --lint-only -Wall -Wno-DECLFILENAME $INC_DIRS "$f" >> "$LOG_DIR/lint_verilator.log" 2>&1 || echo "FAIL on $f" >> "$LOG_DIR/lint_verilator.log"
done

echo "--- Verilating Top Level (amba_fabric_top) ---" >> "$LOG_DIR/lint_verilator.log"
verilator --lint-only -Wall -Wno-DECLFILENAME -Wno-MULTITOP $INC_DIRS "${RTL_FILES[@]}" >> "$LOG_DIR/lint_verilator.log" 2>&1 || echo "FAIL on top" >> "$LOG_DIR/lint_verilator.log"

echo "2. Icarus Verilog compile with -g2012 per file and top-level..."
> "$LOG_DIR/lint_iverilog.log"
for f in "${RTL_FILES[@]}"; do
    echo "--- Icarus compiling $f ---" >> "$LOG_DIR/lint_iverilog.log"
    iverilog -g2012 -t null $INC_DIRS $LIB_DIRS "$f" >> "$LOG_DIR/lint_iverilog.log" 2>&1 || echo "FAIL on $f" >> "$LOG_DIR/lint_iverilog.log"
done

echo "--- Icarus compiling Top Level ---" >> "$LOG_DIR/lint_iverilog.log"
iverilog -g2012 -t null $INC_DIRS $LIB_DIRS -s amba_fabric_top "${RTL_FILES[@]}" >> "$LOG_DIR/lint_iverilog.log" 2>&1 || echo "FAIL on top" >> "$LOG_DIR/lint_iverilog.log"

echo "3. Yosys read_verilog -sv + hierarchy -check..."
> "$LOG_DIR/lint_yosys.log"
yosys -p "read_verilog -sv $INC_DIRS ${RTL_FILES[*]}; hierarchy -check -top amba_fabric_top" >> "$LOG_DIR/lint_yosys.log" 2>&1 || echo "FAIL on Yosys hierarchy" >> "$LOG_DIR/lint_yosys.log"

echo "4. Checking for forbidden port constructs (interfaces, classes, packed structs on ports)..."
> "$LOG_DIR/lint_ports.log"
FORBIDDEN_HITS=0
for f in "${RTL_FILES[@]}"; do
    if grep -E "(interface\s+[a-zA-Z0-9_]+\s*;|class\s+[a-zA-Z0-9_]+|struct\s+packed)" "$f" >/dev/null 2>&1; then
        echo "FORBIDDEN construct found in $f" >> "$LOG_DIR/lint_ports.log"
        FORBIDDEN_HITS=$((FORBIDDEN_HITS + 1))
    fi
done

if [ "$FORBIDDEN_HITS" -eq 0 ]; then
    echo "PASSED: No interfaces, classes, or packed structs found in any RTL file." >> "$LOG_DIR/lint_ports.log"
else
    echo "FAILED: Found $FORBIDDEN_HITS files with forbidden port constructs." >> "$LOG_DIR/lint_ports.log"
fi

echo "=== Lint and Compatibility Checks Complete ==="
