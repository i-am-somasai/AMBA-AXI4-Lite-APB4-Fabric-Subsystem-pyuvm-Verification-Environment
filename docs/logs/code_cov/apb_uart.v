//      // verilator_coverage annotation
        // rtl/apb/apb_uart.v
        // APB4 UART Peripheral (8N1, 16x oversampling, TX/RX sync_fifos, loopback, IRQ)
        `timescale 1ns / 1ps
        
        module apb_uart #(
            parameter FIFO_DEPTH = 8,
            parameter ADDR_WIDTH = 12,
            parameter DATA_WIDTH = 32
        )(
 935460     input  wire                  clk,
~000021     input  wire                  rst_n,
        
            // APB4 Slave Interface
~006582     input  wire [ADDR_WIDTH-1:0] paddr,
 007481     input  wire [2:0]            pprot,
 007557     input  wire                  psel,
 030066     input  wire                  penable,
 007527     input  wire                  pwrite,
 003816     input  wire [DATA_WIDTH-1:0] pwdata,
 005273     input  wire [3:0]            pstrb,
 007557     output reg                   pready,
~006147     output wire [DATA_WIDTH-1:0] prdata,
%000000     output reg                   pslverr,
        
            // External UART Pins
~000026     input  wire                  uart_rx,
 000144     output reg                   uart_tx,
%000002     output wire                  uart_irq
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
 000212     reg [3:0]  reg_ctrl;
 000200     reg [15:0] reg_bauddiv;
%000001     reg        reg_frame_err;
%000000     reg        reg_rx_ovf;
 000197     reg        reg_tx_ovf;
 000032     reg        tx_busy;
        
            // FIFO Interface Signals
 000221     reg        tx_fifo_push;
 003813     reg  [7:0] tx_fifo_wdata;
 000061     wire       tx_fifo_pop;
~000026     wire [7:0] tx_fifo_rdata;
~000024     wire       tx_fifo_full;
 000048     wire       tx_fifo_empty;
        
 000027     reg        rx_fifo_push;
~000014     reg  [7:0] rx_fifo_wdata;
 000027     wire       rx_fifo_pop;
~000014     wire [7:0] rx_fifo_rdata;
%000003     wire       rx_fifo_full;
~000026     wire       rx_fifo_empty;
        
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
 5986824     assign uart_irq = reg_ctrl[3] & ~rx_fifo_empty;
        
            // Baud Rate Generator (16x oversampling tick)
~453844     reg [15:0] baud_cnt;
 002857     reg        baud_tick_16x;
        
 935460     always @(posedge clk or negedge rst_n) begin
 935207         if (!rst_n) begin
 000253             baud_cnt      <= 16'd0;
 000253             baud_tick_16x <= 1'b0;
 935207         end else begin
 906237             if (baud_cnt >= reg_bauddiv) begin
 028970                 baud_cnt      <= 16'd0;
 028970                 baud_tick_16x <= 1'b1;
 906237             end else begin
 906237                 baud_cnt      <= baud_cnt + 1'b1;
 906237                 baud_tick_16x <= 1'b0;
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
        
 000102     reg [2:0] tx_state;
 003336     reg [3:0] tx_tick_cnt;
 000164     reg [2:0] tx_bit_idx;
~000026     reg [7:0] tx_shifter;
        
 5680430     assign tx_fifo_pop = (tx_state == TX_ST_IDLE) && reg_ctrl[0] && !tx_fifo_empty;
        
 935460     always @(posedge clk or negedge rst_n) begin
 935207         if (!rst_n) begin
 000253             tx_state    <= TX_ST_IDLE;
 000253             tx_tick_cnt <= 4'd0;
 000253             tx_bit_idx  <= 3'd0;
 000253             tx_shifter  <= 8'd0;
 000253             tx_busy     <= 1'b0;
 000253             uart_tx     <= 1'b1;
 935207         end else begin
~935207             case (tx_state)
        // [FSM coverage]
%000000        // [fsm_arc amba_fabric_top.u_uart.tx_state::TX_ST_DATA->TX_ST_IDLE]
%000000        // [fsm_arc amba_fabric_top.u_uart.tx_state::TX_ST_LOAD->TX_ST_IDLE]
%000000        // [fsm_arc amba_fabric_top.u_uart.tx_state::TX_ST_START->TX_ST_IDLE]
 000041        // [fsm_arc amba_fabric_top.u_uart.tx_state::TX_ST_STOP->TX_ST_IDLE]
 000041        // [fsm_state amba_fabric_top.u_uart.tx_state::TX_ST_DATA]
 000062        // [fsm_state amba_fabric_top.u_uart.tx_state::TX_ST_IDLE]
 000061        // [fsm_state amba_fabric_top.u_uart.tx_state::TX_ST_LOAD]
 000061        // [fsm_state amba_fabric_top.u_uart.tx_state::TX_ST_START]
 000041        // [fsm_state amba_fabric_top.u_uart.tx_state::TX_ST_STOP]
 068942                 TX_ST_IDLE: begin
 068942                     uart_tx     <= 1'b1;
 068942                     tx_tick_cnt <= 4'd0;
 068942                     tx_bit_idx  <= 3'd0;
        
 068881                     if (reg_ctrl[0] && !tx_fifo_empty) begin // TX_EN
 000061                         tx_busy  <= 1'b1;
 000061                         tx_state <= TX_ST_LOAD;
 068881                     end else begin
 068881                         tx_busy  <= 1'b0;
                            end
                        end
        
 000061                 TX_ST_LOAD: begin
                            // Latch data popped from FIFO during IDLE
 000061                     tx_shifter  <= tx_fifo_rdata;
 000061                     uart_tx     <= 1'b0; // Assert start bit
 000061                     tx_tick_cnt <= 4'd0;
 000061                     tx_state    <= TX_ST_START;
                        end
        
 854540                 TX_ST_START: begin
 854540                     uart_tx <= 1'b0; // Start bit
 853783                     if (baud_tick_16x) begin
 000716                         if (tx_tick_cnt == 4'd15) begin
 000041                             tx_tick_cnt <= 4'd0;
 000041                             tx_state    <= TX_ST_DATA;
 000716                         end else begin
 000716                             tx_tick_cnt <= tx_tick_cnt + 1'b1;
                                end
                            end
                        end
        
 010368                 TX_ST_DATA: begin
 010368                     uart_tx <= tx_shifter[tx_bit_idx];
 005248                     if (baud_tick_16x) begin
 004920                         if (tx_tick_cnt == 4'd15) begin
 000328                             tx_tick_cnt <= 4'd0;
 000287                             if (tx_bit_idx == 3'd7) begin
 000041                                 tx_state <= TX_ST_STOP;
 000287                             end else begin
 000287                                 tx_bit_idx <= tx_bit_idx + 1'b1;
                                    end
 004920                         end else begin
 004920                             tx_tick_cnt <= tx_tick_cnt + 1'b1;
                                end
                            end
                        end
        
 001296                 TX_ST_STOP: begin
 001296                     uart_tx <= 1'b1; // Stop bit
 000656                     if (baud_tick_16x) begin
 000615                         if (tx_tick_cnt == 4'd15) begin
 000041                             tx_tick_cnt <= 4'd0;
 000041                             tx_state    <= TX_ST_IDLE;
 000615                         end else begin
 000615                             tx_tick_cnt <= tx_tick_cnt + 1'b1;
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
        
 000078     reg [1:0] rx_state;
 002333     reg [3:0] rx_tick_cnt;
 000114     reg [2:0] rx_bit_idx;
~000015     reg [7:0] rx_shifter;
        
            // Loopback selector: reg_ctrl[2] connects uart_tx to rx
 3160855     wire rx_raw = reg_ctrl[2] ? uart_tx : uart_rx;
        
            // 2-FF input synchronizer
 000313     reg rx_sync_q1, rx_sync_q2;
 935460     always @(posedge clk or negedge rst_n) begin
 935207         if (!rst_n) begin
 000253             rx_sync_q1 <= 1'b1;
 000253             rx_sync_q2 <= 1'b1;
 935207         end else begin
 935207             rx_sync_q1 <= rx_raw;
 935207             rx_sync_q2 <= rx_sync_q1;
                end
            end
        
 935460     always @(posedge clk or negedge rst_n) begin
 935207         if (!rst_n) begin
 000253             rx_state      <= RX_ST_IDLE;
 000253             rx_tick_cnt   <= 4'd0;
 000253             rx_bit_idx    <= 3'd0;
 000253             rx_shifter    <= 8'd0;
 000253             rx_fifo_push  <= 1'b0;
 000253             rx_fifo_wdata <= 8'd0;
 000253             reg_frame_err <= 1'b0;
 000253             reg_rx_ovf    <= 1'b0;
 000253             reg_tx_ovf    <= 1'b0;
 935207         end else begin
 935207             rx_fifo_push <= 1'b0;
        
                    // Clear status bits on W1C APB writes
 934484             if (psel && penable && pwrite && (paddr[4:2] == 3'b010)) begin // 0x08: STATUS
 000377                 if (pwdata[4]) reg_frame_err <= 1'b0;
 000372                 if (pwdata[5]) reg_rx_ovf    <= 1'b0;
 000379                 if (pwdata[6]) reg_tx_ovf    <= 1'b0;
                    end
        
 935207             case (rx_state)
 107526                 RX_ST_IDLE: begin
 107526                     rx_tick_cnt <= 4'd0;
 107526                     rx_bit_idx  <= 3'd0;
 107476                     if (reg_ctrl[1] && !rx_sync_q2) begin // RX_EN and falling edge (start bit detected)
 000050                         rx_state <= RX_ST_START;
                            end
                        end
        
 817826                 RX_ST_START: begin
 817265                     if (baud_tick_16x) begin
 000032                         if (rx_tick_cnt == 4'd7) begin
                                    // Mid-start bit sample: verify line is still 0
~000030                             if (rx_sync_q2 != 1'b0) begin
%000002                                 rx_state <= RX_ST_IDLE; // False glitch
 000030                             end else begin
 000030                                 rx_tick_cnt <= rx_tick_cnt + 1'b1;
                                    end
 000500                         end else if (rx_tick_cnt == 4'd15) begin
 000029                             rx_tick_cnt <= 4'd0;
 000029                             rx_bit_idx  <= 3'd0;
 000029                             rx_state    <= RX_ST_DATA;
 000500                         end else begin
 000500                             rx_tick_cnt <= rx_tick_cnt + 1'b1;
                                end
                            end
                        end
        
 008767                 RX_ST_DATA: begin
 005120                     if (baud_tick_16x) begin
 000228                         if (rx_tick_cnt == 4'd7) begin
                                    // Mid-bit sample
 000228                             rx_shifter[rx_bit_idx] <= rx_sync_q2;
 000228                             rx_tick_cnt <= rx_tick_cnt + 1'b1;
 003192                         end else if (rx_tick_cnt == 4'd15) begin
 000227                             rx_tick_cnt <= 4'd0;
 000199                             if (rx_bit_idx == 3'd7) begin
 000028                                 rx_state <= RX_ST_STOP;
 000199                             end else begin
 000199                                 rx_bit_idx <= rx_bit_idx + 1'b1;
                                    end
 003192                         end else begin
 003192                             rx_tick_cnt <= rx_tick_cnt + 1'b1;
                                end
                            end
                        end
        
 001088                 RX_ST_STOP: begin
 000640                     if (baud_tick_16x) begin
 000028                         if (rx_tick_cnt == 4'd7) begin
                                    // Mid-stop bit sample: verify stop bit is 1
~000027                             if (rx_sync_q2 == 1'b1) begin
                                        // Valid 8N1 frame
~000027                                 if (!rx_fifo_full) begin
 000027                                     rx_fifo_push  <= 1'b1;
 000027                                     rx_fifo_wdata <= rx_shifter;
%000000                                 end else begin
%000000                                     reg_rx_ovf <= 1'b1; // RX FIFO overflow
                                        end
%000001                             end else begin
%000001                                 reg_frame_err <= 1'b1; // Stop bit frame error
                                    end
 000028                             rx_tick_cnt <= rx_tick_cnt + 1'b1;
 000392                         end else if (rx_tick_cnt == 4'd15) begin
 000028                             rx_tick_cnt <= 4'd0;
 000028                             rx_state    <= RX_ST_IDLE;
 000392                         end else begin
 000392                             rx_tick_cnt <= rx_tick_cnt + 1'b1;
                                end
                            end
                        end
                    endcase
        
                    // Detect TX_OVF on APB writes to TXDATA when TX FIFO is full
 934422             if (psel && penable && pwrite && (paddr[4:2] == 3'b000)) begin
 000564                 if (tx_fifo_full) begin
 000564                     reg_tx_ovf <= 1'b1;
                        end
                    end
                end
            end
        
            // -------------------------------------------------------------
            // APB Register Interface
            // -------------------------------------------------------------
            // Pop RX FIFO on APB read of RXDATA (0x04)
 6040082     assign rx_fifo_pop = psel && !penable && !pwrite && (paddr[4:2] == 3'b001) && !rx_fifo_empty;
        
 000027     reg rx_had_data;
 935460     always @(posedge clk or negedge rst_n) begin
 935207         if (!rst_n) begin
 000253             rx_had_data <= 1'b0;
 920093         end else if (psel && !penable && !pwrite && (paddr[4:2] == 3'b001)) begin
 000782             rx_had_data <= !rx_fifo_empty;
 904359         end else if (penable) begin
 030066             rx_had_data <= 1'b0;
                end
            end
        
            // Push TX FIFO on APB write to TXDATA (0x00)
 6139802     always @(*) begin
 6139802         tx_fifo_push  = 1'b0;
 6139802         tx_fifo_wdata = pwdata[7:0];
 6138297         if (psel && penable && pwrite && (paddr[4:2] == 3'b000) && !tx_fifo_full) begin
 001505             tx_fifo_push = 1'b1;
                end
            end
        
            // Write handling for CTRL and BAUDDIV
 935460     always @(posedge clk or negedge rst_n) begin
 935207         if (!rst_n) begin
 000253             reg_ctrl    <= 4'd0;
 000253             reg_bauddiv <= 16'd0;
 935207         end else begin
 931457             if (psel && penable && pwrite) begin
 003750                 case (paddr[4:2])
 000778                     3'b011: reg_ctrl    <= pwdata[3:0];  // 0x0C: CTRL
 000741                     3'b100: reg_bauddiv <= pwdata[15:0]; // 0x10: BAUDDIV
 002231                     default: ;
                        endcase
                    end
                end
            end
        
            // APB Handshake (1-cycle access)
 935460     always @(posedge clk or negedge rst_n) begin
 935207         if (!rst_n) begin
 000253             pready  <= 1'b0;
 000253             pslverr <= 1'b0;
 935207         end else begin
 927650             if (psel && !penable) begin
 007557                 pready  <= 1'b1;
 007557                 pslverr <= 1'b0;
 927650             end else begin
 927650                 pready  <= 1'b0;
                    end
                end
            end
        
            // STATUS word construction
~000197     wire [7:0] status_word = {
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
 3659377     assign prdata = (paddr[4:2] == 3'b000) ? 32'd0 :
 2696380                     (paddr[4:2] == 3'b001) ? {24'd0, (rx_had_data ? rx_fifo_rdata : 8'd0)} :
 1595565                     (paddr[4:2] == 3'b010) ? {24'd0, status_word} :
 995941                     (paddr[4:2] == 3'b011) ? {28'd0, reg_ctrl} :
~599624                     (paddr[4:2] == 3'b100) ? {16'd0, reg_bauddiv} :
%000000                     32'd0;
        
        `ifdef FORMAL
            // Reset sequence: rst_n low initially, then high
            reg f_past_valid = 1'b0;
            reg f_past_rst_n = 1'b0;
            always @(posedge clk) begin
                f_past_valid <= 1'b1;
                f_past_rst_n <= rst_n;
            end
        
            always @(*) begin
                if (!f_past_valid) assume (!rst_n);
                else assume (rst_n);
            end
        
            // APB Protocol assumptions on slave inputs
            always @(*) begin
                if (!psel) assume (!penable);
            end
        
            reg                  f_past_psel;
            reg                  f_past_penable;
            reg                  f_past_pready;
            reg [ADDR_WIDTH-1:0] f_past_paddr;
            reg                  f_past_pwrite;
            reg [DATA_WIDTH-1:0] f_past_pwdata;
        
            always @(posedge clk) begin
                f_past_psel    <= psel;
                f_past_penable <= penable;
                f_past_pready  <= pready;
                f_past_paddr   <= paddr;
                f_past_pwrite  <= pwrite;
                f_past_pwdata  <= pwdata;
            end
        
            always @(*) begin
                if (f_past_valid && rst_n && psel && penable && (f_past_psel && !f_past_penable)) begin
                    assume (paddr == f_past_paddr);
                    assume (pwrite == f_past_pwrite);
                    assume (pwdata == f_past_pwdata);
                end
            end
        
            always @(*) begin
                if (f_past_valid && rst_n && f_past_psel && f_past_penable && f_past_pready) begin
                    assume (!penable);
                end
            end
        
            // 1. FIFO pointer consistency and full/empty flags
            always @(posedge clk) begin
                if (rst_n && f_past_valid) begin
                    assert (tx_fifo_full == (_unused_tx_count == FIFO_DEPTH));
                    assert (tx_fifo_empty == (_unused_tx_count == 0));
                    assert (rx_fifo_full == (_unused_rx_count == FIFO_DEPTH));
                    assert (rx_fifo_empty == (_unused_rx_count == 0));
        
                    // FIFO protection
                    assert (!(tx_fifo_push && tx_fifo_full));
                    assert (!(tx_fifo_pop && tx_fifo_empty));
                    assert (!(rx_fifo_push && rx_fifo_full));
                    assert (!(rx_fifo_pop && rx_fifo_empty));
                end
            end
        
            // 2. Status register flag mapping
            always @(posedge clk) begin
                if (rst_n && f_past_valid) begin
                    if (psel && penable && !pwrite && (paddr[4:2] == 3'b010) && pready) begin
                        assert (prdata[7:0] == {
                            tx_busy,
                            reg_tx_ovf,
                            reg_rx_ovf,
                            reg_frame_err,
                            rx_fifo_empty,
                            rx_fifo_full,
                            tx_fifo_empty,
                            tx_fifo_full
                        });
                        assert (prdata[31:8] == 24'd0);
                    end
                end
            end
        
            // 3. Interrupt definition
            always @(posedge clk) begin
                if (rst_n && f_past_valid) begin
                    assert (uart_irq == (reg_ctrl[3] & ~rx_fifo_empty));
                end
            end
        
            // 4. Status W1C clearing
            always @(posedge clk) begin
                if (rst_n && f_past_valid && f_past_rst_n) begin
                    if (f_past_psel && f_past_penable && f_past_pwrite && (f_past_paddr[4:2] == 3'b010)) begin
                        if (f_past_pwdata[4]) assert (!reg_frame_err || (rx_state == RX_ST_STOP && baud_tick_16x && rx_tick_cnt == 4'd7 && rx_sync_q2 == 1'b0));
                        if (f_past_pwdata[5]) assert (!reg_rx_ovf    || (rx_state == RX_ST_STOP && baud_tick_16x && rx_tick_cnt == 4'd7 && rx_sync_q2 == 1'b1 && rx_fifo_full));
                        if (f_past_pwdata[6]) assert (!reg_tx_ovf    || (psel && penable && pwrite && (paddr[4:2] == 3'b000) && tx_fifo_full));
                    end
                end
            end
        
            // 5. APB handshake & responsiveness
            always @(posedge clk) begin
                if (rst_n && f_past_valid && f_past_rst_n) begin
                    if (f_past_psel && !f_past_penable) begin
                        assert (pready);
                        assert (!pslverr);
                    end
                end
            end
        
            // 6. Precondition covers
            always @(posedge clk) begin
                if (rst_n && f_past_valid) begin
                    cover (psel && penable && pwrite && (paddr[4:2] == 3'b000) && pready);
                    cover (psel && penable && !pwrite && (paddr[4:2] == 3'b001) && pready);
                    cover (psel && penable && !pwrite && (paddr[4:2] == 3'b010) && pready);
                    cover (psel && penable && pwrite && (paddr[4:2] == 3'b011) && pready);
                    cover (psel && penable && pwrite && (paddr[4:2] == 3'b100) && pready);
                    cover (tx_fifo_full);
                    cover (tx_busy);
                    cover (reg_tx_ovf);
                    cover (f_past_psel && f_past_penable && f_past_pwrite && (f_past_paddr[4:2] == 3'b010) && f_past_pwdata[6] && !reg_tx_ovf);
                end
            end
        `endif
        
        endmodule
        
