// tb/block/tb_axil_xbar.v
// Testbench wrapper exposing individual master and slave ports for axil_xbar
`timescale 1ns / 1ps

module tb_axil_xbar #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 32,
    parameter STRB_WIDTH = DATA_WIDTH / 8
)(
    input  wire                  clk,
    input  wire                  rst_n,

    // Master 0 Interface
    input  wire [ADDR_WIDTH-1:0] m0_awaddr,
    input  wire [2:0]            m0_awprot,
    input  wire                  m0_awvalid,
    output wire                  m0_awready,
    input  wire [DATA_WIDTH-1:0] m0_wdata,
    input  wire [STRB_WIDTH-1:0] m0_wstrb,
    input  wire                  m0_wvalid,
    output wire                  m0_wready,
    output wire [1:0]            m0_bresp,
    output wire                  m0_bvalid,
    input  wire                  m0_bready,
    input  wire [ADDR_WIDTH-1:0] m0_araddr,
    input  wire [2:0]            m0_arprot,
    input  wire                  m0_arvalid,
    output wire                  m0_arready,
    output wire [DATA_WIDTH-1:0] m0_rdata,
    output wire [1:0]            m0_rresp,
    output wire                  m0_rvalid,
    input  wire                  m0_rready,

    // Master 1 Interface
    input  wire [ADDR_WIDTH-1:0] m1_awaddr,
    input  wire [2:0]            m1_awprot,
    input  wire                  m1_awvalid,
    output wire                  m1_awready,
    input  wire [DATA_WIDTH-1:0] m1_wdata,
    input  wire [STRB_WIDTH-1:0] m1_wstrb,
    input  wire                  m1_wvalid,
    output wire                  m1_wready,
    output wire [1:0]            m1_bresp,
    output wire                  m1_bvalid,
    input  wire                  m1_bready,
    input  wire [ADDR_WIDTH-1:0] m1_araddr,
    input  wire [2:0]            m1_arprot,
    input  wire                  m1_arvalid,
    output wire                  m1_arready,
    output wire [DATA_WIDTH-1:0] m1_rdata,
    output wire [1:0]            m1_rresp,
    output wire                  m1_rvalid,
    input  wire                  m1_rready,

    // Slave 0 Interface (APB: 0x4000_0000)
    output wire [ADDR_WIDTH-1:0] s0_awaddr,
    output wire [2:0]            s0_awprot,
    output wire                  s0_awvalid,
    input  wire                  s0_awready,
    output wire [DATA_WIDTH-1:0] s0_wdata,
    output wire [STRB_WIDTH-1:0] s0_wstrb,
    output wire                  s0_wvalid,
    input  wire                  s0_wready,
    input  wire [1:0]            s0_bresp,
    input  wire                  s0_bvalid,
    output wire                  s0_bready,
    output wire [ADDR_WIDTH-1:0] s0_araddr,
    output wire [2:0]            s0_arprot,
    output wire                  s0_arvalid,
    input  wire                  s0_arready,
    input  wire [DATA_WIDTH-1:0] s0_rdata,
    input  wire [1:0]            s0_rresp,
    input  wire                  s0_rvalid,
    output wire                  s0_rready,

    // Slave 1 Interface (RAM: 0x5000_0000)
    output wire [ADDR_WIDTH-1:0] s1_awaddr,
    output wire [2:0]            s1_awprot,
    output wire                  s1_awvalid,
    input  wire                  s1_awready,
    output wire [DATA_WIDTH-1:0] s1_wdata,
    output wire [STRB_WIDTH-1:0] s1_wstrb,
    output wire                  s1_wvalid,
    input  wire                  s1_wready,
    input  wire [1:0]            s1_bresp,
    input  wire                  s1_bvalid,
    output wire                  s1_bready,
    output wire [ADDR_WIDTH-1:0] s1_araddr,
    output wire [2:0]            s1_arprot,
    output wire                  s1_arvalid,
    input  wire                  s1_arready,
    input  wire [DATA_WIDTH-1:0] s1_rdata,
    input  wire [1:0]            s1_rresp,
    input  wire                  s1_rvalid,
    output wire                  s1_rready,

    // Slave 2 Interface (CSR: 0x6000_0000)
    output wire [ADDR_WIDTH-1:0] s2_awaddr,
    output wire [2:0]            s2_awprot,
    output wire                  s2_awvalid,
    input  wire                  s2_awready,
    output wire [DATA_WIDTH-1:0] s2_wdata,
    output wire [STRB_WIDTH-1:0] s2_wstrb,
    output wire                  s2_wvalid,
    input  wire                  s2_wready,
    input  wire [1:0]            s2_bresp,
    input  wire                  s2_bvalid,
    output wire                  s2_bready,
    output wire [ADDR_WIDTH-1:0] s2_araddr,
    output wire [2:0]            s2_arprot,
    output wire                  s2_arvalid,
    input  wire                  s2_arready,
    input  wire [DATA_WIDTH-1:0] s2_rdata,
    input  wire [1:0]            s2_rresp,
    input  wire                  s2_rvalid,
    output wire                  s2_rready,

    // Slave 3 Interface (CDC: 0x7000_0000)
    output wire [ADDR_WIDTH-1:0] s3_awaddr,
    output wire [2:0]            s3_awprot,
    output wire                  s3_awvalid,
    input  wire                  s3_awready,
    output wire [DATA_WIDTH-1:0] s3_wdata,
    output wire [STRB_WIDTH-1:0] s3_wstrb,
    output wire                  s3_wvalid,
    input  wire                  s3_wready,
    input  wire [1:0]            s3_bresp,
    input  wire                  s3_bvalid,
    output wire                  s3_bready,
    output wire [ADDR_WIDTH-1:0] s3_araddr,
    output wire [2:0]            s3_arprot,
    output wire                  s3_arvalid,
    input  wire                  s3_arready,
    input  wire [DATA_WIDTH-1:0] s3_rdata,
    input  wire [1:0]            s3_rresp,
    input  wire                  s3_rvalid,
    output wire                  s3_rready
);

    axil_xbar #(
        .DATA_WIDTH (DATA_WIDTH),
        .ADDR_WIDTH (ADDR_WIDTH),
        .NUM_MASTERS(2),
        .NUM_SLAVES (4)
    ) u_xbar (
        .clk           (clk),
        .rst_n         (rst_n),

        .s_axil_awaddr ({m1_awaddr, m0_awaddr}),
        .s_axil_awprot ({m1_awprot, m0_awprot}),
        .s_axil_awvalid({m1_awvalid, m0_awvalid}),
        .s_axil_awready({m1_awready, m0_awready}),

        .s_axil_wdata  ({m1_wdata, m0_wdata}),
        .s_axil_wstrb  ({m1_wstrb, m0_wstrb}),
        .s_axil_wvalid ({m1_wvalid, m0_wvalid}),
        .s_axil_wready ({m1_wready, m0_wready}),

        .s_axil_bresp  ({m1_bresp, m0_bresp}),
        .s_axil_bvalid ({m1_bvalid, m0_bvalid}),
        .s_axil_bready ({m1_bready, m0_bready}),

        .s_axil_araddr ({m1_araddr, m0_araddr}),
        .s_axil_arprot ({m1_arprot, m0_arprot}),
        .s_axil_arvalid({m1_arvalid, m0_arvalid}),
        .s_axil_arready({m1_arready, m0_arready}),

        .s_axil_rdata  ({m1_rdata, m0_rdata}),
        .s_axil_rresp  ({m1_rresp, m0_rresp}),
        .s_axil_rvalid ({m1_rvalid, m0_rvalid}),
        .s_axil_rready ({m1_rready, m0_rready}),

        .m_axil_awaddr ({s3_awaddr, s2_awaddr, s1_awaddr, s0_awaddr}),
        .m_axil_awprot ({s3_awprot, s2_awprot, s1_awprot, s0_awprot}),
        .m_axil_awvalid({s3_awvalid, s2_awvalid, s1_awvalid, s0_awvalid}),
        .m_axil_awready({s3_awready, s2_awready, s1_awready, s0_awready}),

        .m_axil_wdata  ({s3_wdata, s2_wdata, s1_wdata, s0_wdata}),
        .m_axil_wstrb  ({s3_wstrb, s2_wstrb, s1_wstrb, s0_wstrb}),
        .m_axil_wvalid ({s3_wvalid, s2_wvalid, s1_wvalid, s0_wvalid}),
        .m_axil_wready ({s3_wready, s2_wready, s1_wready, s0_wready}),

        .m_axil_bresp  ({s3_bresp, s2_bresp, s1_bresp, s0_bresp}),
        .m_axil_bvalid ({s3_bvalid, s2_bvalid, s1_bvalid, s0_bvalid}),
        .m_axil_bready ({s3_bready, s2_bready, s1_bready, s0_bready}),

        .m_axil_araddr ({s3_araddr, s2_araddr, s1_araddr, s0_araddr}),
        .m_axil_arprot ({s3_arprot, s2_arprot, s1_arprot, s0_arprot}),
        .m_axil_arvalid({s3_arvalid, s2_arvalid, s1_arvalid, s0_arvalid}),
        .m_axil_arready({s3_arready, s2_arready, s1_arready, s0_arready}),

        .m_axil_rdata  ({s3_rdata, s2_rdata, s1_rdata, s0_rdata}),
        .m_axil_rresp  ({s3_rresp, s2_rresp, s1_rresp, s0_rresp}),
        .m_axil_rvalid ({s3_rvalid, s2_rvalid, s1_rvalid, s0_rvalid}),
        .m_axil_rready ({s3_rready, s2_rready, s1_rready, s0_rready})
    );

`ifdef COCOTB_SIM
    initial begin
        $dumpfile("dump.vcd");
        $dumpvars(0, tb_axil_xbar);
    end
`endif

endmodule
