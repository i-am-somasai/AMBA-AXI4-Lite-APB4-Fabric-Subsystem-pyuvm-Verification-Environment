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

`ifdef FORMAL
    reg f_past_valid = 1'b0;
    always @(posedge clk) f_past_valid <= 1'b1;

    always @(*) begin
        if (!f_past_valid) assume (!rst_n);
    end

    // Inductive FIFO Data Integrity & Strict Ordering via (* anyconst *) Magic Value
    (* anyconst *) reg [WIDTH-1:0] f_magic_val;
    reg                f_armed = 1'b0;
    reg [ADDR_WIDTH:0] f_pos   = {(ADDR_WIDTH+1){1'b0}};

    wire f_will_push = push && (!full || pop);
    wire f_will_pop  = pop  && !empty;
    wire [ADDR_WIDTH-1:0] f_magic_idx = rptr + f_pos[ADDR_WIDTH-1:0];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            f_armed <= 1'b0;
            f_pos   <= {(ADDR_WIDTH+1){1'b0}};
        end else begin
            if (!f_armed) begin
                if (f_will_push && (wdata == f_magic_val)) begin
                    f_armed <= 1'b1;
                    f_pos   <= f_will_pop ? (count - {{ADDR_WIDTH{1'b0}}, 1'b1}) : count;
                end
            end else if (f_will_pop) begin
                if (f_pos == {(ADDR_WIDTH+1){1'b0}}) begin
                    if (f_will_push && (wdata == f_magic_val)) begin
                        f_armed <= 1'b1;
                        f_pos   <= count - {{ADDR_WIDTH{1'b0}}, 1'b1};
                    end else begin
                        f_armed <= 1'b0;
                        f_pos   <= {(ADDR_WIDTH+1){1'b0}};
                    end
                end else begin
                    f_pos <= f_pos - {{ADDR_WIDTH{1'b0}}, 1'b1};
                end
            end
        end
    end

    always @(posedge clk) begin
        if (rst_n) begin
            assert (count <= DEPTH_VAL);
            assert (wptr == (rptr + count[ADDR_WIDTH-1:0]));
            if (f_armed) begin
                assert (f_pos < count);
                assert (mem[f_magic_idx] == f_magic_val);
            end
            if (f_past_valid && $past(rst_n) && $past(f_armed) && ($past(f_pos) == {(ADDR_WIDTH+1){1'b0}}) && $past(f_will_pop)) begin
                assert (rdata == f_magic_val);
            end
        end
    end

`ifndef NO_INTERNAL_FIFO_COVERS
    always @(posedge clk) begin
        if (rst_n && f_past_valid) begin
            cover (f_armed && f_pos > 0);
            cover ($past(rst_n) && $past(f_armed) && ($past(f_pos) == 0) && $past(f_will_pop) && (rdata == f_magic_val));
        end
    end
`endif
`endif

endmodule
