// rtl/apb/apb_gpio.v
// APB4 GPIO Peripheral with 2-FF input synchronization and rising-edge interrupt detection
`timescale 1ns / 1ps

module apb_gpio #(
    parameter GPIO_WIDTH = 16,
    parameter ADDR_WIDTH = 12,
    parameter DATA_WIDTH = 32
)(
    input  wire                  clk,
    input  wire                  rst_n,

    // APB4 Slave Interface
    input  wire [ADDR_WIDTH-1:0] paddr,
    input  wire [2:0]            pprot,
    input  wire                  psel,
    input  wire                  penable,
    input  wire                  pwrite,
    input  wire [DATA_WIDTH-1:0] pwdata,
    input  wire [3:0]            pstrb,
    output reg                   pready,
    output reg  [DATA_WIDTH-1:0] prdata,
    output reg                   pslverr,

    // External GPIO Pins
    input  wire [GPIO_WIDTH-1:0] gpio_i,
    output reg  [GPIO_WIDTH-1:0] gpio_o,
    output reg  [GPIO_WIDTH-1:0] gpio_dir,
    output wire                  gpio_irq
);

    // Suppress lint for unused ports
    wire _unused = &{1'b0, pprot, pstrb, paddr[ADDR_WIDTH-1:5], paddr[1:0], pwdata[31:16]};

    // 2-FF Input Synchronizer + 1 cycle history for edge detection
    reg [GPIO_WIDTH-1:0] sync_gpio_q1;
    reg [GPIO_WIDTH-1:0] sync_gpio_q2;
    reg [GPIO_WIDTH-1:0] sync_gpio_prev;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sync_gpio_q1   <= {GPIO_WIDTH{1'b0}};
            sync_gpio_q2   <= {GPIO_WIDTH{1'b0}};
            sync_gpio_prev <= {GPIO_WIDTH{1'b0}};
        end else begin
            sync_gpio_q1   <= gpio_i;
            sync_gpio_q2   <= sync_gpio_q1;
            sync_gpio_prev <= sync_gpio_q2;
        end
    end

    // Rising edge detection on synchronized input
    wire [GPIO_WIDTH-1:0] gpio_rising_edges = sync_gpio_q2 & ~sync_gpio_prev;

    // Registers
    // 0x00: DIR        [GPIO_WIDTH-1:0]
    // 0x04: OUT        [GPIO_WIDTH-1:0]
    // 0x08: IN         [GPIO_WIDTH-1:0] (RO)
    // 0x0C: IRQ_EN     [GPIO_WIDTH-1:0]
    // 0x10: IRQ_STATUS [GPIO_WIDTH-1:0] (W1C)
    reg [GPIO_WIDTH-1:0] reg_irq_en;
    reg [GPIO_WIDTH-1:0] reg_irq_status;

    assign gpio_irq = |reg_irq_status;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            gpio_dir       <= {GPIO_WIDTH{1'b0}};
            gpio_o         <= {GPIO_WIDTH{1'b0}};
            reg_irq_en     <= {GPIO_WIDTH{1'b0}};
            reg_irq_status <= {GPIO_WIDTH{1'b0}};
        end else begin
            // Latch rising-edge interrupts
            reg_irq_status <= (reg_irq_status | (gpio_rising_edges & reg_irq_en));

            // APB Register Writes
            if (psel && penable && pwrite) begin
                case (paddr[4:2])
                    3'b000: gpio_dir       <= pwdata[GPIO_WIDTH-1:0];       // 0x00: DIR
                    3'b001: gpio_o         <= pwdata[GPIO_WIDTH-1:0];       // 0x04: OUT
                    3'b010: ;                                               // 0x08: IN is RO
                    3'b011: reg_irq_en     <= pwdata[GPIO_WIDTH-1:0];       // 0x0C: IRQ_EN
                    3'b100: begin                                           // 0x10: IRQ_STATUS (W1C)
                        // Clear written 1s while still allowing new rising edges to be latched
                        reg_irq_status <= (reg_irq_status & ~pwdata[GPIO_WIDTH-1:0]) | (gpio_rising_edges & reg_irq_en);
                    end
                    default: ;
                endcase
            end
        end
    end

    // APB Read Response & Handshake (1-cycle access)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pready  <= 1'b0;
            prdata  <= 32'd0;
            pslverr <= 1'b0;
        end else begin
            if (psel && !penable) begin
                // SETUP phase
                pready  <= 1'b1;
                pslverr <= 1'b0;
                case (paddr[4:2])
                    3'b000:  prdata <= {{(32-GPIO_WIDTH){1'b0}}, gpio_dir};
                    3'b001:  prdata <= {{(32-GPIO_WIDTH){1'b0}}, gpio_o};
                    3'b010:  prdata <= {{(32-GPIO_WIDTH){1'b0}}, sync_gpio_q2};
                    3'b011:  prdata <= {{(32-GPIO_WIDTH){1'b0}}, reg_irq_en};
                    3'b100:  prdata <= {{(32-GPIO_WIDTH){1'b0}}, reg_irq_status};
                    default: prdata <= 32'd0;
                endcase
            end else if (psel && penable) begin
                pready <= 1'b0;
            end else begin
                pready <= 1'b0;
            end
        end
    end

endmodule
