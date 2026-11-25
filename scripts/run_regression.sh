#!/usr/bin/env bash
# scripts/run_regression.sh - Runs full pyuvm + block regression, collects Verilator & functional coverage
set -euo pipefail

PROJ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PROJ_DIR
BUILD_DIR="${BUILD_DIR:-${PROJ_DIR}/build}"
export BUILD_DIR
export TMPDIR="${BUILD_DIR}/tmp"

LOG_DIR="${PROJ_DIR}/docs/logs"
COV_DAT_DIR="${BUILD_DIR}/coverage"
mkdir -p "${LOG_DIR}" "${COV_DAT_DIR}" "${TMPDIR}"

source "${PROJ_DIR}/scripts/env.sh"

echo "================================================================================"
echo " Starting Full Verification Regression & Coverage Collection"
echo " Simulator: Verilator (with HDL Code Coverage & pyuvm Functional Coverage)"
echo " BUILD_DIR: ${BUILD_DIR}"
echo "================================================================================"

# 1. Clean previous build & coverage
make -C "${PROJ_DIR}/tb/pyuvm" clean
make -C "${PROJ_DIR}/tb/block" clean
rm -rf "${COV_DAT_DIR}" "${LOG_DIR}"/cov_*.yaml "${LOG_DIR}"/coverage_*.dat
mkdir -p "${COV_DAT_DIR}"

# 2. Run Top-Level Directed Tests (XB-09..XB-15, CDC ratio sweeps 25ns / 10.3ns / 6.0ns)
echo ">>> Step 1/4: Running pyuvm Directed & CDC Sweep Verification Suite..."
rm -f "${PROJ_DIR}/tb/pyuvm/coverage.dat"
make -C "${PROJ_DIR}/tb/pyuvm" -j2 test_directed SIM=verilator VERILATOR_COVERAGE=1
cp "${PROJ_DIR}/tb/pyuvm/coverage.dat" "${COV_DAT_DIR}/coverage_directed.dat"

# 3. Run Block-Level AXI4-Lite to APB4 Bridge Coverage Closure (cg_apb wait states & PSTRB=0)
echo ">>> Step 2/4: Running Block-Level Bridge Tests (cg_apb wait states & PSTRB=0)..."
rm -f "${PROJ_DIR}/tb/block/coverage.dat"
make -C "${PROJ_DIR}/tb/block" -j2 test_axil2apb_bridge SIM=verilator VERILATOR_COVERAGE=1
cp "${PROJ_DIR}/tb/block/coverage.dat" "${COV_DAT_DIR}/coverage_bridge_block.dat"

# 4. Run 20-Seed Stress Regression (XB-13: 20 seeds x 10,000 txns = 200,000 txns total)
SEEDS_STR="${SEEDS_LIST:-$(seq 1 20)}"
NUM_TRANS="${NUM_TRANS_PER_MASTER:-5000}"

echo ">>> Step 3/4: Running 20-Seed Stress Regression (${NUM_TRANS}*2 txns/seed)..."
for s in ${SEEDS_STR}; do
    echo "    -> Running Seed ${s} ($((NUM_TRANS * 2)) concurrent transactions)..."
    rm -f "${PROJ_DIR}/tb/pyuvm/coverage.dat"
    SEED=${s} NUM_TRANS_PER_MASTER=${NUM_TRANS} \
    make -C "${PROJ_DIR}/tb/pyuvm" -j2 test_stress \
        SIM=verilator VERILATOR_COVERAGE=1 \
        STRESS_SIM_BUILD="${BUILD_DIR}/sim_build/pyuvm_stress_cov" \
        COCOTB_RESULTS_FILE="${BUILD_DIR}/results/pyuvm/results_test_stress_${s}.xml"
    cp "${PROJ_DIR}/tb/pyuvm/coverage.dat" "${COV_DAT_DIR}/coverage_stress_seed_${s}.dat"
done

# 5. Merge Verilator Code Coverage
echo ">>> Step 4/4: Merging Code & Functional Coverage Reports..."
verilator_coverage -write "${COV_DAT_DIR}/coverage_merged.dat" "${COV_DAT_DIR}"/coverage_*.dat
verilator_coverage --report summary "${COV_DAT_DIR}/coverage_merged.dat" \
    | sed "s|${PROJ_DIR}/||g; s|/home/[^/ ]*/||g" > "${LOG_DIR}/code_cov_summary.txt"
cat "${LOG_DIR}/code_cov_summary.txt"
rm -rf "${LOG_DIR}/code_cov"
verilator_coverage --annotate "${LOG_DIR}/code_cov" "${COV_DAT_DIR}/coverage_merged.dat"

# Strip intermediate sim_build directories cleanly to conserve workspace disk space
rm -rf "${BUILD_DIR}/sim_build/pyuvm_"* "${BUILD_DIR}/sim_build/block_"* "${PROJ_DIR}/tb/pyuvm/coverage.dat" "${PROJ_DIR}/tb/block/coverage.dat"

# 6. Merge pyuvm Functional Coverage (top_level + block cg_apb)
python3 "${PROJ_DIR}/scripts/merge_cov.py" "${LOG_DIR}"

echo "================================================================================"
echo " Regression & Coverage Collection Complete!"
echo " Results available in ${LOG_DIR}/"
echo "================================================================================"
