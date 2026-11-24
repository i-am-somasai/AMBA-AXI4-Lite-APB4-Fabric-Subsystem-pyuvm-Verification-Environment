#!/usr/bin/env bash
# scripts/check_no_synthetic_cov.sh
# Verifies that NO sample_* calls appear outside approved monitor/collector files.
set -e

PROJ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJ_DIR"

echo "=== Checking for illegal/synthetic coverage sampling calls ==="

# Approved files where sample_* calls are legally allowed:
# - tb/pyuvm/func_cov/fabric_cov.py (covergroup definition and collector)
# - tb/pyuvm/monitors/ (passive monitors observing real hardware signals)
VIOLATIONS=$(grep -rnE "\bsample_[a-zA-Z0-9_]+\s*\(" tb/ \
    --exclude="*.pyc" \
    --exclude-dir="__pycache__" \
    | grep -v "tb/pyuvm/func_cov/" \
    | grep -v "tb/pyuvm/monitors/" || true)

if [ -n "$VIOLATIONS" ]; then
    echo "ERROR: Found sample_* coverage calls outside approved monitor/collector files:"
    echo "$VIOLATIONS"
    exit 1
fi

echo "PASS: Zero synthetic coverage sampling calls found outside monitor/collector files."
exit 0
