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
    input  wire                  clk_sys,
    input  wire                  rst_sys_n,
    input  wire                  clk_slow,
    input  wire                  rst_slow_n,

    // AXI4-Lite Slave Interface (on clk_sys)
    input  wire [ADDR_WIDTH-1:0] s_axil_awaddr,
    input  wire [2:0]            s_axil_awprot,
    input  wire                  s_axil_awvalid,
    output reg                   s_axil_awready,

    input  wire [DATA_WIDTH-1:0] s_axil_wdata,
    input  wire [STRB_WIDTH-1:0] s_axil_wstrb,
    input  wire                  s_axil_wvalid,
    output reg                   s_axil_wready,

    output reg  [1:0]            s_axil_bresp,
    output reg                   s_axil_bvalid,
    input  wire                  s_axil_bready,

    input  wire [ADDR_WIDTH-1:0] s_axil_araddr,
    input  wire [2:0]            s_axil_arprot,
    input  wire                  s_axil_arvalid,
    output reg                   s_axil_arready,

    output reg  [DATA_WIDTH-1:0] s_axil_rdata,
    output reg  [1:0]            s_axil_rresp,
    output reg                   s_axil_rvalid,
    input  wire                  s_axil_rready
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

    reg                  req_push;
    reg  [REQ_WIDTH-1:0] req_wdata;
    wire                 req_full;

    wire                 req_empty;
    wire                 req_pop;
    wire [REQ_WIDTH-1:0] req_rdata;

    reg                  resp_pop;
    wire [RESP_WIDTH-1:0] resp_rdata;
    wire                 resp_empty;

    wire                 resp_push;
    wire [RESP_WIDTH-1:0] resp_wdata;
    wire                 resp_full;

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

    reg [2:0]            state;
    reg                  reg_is_write;
    reg [7:0]            reg_addr;
    reg [DATA_WIDTH-1:0] reg_wdata;
    reg [STRB_WIDTH-1:0] reg_wstrb;

    always @(posedge clk_sys or negedge rst_sys_n) begin
        if (!rst_sys_n) begin
            state          <= ST_IDLE;
            s_axil_awready <= 1'b0;
            s_axil_wready  <= 1'b0;
            s_axil_arready <= 1'b0;
            s_axil_bvalid  <= 1'b0;
            s_axil_bresp   <= 2'b00;
            s_axil_rvalid  <= 1'b0;
            s_axil_rdata   <= {DATA_WIDTH{1'b0}};
            s_axil_rresp   <= 2'b00;
            req_push       <= 1'b0;
            req_wdata      <= {REQ_WIDTH{1'b0}};
            resp_pop       <= 1'b0;
            reg_is_write   <= 1'b0;
            reg_addr       <= 8'd0;
            reg_wdata      <= {DATA_WIDTH{1'b0}};
            reg_wstrb      <= {STRB_WIDTH{1'b0}};
        end else begin
            req_push <= 1'b0;
            resp_pop <= 1'b0;

            case (state)
                ST_IDLE: begin
                    s_axil_awready <= 1'b0;
                    s_axil_wready  <= 1'b0;
                    s_axil_arready <= 1'b0;

                    // Prioritize read if pending
                    if (s_axil_arvalid && !req_full) begin
                        s_axil_arready <= 1'b1;
                        reg_is_write   <= 1'b0;
                        reg_addr       <= s_axil_araddr[7:0];
                        reg_wdata      <= {DATA_WIDTH{1'b0}};
                        reg_wstrb      <= {STRB_WIDTH{1'b0}};
                        state          <= ST_PUSH_REQ;
                    end else if (s_axil_awvalid && s_axil_wvalid && !req_full) begin
                        s_axil_awready <= 1'b1;
                        s_axil_wready  <= 1'b1;
                        reg_is_write   <= 1'b1;
                        reg_addr       <= s_axil_awaddr[7:0];
                        reg_wdata      <= s_axil_wdata;
                        reg_wstrb      <= s_axil_wstrb;
                        state          <= ST_PUSH_REQ;
                    end else if (s_axil_awvalid && !req_full) begin
                        s_axil_awready <= 1'b1;
                        reg_is_write   <= 1'b1;
                        reg_addr       <= s_axil_awaddr[7:0];
                        state          <= ST_WAIT_W;
                    end else if (s_axil_wvalid && !req_full) begin
                        s_axil_wready  <= 1'b1;
                        reg_is_write   <= 1'b1;
                        reg_wdata      <= s_axil_wdata;
                        reg_wstrb      <= s_axil_wstrb;
                        state          <= ST_WAIT_AW;
                    end
                end

                ST_WAIT_W: begin
                    s_axil_awready <= 1'b0;
                    if (s_axil_wvalid) begin
                        s_axil_wready <= 1'b1;
                        reg_wdata     <= s_axil_wdata;
                        reg_wstrb     <= s_axil_wstrb;
                        state         <= ST_PUSH_REQ;
                    end
                end

                ST_WAIT_AW: begin
                    s_axil_wready <= 1'b0;
                    if (s_axil_awvalid) begin
                        s_axil_awready <= 1'b1;
                        reg_addr       <= s_axil_awaddr[7:0];
                        state          <= ST_PUSH_REQ;
                    end
                end

                ST_PUSH_REQ: begin
                    s_axil_awready <= 1'b0;
                    s_axil_wready  <= 1'b0;
                    s_axil_arready <= 1'b0;

                    if (!req_full) begin
                        req_push  <= 1'b1;
                        req_wdata <= {reg_is_write, reg_addr, reg_wdata, reg_wstrb};
                        state     <= ST_WAIT_RESP;
                    end
                end

                ST_WAIT_RESP: begin
                    req_push <= 1'b0;

                    if (!resp_empty) begin
                        resp_pop <= 1'b1;
                        if (reg_is_write) begin
                            s_axil_bvalid <= 1'b1;
                            s_axil_bresp  <= resp_rdata[1:0];
                            state         <= ST_BRESP;
                        end else begin
                            s_axil_rvalid <= 1'b1;
                            s_axil_rdata  <= resp_rdata[33:2];
                            s_axil_rresp  <= resp_rdata[1:0];
                            state         <= ST_RRESP;
                        end
                    end
                end

                ST_BRESP: begin
                    resp_pop <= 1'b0;
                    if (s_axil_bready) begin
                        s_axil_bvalid <= 1'b0;
                        state         <= ST_IDLE;
                    end
                end

                ST_RRESP: begin
                    resp_pop <= 1'b0;
                    if (s_axil_rready) begin
                        s_axil_rvalid <= 1'b0;
                        state         <= ST_IDLE;
                    end
                end

                default: state <= ST_IDLE;
            endcase
        end
    end

endmodule
