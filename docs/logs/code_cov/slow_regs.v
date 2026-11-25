//      // verilator_coverage annotation
        // rtl/cdc/slow_regs.v
        // Registers located in clk_slow domain (SLVERR on undefined offsets, free-running counter)
        `timescale 1ns / 1ps
        
        module slow_regs (
 389558     input  wire        clk_slow,
~000021     input  wire        rst_slow_n,
        
            // Interface to Request FIFO (read side of req async FIFO)
 030393     input  wire        req_empty,
 030372     output reg         req_pop,
~015281     input  wire [44:0] req_data, // {is_write, addr[7:0], wdata[31:0], wstrb[3:0]}
        
            // Interface to Response FIFO (write side of resp async FIFO)
%000000     input  wire        resp_full,
 030372     output reg         resp_push,
~006570     output reg  [33:0] resp_data  // {rdata[31:0], resp[1:0]}
        );
        
            // Unpack request fields
 015148     wire        req_is_write = req_data[44];
~015281     wire [7:0]  req_addr     = req_data[43:36];
 011497     wire [31:0] req_wdata    = req_data[35:4];
 010567     wire [3:0]  req_wstrb    = req_data[3:0];
        
            // Registers
            // 0x00: SLOW_ID      (RO) 0x510E_0001
            // 0x04: SLOW_SCRATCH (RW) 32-bit byte-strobe writable
            // 0x08: SLOW_COUNTER (RO) 32-bit free-running up counter
            // 0x0C: SLOW_CTRL    (RW) [0] counter enable (default 1)
            localparam [31:0] CONST_SLOW_ID = 32'h510E_0001;
        
 000889     reg [31:0] reg_scratch;
~103139     reg [31:0] reg_counter;
 001932     reg        reg_ctrl;
        
            // FSM States
            localparam ST_IDLE = 1'b0,
                       ST_RESP = 1'b1;
        
 030372     reg state;
        
            // Request latch registers
 007548     reg        req_is_write_q;
~009290     reg [7:0]  req_addr_q;
 005789     reg [31:0] req_wdata_q;
 005310     reg [3:0]  req_wstrb_q;
        
            // Suppress unused address bits
~6344689     wire _unused = &{1'b0, req_addr[7:4], req_addr[1:0], req_addr_q[1:0]};
        
            // Free-running counter and registers in clk_slow
 389558     always @(posedge clk_slow or negedge rst_slow_n) begin
 389376         if (!rst_slow_n) begin
 000182             reg_counter    <= 32'd0;
 000182             reg_ctrl       <= 1'b1; // Default enabled
 000182             reg_scratch    <= 32'd0;
 000182             req_is_write_q <= 1'b0;
 000182             req_addr_q     <= 8'd0;
 000182             req_wdata_q    <= 32'd0;
 000182             req_wstrb_q    <= 4'd0;
 389376         end else begin
 206267             if (reg_ctrl) begin
 206267                 reg_counter <= reg_counter + 1'b1;
                    end
        
                    // Latch request when transitioning from IDLE to RESP
~359004             if (state == ST_IDLE && !req_empty && !resp_full) begin
 030372                 req_is_write_q <= req_is_write;
 030372                 req_addr_q     <= req_addr;
 030372                 req_wdata_q    <= req_wdata;
 030372                 req_wstrb_q    <= req_wstrb;
                    end
        
                    // Process writes when in ST_RESP
 374166             if (state == ST_RESP && req_is_write_q) begin
 015210                 case (req_addr_q[3:2])
%000002                     2'b00: ; // 0x00: SLOW_ID is RO
 007575                     2'b01: begin // 0x04: SLOW_SCRATCH
 004192                         if (req_wstrb_q[0]) reg_scratch[7:0]   <= req_wdata_q[7:0];
 004127                         if (req_wstrb_q[1]) reg_scratch[15:8]  <= req_wdata_q[15:8];
 004236                         if (req_wstrb_q[2]) reg_scratch[23:16] <= req_wdata_q[23:16];
 004183                         if (req_wstrb_q[3]) reg_scratch[31:24] <= req_wdata_q[31:24];
                            end
%000000                     2'b10: ; // 0x08: SLOW_COUNTER is RO
 007633                     2'b11: reg_ctrl <= req_wdata_q[0]; // 0x0C: SLOW_CTRL
%000000                     default: ;
                        endcase
                    end
                end
            end
        
            // Request-Response FSM
 389558     always @(posedge clk_slow or negedge rst_slow_n) begin
 389376         if (!rst_slow_n) begin
 000182             state     <= ST_IDLE;
 000182             req_pop   <= 1'b0;
 000182             resp_push <= 1'b0;
 000182             resp_data <= 34'd0;
 389376         end else begin
 389376             req_pop   <= 1'b0;
 389376             resp_push <= 1'b0;
        
 389376             case (state)
 359004                 ST_IDLE: begin
~328632                     if (!req_empty && !resp_full) begin
 030372                         req_pop <= 1'b1; // Pop request
 030372                         state   <= ST_RESP;
                            end
                        end
        
 030372                 ST_RESP: begin
~030372                     if (!resp_full) begin
 030372                         resp_push <= 1'b1;
 030372                         state     <= ST_IDLE;
        
 015210                         if (req_is_write_q) begin
                                    // Write response: check address validity
~015208                             if (req_addr_q[7:4] == 4'h0) begin
 015208                                 resp_data <= {32'd0, 2'b00}; // OKAY
%000002                             end else begin
%000002                                 resp_data <= {32'd0, 2'b10}; // SLVERR
                                    end
 015162                         end else begin
                                    // Read response
~015160                             if (req_addr_q[7:4] == 4'h0) begin
 015160                                 case (req_addr_q[3:2])
 005010                                     2'b00:   resp_data <= {CONST_SLOW_ID, 2'b00};
 002528                                     2'b01:   resp_data <= {reg_scratch,   2'b00};
 005113                                     2'b10:   resp_data <= {reg_counter,   2'b00};
 002509                                     2'b11:   resp_data <= {{31'd0, reg_ctrl}, 2'b00};
%000000                                     default: resp_data <= {32'd0,         2'b10}; // SLVERR
                                        endcase
%000002                             end else begin
%000002                                 resp_data <= {32'd0, 2'b10}; // SLVERR
                                    end
                                end
                            end
                        end
                    endcase
                end
            end
        
        endmodule
        
