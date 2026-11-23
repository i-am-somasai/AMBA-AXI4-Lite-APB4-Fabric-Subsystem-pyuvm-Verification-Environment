# Top-level block test runner for L1 block tests and top-level integration
SIM ?= icarus
PROJ_DIR ?= $(abspath ../..)

BLOCK_TESTS = test_axil2apb_bridge \
              test_axil_xbar \
              test_apb_timer \
              test_apb_gpio \
              test_apb_uart \
              test_axil_cdc_bridge \
              test_amba_fabric_top

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

.PHONY: all clean $(BLOCK_TESTS)

all: $(BLOCK_TESTS)
	@echo "====================================================="
	@echo "All Phase 3 block and top tests executed successfully (SIM=$(SIM))."
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

test_apb_timer:
	@echo "--- Running test_apb_timer (TM-01..TM-03) ---"
	$(MAKE) -f $(PROJ_DIR)/tb/block/Makefile.single \
		TOPLEVEL=apb_timer \
		MODULE=test_apb_timer \
		VERILOG_SOURCES=$(PROJ_DIR)/rtl/apb/apb_timer.v \
		SIM=$(SIM)

test_apb_gpio:
	@echo "--- Running test_apb_gpio (GP-01..GP-03) ---"
	$(MAKE) -f $(PROJ_DIR)/tb/block/Makefile.single \
		TOPLEVEL=apb_gpio \
		MODULE=test_apb_gpio \
		VERILOG_SOURCES=$(PROJ_DIR)/rtl/apb/apb_gpio.v \
		SIM=$(SIM)

test_apb_uart:
	@echo "--- Running test_apb_uart (UA-01..UA-03, UA-05) ---"
	$(MAKE) -f $(PROJ_DIR)/tb/block/Makefile.single \
		TOPLEVEL=apb_uart \
		MODULE=test_apb_uart \
		VERILOG_SOURCES="$(PROJ_DIR)/rtl/common/sync_fifo.v $(PROJ_DIR)/rtl/apb/apb_uart.v" \
		SIM=$(SIM)

test_axil_cdc_bridge:
	@echo "--- Running test_axil_cdc_bridge (CD-01, CD-04, CD-05) ---"
	$(MAKE) -f $(PROJ_DIR)/tb/block/Makefile.single \
		TOPLEVEL=axil_cdc_bridge \
		MODULE=test_axil_cdc_bridge \
		VERILOG_SOURCES="$(PROJ_DIR)/rtl/common/async_fifo.v $(PROJ_DIR)/rtl/cdc/slow_regs.v $(PROJ_DIR)/rtl/cdc/axil_cdc_bridge.v" \
		SIM=$(SIM)

test_amba_fabric_top:
	@echo "--- Running test_amba_fabric_top (TOP-01, TOP-02) ---"
	$(MAKE) -f $(PROJ_DIR)/tb/block/Makefile.single \
		TOPLEVEL=amba_fabric_top \
		MODULE=test_amba_fabric_top \
		VERILOG_SOURCES="$(ALL_RTL_SOURCES)" \
		SIM=$(SIM)

clean:
	rm -rf sim_build* results*.xml results.xml dump.vcd *.vcd __pycache__
