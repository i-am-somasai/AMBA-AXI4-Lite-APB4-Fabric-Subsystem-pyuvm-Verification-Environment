// rtl/apb/apb_uart.v
// APB4 UART Peripheral (8N1, 16x oversampling, TX/RX sync_fifos, loopback, IRQ)
`timescale 1ns / 1ps

module apb_uart #(
    parameter FIFO_DEPTH = 8,
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
    output wire [DATA_WIDTH-1:0] prdata,
    output reg                   pslverr,

    // External UART Pins
    input  wire                  uart_rx,
    output reg                   uart_tx,
    output wire                  uart_irq
);

    // Suppress lint for unused ports
    wire _unused = &{1'b0, pprot, pstrb, paddr[ADDR_WIDTH-1:5], paddr[1:0], pwdata[31:16]};

    // Dummy wires for unused FIFO outputs
    /* verilator lint_off UNUSEDSIGNAL */
    wire [$clog2(FIFO_DEPTH):0] _unused_tx_count;
    wire                        _unused_tx_fifo_ovf;
    wire                        _unused_tx_fifo_unf;
    wire [$clog2(FIFO_DEPTH):0] _unused_rx_count;
    wire                        _unused_rx_fifo_ovf;
    wire                        _unused_rx_fifo_unf;
    /* verilator lint_on UNUSEDSIGNAL */

    // Registers
    // 0x00: TXDATA   [7:0] WO
    // 0x04: RXDATA   [7:0] RO
    // 0x08: STATUS   [7:0] RO/W1C
    // 0x0C: CTRL     [3:0] RW ([0] TX_EN, [1] RX_EN, [2] LOOPBACK, [3] RX_IRQ_EN)
    // 0x10: BAUDDIV  [15:0] RW
    reg [3:0]  reg_ctrl;
    reg [15:0] reg_bauddiv;
    reg        reg_frame_err;
    reg        reg_rx_ovf;
    reg        reg_tx_ovf;
    reg        tx_busy;

    // FIFO Interface Signals
    reg        tx_fifo_push;
    reg  [7:0] tx_fifo_wdata;
    wire       tx_fifo_pop;
    wire [7:0] tx_fifo_rdata;
    wire       tx_fifo_full;
    wire       tx_fifo_empty;

    reg        rx_fifo_push;
    reg  [7:0] rx_fifo_wdata;
    wire       rx_fifo_pop;
    wire [7:0] rx_fifo_rdata;
    wire       rx_fifo_full;
    wire       rx_fifo_empty;

    // Instantiate TX FIFO
    sync_fifo #(
        .WIDTH(8),
        .DEPTH(FIFO_DEPTH)
    ) u_tx_fifo (
        .clk      (clk),
        .rst_n    (rst_n),
        .push     (tx_fifo_push),
        .wdata    (tx_fifo_wdata),
        .pop      (tx_fifo_pop),
        .rdata    (tx_fifo_rdata),
        .full     (tx_fifo_full),
        .empty    (tx_fifo_empty),
        .count    (_unused_tx_count),
        .overflow (_unused_tx_fifo_ovf),
        .underflow(_unused_tx_fifo_unf)
    );

    // Instantiate RX FIFO
    sync_fifo #(
        .WIDTH(8),
        .DEPTH(FIFO_DEPTH)
    ) u_rx_fifo (
        .clk      (clk),
        .rst_n    (rst_n),
        .push     (rx_fifo_push),
        .wdata    (rx_fifo_wdata),
        .pop      (rx_fifo_pop),
        .rdata    (rx_fifo_rdata),
        .full     (rx_fifo_full),
        .empty    (rx_fifo_empty),
        .count    (_unused_rx_count),
        .overflow (_unused_rx_fifo_ovf),
        .underflow(_unused_rx_fifo_unf)
    );

    // Interrupt Generation
    assign uart_irq = reg_ctrl[3] & ~rx_fifo_empty;

    // Baud Rate Generator (16x oversampling tick)
    reg [15:0] baud_cnt;
    reg        baud_tick_16x;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            baud_cnt      <= 16'd0;
            baud_tick_16x <= 1'b0;
        end else begin
            if (baud_cnt >= reg_bauddiv) begin
                baud_cnt      <= 16'd0;
                baud_tick_16x <= 1'b1;
            end else begin
                baud_cnt      <= baud_cnt + 1'b1;
                baud_tick_16x <= 1'b0;
            end
        end
    end

    // -------------------------------------------------------------
    // UART Transmitter FSM
    // -------------------------------------------------------------
    localparam [2:0] TX_ST_IDLE  = 3'b000,
                     TX_ST_LOAD  = 3'b001,
                     TX_ST_START = 3'b010,
                     TX_ST_DATA  = 3'b011,
                     TX_ST_STOP  = 3'b100;

    reg [2:0] tx_state;
    reg [3:0] tx_tick_cnt;
    reg [2:0] tx_bit_idx;
    reg [7:0] tx_shifter;

    assign tx_fifo_pop = (tx_state == TX_ST_IDLE) && reg_ctrl[0] && !tx_fifo_empty;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_state    <= TX_ST_IDLE;
            tx_tick_cnt <= 4'd0;
            tx_bit_idx  <= 3'd0;
            tx_shifter  <= 8'd0;
            tx_busy     <= 1'b0;
            uart_tx     <= 1'b1;
        end else begin
            case (tx_state)
                TX_ST_IDLE: begin
                    uart_tx     <= 1'b1;
                    tx_tick_cnt <= 4'd0;
                    tx_bit_idx  <= 3'd0;

                    if (reg_ctrl[0] && !tx_fifo_empty) begin // TX_EN
                        tx_busy  <= 1'b1;
                        tx_state <= TX_ST_LOAD;
                    end else begin
                        tx_busy  <= 1'b0;
                    end
                end

                TX_ST_LOAD: begin
                    // Latch data popped from FIFO during IDLE
                    tx_shifter  <= tx_fifo_rdata;
                    uart_tx     <= 1'b0; // Assert start bit
                    tx_tick_cnt <= 4'd0;
                    tx_state    <= TX_ST_START;
                end

                TX_ST_START: begin
                    uart_tx <= 1'b0; // Start bit
                    if (baud_tick_16x) begin
                        if (tx_tick_cnt == 4'd15) begin
                            tx_tick_cnt <= 4'd0;
                            tx_state    <= TX_ST_DATA;
                        end else begin
                            tx_tick_cnt <= tx_tick_cnt + 1'b1;
                        end
                    end
                end

                TX_ST_DATA: begin
                    uart_tx <= tx_shifter[tx_bit_idx];
                    if (baud_tick_16x) begin
                        if (tx_tick_cnt == 4'd15) begin
                            tx_tick_cnt <= 4'd0;
                            if (tx_bit_idx == 3'd7) begin
                                tx_state <= TX_ST_STOP;
                            end else begin
                                tx_bit_idx <= tx_bit_idx + 1'b1;
                            end
                        end else begin
                            tx_tick_cnt <= tx_tick_cnt + 1'b1;
                        end
                    end
                end

                TX_ST_STOP: begin
                    uart_tx <= 1'b1; // Stop bit
                    if (baud_tick_16x) begin
                        if (tx_tick_cnt == 4'd15) begin
                            tx_tick_cnt <= 4'd0;
                            tx_state    <= TX_ST_IDLE;
                        end else begin
                            tx_tick_cnt <= tx_tick_cnt + 1'b1;
                        end
                    end
                end

                default: tx_state <= TX_ST_IDLE;
            endcase
        end
    end

    // -------------------------------------------------------------
    // UART Receiver FSM (16x oversampled, mid-bit sample at tick 7)
    // -------------------------------------------------------------
    localparam [1:0] RX_ST_IDLE  = 2'b00,
                     RX_ST_START = 2'b01,
                     RX_ST_DATA  = 2'b10,
                     RX_ST_STOP  = 2'b11;

    reg [1:0] rx_state;
    reg [3:0] rx_tick_cnt;
    reg [2:0] rx_bit_idx;
    reg [7:0] rx_shifter;

    // Loopback selector: reg_ctrl[2] connects uart_tx to rx
    wire rx_raw = reg_ctrl[2] ? uart_tx : uart_rx;

    // 2-FF input synchronizer
    reg rx_sync_q1, rx_sync_q2;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_sync_q1 <= 1'b1;
            rx_sync_q2 <= 1'b1;
        end else begin
            rx_sync_q1 <= rx_raw;
            rx_sync_q2 <= rx_sync_q1;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_state      <= RX_ST_IDLE;
            rx_tick_cnt   <= 4'd0;
            rx_bit_idx    <= 3'd0;
            rx_shifter    <= 8'd0;
            rx_fifo_push  <= 1'b0;
            rx_fifo_wdata <= 8'd0;
            reg_frame_err <= 1'b0;
            reg_rx_ovf    <= 1'b0;
            reg_tx_ovf    <= 1'b0;
        end else begin
            rx_fifo_push <= 1'b0;

            // Clear status bits on W1C APB writes
            if (psel && penable && pwrite && (paddr[4:2] == 3'b010)) begin // 0x08: STATUS
                if (pwdata[4]) reg_frame_err <= 1'b0;
                if (pwdata[5]) reg_rx_ovf    <= 1'b0;
                if (pwdata[6]) reg_tx_ovf    <= 1'b0;
            end

            case (rx_state)
                RX_ST_IDLE: begin
                    rx_tick_cnt <= 4'd0;
                    rx_bit_idx  <= 3'd0;
                    if (reg_ctrl[1] && !rx_sync_q2) begin // RX_EN and falling edge (start bit detected)
                        rx_state <= RX_ST_START;
                    end
                end

                RX_ST_START: begin
                    if (baud_tick_16x) begin
                        if (rx_tick_cnt == 4'd7) begin
                            // Mid-start bit sample: verify line is still 0
                            if (rx_sync_q2 != 1'b0) begin
                                rx_state <= RX_ST_IDLE; // False glitch
                            end else begin
                                rx_tick_cnt <= rx_tick_cnt + 1'b1;
                            end
                        end else if (rx_tick_cnt == 4'd15) begin
                            rx_tick_cnt <= 4'd0;
                            rx_bit_idx  <= 3'd0;
                            rx_state    <= RX_ST_DATA;
                        end else begin
                            rx_tick_cnt <= rx_tick_cnt + 1'b1;
                        end
                    end
                end

                RX_ST_DATA: begin
                    if (baud_tick_16x) begin
                        if (rx_tick_cnt == 4'd7) begin
                            // Mid-bit sample
                            rx_shifter[rx_bit_idx] <= rx_sync_q2;
                            rx_tick_cnt <= rx_tick_cnt + 1'b1;
                        end else if (rx_tick_cnt == 4'd15) begin
                            rx_tick_cnt <= 4'd0;
                            if (rx_bit_idx == 3'd7) begin
                                rx_state <= RX_ST_STOP;
                            end else begin
                                rx_bit_idx <= rx_bit_idx + 1'b1;
                            end
                        end else begin
                            rx_tick_cnt <= rx_tick_cnt + 1'b1;
                        end
                    end
                end

                RX_ST_STOP: begin
                    if (baud_tick_16x) begin
                        if (rx_tick_cnt == 4'd7) begin
                            // Mid-stop bit sample: verify stop bit is 1
                            if (rx_sync_q2 == 1'b1) begin
                                // Valid 8N1 frame
                                if (!rx_fifo_full) begin
                                    rx_fifo_push  <= 1'b1;
                                    rx_fifo_wdata <= rx_shifter;
                                end else begin
                                    reg_rx_ovf <= 1'b1; // RX FIFO overflow
                                end
                            end else begin
                                reg_frame_err <= 1'b1; // Stop bit frame error
                            end
                            rx_tick_cnt <= rx_tick_cnt + 1'b1;
                        end else if (rx_tick_cnt == 4'd15) begin
                            rx_tick_cnt <= 4'd0;
                            rx_state    <= RX_ST_IDLE;
                        end else begin
                            rx_tick_cnt <= rx_tick_cnt + 1'b1;
                        end
                    end
                end
            endcase

            // Detect TX_OVF on APB writes to TXDATA when TX FIFO is full
            if (psel && penable && pwrite && (paddr[4:2] == 3'b000)) begin
                if (tx_fifo_full) begin
                    reg_tx_ovf <= 1'b1;
                end
            end
        end
    end

    // -------------------------------------------------------------
    // APB Register Interface
    // -------------------------------------------------------------
    // Pop RX FIFO on APB read of RXDATA (0x04)
    assign rx_fifo_pop = psel && !penable && !pwrite && (paddr[4:2] == 3'b001) && !rx_fifo_empty;

    reg rx_had_data;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_had_data <= 1'b0;
        end else if (psel && !penable && !pwrite && (paddr[4:2] == 3'b001)) begin
            rx_had_data <= !rx_fifo_empty;
        end else if (penable) begin
            rx_had_data <= 1'b0;
        end
    end

    // Push TX FIFO on APB write to TXDATA (0x00)
    always @(*) begin
        tx_fifo_push  = 1'b0;
        tx_fifo_wdata = pwdata[7:0];
        if (psel && penable && pwrite && (paddr[4:2] == 3'b000) && !tx_fifo_full) begin
            tx_fifo_push = 1'b1;
        end
    end

    // Write handling for CTRL and BAUDDIV
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            reg_ctrl    <= 4'd0;
            reg_bauddiv <= 16'd0;
        end else begin
            if (psel && penable && pwrite) begin
                case (paddr[4:2])
                    3'b011: reg_ctrl    <= pwdata[3:0];  // 0x0C: CTRL
                    3'b100: reg_bauddiv <= pwdata[15:0]; // 0x10: BAUDDIV
                    default: ;
                endcase
            end
        end
    end

    // APB Handshake (1-cycle access)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pready  <= 1'b0;
            pslverr <= 1'b0;
        end else begin
            if (psel && !penable) begin
                pready  <= 1'b1;
                pslverr <= 1'b0;
            end else begin
                pready  <= 1'b0;
            end
        end
    end

    // STATUS word construction
    wire [7:0] status_word = {
        tx_busy,
        reg_tx_ovf,
        reg_rx_ovf,
        reg_frame_err,
        rx_fifo_empty,
        rx_fifo_full,
        tx_fifo_empty,
        tx_fifo_full
    };

    // APB Read Data Mux
    assign prdata = (paddr[4:2] == 3'b000) ? 32'd0 :
                    (paddr[4:2] == 3'b001) ? {24'd0, (rx_had_data ? rx_fifo_rdata : 8'd0)} :
                    (paddr[4:2] == 3'b010) ? {24'd0, status_word} :
                    (paddr[4:2] == 3'b011) ? {28'd0, reg_ctrl} :
                    (paddr[4:2] == 3'b100) ? {16'd0, reg_bauddiv} :
                    32'd0;

endmodule
