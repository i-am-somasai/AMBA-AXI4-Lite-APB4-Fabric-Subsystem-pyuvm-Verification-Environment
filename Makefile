# AMBA-Fabric Top-Level Makefile
# Open-source EDA tools & pyuvm verification environment

SHELL := /bin/bash
PROJ_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
BUILD_DIR ?= $(PROJ_DIR)/build
export BUILD_DIR
export TMPDIR := $(BUILD_DIR)/tmp

# Toolchain paths
OSS_CAD_SUITE ?= $(HOME)/oss-cad-suite
STA_BIN       ?= /nix/store/q5ycjmn0d9awbcq05c75z2rmgwjgbc9g-opensta/bin/sta
SKY130_LIB    ?= $(HOME)/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib

# Environment setup wrapper (safe even if scripts/env.sh is absent in CI)
ENV_CMD := mkdir -p $(BUILD_DIR)/tmp $(BUILD_DIR)/results $(BUILD_DIR)/sim_build && if [ -f "$(PROJ_DIR)/scripts/env.sh" ]; then source "$(PROJ_DIR)/scripts/env.sh"; else export TMPDIR="$(BUILD_DIR)/tmp" PYTHONPATH="$(PROJ_DIR):$(PROJ_DIR)/tb:$(PROJ_DIR)/tb/unit:$(PROJ_DIR)/tb/pyuvm:$(PROJ_DIR)/tb/models$${PYTHONPATH:+:$$PYTHONPATH}"; fi

# Simulation parameters (G2: max 2 parallel Verilator compiles, 4 for Icarus)
SIM ?= icarus
SEEDS ?= 20
MAX_JOBS ?= $(if $(filter verilator,$(SIM)),2,4)

# RTL Source directories
RTL_DIRS := $(PROJ_DIR)/rtl/common $(PROJ_DIR)/rtl/axil $(PROJ_DIR)/rtl/apb $(PROJ_DIR)/rtl/cdc $(PROJ_DIR)/rtl
RTL_SRCS := $(wildcard $(PROJ_DIR)/rtl/common/*.v) \
            $(wildcard $(PROJ_DIR)/rtl/axil/*.v) \
            $(wildcard $(PROJ_DIR)/rtl/apb/*.v) \
            $(wildcard $(PROJ_DIR)/rtl/cdc/*.v) \
            $(wildcard $(PROJ_DIR)/rtl/*.v)

.PHONY: all env-check lint unit block regress regress-verilator cov-report formal sanity mutation mutation-sample synth sta clean

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

# RTL Lint target using Verilator, coverage honesty check, bug refs, and docs consistency
lint:
	@$(ENV_CMD) && echo "=== Checking for Synthetic Coverage Calls ===" && \
	$(PROJ_DIR)/scripts/check_no_synthetic_cov.sh
	@$(ENV_CMD) && echo "=== Checking Bug Regression References ===" && \
	python3 $(PROJ_DIR)/scripts/check_bug_refs.py
	@$(ENV_CMD) && echo "=== Checking Documentation Consistency against metrics.json ===" && \
	python3 $(PROJ_DIR)/scripts/check_docs_consistency.py
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

# Sanity mutants gate (count driven by mutation/sanity/run_sanity.py -> docs/metrics.json)
sanity:
	@$(ENV_CMD) && echo "=== Running Sanity Gate ===" && \
	mkdir -p $(PROJ_DIR)/docs/logs && \
	python3 $(PROJ_DIR)/mutation/sanity/run_sanity.py | tee $(PROJ_DIR)/docs/logs/sanity.log

# Mutation testing (full run)
mutation:
	@$(ENV_CMD) && echo "=== Running Full Mutation Testing ===" && \
	if [ -f "$(PROJ_DIR)/mutation/run_mutants.py" ]; then \
		python3 $(PROJ_DIR)/mutation/run_mutants.py --max-mutants 240; \
	else \
		echo "Mutation testing runner will be populated in Phase 6."; \
	fi

# Mutation testing (sample for CI)
mutation-sample:
	@$(ENV_CMD) && echo "=== Running Sampled Mutation Testing (CI) ===" && \
	mkdir -p $(BUILD_DIR)/results && \
	python3 $(PROJ_DIR)/mutation/run_mutants.py --sample --output $(BUILD_DIR)/results/mutation_sample.log

# Yosys Synthesis for SKY130 (Spec Section 13.1 via synth/synth.ys)
synth:
	@$(ENV_CMD) && set -o pipefail && echo "=== Running Yosys Synthesis for SKY130 ===" && \
	test -f "$(SKY130_LIB)" && \
	mkdir -p synth/results $(PROJ_DIR)/build && \
	ln -sf "$(SKY130_LIB)" "$(PROJ_DIR)/build/sky130_tt.lib" && \
	yosys -s $(PROJ_DIR)/synth/synth.ys | sed "s|$(PROJ_DIR)/||g; s|/home/[^/ ]*/||g" | tee synth/results/synth.log

# OpenSTA Static Timing Analysis (Spec Section 13.3)
sta:
	@$(ENV_CMD) && set -o pipefail && echo "=== Running OpenSTA Timing Analysis ===" && \
	mkdir -p synth/results && \
	sta -exit $(PROJ_DIR)/synth/sta.tcl | sed "s|$(PROJ_DIR)/||g; s|/home/[^/ ]*/||g" | tee synth/results/sta.log && \
	python3 $(PROJ_DIR)/synth/fmax_sweep.py

# Clean build artifacts
clean:
	@rm -rf $(BUILD_DIR)
	@rm -rf tb/unit/sim_build* tb/unit/__pycache__ tb/unit/results*.xml tb/unit/*.vcd
	@rm -rf tb/block/sim_build* tb/block/__pycache__ tb/block/results*.xml tb/block/*.vcd
	@rm -rf tb/pyuvm/sim_build* tb/pyuvm/__pycache__ tb/pyuvm/results*.xml tb/pyuvm/*.vcd
	@rm -rf sim_build* obj_dir __pycache__ results*.xml dump.vcd *.log
	@echo "Clean completed."
