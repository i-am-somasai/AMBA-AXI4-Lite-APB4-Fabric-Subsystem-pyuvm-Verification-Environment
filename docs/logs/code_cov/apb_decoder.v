//      // verilator_coverage annotation
        // rtl/apb/apb_decoder.v
        // APB4 address decoder routing to UART (P0), Timer (P1), GPIO (P2), and unmapped error space
        `timescale 1ns / 1ps
        
        module apb_decoder #(
            parameter ADDR_WIDTH = 32,
            parameter DATA_WIDTH = 32
        )(
            // Input APB interface from bridge
~000946     input  wire [ADDR_WIDTH-1:0] paddr,
 003899     input  wire                  psel,
 003899     input  wire                  penable,
 003899     output reg                   pready,
 000986     output reg  [DATA_WIDTH-1:0] prdata,
 000957     output reg                   pslverr,
        
            // Peripheral 0: UART (0x4000_0000 - 0x4000_0FFF)
 001035     output wire                  psel_uart,
 001035     input  wire                  pready_uart,
~000791     input  wire [DATA_WIDTH-1:0] prdata_uart,
%000000     input  wire                  pslverr_uart,
        
            // Peripheral 1: Timer (0x4000_1000 - 0x4000_1FFF)
 000990     output wire                  psel_timer,
 000990     input  wire                  pready_timer,
 000185     input  wire [DATA_WIDTH-1:0] prdata_timer,
%000000     input  wire                  pslverr_timer,
        
            // Peripheral 2: GPIO (0x4000_2000 - 0x4000_2FFF)
 000917     output wire                  psel_gpio,
 000917     input  wire                  pready_gpio,
~000185     input  wire [DATA_WIDTH-1:0] prdata_gpio,
%000000     input  wire                  pslverr_gpio
        );
        
 000712     wire is_uart  = (paddr[15:12] == 4'h0);
 000663     wire is_timer = (paddr[15:12] == 4'h1);
 000673     wire is_gpio  = (paddr[15:12] == 4'h2);
 580311     wire is_unmapped = psel && !is_uart && !is_timer && !is_gpio;
        
~629953     wire _unused_addr = &{1'b0, paddr[31:16], paddr[11:0]};
        
 580311     assign psel_uart  = psel && is_uart;
 580311     assign psel_timer = psel && is_timer;
 580311     assign psel_gpio  = psel && is_gpio;
        
 629953     always @(*) begin
 177811         if (is_uart) begin
 177811             pready  = pready_uart;
 177811             prdata  = prdata_uart;
 177811             pslverr = pslverr_uart;
 150674         end else if (is_timer) begin
 150674             pready  = pready_timer;
 150674             prdata  = prdata_timer;
 150674             pslverr = pslverr_timer;
 147160         end else if (is_gpio) begin
 147160             pready  = pready_gpio;
 147160             prdata  = prdata_gpio;
 147160             pslverr = pslverr_gpio;
 142142         end else if (is_unmapped) begin
                    // Unmapped space responds immediately on ACCESS phase with PSLVERR
 012166             pready  = penable;
 012166             prdata  = {DATA_WIDTH{1'b0}};
 012166             pslverr = penable;
 142142         end else begin
 142142             pready  = 1'b1;
 142142             prdata  = {DATA_WIDTH{1'b0}};
 142142             pslverr = 1'b0;
                end
            end
        
        endmodule
        
