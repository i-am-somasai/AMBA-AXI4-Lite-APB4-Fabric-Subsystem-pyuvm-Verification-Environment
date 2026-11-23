// AXI4-Lite Default Slave returning DECERR
`timescale 1ns/1ps

module axil_default_slave #(
    parameter integer ADDR_WIDTH = 32,
    parameter integer DATA_WIDTH = 32
) (
    input  wire                  clk,
    input  wire                  rst_n,

    // Write address channel
    input  wire [ADDR_WIDTH-1:0] s_axil_awaddr,
    input  wire [2:0]            s_axil_awprot,
    input  wire                  s_axil_awvalid,
    output reg                   s_axil_awready,

    // Write data channel
    input  wire [DATA_WIDTH-1:0] s_axil_wdata,
    input  wire [(DATA_WIDTH/8)-1:0] s_axil_wstrb,
    input  wire                  s_axil_wvalid,
    output reg                   s_axil_wready,

    // Write response channel
    output reg  [1:0]            s_axil_bresp,
    output reg                   s_axil_bvalid,
    input  wire                  s_axil_bready,

    // Read address channel
    input  wire [ADDR_WIDTH-1:0] s_axil_araddr,
    input  wire [2:0]            s_axil_arprot,
    input  wire                  s_axil_arvalid,
    output reg                   s_axil_arready,

    // Read data channel
    output reg  [DATA_WIDTH-1:0] s_axil_rdata,
    output reg  [1:0]            s_axil_rresp,
    output reg                   s_axil_rvalid,
    input  wire                  s_axil_rready
);

    localparam [1:0] RESP_DECERR = 2'b11;

    // Lint suppression for consumed but unused payload inputs
    wire _unused_inputs = &{1'b0, s_axil_awaddr, s_axil_awprot, s_axil_wdata, s_axil_wstrb, s_axil_araddr, s_axil_arprot};

    // Track write handshake completion
    reg aw_done;
    reg w_done;

    // --- Write Channel Logic ---
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axil_awready <= 1'b0;
            s_axil_wready  <= 1'b0;
            s_axil_bvalid  <= 1'b0;
            s_axil_bresp   <= 2'b00;
            aw_done        <= 1'b0;
            w_done         <= 1'b0;
        end else begin
            s_axil_awready <= (!s_axil_bvalid || s_axil_bready) && !aw_done;
            s_axil_wready  <= (!s_axil_bvalid || s_axil_bready) && !w_done;

            if (s_axil_awvalid && s_axil_awready) begin
                aw_done <= 1'b1;
            end

            if (s_axil_wvalid && s_axil_wready) begin
                w_done <= 1'b1;
            end

            // When both AW and W are collected, generate DECERR response
            if ((s_axil_awvalid && s_axil_awready || aw_done) &&
                (s_axil_wvalid && s_axil_wready || w_done) &&
                (!s_axil_bvalid || s_axil_bready)) begin
                s_axil_bvalid <= 1'b1;
                s_axil_bresp  <= RESP_DECERR;
                aw_done       <= 1'b0;
                w_done        <= 1'b0;
            end else if (s_axil_bvalid && s_axil_bready) begin
                s_axil_bvalid <= 1'b0;
            end
        end
    end

    // --- Read Channel Logic ---
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axil_arready <= 1'b0;
            s_axil_rvalid  <= 1'b0;
            s_axil_rresp   <= 2'b00;
            s_axil_rdata   <= {DATA_WIDTH{1'b0}};
        end else begin
            s_axil_arready <= !s_axil_rvalid || s_axil_rready;

            if (s_axil_arvalid && s_axil_arready) begin
                s_axil_rvalid <= 1'b1;
                s_axil_rresp  <= RESP_DECERR;
                s_axil_rdata  <= {DATA_WIDTH{1'b0}};
            end else if (s_axil_rvalid && s_axil_rready) begin
                s_axil_rvalid <= 1'b0;
            end
        end
    end

endmodule
