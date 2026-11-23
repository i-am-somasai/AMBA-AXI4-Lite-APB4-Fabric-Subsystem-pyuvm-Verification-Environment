// rtl/apb/apb_decoder.v
// APB4 address decoder routing to UART (P0), Timer (P1), GPIO (P2), and unmapped error space
`timescale 1ns / 1ps

module apb_decoder #(
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 32
)(
    // Input APB interface from bridge
    input  wire [ADDR_WIDTH-1:0] paddr,
    input  wire                  psel,
    input  wire                  penable,
    output reg                   pready,
    output reg  [DATA_WIDTH-1:0] prdata,
    output reg                   pslverr,

    // Peripheral 0: UART (0x4000_0000 - 0x4000_0FFF)
    output wire                  psel_uart,
    input  wire                  pready_uart,
    input  wire [DATA_WIDTH-1:0] prdata_uart,
    input  wire                  pslverr_uart,

    // Peripheral 1: Timer (0x4000_1000 - 0x4000_1FFF)
    output wire                  psel_timer,
    input  wire                  pready_timer,
    input  wire [DATA_WIDTH-1:0] prdata_timer,
    input  wire                  pslverr_timer,

    // Peripheral 2: GPIO (0x4000_2000 - 0x4000_2FFF)
    output wire                  psel_gpio,
    input  wire                  pready_gpio,
    input  wire [DATA_WIDTH-1:0] prdata_gpio,
    input  wire                  pslverr_gpio
);

    wire is_uart  = (paddr[15:12] == 4'h0);
    wire is_timer = (paddr[15:12] == 4'h1);
    wire is_gpio  = (paddr[15:12] == 4'h2);
    wire is_unmapped = psel && !is_uart && !is_timer && !is_gpio;

    wire _unused_addr = &{1'b0, paddr[31:16], paddr[11:0]};

    assign psel_uart  = psel && is_uart;
    assign psel_timer = psel && is_timer;
    assign psel_gpio  = psel && is_gpio;

    always @(*) begin
        if (is_uart) begin
            pready  = pready_uart;
            prdata  = prdata_uart;
            pslverr = pslverr_uart;
        end else if (is_timer) begin
            pready  = pready_timer;
            prdata  = prdata_timer;
            pslverr = pslverr_timer;
        end else if (is_gpio) begin
            pready  = pready_gpio;
            prdata  = prdata_gpio;
            pslverr = pslverr_gpio;
        end else if (is_unmapped) begin
            // Unmapped space responds immediately on ACCESS phase with PSLVERR
            pready  = penable;
            prdata  = {DATA_WIDTH{1'b0}};
            pslverr = penable;
        end else begin
            pready  = 1'b1;
            prdata  = {DATA_WIDTH{1'b0}};
            pslverr = 1'b0;
        end
    end

endmodule
