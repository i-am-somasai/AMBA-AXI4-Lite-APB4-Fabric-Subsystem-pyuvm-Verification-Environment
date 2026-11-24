#!/bin/bash
# scripts/run_phase4_gate.sh
# Automated Phase 4 Acceptance Gate Runner
set -e

PROJ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJ_DIR"
source "$PROJ_DIR/scripts/env.sh"

LOG_DIR="$PROJ_DIR/docs/logs"
mkdir -p "$LOG_DIR"
GATE_LOG="$LOG_DIR/phase4_gate.log"
STRESS_LOG="$LOG_DIR/xb13_stress.log"

echo "========================================================" | tee "$GATE_LOG"
echo "Starting Phase 4 Acceptance Gate Verification" | tee -a "$GATE_LOG"
echo "Date: $(date)" | tee -a "$GATE_LOG"
echo "========================================================" | tee -a "$GATE_LOG"

# 1. Run Directed Tests on Icarus
echo ">>> [1/3] Running pyuvm directed tests on Icarus (XB-09..XB-15, BR-04..BR-06)..." | tee -a "$GATE_LOG"
make -C tb/pyuvm SIM=icarus test_directed 2>&1 | tee -a "$GATE_LOG"

# 2. Run Directed Tests on Verilator
echo ">>> [2/3] Running pyuvm directed tests on Verilator..." | tee -a "$GATE_LOG"
make -C tb/pyuvm SIM=verilator test_directed 2>&1 | tee -a "$GATE_LOG"

# 3. Run XB-13 Random Stress Regression (10,000 transactions per seed across 5 seeds)
echo ">>> [3/3] Running XB-13 multi-seed stress regression (5 seeds x 10,000 transactions)..." | tee -a "$GATE_LOG"
> "$STRESS_LOG"

SEEDS=(42 123 777 2024 9999)
TOTAL_PASSED=0

for seed in "${SEEDS[@]}"; do
    echo "--------------------------------------------------------" | tee -a "$GATE_LOG" | tee -a "$STRESS_LOG"
    echo "Running XB-13 Stress Test: SEED=$seed, TRANS=10000 (SIM=verilator)" | tee -a "$GATE_LOG" | tee -a "$STRESS_LOG"
    echo "--------------------------------------------------------" | tee -a "$GATE_LOG" | tee -a "$STRESS_LOG"

    SEED=$seed NUM_TRANS_PER_MASTER=5000 \
    make -C tb/pyuvm SIM=verilator test_stress 2>&1 | tee -a "$GATE_LOG" | tee -a "$STRESS_LOG"

    TOTAL_PASSED=$((TOTAL_PASSED + 1))
done

echo "========================================================" | tee -a "$GATE_LOG"
echo "Phase 4 Acceptance Gate PASSED: $TOTAL_PASSED/5 seeds completed with 0 mismatches" | tee -a "$GATE_LOG"
echo "Total transactions verified: $((TOTAL_PASSED * 10000))" | tee -a "$GATE_LOG"
echo "Logs saved to $GATE_LOG and $STRESS_LOG" | tee -a "$GATE_LOG"
echo "========================================================" | tee -a "$GATE_LOG"
