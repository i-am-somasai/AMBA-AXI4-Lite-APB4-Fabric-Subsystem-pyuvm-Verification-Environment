// Synchronous FIFO with count, overflow, underflow flags
`timescale 1ns/1ps

module sync_fifo #(
    parameter integer WIDTH = 8,
    parameter integer DEPTH = 8
) (
    input  wire                      clk,
    input  wire                      rst_n,
    input  wire                      push,
    input  wire [WIDTH-1:0]          wdata,
    input  wire                      pop,
    output reg  [WIDTH-1:0]          rdata,
    output wire                      full,
    output wire                      empty,
    output reg  [$clog2(DEPTH):0]    count,
    output reg                       overflow,
    output reg                       underflow
);

    localparam integer ADDR_WIDTH = $clog2(DEPTH);
    localparam [ADDR_WIDTH:0] DEPTH_VAL = DEPTH[ADDR_WIDTH:0];

    reg [WIDTH-1:0] mem [0:DEPTH-1];
    reg [ADDR_WIDTH-1:0] wptr;
    reg [ADDR_WIDTH-1:0] rptr;

    assign full  = (count == DEPTH_VAL);
    assign empty = (count == { (ADDR_WIDTH+1){1'b0} });

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wptr      <= {ADDR_WIDTH{1'b0}};
            rptr      <= {ADDR_WIDTH{1'b0}};
            count     <= {(ADDR_WIDTH+1){1'b0}};
            rdata     <= {WIDTH{1'b0}};
            overflow  <= 1'b0;
            underflow <= 1'b0;
        end else begin
            overflow  <= 1'b0;
            underflow <= 1'b0;

            case ({push, pop})
                2'b10: begin // Push only
                    if (!full) begin
                        mem[wptr] <= wdata;
                        wptr      <= wptr + 1'b1;
                        count     <= count + 1'b1;
                    end else begin
                        overflow  <= 1'b1;
                    end
                end

                2'b01: begin // Pop only
                    if (!empty) begin
                        rdata     <= mem[rptr];
                        rptr      <= rptr + 1'b1;
                        count     <= count - 1'b1;
                    end else begin
                        underflow <= 1'b1;
                    end
                end

                2'b11: begin // Push and Pop simultaneously
                    if (empty) begin
                        mem[wptr] <= wdata;
                        wptr      <= wptr + 1'b1;
                        count     <= count + 1'b1;
                        underflow <= 1'b1;
                    end else if (full) begin
                        mem[wptr] <= wdata;
                        wptr      <= wptr + 1'b1;
                        rdata     <= mem[rptr];
                        rptr      <= rptr + 1'b1;
                    end else begin
                        mem[wptr] <= wdata;
                        wptr      <= wptr + 1'b1;
                        rdata     <= mem[rptr];
                        rptr      <= rptr + 1'b1;
                    end
                end

                default: begin
                    // Idle
                end
            endcase
        end
    end

endmodule
