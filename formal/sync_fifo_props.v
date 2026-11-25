// formal/sync_fifo_props.v
// Formal verification properties for sync_fifo
`timescale 1ns/1ps

module sync_fifo_props #(
    parameter integer WIDTH = 8,
    parameter integer DEPTH = 8
)(
    input  wire                   clk,
    input  wire                   rst_n,
    input  wire                   push,
    input  wire [WIDTH-1:0]       wdata,
    input  wire                   pop,
    output wire [WIDTH-1:0]       rdata,
    output wire                   full,
    output wire                   empty,
    output wire [$clog2(DEPTH):0] count,
    output wire                   overflow,
    output wire                   underflow
);

    // Instantiate DUT
    sync_fifo #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH)
    ) dut (
        .clk      (clk),
        .rst_n    (rst_n),
        .push     (push),
        .wdata    (wdata),
        .pop      (pop),
        .rdata    (rdata),
        .full     (full),
        .empty    (empty),
        .count    (count),
        .overflow (overflow),
        .underflow(underflow)
    );

`ifdef FORMAL
    reg f_past_valid = 0;
    always @(posedge clk) begin
        f_past_valid <= 1;
    end

    // Initial reset assumption
    always @(*) begin
        if (!f_past_valid)
            assume (!rst_n);
    end

    // Flag correctness
    always @(posedge clk) begin
        if (rst_n) begin
            // 1. Empty and full consistency with count
            assert (empty == (count == 0));
            assert (full == (count == DEPTH));
            assert (count <= DEPTH);

            // 2. Cannot be both empty and full (when DEPTH > 0)
            if (DEPTH > 0) begin
                assert (!(empty && full));
            end
        end
    end

    // State transition tracking
    always @(posedge clk) begin
        if (f_past_valid && $past(rst_n) && rst_n) begin
            case ({$past(push), $past(pop)})
                2'b10: begin // Push only
                    if (!$past(full)) begin
                        assert (count == $past(count) + 1'b1);
                        assert (!overflow);
                    end else begin
                        assert (count == $past(count));
                        assert (overflow);
                    end
                    assert (!underflow);
                end

                2'b01: begin // Pop only
                    if (!$past(empty)) begin
                        assert (count == $past(count) - 1'b1);
                        assert (!underflow);
                    end else begin
                        assert (count == $past(count));
                        assert (underflow);
                    end
                    assert (!overflow);
                end

                2'b11: begin // Push and Pop
                    if ($past(empty)) begin
                        assert (count == $past(count) + 1'b1);
                        assert (underflow);
                        assert (!overflow);
                    end else begin
                        assert (count == $past(count));
                        assert (!overflow);
                        assert (!underflow);
                    end
                end

                2'b00: begin // Idle
                    assert (count == $past(count));
                    assert (!overflow);
                    assert (!underflow);
                end
            endcase
        end
    end

    // Cover statements (magic-value ordering & integrity proven in sync_fifo.v under `ifdef FORMAL)
    always @(posedge clk) begin
        if (rst_n) begin
            cover (empty);
            cover (full);
            cover (count == DEPTH/2);
            cover (push && pop && !full && !empty);
            cover (overflow);
            cover (underflow);
        end
    end
`endif

endmodule
