#!/usr/bin/env bash
set -euo pipefail
PROJ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${PROJ_DIR}/scripts/env.sh"
python3 "${PROJ_DIR}/mutation/sanity/run_sanity.py"
