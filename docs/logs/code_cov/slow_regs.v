//      // verilator_coverage annotation
        // rtl/cdc/slow_regs.v
        // Registers located in clk_slow domain (SLVERR on undefined offsets, free-running counter)
        `timescale 1ns / 1ps
        
        module slow_regs (
 040010     input  wire        clk_slow,
~000014     input  wire        rst_slow_n,
        
            // Interface to Request FIFO (read side of req async FIFO)
 003927     input  wire        req_empty,
 003921     output reg         req_pop,
~001969     input  wire [44:0] req_data, // {is_write, addr[7:0], wdata[31:0], wstrb[3:0]}
        
            // Interface to Response FIFO (write side of resp async FIFO)
%000000     input  wire        resp_full,
 003921     output reg         resp_push,
~000882     output reg  [33:0] resp_data  // {rdata[31:0], resp[1:0]}
        );
        
            // Unpack request fields
 001935     wire        req_is_write = req_data[44];
~001969     wire [7:0]  req_addr     = req_data[43:36];
 001531     wire [31:0] req_wdata    = req_data[35:4];
 001413     wire [3:0]  req_wstrb    = req_data[3:0];
        
            // Registers
            // 0x00: SLOW_ID      (RO) 0x510E_0001
            // 0x04: SLOW_SCRATCH (RW) 32-bit byte-strobe writable
            // 0x08: SLOW_COUNTER (RO) 32-bit free-running up counter
            // 0x0C: SLOW_CTRL    (RW) [0] counter enable (default 1)
            localparam [31:0] CONST_SLOW_ID = 32'h510E_0001;
        
 000122     reg [31:0] reg_scratch;
~010880     reg [31:0] reg_counter;
 000250     reg        reg_ctrl;
        
            // FSM States
            localparam ST_IDLE = 1'b0,
                       ST_RESP = 1'b1;
        
 003921     reg state;
        
            // Request latch registers
 000997     reg        req_is_write_q;
~001273     reg [7:0]  req_addr_q;
 000777     reg [31:0] req_wdata_q;
 000714     reg [3:0]  req_wstrb_q;
        
            // Suppress unused address bits
~649959     wire _unused = &{1'b0, req_addr[7:4], req_addr[1:0], req_addr_q[1:0]};
        
            // Free-running counter and registers in clk_slow
 040018     always @(posedge clk_slow or negedge rst_slow_n) begin
 039928         if (!rst_slow_n) begin
 000090             reg_counter    <= 32'd0;
 000090             reg_ctrl       <= 1'b1; // Default enabled
 000090             reg_scratch    <= 32'd0;
 000090             req_is_write_q <= 1'b0;
 000090             req_addr_q     <= 8'd0;
 000090             req_wdata_q    <= 32'd0;
 000090             req_wstrb_q    <= 4'd0;
 039928         end else begin
 021756             if (reg_ctrl) begin
 021756                 reg_counter <= reg_counter + 1'b1;
                    end
        
                    // Latch request when transitioning from IDLE to RESP
~036007             if (state == ST_IDLE && !req_empty && !resp_full) begin
 003921                 req_is_write_q <= req_is_write;
 003921                 req_addr_q     <= req_addr;
 003921                 req_wdata_q    <= req_wdata;
 003921                 req_wstrb_q    <= req_wstrb;
                    end
        
                    // Process writes when in ST_RESP
 037916             if (state == ST_RESP && req_is_write_q) begin
 002012                 case (req_addr_q[3:2])
%000003                     2'b00: ; // 0x00: SLOW_ID is RO
 001013                     2'b01: begin // 0x04: SLOW_SCRATCH
 000551                         if (req_wstrb_q[0]) reg_scratch[7:0]   <= req_wdata_q[7:0];
 000567                         if (req_wstrb_q[1]) reg_scratch[15:8]  <= req_wdata_q[15:8];
 000554                         if (req_wstrb_q[2]) reg_scratch[23:16] <= req_wdata_q[23:16];
 000569                         if (req_wstrb_q[3]) reg_scratch[31:24] <= req_wdata_q[31:24];
                            end
%000000                     2'b10: ; // 0x08: SLOW_COUNTER is RO
 000996                     2'b11: reg_ctrl <= req_wdata_q[0]; // 0x0C: SLOW_CTRL
%000000                     default: ;
                        endcase
                    end
                end
            end
        
            // Request-Response FSM
 040018     always @(posedge clk_slow or negedge rst_slow_n) begin
 039928         if (!rst_slow_n) begin
 000090             state     <= ST_IDLE;
 000090             req_pop   <= 1'b0;
 000090             resp_push <= 1'b0;
 000090             resp_data <= 34'd0;
 039928         end else begin
 039928             req_pop   <= 1'b0;
 039928             resp_push <= 1'b0;
        
 039928             case (state)
 036007                 ST_IDLE: begin
~032086                     if (!req_empty && !resp_full) begin
 003921                         req_pop <= 1'b1; // Pop request
 003921                         state   <= ST_RESP;
                            end
                        end
        
 003921                 ST_RESP: begin
~003921                     if (!resp_full) begin
 003921                         resp_push <= 1'b1;
 003921                         state     <= ST_IDLE;
        
 002012                         if (req_is_write_q) begin
                                    // Write response: check address validity
~002009                             if (req_addr_q[7:4] == 4'h0) begin
 002009                                 resp_data <= {32'd0, 2'b00}; // OKAY
%000003                             end else begin
%000003                                 resp_data <= {32'd0, 2'b10}; // SLVERR
                                    end
 001909                         end else begin
                                    // Read response
~001906                             if (req_addr_q[7:4] == 4'h0) begin
 001906                                 case (req_addr_q[3:2])
 000654                                     2'b00:   resp_data <= {CONST_SLOW_ID, 2'b00};
 000313                                     2'b01:   resp_data <= {reg_scratch,   2'b00};
 000627                                     2'b10:   resp_data <= {reg_counter,   2'b00};
 000312                                     2'b11:   resp_data <= {{31'd0, reg_ctrl}, 2'b00};
%000000                                     default: resp_data <= {32'd0,         2'b10}; // SLVERR
                                        endcase
%000003                             end else begin
%000003                                 resp_data <= {32'd0, 2'b10}; // SLVERR
                                    end
                                end
                            end
                        end
                    endcase
                end
            end
        
        endmodule
        
