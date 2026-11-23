# Top-level block test runner for L1 block tests
SIM ?= icarus
PROJ_DIR ?= $(abspath ../..)

BLOCK_TESTS = test_axil2apb_bridge \
              test_axil_xbar

.PHONY: all clean $(BLOCK_TESTS)

all: $(BLOCK_TESTS)
	@echo "====================================================="
	@echo "All L1 block tests executed successfully (SIM=$(SIM))."
	@echo "====================================================="

test_axil2apb_bridge:
	@echo "--- Running test_axil2apb_bridge (BR-01..BR-03) ---"
	$(MAKE) -f $(PROJ_DIR)/tb/block/Makefile.single \
		TOPLEVEL=axil2apb_bridge \
		MODULE=test_axil2apb_bridge \
		VERILOG_SOURCES=$(PROJ_DIR)/rtl/apb/axil2apb_bridge.v \
		SIM=$(SIM)

test_axil_xbar:
	@echo "--- Running test_axil_xbar (XB-01..XB-08) ---"
	$(MAKE) -f $(PROJ_DIR)/tb/block/Makefile.single \
		TOPLEVEL=tb_axil_xbar \
		MODULE=test_axil_xbar \
		VERILOG_SOURCES="$(PROJ_DIR)/rtl/axil/axil_decoder.v $(PROJ_DIR)/rtl/axil/axil_default_slave.v $(PROJ_DIR)/rtl/axil/axil_xbar.v $(PROJ_DIR)/tb/block/tb_axil_xbar.v" \
		SIM=$(SIM)

clean:
	rm -rf sim_build* results*.xml results.xml dump.vcd *.vcd __pycache__
