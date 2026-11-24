#!/usr/bin/env bash
# scripts/run_mutation.sh
# Run scaled parallel mutation testing with open-source toolchain
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/env.sh"

cd "${PROJ_DIR}"
mkdir -p docs/logs mutation/results/survivors

python3 mutation/run_mutants.py "$@"
