// Hello world test module for Phase 0 smoke test
`timescale 1ns/1ps

module hello_world (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       en,
    output reg  [7:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 8'h00;
        end else if (en) begin
            count <= count + 1'b1;
        end
    end

endmodule
