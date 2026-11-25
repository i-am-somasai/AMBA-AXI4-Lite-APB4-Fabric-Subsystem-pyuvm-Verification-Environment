//      // verilator_coverage annotation
        // rtl/cdc/axil_cdc_bridge.v
        // AXI4-Lite CDC Bridge between clk_sys and clk_slow using dual-clock async FIFOs
        `timescale 1ns / 1ps
        
        module axil_cdc_bridge #(
            parameter ADDR_WIDTH = 32,
            parameter DATA_WIDTH = 32,
            parameter STRB_WIDTH = DATA_WIDTH / 8,
            parameter FIFO_DEPTH = 4
        )(
            // Clocks and Resets
 935460     input  wire                  clk_sys,
~000021     input  wire                  rst_sys_n,
 389558     input  wire                  clk_slow,
~000021     input  wire                  rst_slow_n,
        
            // AXI4-Lite Slave Interface (on clk_sys)
~013725     input  wire [ADDR_WIDTH-1:0] s_axil_awaddr,
 012615     input  wire [2:0]            s_axil_awprot,
 015210     input  wire                  s_axil_awvalid,
 015210     output reg                   s_axil_awready,
        
 012686     input  wire [DATA_WIDTH-1:0] s_axil_wdata,
 012493     input  wire [STRB_WIDTH-1:0] s_axil_wstrb,
 015210     input  wire                  s_axil_wvalid,
 015210     output reg                   s_axil_wready,
        
%000002     output reg  [1:0]            s_axil_bresp,
 015210     output reg                   s_axil_bvalid,
 015210     input  wire                  s_axil_bready,
        
~012803     input  wire [ADDR_WIDTH-1:0] s_axil_araddr,
 012912     input  wire [2:0]            s_axil_arprot,
 015162     input  wire                  s_axil_arvalid,
 015162     output reg                   s_axil_arready,
        
 003680     output reg  [DATA_WIDTH-1:0] s_axil_rdata,
%000002     output reg  [1:0]            s_axil_rresp,
 015162     output reg                   s_axil_rvalid,
 015162     input  wire                  s_axil_rready
        );
        
            // Suppress unused address/prot bits
            wire _unused = &{1'b0, s_axil_awprot, s_axil_arprot, s_axil_awaddr[ADDR_WIDTH-1:8], s_axil_araddr[ADDR_WIDTH-1:8]};
        
            // -------------------------------------------------------------
            // Request & Response Async FIFOs
            // -------------------------------------------------------------
            // Request payload: {is_write, addr[7:0], wdata[31:0], wstrb[3:0]} = 45 bits
            localparam REQ_WIDTH = 1 + 8 + 32 + 4; // 45
            // Response payload: {rdata[31:0], resp[1:0]} = 34 bits
            localparam RESP_WIDTH = 32 + 2; // 34
        
 030372     reg                  req_push;
~009290     reg  [REQ_WIDTH-1:0] req_wdata;
%000000     wire                 req_full;
        
 030393     wire                 req_empty;
 030372     wire                 req_pop;
~015281     wire [REQ_WIDTH-1:0] req_rdata;
        
 030372     reg                  resp_pop;
~013075     wire [RESP_WIDTH-1:0] resp_rdata;
 030393     wire                 resp_empty;
        
 030372     wire                 resp_push;
~006570     wire [RESP_WIDTH-1:0] resp_wdata;
%000000     wire                 resp_full;
        
            // -------------------------------------------------------------
            // Cross-Domain Reset Synchronizers (kept on pure reset nets to
            // avoid mixed sync/async reset usage)
            // -------------------------------------------------------------
~6342945     wire both_rst_n = rst_sys_n & rst_slow_n;
        
~000021     reg fifo_rst_sys_q1;
~000021     reg fifo_rst_sys_q2;
 935460     always @(posedge clk_sys or negedge both_rst_n) begin
 935187         if (!both_rst_n) begin
 000273             fifo_rst_sys_q1 <= 1'b0;
 000273             fifo_rst_sys_q2 <= 1'b0;
 935187         end else begin
 935187             fifo_rst_sys_q1 <= 1'b1;
 935187             fifo_rst_sys_q2 <= fifo_rst_sys_q1;
                end
            end
~000021     wire fifo_rst_sys_n = fifo_rst_sys_q2;
        
~000021     reg slow_rst_seen_q1;
~000021     reg slow_rst_seen_q2;
 935460     always @(posedge clk_sys or negedge rst_slow_n) begin
 935189         if (!rst_slow_n) begin
 000271             slow_rst_seen_q1 <= 1'b0;
 000271             slow_rst_seen_q2 <= 1'b0;
 935189         end else begin
 935189             slow_rst_seen_q1 <= 1'b1;
 935189             slow_rst_seen_q2 <= slow_rst_seen_q1;
                end
            end
~000021     wire slow_rst_seen_n = slow_rst_seen_q2;
        
~000021     reg fifo_rst_slow_q1;
~000021     reg fifo_rst_slow_q2;
 389558     always @(posedge clk_slow or negedge both_rst_n) begin
 389418         if (!both_rst_n) begin
 000140             fifo_rst_slow_q1 <= 1'b0;
 000140             fifo_rst_slow_q2 <= 1'b0;
 389418         end else begin
 389418             fifo_rst_slow_q1 <= 1'b1;
 389418             fifo_rst_slow_q2 <= fifo_rst_slow_q1;
                end
            end
~000021     wire fifo_rst_slow_n = fifo_rst_slow_q2;
        
            // Gate FIFO control pulses when either reset is active so an async slow reset
            // cannot assert rempty while a previously-registered req_push/resp_pop is high
 5938716     wire fifo_req_push = req_push && slow_rst_seen_n;
 5949715     wire fifo_resp_pop = resp_pop && slow_rst_seen_n;
        
            // Request FIFO: clk_sys -> clk_slow
            async_fifo #(
                .WIDTH(REQ_WIDTH),
                .DEPTH(FIFO_DEPTH)
            ) u_req_fifo (
                .wclk   (clk_sys),
                .wrst_n (fifo_rst_sys_n),
                .winc   (fifo_req_push),
                .wdata  (req_wdata),
                .wfull  (req_full),
                .rclk   (clk_slow),
                .rrst_n (fifo_rst_slow_n),
                .rinc   (req_pop),
                .rdata  (req_rdata),
                .rempty (req_empty)
            );
        
            // Response FIFO: clk_slow -> clk_sys
            async_fifo #(
                .WIDTH(RESP_WIDTH),
                .DEPTH(FIFO_DEPTH)
            ) u_resp_fifo (
                .wclk   (clk_slow),
                .wrst_n (fifo_rst_slow_n),
                .winc   (resp_push),
                .wdata  (resp_wdata),
                .wfull  (resp_full),
                .rclk   (clk_sys),
                .rrst_n (fifo_rst_sys_n),
                .rinc   (fifo_resp_pop),
                .rdata  (resp_rdata),
                .rempty (resp_empty)
            );
        
            // Instantiate slow_regs in clk_slow domain
            slow_regs u_slow_regs (
                .clk_slow   (clk_slow),
                .rst_slow_n (fifo_rst_slow_n),
                .req_empty  (req_empty),
                .req_pop    (req_pop),
                .req_data   (req_rdata),
                .resp_full  (resp_full),
                .resp_push  (resp_push),
                .resp_data  (resp_wdata)
            );
        
            // -------------------------------------------------------------
            // AXI4-Lite FSM in clk_sys domain
            // -------------------------------------------------------------
            localparam [2:0] ST_IDLE      = 3'd0,
                             ST_WAIT_W    = 3'd1,
                             ST_WAIT_AW   = 3'd2,
                             ST_PUSH_REQ  = 3'd3,
                             ST_WAIT_RESP = 3'd4,
                             ST_BRESP     = 3'd5,
                             ST_RRESP     = 3'd6;
        
 045582     reg [2:0]            state;
 007548     reg                  reg_is_write;
~009290     reg [7:0]            reg_addr;
 005789     reg [DATA_WIDTH-1:0] reg_wdata;
 005310     reg [STRB_WIDTH-1:0] reg_wstrb;
%000000     reg                  slow_rst_aborted;
        
 935460     always @(posedge clk_sys or negedge rst_sys_n) begin
 935207         if (!rst_sys_n) begin
 000253             state            <= ST_IDLE;
 000253             s_axil_awready   <= 1'b0;
 000253             s_axil_wready    <= 1'b0;
 000253             s_axil_arready   <= 1'b0;
 000253             s_axil_bvalid    <= 1'b0;
 000253             s_axil_bresp     <= 2'b00;
 000253             s_axil_rvalid    <= 1'b0;
 000253             s_axil_rdata     <= {DATA_WIDTH{1'b0}};
 000253             s_axil_rresp     <= 2'b00;
 000253             req_push         <= 1'b0;
 000253             req_wdata        <= {REQ_WIDTH{1'b0}};
 000253             resp_pop         <= 1'b0;
 000253             reg_is_write     <= 1'b0;
 000253             reg_addr         <= 8'd0;
 000253             reg_wdata        <= {DATA_WIDTH{1'b0}};
 000253             reg_wstrb        <= {STRB_WIDTH{1'b0}};
 000253             slow_rst_aborted <= 1'b0;
 935207         end else begin
 935207             req_push <= 1'b0;
 935207             resp_pop <= 1'b0;
        
~935207             if (!slow_rst_seen_n && (state == ST_WAIT_W || state == ST_WAIT_AW || state == ST_PUSH_REQ || state == ST_WAIT_RESP)) begin
%000000                 slow_rst_aborted <= 1'b1;
                    end
        
 935207             case (state)
 238030                 ST_IDLE: begin
 238030                     s_axil_awready   <= 1'b0;
 238030                     s_axil_wready    <= 1'b0;
 238030                     s_axil_arready   <= 1'b0;
 238030                     slow_rst_aborted <= 1'b0;
        
                            // Wait until slow domain reset synchronizer releases before accepting new transactions
 237970                     if (slow_rst_seen_n) begin
                                // Prioritize read if pending
~222808                         if (s_axil_arvalid && !req_full) begin
 015162                             s_axil_arready <= 1'b1;
 015162                             reg_is_write   <= 1'b0;
 015162                             reg_addr       <= s_axil_araddr[7:0];
 015162                             reg_wdata      <= {DATA_WIDTH{1'b0}};
 015162                             reg_wstrb      <= {STRB_WIDTH{1'b0}};
 015162                             state          <= ST_PUSH_REQ;
~212622                         end else if (s_axil_awvalid && s_axil_wvalid && !req_full) begin
 010186                             s_axil_awready <= 1'b1;
 010186                             s_axil_wready  <= 1'b1;
 010186                             reg_is_write   <= 1'b1;
 010186                             reg_addr       <= s_axil_awaddr[7:0];
 010186                             reg_wdata      <= s_axil_wdata;
 010186                             reg_wstrb      <= s_axil_wstrb;
 010186                             state          <= ST_PUSH_REQ;
~207598                         end else if (s_axil_awvalid && !req_full) begin
 005024                             s_axil_awready <= 1'b1;
 005024                             reg_is_write   <= 1'b1;
 005024                             reg_addr       <= s_axil_awaddr[7:0];
 005024                             state          <= ST_WAIT_W;
~207598                         end else if (s_axil_wvalid && !req_full) begin
%000000                             s_axil_wready  <= 1'b1;
%000000                             reg_is_write   <= 1'b1;
%000000                             reg_wdata      <= s_axil_wdata;
%000000                             reg_wstrb      <= s_axil_wstrb;
%000000                             state          <= ST_WAIT_AW;
                                end
                            end
                        end
        
 010048                 ST_WAIT_W: begin
 010048                     s_axil_awready <= 1'b0;
 005024                     if (s_axil_wvalid) begin
 005024                         s_axil_wready <= 1'b1;
 005024                         reg_wdata     <= s_axil_wdata;
 005024                         reg_wstrb     <= s_axil_wstrb;
 005024                         state         <= ST_PUSH_REQ;
                            end
                        end
        
%000000                 ST_WAIT_AW: begin
%000000                     s_axil_wready <= 1'b0;
%000000                     if (s_axil_awvalid) begin
%000000                         s_axil_awready <= 1'b1;
%000000                         reg_addr       <= s_axil_awaddr[7:0];
%000000                         state          <= ST_PUSH_REQ;
                            end
                        end
        
 030372                 ST_PUSH_REQ: begin
 030372                     s_axil_awready <= 1'b0;
 030372                     s_axil_wready  <= 1'b0;
 030372                     s_axil_arready <= 1'b0;
        
~030372                     if (slow_rst_aborted || !slow_rst_seen_n) begin
                                // Complete accepted AXI request with SLVERR if slow domain reset occurred
%000000                         if (reg_is_write) begin
%000000                             s_axil_bvalid <= 1'b1;
%000000                             s_axil_bresp  <= 2'b10;
%000000                             state         <= ST_BRESP;
%000000                         end else begin
%000000                             s_axil_rvalid <= 1'b1;
%000000                             s_axil_rdata  <= {DATA_WIDTH{1'b0}};
%000000                             s_axil_rresp  <= 2'b10;
%000000                             state         <= ST_RRESP;
                                end
~030372                     end else if (!req_full) begin
 030372                         req_push  <= 1'b1;
 030372                         req_wdata <= {reg_is_write, reg_addr, reg_wdata, reg_wstrb};
 030372                         state     <= ST_WAIT_RESP;
                            end
                        end
        
 574726                 ST_WAIT_RESP: begin
 574726                     req_push <= 1'b0;
        
~574726                     if (slow_rst_aborted || !slow_rst_seen_n) begin
                                // Abort slow-domain wait cleanly with SLVERR so master never hangs
%000000                         if (reg_is_write) begin
%000000                             s_axil_bvalid <= 1'b1;
%000000                             s_axil_bresp  <= 2'b10;
%000000                             state         <= ST_BRESP;
%000000                         end else begin
%000000                             s_axil_rvalid <= 1'b1;
%000000                             s_axil_rdata  <= {DATA_WIDTH{1'b0}};
%000000                             s_axil_rresp  <= 2'b10;
%000000                             state         <= ST_RRESP;
                                end
 544354                     end else if (!resp_empty) begin
 030372                         resp_pop <= 1'b1;
 015210                         if (reg_is_write) begin
 015210                             s_axil_bvalid <= 1'b1;
 015210                             s_axil_bresp  <= resp_rdata[1:0];
 015210                             state         <= ST_BRESP;
 015162                         end else begin
 015162                             s_axil_rvalid <= 1'b1;
 015162                             s_axil_rdata  <= resp_rdata[33:2];
 015162                             s_axil_rresp  <= resp_rdata[1:0];
 015162                             state         <= ST_RRESP;
                                end
                            end
                        end
        
 041096                 ST_BRESP: begin
 041096                     resp_pop <= 1'b0;
 025886                     if (s_axil_bready) begin
 015210                         s_axil_bvalid <= 1'b0;
 015210                         state         <= ST_IDLE;
                            end
                        end
        
 040935                 ST_RRESP: begin
 040935                     resp_pop <= 1'b0;
 025773                     if (s_axil_rready) begin
 015162                         s_axil_rvalid <= 1'b0;
 015162                         state         <= ST_IDLE;
                            end
                        end
        
%000000                 default: state <= ST_IDLE;
                    endcase
                end
            end
        
        `ifdef FORMAL
            // Protocol checker on s_axil
            axil_props #(
                .ADDR_WIDTH        (ADDR_WIDTH),
                .DATA_WIDTH        (DATA_WIDTH),
                .STRB_WIDTH        (STRB_WIDTH),
                .IS_SLAVE          (1),
                .SINGLE_OUTSTANDING(1),
                .CHECK_CAUSALITY   (1)
            ) u_axil_props (
                .clk    (clk_sys),
                .rst_n  (rst_sys_n),
                .awaddr (s_axil_awaddr),
                .awprot (s_axil_awprot),
                .awvalid(s_axil_awvalid),
                .awready(s_axil_awready),
                .wdata  (s_axil_wdata),
                .wstrb  (s_axil_wstrb),
                .wvalid (s_axil_wvalid),
                .wready (s_axil_wready),
                .bresp  (s_axil_bresp),
                .bvalid (s_axil_bvalid),
                .bready (s_axil_bready),
                .araddr (s_axil_araddr),
                .arprot (s_axil_arprot),
                .arvalid(s_axil_arvalid),
                .arready(s_axil_arready),
                .rdata  (s_axil_rdata),
                .rresp  (s_axil_rresp),
                .rvalid (s_axil_rvalid),
                .rready (s_axil_rready)
            );
        
            reg f_sys_past = 1'b0;
            reg f_slow_past = 1'b0;
            always @(posedge clk_sys) f_sys_past <= 1'b1;
            always @(posedge clk_slow) f_slow_past <= 1'b1;
        
            always @(*) begin
                if (!f_sys_past)  assume (!rst_sys_n);
                else              assume (rst_sys_n);
                if (!f_slow_past) assume (!rst_slow_n);
                else              assume (rst_slow_n);
            end
        
            // FIFO Handshake Safety (clk_sys domain)
            always @(posedge clk_sys) begin
                if (rst_sys_n && slow_rst_seen_n && f_sys_past) begin
                    assert (!(fifo_req_push && req_full));
                    assert (!(fifo_resp_pop && resp_empty));
                end
            end
        
            // FIFO Handshake Safety (clk_slow domain)
            always @(posedge clk_slow) begin
                if (rst_slow_n && rst_sys_n && f_slow_past) begin
                    assert (!(req_pop && req_empty));
                    assert (!(resp_push && resp_full));
                end
            end
        
            // Response code validity
            always @(posedge clk_sys) begin
                if (rst_sys_n && f_sys_past) begin
                    if (s_axil_bvalid) begin
                        assert (s_axil_bresp == 2'b00 || s_axil_bresp == 2'b10);
                    end
                    if (s_axil_rvalid) begin
                        assert (s_axil_rresp == 2'b00 || s_axil_rresp == 2'b10);
                    end
                end
            end
        
            // Data integrity on SLOW_ID (offset 0x00..0x03) read & slow-reset abort check
            reg [7:0] f_saved_araddr;
            reg       f_read_aborted;
            always @(posedge clk_sys) begin
                if (!rst_sys_n) begin
                    f_saved_araddr <= 8'd0;
                    f_read_aborted <= 1'b0;
                end else begin
                    if (s_axil_arvalid && s_axil_arready) begin
                        f_saved_araddr <= s_axil_araddr[7:0];
                        f_read_aborted <= 1'b0;
                    end
                    if (!reg_is_write && (state == ST_PUSH_REQ || state == ST_WAIT_RESP) &&
                        (slow_rst_aborted || !slow_rst_seen_n)) begin
                        f_read_aborted <= 1'b1;
                    end
                end
            end
        
            always @(posedge clk_sys) begin
                if (rst_sys_n && f_sys_past) begin
                    if (s_axil_rvalid && f_read_aborted) begin
                        assert (s_axil_rresp == 2'b10);
                    end else if (s_axil_rvalid && (f_saved_araddr[7:2] == 6'h00)) begin
                        assert (s_axil_rdata == 32'h510E_0001);
                        assert (s_axil_rresp == 2'b00);
                    end
                end
            end
        
            // Precondition Covers
            always @(posedge clk_sys) begin
                if (rst_sys_n && f_sys_past) begin
                    cover (s_axil_bvalid && s_axil_bready);
                    cover (s_axil_rvalid && s_axil_rready);
                    cover (s_axil_rvalid && s_axil_rready && s_axil_rdata == 32'h510E_0001);
                    cover (s_axil_bvalid && s_axil_bready && s_axil_bresp == 2'b10);
                    cover (s_axil_rvalid && s_axil_rready && s_axil_rresp == 2'b10);
                end
            end
        `endif
        
        endmodule
        
