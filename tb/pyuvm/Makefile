# Top-level pyuvm test runner for Phase 4 verification
SIM ?= icarus
PROJ_DIR ?= $(abspath ../..)
SEED ?= 42
NUM_TRANS_PER_MASTER ?= 5000
SEEDS ?= 20

ALL_RTL_SOURCES = $(PROJ_DIR)/rtl/common/rst_sync.v \
                  $(PROJ_DIR)/rtl/common/sync_fifo.v \
                  $(PROJ_DIR)/rtl/common/async_fifo.v \
                  $(PROJ_DIR)/rtl/common/rr_arbiter.v \
                  $(PROJ_DIR)/rtl/axil/axil_default_slave.v \
                  $(PROJ_DIR)/rtl/axil/axil_decoder.v \
                  $(PROJ_DIR)/rtl/axil/axil_xbar.v \
                  $(PROJ_DIR)/rtl/axil/axil_ram.v \
                  $(PROJ_DIR)/rtl/axil/axil_csr.v \
                  $(PROJ_DIR)/rtl/apb/axil2apb_bridge.v \
                  $(PROJ_DIR)/rtl/apb/apb_decoder.v \
                  $(PROJ_DIR)/rtl/apb/apb_uart.v \
                  $(PROJ_DIR)/rtl/apb/apb_timer.v \
                  $(PROJ_DIR)/rtl/apb/apb_gpio.v \
                  $(PROJ_DIR)/rtl/cdc/slow_regs.v \
                  $(PROJ_DIR)/rtl/cdc/axil_cdc_bridge.v \
                  $(PROJ_DIR)/rtl/amba_fabric_top.v

ifeq ($(words $(SEEDS)),1)
  ifeq ($(shell test $(SEEDS) -gt 0 2>/dev/null && echo yes),yes)
    SEED_LIST := $(shell seq 1 $(SEEDS))
  else
    SEED_LIST := $(SEEDS)
  endif
else
  SEED_LIST := $(SEEDS)
endif

.PHONY: all clean test_stress test_directed stress_regression regress $(addprefix stress_seed_, $(SEED_LIST))

all: test_directed stress_regression
	@echo "====================================================="
	@echo "All pyuvm directed and stress tests passed successfully."
	@echo "====================================================="

regress: all

test_directed:
	@echo "--- Running pyuvm directed tests (XB-09..XB-15, BR-04..BR-06) ---"
	$(MAKE) -f $(PROJ_DIR)/tb/pyuvm/Makefile.single \
		TOPLEVEL=amba_fabric_top \
		MODULE=test_directed \
		SIM_BUILD=sim_build_directed \
		COCOTB_RESULTS_FILE=results_test_directed.xml \
		VERILOG_SOURCES="$(ALL_RTL_SOURCES)" \
		SIM=$(SIM)
	@echo "--- Running CDC sweeps across clock ratios and phases ---"
	CLK_SLOW_PERIOD_NS=10.3 CLK_SLOW_PHASE_NS=2.5 SEED=103 \
	$(MAKE) -f $(PROJ_DIR)/tb/pyuvm/Makefile.single \
		TOPLEVEL=amba_fabric_top \
		MODULE=test_directed \
		TESTCASE=TestCoverageClosure \
		SIM_BUILD=sim_build_cdc_10_3 \
		COCOTB_RESULTS_FILE=results_test_cdc_10_3.xml \
		VERILOG_SOURCES="$(ALL_RTL_SOURCES)" \
		SIM=$(SIM)
	CLK_SLOW_PERIOD_NS=6.0 CLK_SLOW_PHASE_NS=1.2 SEED=60 \
	$(MAKE) -f $(PROJ_DIR)/tb/pyuvm/Makefile.single \
		TOPLEVEL=amba_fabric_top \
		MODULE=test_directed \
		TESTCASE=TestCoverageClosure \
		SIM_BUILD=sim_build_cdc_6_0 \
		COCOTB_RESULTS_FILE=results_test_cdc_6_0.xml \
		VERILOG_SOURCES="$(ALL_RTL_SOURCES)" \
		SIM=$(SIM)

test_stress:
	@echo "--- Running XB-13 stress test (SEED=$(SEED), TRANS=$(shell echo $$(($(NUM_TRANS_PER_MASTER)*2)))) ---"
	SEED=$(SEED) NUM_TRANS_PER_MASTER=$(NUM_TRANS_PER_MASTER) \
	$(MAKE) -f $(PROJ_DIR)/tb/pyuvm/Makefile.single \
		TOPLEVEL=amba_fabric_top \
		MODULE=test_stress \
		SIM_BUILD=sim_build_stress_$(SEED) \
		COCOTB_RESULTS_FILE=results_test_stress_$(SEED).xml \
		VERILOG_SOURCES="$(ALL_RTL_SOURCES)" \
		SIM=$(SIM)

stress_regression: $(addprefix stress_seed_, $(SEED_LIST))
	@echo "=== All $(words $(SEED_LIST)) stress seeds passed with zero mismatches ==="

$(addprefix stress_seed_, $(SEED_LIST)): stress_seed_%: | test_directed
	@echo ">>> Running stress seed $*..."
	@SEED=$* NUM_TRANS_PER_MASTER=$(NUM_TRANS_PER_MASTER) \
	$(MAKE) -f $(PROJ_DIR)/tb/pyuvm/Makefile.single \
		TOPLEVEL=amba_fabric_top \
		MODULE=test_stress \
		SIM_BUILD=sim_build_stress_$* \
		COCOTB_RESULTS_FILE=results_test_stress_$*.xml \
		VERILOG_SOURCES="$(ALL_RTL_SOURCES)" \
		SIM=$(SIM)

clean:
	rm -rf sim_build* results*.xml dump.vcd *.vcd __pycache__
