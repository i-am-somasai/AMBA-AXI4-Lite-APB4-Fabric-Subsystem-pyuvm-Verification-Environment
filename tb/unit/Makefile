# Unit test Makefile for hello_world
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

PROJ_DIR ?= $(abspath ../..)
VERILOG_SOURCES = $(PROJ_DIR)/tb/unit/hello_world.v
TOPLEVEL = hello_world
MODULE = test_hello_world

# Include cocotb makefiles
include $(shell cocotb-config --makefiles)/Makefile.sim
