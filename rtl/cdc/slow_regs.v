// rtl/cdc/slow_regs.v
// Registers located in clk_slow domain (SLVERR on undefined offsets, free-running counter)
`timescale 1ns / 1ps

module slow_regs (
    input  wire        clk_slow,
    input  wire        rst_slow_n,

    // Interface to Request FIFO (read side of req async FIFO)
    input  wire        req_empty,
    output reg         req_pop,
    input  wire [44:0] req_data, // {is_write, addr[7:0], wdata[31:0], wstrb[3:0]}

    // Interface to Response FIFO (write side of resp async FIFO)
    input  wire        resp_full,
    output reg         resp_push,
    output reg  [33:0] resp_data  // {rdata[31:0], resp[1:0]}
);

    // Unpack request fields
    wire        req_is_write = req_data[44];
    wire [7:0]  req_addr     = req_data[43:36];
    wire [31:0] req_wdata    = req_data[35:4];
    wire [3:0]  req_wstrb    = req_data[3:0];

    // Registers
    // 0x00: SLOW_ID      (RO) 0x510E_0001
    // 0x04: SLOW_SCRATCH (RW) 32-bit byte-strobe writable
    // 0x08: SLOW_COUNTER (RO) 32-bit free-running up counter
    // 0x0C: SLOW_CTRL    (RW) [0] counter enable (default 1)
    localparam [31:0] CONST_SLOW_ID = 32'h510E_0001;

    reg [31:0] reg_scratch;
    reg [31:0] reg_counter;
    reg        reg_ctrl;

    // FSM States
    localparam ST_IDLE = 1'b0,
               ST_RESP = 1'b1;

    reg state;

    // Request latch registers
    reg        req_is_write_q;
    reg [7:0]  req_addr_q;
    reg [31:0] req_wdata_q;
    reg [3:0]  req_wstrb_q;

    // Suppress unused address bits
    wire _unused = &{1'b0, req_addr[7:4], req_addr[1:0], req_addr_q[1:0]};

    // Free-running counter and registers in clk_slow
    always @(posedge clk_slow or negedge rst_slow_n) begin
        if (!rst_slow_n) begin
            reg_counter    <= 32'd0;
            reg_ctrl       <= 1'b1; // Default enabled
            reg_scratch    <= 32'd0;
            req_is_write_q <= 1'b0;
            req_addr_q     <= 8'd0;
            req_wdata_q    <= 32'd0;
            req_wstrb_q    <= 4'd0;
        end else begin
            if (reg_ctrl) begin
                reg_counter <= reg_counter + 1'b1;
            end

            // Latch request when transitioning from IDLE to RESP
            if (state == ST_IDLE && !req_empty && !resp_full) begin
                req_is_write_q <= req_is_write;
                req_addr_q     <= req_addr;
                req_wdata_q    <= req_wdata;
                req_wstrb_q    <= req_wstrb;
            end

            // Process writes when in ST_RESP
            if (state == ST_RESP && req_is_write_q) begin
                case (req_addr_q[3:2])
                    2'b00: ; // 0x00: SLOW_ID is RO
                    2'b01: begin // 0x04: SLOW_SCRATCH
                        if (req_wstrb_q[0]) reg_scratch[7:0]   <= req_wdata_q[7:0];
                        if (req_wstrb_q[1]) reg_scratch[15:8]  <= req_wdata_q[15:8];
                        if (req_wstrb_q[2]) reg_scratch[23:16] <= req_wdata_q[23:16];
                        if (req_wstrb_q[3]) reg_scratch[31:24] <= req_wdata_q[31:24];
                    end
                    2'b10: ; // 0x08: SLOW_COUNTER is RO
                    2'b11: reg_ctrl <= req_wdata_q[0]; // 0x0C: SLOW_CTRL
                    default: ;
                endcase
            end
        end
    end

    // Request-Response FSM
    always @(posedge clk_slow or negedge rst_slow_n) begin
        if (!rst_slow_n) begin
            state     <= ST_IDLE;
            req_pop   <= 1'b0;
            resp_push <= 1'b0;
            resp_data <= 34'd0;
        end else begin
            req_pop   <= 1'b0;
            resp_push <= 1'b0;

            case (state)
                ST_IDLE: begin
                    if (!req_empty && !resp_full) begin
                        req_pop <= 1'b1; // Pop request
                        state   <= ST_RESP;
                    end
                end

                ST_RESP: begin
                    if (!resp_full) begin
                        resp_push <= 1'b1;
                        state     <= ST_IDLE;

                        if (req_is_write_q) begin
                            // Write response: check address validity
                            if (req_addr_q[7:4] == 4'h0) begin
                                resp_data <= {32'd0, 2'b00}; // OKAY
                            end else begin
                                resp_data <= {32'd0, 2'b10}; // SLVERR
                            end
                        end else begin
                            // Read response
                            if (req_addr_q[7:4] == 4'h0) begin
                                case (req_addr_q[3:2])
                                    2'b00:   resp_data <= {CONST_SLOW_ID, 2'b00};
                                    2'b01:   resp_data <= {reg_scratch,   2'b00};
                                    2'b10:   resp_data <= {reg_counter,   2'b00};
                                    2'b11:   resp_data <= {{31'd0, reg_ctrl}, 2'b00};
                                    default: resp_data <= {32'd0,         2'b10}; // SLVERR
                                endcase
                            end else begin
                                resp_data <= {32'd0, 2'b10}; // SLVERR
                            end
                        end
                    end
                end
            endcase
        end
    end

endmodule
