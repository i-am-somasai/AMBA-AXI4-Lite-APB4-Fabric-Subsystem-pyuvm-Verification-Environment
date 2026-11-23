#!/usr/bin/env bash
# scripts/run_all_formal.sh - Run all formal proofs in formal/ and print a PASS/FAIL summary table
set -euo pipefail

PROJ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FORMAL_DIR="${PROJ_DIR}/formal"

echo "========================================================"
echo " Running SymbiYosys Formal Verification Suite"
echo " Directory: ${FORMAL_DIR}"
echo "========================================================"

FAILED=0
TOTAL=0
RESULTS=()

for sby_file in $(find "${FORMAL_DIR}" -maxdepth 1 -name "*.sby" | sort); do
    base_name=$(basename "${sby_file}" .sby)
    echo "--- Running SBY for ${base_name} ---"
    TOTAL=$((TOTAL + 1))
    if (cd "${FORMAL_DIR}" && sby -f "${base_name}.sby"); then
        RESULTS+=("${base_name}: PASS")
    else
        RESULTS+=("${base_name}: FAIL")
        FAILED=$((FAILED + 1))
    fi
    echo ""
done

echo "========================================================"
echo " Formal Verification Summary"
echo "========================================================"
for res in "${RESULTS[@]}"; do
    echo "  ${res}"
done
echo "--------------------------------------------------------"
echo " Total: ${TOTAL} | Passed: $((TOTAL - FAILED)) | Failed: ${FAILED}"
echo "========================================================"

if [ ${FAILED} -ne 0 ]; then
    exit 1
fi
exit 0
