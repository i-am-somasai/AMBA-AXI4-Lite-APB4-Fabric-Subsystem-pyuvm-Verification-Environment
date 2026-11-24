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
 100022     input  wire                  clk_sys,
~000014     input  wire                  rst_sys_n,
 040010     input  wire                  clk_slow,
~000014     input  wire                  rst_slow_n,
        
            // AXI4-Lite Slave Interface (on clk_sys)
~001631     input  wire [ADDR_WIDTH-1:0] s_axil_awaddr,
 001471     input  wire [2:0]            s_axil_awprot,
 002012     input  wire                  s_axil_awvalid,
 002012     output reg                   s_axil_awready,
        
 001499     input  wire [DATA_WIDTH-1:0] s_axil_wdata,
 001460     input  wire [STRB_WIDTH-1:0] s_axil_wstrb,
 002012     input  wire                  s_axil_wvalid,
 002012     output reg                   s_axil_wready,
        
%000002     output reg  [1:0]            s_axil_bresp,
 002012     output reg                   s_axil_bvalid,
 002012     input  wire                  s_axil_bready,
        
~001517     input  wire [ADDR_WIDTH-1:0] s_axil_araddr,
 001561     input  wire [2:0]            s_axil_arprot,
 001909     input  wire                  s_axil_arvalid,
 001909     output reg                   s_axil_arready,
        
 000469     output reg  [DATA_WIDTH-1:0] s_axil_rdata,
%000002     output reg  [1:0]            s_axil_rresp,
 001909     output reg                   s_axil_rvalid,
 001909     input  wire                  s_axil_rready
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
        
 003921     reg                  req_push;
~001273     reg  [REQ_WIDTH-1:0] req_wdata;
%000000     wire                 req_full;
        
 003927     wire                 req_empty;
 003921     wire                 req_pop;
~001969     wire [REQ_WIDTH-1:0] req_rdata;
        
 003921     reg                  resp_pop;
~001713     wire [RESP_WIDTH-1:0] resp_rdata;
 003927     wire                 resp_empty;
        
 003921     wire                 resp_push;
