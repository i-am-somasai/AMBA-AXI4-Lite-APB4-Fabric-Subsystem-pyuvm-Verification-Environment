//      // verilator_coverage annotation
        // rtl/apb/apb_uart.v
        // APB4 UART Peripheral (8N1, 16x oversampling, TX/RX sync_fifos, loopback, IRQ)
        `timescale 1ns / 1ps
        
        module apb_uart #(
            parameter FIFO_DEPTH = 8,
            parameter ADDR_WIDTH = 12,
            parameter DATA_WIDTH = 32
        )(
 100022     input  wire                  clk,
~000014     input  wire                  rst_n,
        
            // APB4 Slave Interface
~000863     input  wire [ADDR_WIDTH-1:0] paddr,
 000996     input  wire [2:0]            pprot,
 001035     input  wire                  psel,
 003899     input  wire                  penable,
 001004     input  wire                  pwrite,
 000488     input  wire [DATA_WIDTH-1:0] pwdata,
 000697     input  wire [3:0]            pstrb,
 001035     output reg                   pready,
~000791     output wire [DATA_WIDTH-1:0] prdata,
%000000     output reg                   pslverr,
        
            // External UART Pins
%000006     input  wire                  uart_rx,
 000014     output reg                   uart_tx,
%000000     output wire                  uart_irq
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
 000038     reg [3:0]  reg_ctrl;
 000031     reg [15:0] reg_bauddiv;
%000000     reg        reg_frame_err;
%000000     reg        reg_rx_ovf;
 000021     reg        reg_tx_ovf;
%000008     reg        tx_busy;
        
            // FIFO Interface Signals
 000048     reg        tx_fifo_push;
 000486     reg  [7:0] tx_fifo_wdata;
%000008     wire       tx_fifo_pop;
%000005     wire [7:0] tx_fifo_rdata;
%000005     wire       tx_fifo_full;
 000012     wire       tx_fifo_empty;
        
%000000     reg        rx_fifo_push;
%000000     reg  [7:0] rx_fifo_wdata;
%000000     wire       rx_fifo_pop;
%000000     wire [7:0] rx_fifo_rdata;
%000000     wire       rx_fifo_full;
%000006     wire       rx_fifo_empty;
        
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
~629953     assign uart_irq = reg_ctrl[3] & ~rx_fifo_empty;
        
            // Baud Rate Generator (16x oversampling tick)
~045649     reg [15:0] baud_cnt;
 000026     reg        baud_tick_16x;
        
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             baud_cnt      <= 16'd0;
 000171             baud_tick_16x <= 1'b0;
 099859         end else begin
 091291             if (baud_cnt >= reg_bauddiv) begin
 008568                 baud_cnt      <= 16'd0;
 008568                 baud_tick_16x <= 1'b1;
 091291             end else begin
 091291                 baud_cnt      <= baud_cnt + 1'b1;
 091291                 baud_tick_16x <= 1'b0;
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
        
~000011     reg [2:0] tx_state;
 000247     reg [3:0] tx_tick_cnt;
~000012     reg [2:0] tx_bit_idx;
%000005     reg [7:0] tx_shifter;
        
 543692     assign tx_fifo_pop = (tx_state == TX_ST_IDLE) && reg_ctrl[0] && !tx_fifo_empty;
        
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             tx_state    <= TX_ST_IDLE;
 000171             tx_tick_cnt <= 4'd0;
 000171             tx_bit_idx  <= 3'd0;
 000171             tx_shifter  <= 8'd0;
 000171             tx_busy     <= 1'b0;
 000171             uart_tx     <= 1'b1;
 099859         end else begin
~099859             case (tx_state)
        // [FSM coverage]
%000000        // [fsm_arc amba_fabric_top.u_uart.tx_state::TX_ST_DATA->TX_ST_IDLE]
%000000        // [fsm_arc amba_fabric_top.u_uart.tx_state::TX_ST_LOAD->TX_ST_IDLE]
%000000        // [fsm_arc amba_fabric_top.u_uart.tx_state::TX_ST_START->TX_ST_IDLE]
%000003        // [fsm_arc amba_fabric_top.u_uart.tx_state::TX_ST_STOP->TX_ST_IDLE]
%000003        // [fsm_state amba_fabric_top.u_uart.tx_state::TX_ST_DATA]
%000009        // [fsm_state amba_fabric_top.u_uart.tx_state::TX_ST_IDLE]
%000008        // [fsm_state amba_fabric_top.u_uart.tx_state::TX_ST_LOAD]
%000008        // [fsm_state amba_fabric_top.u_uart.tx_state::TX_ST_START]
%000003        // [fsm_state amba_fabric_top.u_uart.tx_state::TX_ST_STOP]
 013628                 TX_ST_IDLE: begin
 013628                     uart_tx     <= 1'b1;
 013628                     tx_tick_cnt <= 4'd0;
 013628                     tx_bit_idx  <= 3'd0;
        
~013620                     if (reg_ctrl[0] && !tx_fifo_empty) begin // TX_EN
%000008                         tx_busy  <= 1'b1;
%000008                         tx_state <= TX_ST_LOAD;
 013620                     end else begin
 013620                         tx_busy  <= 1'b0;
                            end
                        end
        
%000008                 TX_ST_LOAD: begin
                            // Latch data popped from FIFO during IDLE
%000008                     tx_shifter  <= tx_fifo_rdata;
%000008                     uart_tx     <= 1'b0; // Assert start bit
%000008                     tx_tick_cnt <= 4'd0;
%000008                     tx_state    <= TX_ST_START;
                        end
        
 085791                 TX_ST_START: begin
 085791                     uart_tx <= 1'b0; // Start bit
 085731                     if (baud_tick_16x) begin
~000057                         if (tx_tick_cnt == 4'd15) begin
%000003                             tx_tick_cnt <= 4'd0;
%000003                             tx_state    <= TX_ST_DATA;
 000057                         end else begin
 000057                             tx_tick_cnt <= tx_tick_cnt + 1'b1;
                                end
                            end
                        end
        
 000384                 TX_ST_DATA: begin
 000384                     uart_tx <= tx_shifter[tx_bit_idx];
~000384                     if (baud_tick_16x) begin
 000360                         if (tx_tick_cnt == 4'd15) begin
 000024                             tx_tick_cnt <= 4'd0;
~000021                             if (tx_bit_idx == 3'd7) begin
%000003                                 tx_state <= TX_ST_STOP;
 000021                             end else begin
 000021                                 tx_bit_idx <= tx_bit_idx + 1'b1;
                                    end
 000360                         end else begin
 000360                             tx_tick_cnt <= tx_tick_cnt + 1'b1;
                                end
                            end
                        end
        
 000048                 TX_ST_STOP: begin
 000048                     uart_tx <= 1'b1; // Stop bit
~000048                     if (baud_tick_16x) begin
~000045                         if (tx_tick_cnt == 4'd15) begin
%000003                             tx_tick_cnt <= 4'd0;
%000003                             tx_state    <= TX_ST_IDLE;
 000045                         end else begin
 000045                             tx_tick_cnt <= tx_tick_cnt + 1'b1;
                                end
                            end
                        end
        
%000000                 default: tx_state <= TX_ST_IDLE;
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
        
%000005     reg [1:0] rx_state;
%000007     reg [3:0] rx_tick_cnt;
%000000     reg [2:0] rx_bit_idx;
%000000     reg [7:0] rx_shifter;
        
            // Loopback selector: reg_ctrl[2] connects uart_tx to rx
 319957     wire rx_raw = reg_ctrl[2] ? uart_tx : uart_rx;
        
            // 2-FF input synchronizer
 000036     reg rx_sync_q1, rx_sync_q2;
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             rx_sync_q1 <= 1'b1;
 000171             rx_sync_q2 <= 1'b1;
 099859         end else begin
 099859             rx_sync_q1 <= rx_raw;
 099859             rx_sync_q2 <= rx_sync_q1;
                end
            end
        
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             rx_state      <= RX_ST_IDLE;
 000171             rx_tick_cnt   <= 4'd0;
 000171             rx_bit_idx    <= 3'd0;
 000171             rx_shifter    <= 8'd0;
 000171             rx_fifo_push  <= 1'b0;
 000171             rx_fifo_wdata <= 8'd0;
 000171             reg_frame_err <= 1'b0;
 000171             reg_rx_ovf    <= 1'b0;
 000171             reg_tx_ovf    <= 1'b0;
 099859         end else begin
 099859             rx_fifo_push <= 1'b0;
        
                    // Clear status bits on W1C APB writes
 099754             if (psel && penable && pwrite && (paddr[4:2] == 3'b010)) begin // 0x08: STATUS
 000054                 if (pwdata[4]) reg_frame_err <= 1'b0;
 000055                 if (pwdata[5]) reg_rx_ovf    <= 1'b0;
 000056                 if (pwdata[6]) reg_tx_ovf    <= 1'b0;
                    end
        
 099859             case (rx_state)
 019344                 RX_ST_IDLE: begin
 019344                     rx_tick_cnt <= 4'd0;
 019344                     rx_bit_idx  <= 3'd0;
~019339                     if (reg_ctrl[1] && !rx_sync_q2) begin // RX_EN and falling edge (start bit detected)
%000005                         rx_state <= RX_ST_START;
                            end
                        end
        
 080515                 RX_ST_START: begin
 080504                     if (baud_tick_16x) begin
%000000                         if (rx_tick_cnt == 4'd7) begin
                                    // Mid-start bit sample: verify line is still 0
%000000                             if (rx_sync_q2 != 1'b0) begin
%000000                                 rx_state <= RX_ST_IDLE; // False glitch
%000000                             end else begin
%000000                                 rx_tick_cnt <= rx_tick_cnt + 1'b1;
                                    end
~000011                         end else if (rx_tick_cnt == 4'd15) begin
%000000                             rx_tick_cnt <= 4'd0;
%000000                             rx_bit_idx  <= 3'd0;
%000000                             rx_state    <= RX_ST_DATA;
 000011                         end else begin
 000011                             rx_tick_cnt <= rx_tick_cnt + 1'b1;
                                end
                            end
                        end
        
%000000                 RX_ST_DATA: begin
%000000                     if (baud_tick_16x) begin
%000000                         if (rx_tick_cnt == 4'd7) begin
                                    // Mid-bit sample
%000000                             rx_shifter[rx_bit_idx] <= rx_sync_q2;
%000000                             rx_tick_cnt <= rx_tick_cnt + 1'b1;
%000000                         end else if (rx_tick_cnt == 4'd15) begin
%000000                             rx_tick_cnt <= 4'd0;
%000000                             if (rx_bit_idx == 3'd7) begin
%000000                                 rx_state <= RX_ST_STOP;
%000000                             end else begin
%000000                                 rx_bit_idx <= rx_bit_idx + 1'b1;
                                    end
%000000                         end else begin
%000000                             rx_tick_cnt <= rx_tick_cnt + 1'b1;
                                end
                            end
                        end
        
%000000                 RX_ST_STOP: begin
%000000                     if (baud_tick_16x) begin
%000000                         if (rx_tick_cnt == 4'd7) begin
                                    // Mid-stop bit sample: verify stop bit is 1
%000000                             if (rx_sync_q2 == 1'b1) begin
                                        // Valid 8N1 frame
%000000                                 if (!rx_fifo_full) begin
%000000                                     rx_fifo_push  <= 1'b1;
%000000                                     rx_fifo_wdata <= rx_shifter;
%000000                                 end else begin
%000000                                     reg_rx_ovf <= 1'b1; // RX FIFO overflow
                                        end
%000000                             end else begin
%000000                                 reg_frame_err <= 1'b1; // Stop bit frame error
                                    end
%000000                             rx_tick_cnt <= rx_tick_cnt + 1'b1;
%000000                         end else if (rx_tick_cnt == 4'd15) begin
%000000                             rx_tick_cnt <= 4'd0;
%000000                             rx_state    <= RX_ST_IDLE;
%000000                         end else begin
%000000                             rx_tick_cnt <= rx_tick_cnt + 1'b1;
                                end
                            end
                        end
                    endcase
        
                    // Detect TX_OVF on APB writes to TXDATA when TX FIFO is full
 099752             if (psel && penable && pwrite && (paddr[4:2] == 3'b000)) begin
 000059                 if (tx_fifo_full) begin
 000059                     reg_tx_ovf <= 1'b1;
                        end
                    end
                end
            end
        
            // -------------------------------------------------------------
            // APB Register Interface
            // -------------------------------------------------------------
            // Pop RX FIFO on APB read of RXDATA (0x04)
~629953     assign rx_fifo_pop = psel && !penable && !pwrite && (paddr[4:2] == 3'b001) && !rx_fifo_empty;
        
%000000     reg rx_had_data;
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             rx_had_data <= 1'b0;
 097789         end else if (psel && !penable && !pwrite && (paddr[4:2] == 3'b001)) begin
~000114             rx_had_data <= !rx_fifo_empty;
 095846         end else if (penable) begin
 003899             rx_had_data <= 1'b0;
                end
            end
        
            // Push TX FIFO on APB write to TXDATA (0x00)
 629953     always @(*) begin
 629953         tx_fifo_push  = 1'b0;
 629953         tx_fifo_wdata = pwdata[7:0];
 629675         if (psel && penable && pwrite && (paddr[4:2] == 3'b000) && !tx_fifo_full) begin
 000278             tx_fifo_push = 1'b1;
                end
            end
        
            // Write handling for CTRL and BAUDDIV
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             reg_ctrl    <= 4'd0;
 000171             reg_bauddiv <= 16'd0;
 099859         end else begin
 099334             if (psel && penable && pwrite) begin
 000525                 case (paddr[4:2])
 000109                     3'b011: reg_ctrl    <= pwdata[3:0];  // 0x0C: CTRL
 000108                     3'b100: reg_bauddiv <= pwdata[15:0]; // 0x10: BAUDDIV
 000308                     default: ;
                        endcase
                    end
                end
            end
        
            // APB Handshake (1-cycle access)
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             pready  <= 1'b0;
 000171             pslverr <= 1'b0;
 099859         end else begin
 098824             if (psel && !penable) begin
 001035                 pready  <= 1'b1;
 001035                 pslverr <= 1'b0;
 098824             end else begin
 098824                 pready  <= 1'b0;
                    end
                end
            end
        
            // STATUS word construction
~000021     wire [7:0] status_word = {
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
 379051     assign prdata = (paddr[4:2] == 3'b000) ? 32'd0 :
 281749                     (paddr[4:2] == 3'b001) ? {24'd0, (rx_had_data ? rx_fifo_rdata : 8'd0)} :
 178303                     (paddr[4:2] == 3'b010) ? {24'd0, status_word} :
 111428                     (paddr[4:2] == 3'b011) ? {28'd0, reg_ctrl} :
~066875                     (paddr[4:2] == 3'b100) ? {16'd0, reg_bauddiv} :
%000000                     32'd0;
        
        endmodule
        
