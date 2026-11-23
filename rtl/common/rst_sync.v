// Reset synchronizer (2-FF, async assert, sync deassert)
`timescale 1ns/1ps

module rst_sync (
    input  wire clk,
    input  wire rst_n_in,
    output wire rst_n_out
);

    reg sync_q1;
    reg sync_q2;

    always @(posedge clk or negedge rst_n_in) begin
        if (!rst_n_in) begin
            sync_q1 <= 1'b0;
            sync_q2 <= 1'b0;
        end else begin
            sync_q1 <= 1'b1;
            sync_q2 <= sync_q1;
        end
    end

    assign rst_n_out = sync_q2;

endmodule
