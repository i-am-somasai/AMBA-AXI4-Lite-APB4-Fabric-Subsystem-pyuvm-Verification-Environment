# Top-level unit test runner for all L0 unit tests
SIM ?= icarus
PROJ_DIR ?= $(abspath ../..)
BUILD_DIR ?= $(PROJ_DIR)/build

UNIT_TESTS = test_hello_world \
             test_rst_sync \
             test_sync_fifo \
             test_async_fifo \
             test_rr_arbiter \
             test_axil_decoder \
             test_axil_default_slave \
             test_axil_ram \
             test_axil_csr

.PHONY: all clean $(UNIT_TESTS)

all: $(UNIT_TESTS)
	@echo "====================================================="
	@echo "All L0 unit tests executed successfully (SIM=$(SIM))."
	@echo "====================================================="

test_hello_world:
	@echo "--- Running test_hello_world ---"
	$(MAKE) -f $(PROJ_DIR)/tb/unit/Makefile.single \
		TOPLEVEL=hello_world \
		MODULE=test_hello_world \
		VERILOG_SOURCES=$(PROJ_DIR)/tb/unit/hello_world.v \
		SIM=$(SIM)

test_rst_sync:
	@echo "--- Running test_rst_sync ---"
	$(MAKE) -f $(PROJ_DIR)/tb/unit/Makefile.single \
		TOPLEVEL=rst_sync \
		MODULE=test_rst_sync \
		VERILOG_SOURCES=$(PROJ_DIR)/rtl/common/rst_sync.v \
		SIM=$(SIM)

test_sync_fifo:
	@echo "--- Running test_sync_fifo ---"
	$(MAKE) -f $(PROJ_DIR)/tb/unit/Makefile.single \
		TOPLEVEL=sync_fifo \
		MODULE=test_sync_fifo \
		VERILOG_SOURCES=$(PROJ_DIR)/rtl/common/sync_fifo.v \
		SIM=$(SIM)

test_async_fifo:
	@echo "--- Running test_async_fifo ---"
	$(MAKE) -f $(PROJ_DIR)/tb/unit/Makefile.single \
		TOPLEVEL=async_fifo \
		MODULE=test_async_fifo \
		VERILOG_SOURCES=$(PROJ_DIR)/rtl/common/async_fifo.v \
		SIM=$(SIM)

test_rr_arbiter:
	@echo "--- Running test_rr_arbiter ---"
	$(MAKE) -f $(PROJ_DIR)/tb/unit/Makefile.single \
		TOPLEVEL=rr_arbiter \
		MODULE=test_rr_arbiter \
		VERILOG_SOURCES=$(PROJ_DIR)/rtl/common/rr_arbiter.v \
		SIM=$(SIM)

test_axil_decoder:
	@echo "--- Running test_axil_decoder ---"
	$(MAKE) -f $(PROJ_DIR)/tb/unit/Makefile.single \
		TOPLEVEL=axil_decoder \
		MODULE=test_axil_decoder \
		VERILOG_SOURCES=$(PROJ_DIR)/rtl/axil/axil_decoder.v \
		SIM=$(SIM)

test_axil_default_slave:
	@echo "--- Running test_axil_default_slave ---"
	$(MAKE) -f $(PROJ_DIR)/tb/unit/Makefile.single \
		TOPLEVEL=axil_default_slave \
		MODULE=test_axil_default_slave \
		VERILOG_SOURCES=$(PROJ_DIR)/rtl/axil/axil_default_slave.v \
		SIM=$(SIM)

test_axil_ram:
	@echo "--- Running test_axil_ram ---"
	$(MAKE) -f $(PROJ_DIR)/tb/unit/Makefile.single \
		TOPLEVEL=axil_ram \
		MODULE=test_axil_ram \
		VERILOG_SOURCES=$(PROJ_DIR)/rtl/axil/axil_ram.v \
		SIM=$(SIM)

test_axil_csr:
	@echo "--- Running test_axil_csr ---"
	$(MAKE) -f $(PROJ_DIR)/tb/unit/Makefile.single \
		TOPLEVEL=axil_csr \
		MODULE=test_axil_csr \
		VERILOG_SOURCES=$(PROJ_DIR)/rtl/axil/axil_csr.v \
		SIM=$(SIM)

clean:
	rm -rf sim_build* $(BUILD_DIR)/sim_build/unit_* $(BUILD_DIR)/results/unit results*.xml results.xml dump.vcd *.vcd __pycache__
