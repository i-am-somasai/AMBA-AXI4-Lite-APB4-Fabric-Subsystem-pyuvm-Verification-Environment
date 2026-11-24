//      // verilator_coverage annotation
        // rtl/apb/apb_gpio.v
        // APB4 GPIO Peripheral with 2-FF input synchronization and rising-edge interrupt detection
        `timescale 1ns / 1ps
        
        module apb_gpio #(
            parameter GPIO_WIDTH = 16,
            parameter ADDR_WIDTH = 12,
            parameter DATA_WIDTH = 32
        )(
 100022     input  wire                  clk,
~000014     input  wire                  rst_n,
        
            // APB4 Slave Interface
~000863     input  wire [ADDR_WIDTH-1:0] paddr,
 000996     input  wire [2:0]            pprot,
 000917     input  wire                  psel,
 003899     input  wire                  penable,
 001004     input  wire                  pwrite,
 000488     input  wire [DATA_WIDTH-1:0] pwdata,
 000697     input  wire [3:0]            pstrb,
 000917     output reg                   pready,
~000185     output reg  [DATA_WIDTH-1:0] prdata,
%000000     output reg                   pslverr,
        
            // External GPIO Pins
%000000     input  wire [GPIO_WIDTH-1:0] gpio_i,
 000027     output reg  [GPIO_WIDTH-1:0] gpio_o,
 000024     output reg  [GPIO_WIDTH-1:0] gpio_dir,
%000000     output wire                  gpio_irq
        );
        
            // Suppress lint for unused ports
            wire _unused = &{1'b0, pprot, pstrb, paddr[ADDR_WIDTH-1:5], paddr[1:0], pwdata[31:16]};
        
            // 2-FF Input Synchronizer + 1 cycle history for edge detection
%000000     reg [GPIO_WIDTH-1:0] sync_gpio_q1;
%000000     reg [GPIO_WIDTH-1:0] sync_gpio_q2;
%000000     reg [GPIO_WIDTH-1:0] sync_gpio_prev;
        
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             sync_gpio_q1   <= {GPIO_WIDTH{1'b0}};
 000171             sync_gpio_q2   <= {GPIO_WIDTH{1'b0}};
 000171             sync_gpio_prev <= {GPIO_WIDTH{1'b0}};
 099859         end else begin
 099859             sync_gpio_q1   <= gpio_i;
 099859             sync_gpio_q2   <= sync_gpio_q1;
 099859             sync_gpio_prev <= sync_gpio_q2;
                end
            end
        
            // Rising edge detection on synchronized input
%000000     wire [GPIO_WIDTH-1:0] gpio_rising_edges = sync_gpio_q2 & ~sync_gpio_prev;
        
            // Registers
            // 0x00: DIR        [GPIO_WIDTH-1:0]
            // 0x04: OUT        [GPIO_WIDTH-1:0]
            // 0x08: IN         [GPIO_WIDTH-1:0] (RO)
            // 0x0C: IRQ_EN     [GPIO_WIDTH-1:0]
            // 0x10: IRQ_STATUS [GPIO_WIDTH-1:0] (W1C)
 000031     reg [GPIO_WIDTH-1:0] reg_irq_en;
%000000     reg [GPIO_WIDTH-1:0] reg_irq_status;
        
~629953     assign gpio_irq = |reg_irq_status;
        
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             gpio_dir       <= {GPIO_WIDTH{1'b0}};
 000171             gpio_o         <= {GPIO_WIDTH{1'b0}};
 000171             reg_irq_en     <= {GPIO_WIDTH{1'b0}};
 000171             reg_irq_status <= {GPIO_WIDTH{1'b0}};
 099859         end else begin
                    // Latch rising-edge interrupts
 099859             reg_irq_status <= (reg_irq_status | (gpio_rising_edges & reg_irq_en));
        
                    // APB Register Writes
 099419             if (psel && penable && pwrite) begin
 000440                 case (paddr[4:2])
 000078                     3'b000: gpio_dir       <= pwdata[GPIO_WIDTH-1:0];       // 0x00: DIR
 000089                     3'b001: gpio_o         <= pwdata[GPIO_WIDTH-1:0];       // 0x04: OUT
 000089                     3'b010: ;                                               // 0x08: IN is RO
 000098                     3'b011: reg_irq_en     <= pwdata[GPIO_WIDTH-1:0];       // 0x0C: IRQ_EN
 000086                     3'b100: begin                                           // 0x10: IRQ_STATUS (W1C)
                                // Clear written 1s while still allowing new rising edges to be latched
 000086                         reg_irq_status <= (reg_irq_status & ~pwdata[GPIO_WIDTH-1:0]) | (gpio_rising_edges & reg_irq_en);
                            end
%000000                     default: ;
                        endcase
                    end
                end
            end
        
            // APB Read Response & Handshake (1-cycle access)
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             pready  <= 1'b0;
 000171             prdata  <= 32'd0;
 000171             pslverr <= 1'b0;
 099859         end else begin
 098025             if (psel && !penable) begin
                        // SETUP phase
 000917                 pready  <= 1'b1;
 000917                 pslverr <= 1'b0;
 000917                 case (paddr[4:2])
 000168                     3'b000:  prdata <= {{(32-GPIO_WIDTH){1'b0}}, gpio_dir};
 000185                     3'b001:  prdata <= {{(32-GPIO_WIDTH){1'b0}}, gpio_o};
 000176                     3'b010:  prdata <= {{(32-GPIO_WIDTH){1'b0}}, sync_gpio_q2};
 000205                     3'b011:  prdata <= {{(32-GPIO_WIDTH){1'b0}}, reg_irq_en};
 000183                     3'b100:  prdata <= {{(32-GPIO_WIDTH){1'b0}}, reg_irq_status};
%000000                     default: prdata <= 32'd0;
                        endcase
 098025             end else if (psel && penable) begin
 000917                 pready <= 1'b0;
 098025             end else begin
 098025                 pready <= 1'b0;
                    end
                end
            end
        
        endmodule
        
