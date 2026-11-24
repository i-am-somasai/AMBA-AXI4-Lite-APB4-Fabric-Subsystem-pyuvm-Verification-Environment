# AMBA-Fabric Top-Level Makefile
# Open-source EDA tools & pyuvm verification environment

SHELL := /bin/bash
PROJ_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

# Toolchain paths
OSS_CAD_SUITE ?= /home/somasai/oss-cad-suite
STA_BIN       ?= /nix/store/q5ycjmn0d9awbcq05c75z2rmgwjgbc9g-opensta/bin/sta
SKY130_LIB    ?= /home/somasai/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib

# Environment setup wrapper
ENV_CMD := source $(PROJ_DIR)/scripts/env.sh

# Simulation parameters
SIM ?= icarus
SEEDS ?= 20
MAX_JOBS ?= 4

# RTL Source directories
RTL_DIRS := $(PROJ_DIR)/rtl/common $(PROJ_DIR)/rtl/axil $(PROJ_DIR)/rtl/apb $(PROJ_DIR)/rtl/cdc $(PROJ_DIR)/rtl
RTL_SRCS := $(wildcard $(PROJ_DIR)/rtl/common/*.v) \
            $(wildcard $(PROJ_DIR)/rtl/axil/*.v) \
            $(wildcard $(PROJ_DIR)/rtl/apb/*.v) \
            $(wildcard $(PROJ_DIR)/rtl/cdc/*.v) \
            $(wildcard $(PROJ_DIR)/rtl/*.v)

.PHONY: all env-check lint unit regress regress-verilator cov-report formal mutation mutation-sample synth sta clean

all: lint unit

# Check toolchain availability
env-check:
	@$(ENV_CMD) && echo "=== Toolchain Environment Check ===" && \
	echo "Icarus:    $$(which iverilog 2>/dev/null || echo 'NOT FOUND')" && \
	echo "Verilator: $$(which verilator 2>/dev/null || echo 'NOT FOUND')" && \
	echo "Yosys:     $$(which yosys 2>/dev/null || echo 'NOT FOUND')" && \
	echo "SBY:       $$(which sby 2>/dev/null || echo 'NOT FOUND')" && \
	echo "OpenSTA:   $$(which sta 2>/dev/null || echo 'NOT FOUND')" && \
	echo "SKY130:    $$(test -f $(SKY130_LIB) && echo 'FOUND' || echo 'NOT FOUND')" && \
	python3 -c "import cocotb, pyuvm, cocotb_coverage; print('Python packages: cocotb, pyuvm, cocotb-coverage OK')"

# RTL Lint target using Verilator and synthetic coverage check
lint:
	@$(ENV_CMD) && echo "=== Checking for Synthetic Coverage Calls ===" && \
	$(PROJ_DIR)/scripts/check_no_synthetic_cov.sh
	@$(ENV_CMD) && echo "=== Running RTL Lint (Verilator) ===" && \
	if [ -n "$$(echo $(RTL_SRCS))" ]; then \
		verilator --lint-only -Wall -Wno-DECLFILENAME -Wno-MULTITOP -I$(PROJ_DIR)/rtl/common -I$(PROJ_DIR)/rtl/axil -I$(PROJ_DIR)/rtl/apb -I$(PROJ_DIR)/rtl/cdc $(RTL_SRCS); \
	else \
		verilator --lint-only -Wall $(PROJ_DIR)/tb/unit/hello_world.v; \
	fi
	@echo "Lint CLEAN."

# L0 Unit tests
unit:
	@$(ENV_CMD) && echo "=== Running L0 Unit Tests (SIM=$(SIM)) ===" && \
	$(MAKE) -C tb/unit SIM=$(SIM) clean && \
	$(MAKE) -C tb/unit SIM=$(SIM)

# L1 Block tests (XB-01..XB-08, BR-01..BR-03)
block:
	@$(ENV_CMD) && echo "=== Running L1 Block Tests (SIM=$(SIM)) ===" && \
	$(MAKE) -C tb/block SIM=$(SIM) clean && \
	$(MAKE) -C tb/block SIM=$(SIM)

# pyuvm Regression (Icarus default)
regress:
	@$(ENV_CMD) && echo "=== Running pyuvm Regression (SIM=$(SIM), SEEDS=$(SEEDS)) ===" && \
	if [ -f "$(PROJ_DIR)/tb/pyuvm/Makefile" ]; then \
		$(MAKE) -C tb/pyuvm -j$(MAX_JOBS) SIM=$(SIM) SEEDS=$(SEEDS) regress; \
	else \
		echo "pyuvm testbench Makefile will be populated in Phase 2-4."; \
	fi

# pyuvm Regression on Verilator
regress-verilator:
	@$(MAKE) regress SIM=verilator SEEDS=$(SEEDS)

# Coverage collection and reporting
cov-report:
	@$(ENV_CMD) && echo "=== Generating Coverage Report ===" && \
	if [ -f "$(PROJ_DIR)/scripts/run_regression.sh" ]; then \
		bash $(PROJ_DIR)/scripts/run_regression.sh; \
	elif [ -f "$(PROJ_DIR)/scripts/merge_cov.py" ]; then \
		python3 $(PROJ_DIR)/scripts/merge_cov.py; \
	fi

# Formal verification with SymbiYosys
formal:
	@$(ENV_CMD) && echo "=== Running Formal Proofs (SymbiYosys) ===" && \
	if [ -f "$(PROJ_DIR)/scripts/run_all_formal.sh" ]; then \
		bash $(PROJ_DIR)/scripts/run_all_formal.sh; \
	else \
		echo "Formal verification scripts will be populated in Phase 1, 2, 5."; \
	fi

# Mutation testing (full run)
mutation:
	@$(ENV_CMD) && echo "=== Running Full Mutation Testing ===" && \
	if [ -f "$(PROJ_DIR)/mutation/run_mutants.py" ]; then \
		python3 $(PROJ_DIR)/mutation/run_mutants.py --max-mutants 300; \
	else \
		echo "Mutation testing runner will be populated in Phase 6."; \
	fi

# Mutation testing (sample for CI)
mutation-sample:
	@$(ENV_CMD) && echo "=== Running Sampled Mutation Testing (CI) ===" && \
	if [ -f "$(PROJ_DIR)/mutation/run_mutants.py" ]; then \
		python3 $(PROJ_DIR)/mutation/run_mutants.py --max-mutants 20; \
	else \
		echo "Mutation testing runner will be populated in Phase 6."; \
	fi

# Yosys Synthesis for SKY130
synth:
	@$(ENV_CMD) && echo "=== Running Yosys Synthesis for SKY130 ===" && \
	mkdir -p synth/results && \
	if [ -f "$(PROJ_DIR)/synth/synth.ys" ]; then \
		yosys $(PROJ_DIR)/synth/synth.ys | tee synth/results/synth.log; \
	else \
		echo "Synthesis script will be populated in Phase 6."; \
	fi

# OpenSTA Static Timing Analysis
sta:
	@$(ENV_CMD) && echo "=== Running OpenSTA Timing Analysis ===" && \
	mkdir -p synth/results && \
	if [ -f "$(PROJ_DIR)/synth/sta.tcl" ]; then \
		sta -exit $(PROJ_DIR)/synth/sta.tcl | tee synth/results/sta.log && \
		python3 $(PROJ_DIR)/synth/fmax_sweep.py; \
	else \
		echo "STA script will be populated in Phase 6."; \
	fi

# Clean build artifacts
clean:
	@rm -rf tb/unit/sim_build tb/unit/__pycache__ tb/unit/results.xml tb/unit/*.vcd
	@rm -rf tb/pyuvm/sim_build tb/pyuvm/__pycache__ tb/pyuvm/results.xml tb/pyuvm/*.vcd
	@rm -rf sim_build obj_dir __pycache__ results.xml dump.vcd *.log
	@echo "Clean completed."
