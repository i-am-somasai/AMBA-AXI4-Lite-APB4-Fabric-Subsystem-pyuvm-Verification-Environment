# SDC Timing Constraints for AMBA-Fabric Top
# Target: clk_sys = 100 MHz (10.0 ns), clk_slow = 41.67 MHz (24.0 ns)
# Spec Section 13.2

# Define Clocks
create_clock -name clk_sys  -period 10.0 [get_ports clk_sys]
create_clock -name clk_slow -period 24.0 [get_ports clk_slow]

# Clock Groups: Asynchronous domains with CDC FIFO synchronizers
set_clock_groups -asynchronous -group {clk_sys} -group {clk_slow}

# Input / Output Delays on clk_sys
set_input_delay 2.0 -clock clk_sys [all_inputs -no_clocks]
set_output_delay 2.0 -clock clk_sys [all_outputs]

# Asynchronous Reset is a false path for static timing analysis
set_false_path -from [get_ports rst_n]

# Driving cell and output load
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_2 [all_inputs -no_clocks]
set_load 0.035 [all_outputs]
