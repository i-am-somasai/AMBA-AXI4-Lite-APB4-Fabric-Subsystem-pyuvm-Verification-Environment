#!/usr/bin/env bash
# scripts/run_regression.sh - Runs full pyuvm regression suite, collects coverage, and reports metrics
set -euo pipefail

PROJ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${PROJ_DIR}/docs/logs"
mkdir -p "${LOG_DIR}"

source "${PROJ_DIR}/scripts/env.sh"

echo "================================================================================"
echo " Starting Full Verification Regression & Coverage Collection"
echo " Simulator: Verilator (with HDL Code Coverage & pyuvm Functional Coverage)"
echo "================================================================================"

# 1. Clean previous build & coverage
make -C "${PROJ_DIR}/tb/pyuvm" clean
rm -f "${LOG_DIR}"/cov_*.yaml "${LOG_DIR}"/coverage_*.dat

# 2. Run Directed Tests (XB-09..XB-15, BR-04..BR-06, Section 10 closure)
echo ">>> Step 1/3: Running pyuvm Directed Verification Suite..."
make -C "${PROJ_DIR}/tb/pyuvm" test_directed SIM=verilator VERILATOR_COVERAGE=1
cp "${PROJ_DIR}/tb/pyuvm/coverage.dat" "${LOG_DIR}/coverage_directed.dat"

# 3. Run Multi-Seed Stress Tests (XB-13: 5 distinct seeds, 25,000 transactions total)
SEEDS=(42 123 777 2024 9999)
NUM_TRANS=2500 # 2500 per master = 5000 per seed = 25,000 transactions

echo ">>> Step 2/3: Running Multi-Seed Stress Regression across 5 seeds..."
for s in "${SEEDS[@]}"; do
    echo "    -> Running Seed ${s} (5,000 concurrent transactions)..."
    SEED=${s} NUM_TRANS_PER_MASTER=${NUM_TRANS} \
        make -C "${PROJ_DIR}/tb/pyuvm" test_stress SIM=verilator VERILATOR_COVERAGE=1
    cp "${PROJ_DIR}/tb/pyuvm/coverage.dat" "${LOG_DIR}/coverage_stress_seed_${s}.dat"
done

# 4. Merge Verilator Code Coverage
echo ">>> Step 3/3: Merging Code and Functional Coverage Reports..."
verilator_coverage -write "${LOG_DIR}/coverage_merged.dat" "${LOG_DIR}"/coverage_*.dat
verilator_coverage --report summary "${LOG_DIR}/coverage_merged.dat" | tee "${LOG_DIR}/code_cov_summary.txt"
verilator_coverage --annotate "${LOG_DIR}/code_cov" "${LOG_DIR}/coverage_merged.dat"

# 5. Merge pyuvm Functional Coverage
python3 "${PROJ_DIR}/scripts/merge_cov.py" "${LOG_DIR}"

echo "================================================================================"
echo " Regression & Coverage Collection Complete!"
echo " Results available in ${LOG_DIR}/"
echo "================================================================================"
