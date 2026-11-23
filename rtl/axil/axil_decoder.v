// rtl/axil/axil_decoder.v
// Address decoder for AXI4-Lite crossbar
`timescale 1ns / 1ps

module axil_decoder #(
    parameter [31:0] S0_BASE = 32'h4000_0000,
    parameter [31:0] S0_MASK = 32'hFFFF_0000, // 64 KB (APB Subsystem)
    parameter [31:0] S1_BASE = 32'h5000_0000,
    parameter [31:0] S1_MASK = 32'hFFFF_F000, // 4 KB  (Scratch RAM)
    parameter [31:0] S2_BASE = 32'h6000_0000,
    parameter [31:0] S2_MASK = 32'hFFFF_FF00, // 256 B (CSR Block)
    parameter [31:0] S3_BASE = 32'h7000_0000,
    parameter [31:0] S3_MASK = 32'hFFFF_FF00  // 256 B (CDC Slow Regs)
)(
    input  wire [31:0] addr,
    output reg  [3:0]  slave_sel,
    output reg         decode_err
);

    always @(*) begin
        slave_sel  = 4'b0000;
        decode_err = 1'b0;

        if ((addr & S0_MASK) == S0_BASE) begin
            slave_sel = 4'b0001;
        end else if ((addr & S1_MASK) == S1_BASE) begin
            slave_sel = 4'b0010;
        end else if ((addr & S2_MASK) == S2_BASE) begin
            slave_sel = 4'b0100;
        end else if ((addr & S3_MASK) == S3_BASE) begin
            slave_sel = 4'b1000;
        end else begin
            decode_err = 1'b1;
        end
    end

endmodule