~000882     wire [RESP_WIDTH-1:0] resp_wdata;
%000000     wire                 resp_full;
        
            // Request FIFO: clk_sys -> clk_slow
            async_fifo #(
                .WIDTH(REQ_WIDTH),
                .DEPTH(FIFO_DEPTH)
            ) u_req_fifo (
                .wclk   (clk_sys),
                .wrst_n (rst_sys_n),
                .winc   (req_push),
                .wdata  (req_wdata),
                .wfull  (req_full),
                .rclk   (clk_slow),
                .rrst_n (rst_slow_n),
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
                .wrst_n (rst_slow_n),
                .winc   (resp_push),
                .wdata  (resp_wdata),
                .wfull  (resp_full),
                .rclk   (clk_sys),
                .rrst_n (rst_sys_n),
                .rinc   (resp_pop),
                .rdata  (resp_rdata),
                .rempty (resp_empty)
            );
        
            // Instantiate slow_regs in clk_slow domain
            slow_regs u_slow_regs (
                .clk_slow   (clk_slow),
                .rst_slow_n (rst_slow_n),
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
        
 005933     reg [2:0]            state;
 000997     reg                  reg_is_write;
~001273     reg [7:0]            reg_addr;
 000777     reg [DATA_WIDTH-1:0] reg_wdata;
 000714     reg [STRB_WIDTH-1:0] reg_wstrb;
        
 100030     always @(posedge clk_sys or negedge rst_sys_n) begin
 099859         if (!rst_sys_n) begin
 000171             state          <= ST_IDLE;
 000171             s_axil_awready <= 1'b0;
 000171             s_axil_wready  <= 1'b0;
 000171             s_axil_arready <= 1'b0;
 000171             s_axil_bvalid  <= 1'b0;
 000171             s_axil_bresp   <= 2'b00;
 000171             s_axil_rvalid  <= 1'b0;
 000171             s_axil_rdata   <= {DATA_WIDTH{1'b0}};
 000171             s_axil_rresp   <= 2'b00;
 000171             req_push       <= 1'b0;
 000171             req_wdata      <= {REQ_WIDTH{1'b0}};
 000171             resp_pop       <= 1'b0;
 000171             reg_is_write   <= 1'b0;
 000171             reg_addr       <= 8'd0;
 000171             reg_wdata      <= {DATA_WIDTH{1'b0}};
 000171             reg_wstrb      <= {STRB_WIDTH{1'b0}};
 099859         end else begin
 099859             req_push <= 1'b0;
 099859             resp_pop <= 1'b0;
        
 099859             case (state)
 015274                 ST_IDLE: begin
 015274                     s_axil_awready <= 1'b0;
 015274                     s_axil_wready  <= 1'b0;
 015274                     s_axil_arready <= 1'b0;
        
                            // Prioritize read if pending
~013365                     if (s_axil_arvalid && !req_full) begin
 001909                         s_axil_arready <= 1'b1;
 001909                         reg_is_write   <= 1'b0;
 001909                         reg_addr       <= s_axil_araddr[7:0];
 001909                         reg_wdata      <= {DATA_WIDTH{1'b0}};
 001909                         reg_wstrb      <= {STRB_WIDTH{1'b0}};
 001909                         state          <= ST_PUSH_REQ;
~011996                     end else if (s_axil_awvalid && s_axil_wvalid && !req_full) begin
 001369                         s_axil_awready <= 1'b1;
 001369                         s_axil_wready  <= 1'b1;
 001369                         reg_is_write   <= 1'b1;
 001369                         reg_addr       <= s_axil_awaddr[7:0];
 001369                         reg_wdata      <= s_axil_wdata;
 001369                         reg_wstrb      <= s_axil_wstrb;
 001369                         state          <= ST_PUSH_REQ;
~011353                     end else if (s_axil_awvalid && !req_full) begin
 000643                         s_axil_awready <= 1'b1;
 000643                         reg_is_write   <= 1'b1;
 000643                         reg_addr       <= s_axil_awaddr[7:0];
 000643                         state          <= ST_WAIT_W;
~011353                     end else if (s_axil_wvalid && !req_full) begin
%000000                         s_axil_wready  <= 1'b1;
%000000                         reg_is_write   <= 1'b1;
%000000                         reg_wdata      <= s_axil_wdata;
%000000                         reg_wstrb      <= s_axil_wstrb;
%000000                         state          <= ST_WAIT_AW;
                            end
                        end
        
 001286                 ST_WAIT_W: begin
 001286                     s_axil_awready <= 1'b0;
 000643                     if (s_axil_wvalid) begin
 000643                         s_axil_wready <= 1'b1;
 000643                         reg_wdata     <= s_axil_wdata;
 000643                         reg_wstrb     <= s_axil_wstrb;
 000643                         state         <= ST_PUSH_REQ;
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
        
 003921                 ST_PUSH_REQ: begin
 003921                     s_axil_awready <= 1'b0;
 003921                     s_axil_wready  <= 1'b0;
 003921                     s_axil_arready <= 1'b0;
        
~003921                     if (!req_full) begin
 003921                         req_push  <= 1'b1;
 003921                         req_wdata <= {reg_is_write, reg_addr, reg_wdata, reg_wstrb};
 003921                         state     <= ST_WAIT_RESP;
                            end
                        end
        
 075457                 ST_WAIT_RESP: begin
 075457                     req_push <= 1'b0;
        
 071536                     if (!resp_empty) begin
 003921                         resp_pop <= 1'b1;
 002012                         if (reg_is_write) begin
 002012                             s_axil_bvalid <= 1'b1;
 002012                             s_axil_bresp  <= resp_rdata[1:0];
 002012                             state         <= ST_BRESP;
 001909                         end else begin
 001909                             s_axil_rvalid <= 1'b1;
 001909                             s_axil_rdata  <= resp_rdata[33:2];
 001909                             s_axil_rresp  <= resp_rdata[1:0];
 001909                             state         <= ST_RRESP;
                                end
                            end
                        end
        
 002012                 ST_BRESP: begin
 002012                     resp_pop <= 1'b0;
~002012                     if (s_axil_bready) begin
 002012                         s_axil_bvalid <= 1'b0;
 002012                         state         <= ST_IDLE;
                            end
                        end
        
 001909                 ST_RRESP: begin
 001909                     resp_pop <= 1'b0;
~001909                     if (s_axil_rready) begin
 001909                         s_axil_rvalid <= 1'b0;
 001909                         state         <= ST_IDLE;
                            end
                        end
        
%000000                 default: state <= ST_IDLE;
                    endcase
                end
            end
        
        endmodule
        
