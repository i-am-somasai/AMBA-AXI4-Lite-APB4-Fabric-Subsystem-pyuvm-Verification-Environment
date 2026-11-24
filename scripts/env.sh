#!/usr/bin/env bash
# Source environment for amba-fabric EDA tools and Python
export PROJ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# OSS CAD Suite (Yosys, SBY, Icarus, Verilator, GTKWave, Boolector, Yices, Z3)
if [ -d "/home/somasai/oss-cad-suite" ]; then
    source /home/somasai/oss-cad-suite/environment
fi

# OpenSTA
export STA_BIN="/nix/store/q5ycjmn0d9awbcq05c75z2rmgwjgbc9g-opensta/bin/sta"
if [ -f "$STA_BIN" ]; then
    export PATH="$(dirname "$STA_BIN"):$PATH"
fi

# SKY130 Liberty
export SKY130_LIB="/home/somasai/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"

# Python path
export PYTHONPATH="$PROJ_DIR:$PROJ_DIR/tb:$PROJ_DIR/tb/unit:$PROJ_DIR/tb/pyuvm:$PROJ_DIR/tb/models${PYTHONPATH:+:$PYTHONPATH}"
