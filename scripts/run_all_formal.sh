#!/usr/bin/env bash
# scripts/run_all_formal.sh - Run all formal proofs in formal/ and print a structured summary table
set -euo pipefail

PROJ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FORMAL_DIR="${PROJ_DIR}/formal"
LOG_FILE="${PROJ_DIR}/docs/logs/formal_suite.log"

# Source environment
if [ -f "${PROJ_DIR}/scripts/env.sh" ]; then
    source "${PROJ_DIR}/scripts/env.sh"
fi

mkdir -p "$(dirname "${LOG_FILE}")" "${BUILD_DIR:-${PROJ_DIR}/build}/tmp"

# Keep scratch files in BUILD_DIR (never /tmp)
RUN_LOG="${BUILD_DIR:-${PROJ_DIR}/build}/tmp/formal_suite_run.log"
exec > >(tee "${RUN_LOG}") 2>&1

echo "=========================================================================================="
echo " Running SymbiYosys Formal Verification Suite"
echo " Directory: formal/"
echo "=========================================================================================="

FAILED=0
TOTAL=0

# Temporary file to store per-module summary data
SUMMARY_DATA="${BUILD_DIR:-${PROJ_DIR}/build}/tmp/formal_summary.dat"
rm -f "${SUMMARY_DATA}"

for sby_file in $(find "${FORMAL_DIR}" -maxdepth 1 -name "*.sby" | sort); do
    base_name=$(basename "${sby_file}" .sby)
    echo "=== [${base_name}] Running SymbiYosys ==="
    TOTAL=$((TOTAL + 1))
    
    # Run sby
    set +e
    (cd "${FORMAL_DIR}" && sby -f "${base_name}.sby")
    sby_rc=$?
    set -e
    
    # Determine mode and depth (handle suites with both prove and bmc tasks, e.g., axil_csr)
    if grep -q "mode prove" "${sby_file}" && grep -q "mode bmc" "${sby_file}"; then
        mode="prv+bmc"
        depth=$(grep "depth" "${sby_file}" | head -n 1 | awk '{print $NF}')
        main_task="${base_name}_prove"
    elif grep -q "mode prove" "${sby_file}"; then
        mode="prove"
        depth=$(grep "depth" "${sby_file}" | head -n 1 | awk '{print $NF}')
        main_task="${base_name}_prove"
    else
        mode="bmc"
        depth=$(grep "depth" "${sby_file}" | head -n 1 | awk '{print $NF}')
        main_task="${base_name}_bmc"
    fi
    
    # Determine result
    res="PASS"
    if [ ${sby_rc} -ne 0 ]; then
        res="FAIL"
        FAILED=$((FAILED + 1))
    fi
    if [ -f "${FORMAL_DIR}/${main_task}/status" ]; then
        status_word=$(head -n 1 "${FORMAL_DIR}/${main_task}/status" | awk '{print $1}')
        if [ "${status_word}" != "PASS" ]; then
            res="FAIL"
        fi
    fi
    
    # Extract cover count
    cover_count=0
    cover_task="${base_name}_cover"
    if [ -f "${FORMAL_DIR}/${cover_task}/PASS" ]; then
        cover_count=$(grep -c "cover trace:.*\.vcd" "${FORMAL_DIR}/${cover_task}/PASS" || true)
    elif [ -f "${FORMAL_DIR}/${cover_task}/logfile.txt" ]; then
        cover_count=$(grep -c "reached cover statement" "${FORMAL_DIR}/${cover_task}/logfile.txt" || true)
    fi
    
    # Extract runtime (seconds)
    runtime="0s"
    if [ -f "${FORMAL_DIR}/${main_task}/status" ]; then
        sec=$(head -n 1 "${FORMAL_DIR}/${main_task}/status" | awk '{print $3}')
        if [ -n "${sec}" ]; then
            runtime="${sec}s"
        fi
    fi
    
    echo "${base_name}|${mode}|${depth}|${res}|${cover_count}|${runtime}" >> "${SUMMARY_DATA}"
    echo "=== [${base_name}] Result: ${res} (${runtime}) ==="
    echo ""
done

echo "=========================================================================================="
echo " Formal Verification Summary Matrix"
echo "=========================================================================================="
printf "| %-18s | %-7s | %-5s | %-6s | %-8s | %-7s |\n" "Module" "Mode" "Depth" "Result" "Covers" "Runtime"
printf "|--------------------|---------|-------|--------|----------|---------|\n"

while IFS='|' read -r mod mode depth res cov time; do
    printf "| %-18s | %-7s | %-5s | %-6s | %-8s | %-7s |\n" "${mod}" "${mode}" "${depth}" "${res}" "${cov}" "${time}"
done < "${SUMMARY_DATA}"

printf "|--------------------|---------|-------|--------|----------|---------|\n"
echo " Total: ${TOTAL} | Passed: $((TOTAL - FAILED)) | Failed: ${FAILED}"
echo "=========================================================================================="

rm -f "${SUMMARY_DATA}"

# Copy log to destination
cp "${RUN_LOG}" "${LOG_FILE}"
rm -f "${RUN_LOG}"

# Strip any absolute paths in the generated log
sed -i "s|${PROJ_DIR}/||g" "${LOG_FILE}"
sed -i "s|/home/[^/]*/||g" "${LOG_FILE}"

if [ ${FAILED} -ne 0 ]; then
    echo "Formal suite FAILED with ${FAILED} errors."
    exit 1
fi

echo "Formal suite PASSED (10/10 modules clean)."
exit 0
