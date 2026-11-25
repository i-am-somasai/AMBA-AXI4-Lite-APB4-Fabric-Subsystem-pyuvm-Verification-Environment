//      // verilator_coverage annotation
        // rtl/apb/apb_decoder.v
        // APB4 address decoder routing to UART (P0), Timer (P1), GPIO (P2), and unmapped error space
        `timescale 1ns / 1ps
        
        module apb_decoder #(
            parameter ADDR_WIDTH = 32,
            parameter DATA_WIDTH = 32
        )(
            // Input APB interface from bridge
~007436     input  wire [ADDR_WIDTH-1:0] paddr,
 030066     input  wire                  psel,
 030066     input  wire                  penable,
 030066     output reg                   pready,
 008155     output reg  [DATA_WIDTH-1:0] prdata,
 007437     output reg                   pslverr,
        
            // Peripheral 0: UART (0x4000_0000 - 0x4000_0FFF)
 007557     output wire                  psel_uart,
 007557     input  wire                  pready_uart,
~006147     input  wire [DATA_WIDTH-1:0] prdata_uart,
%000000     input  wire                  pslverr_uart,
        
            // Peripheral 1: Timer (0x4000_1000 - 0x4000_1FFF)
 007496     output wire                  psel_timer,
 007496     input  wire                  pready_timer,
 001543     input  wire [DATA_WIDTH-1:0] prdata_timer,
%000000     input  wire                  pslverr_timer,
        
            // Peripheral 2: GPIO (0x4000_2000 - 0x4000_2FFF)
 007576     output wire                  psel_gpio,
 007576     input  wire                  pready_gpio,
~001533     input  wire [DATA_WIDTH-1:0] prdata_gpio,
%000000     input  wire                  pslverr_gpio
        );
        
 005498     wire is_uart  = (paddr[15:12] == 4'h0);
 005559     wire is_timer = (paddr[15:12] == 4'h1);
 005607     wire is_gpio  = (paddr[15:12] == 4'h2);
 5748110     wire is_unmapped = psel && !is_uart && !is_timer && !is_gpio;
        
~6139802     wire _unused_addr = &{1'b0, paddr[31:16], paddr[11:0]};
        
 5748110     assign psel_uart  = psel && is_uart;
 5748110     assign psel_timer = psel && is_timer;
 5748110     assign psel_gpio  = psel && is_gpio;
        
 6139802     always @(*) begin
 1635802         if (is_uart) begin
 1635802             pready  = pready_uart;
 1635802             prdata  = prdata_uart;
 1635802             pslverr = pslverr_uart;
 1492523         end else if (is_timer) begin
 1492523             pready  = pready_timer;
 1492523             prdata  = prdata_timer;
 1492523             pslverr = pslverr_timer;
 1497968         end else if (is_gpio) begin
 1497968             pready  = pready_gpio;
 1497968             prdata  = prdata_gpio;
 1497968             pslverr = pslverr_gpio;
 1417227         end else if (is_unmapped) begin
                    // Unmapped space responds immediately on ACCESS phase with PSLVERR
 096282             pready  = penable;
 096282             prdata  = {DATA_WIDTH{1'b0}};
 096282             pslverr = penable;
 1417227         end else begin
 1417227             pready  = 1'b1;
 1417227             prdata  = {DATA_WIDTH{1'b0}};
 1417227             pslverr = 1'b0;
                end
            end
        
        endmodule
        
