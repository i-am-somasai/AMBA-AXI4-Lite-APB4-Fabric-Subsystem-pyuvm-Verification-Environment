// formal/axil_xbar_props.v
// Formal property specification for axil_xbar
`timescale 1ns / 1ps

module axil_xbar_props #(
    parameter DATA_WIDTH  = 32,
    parameter ADDR_WIDTH  = 32,
    parameter STRB_WIDTH  = DATA_WIDTH / 8,
    parameter NUM_MASTERS = 2,
    parameter NUM_SLAVES  = 4
)(
    input wire                                clk,
    input wire                                rst_n,

    // Master Ports
    input  wire [NUM_MASTERS*ADDR_WIDTH-1:0]   s_axil_awaddr,
    input  wire [NUM_MASTERS*3-1:0]            s_axil_awprot,
    input  wire [NUM_MASTERS-1:0]              s_axil_awvalid,
    output wire [NUM_MASTERS-1:0]              s_axil_awready,

    input  wire [NUM_MASTERS*DATA_WIDTH-1:0]   s_axil_wdata,
    input  wire [NUM_MASTERS*STRB_WIDTH-1:0]   s_axil_wstrb,
    input  wire [NUM_MASTERS-1:0]              s_axil_wvalid,
    output wire [NUM_MASTERS-1:0]              s_axil_wready,

    output wire [NUM_MASTERS*2-1:0]            s_axil_bresp,
    output wire [NUM_MASTERS-1:0]              s_axil_bvalid,
    input  wire [NUM_MASTERS-1:0]              s_axil_bready,

    input  wire [NUM_MASTERS*ADDR_WIDTH-1:0]   s_axil_araddr,
    input  wire [NUM_MASTERS*3-1:0]            s_axil_arprot,
    input  wire [NUM_MASTERS-1:0]              s_axil_arvalid,
    output wire [NUM_MASTERS-1:0]              s_axil_arready,

    output wire [NUM_MASTERS*DATA_WIDTH-1:0]   s_axil_rdata,
    output wire [NUM_MASTERS*2-1:0]            s_axil_rresp,
    output wire [NUM_MASTERS-1:0]              s_axil_rvalid,
    input  wire [NUM_MASTERS-1:0]              s_axil_rready,

    // Slave Ports
    output wire [NUM_SLAVES*ADDR_WIDTH-1:0]    m_axil_awaddr,
    output wire [NUM_SLAVES*3-1:0]             m_axil_awprot,
    output wire [NUM_SLAVES-1:0]               m_axil_awvalid,
    input  wire [NUM_SLAVES-1:0]               m_axil_awready,

    output wire [NUM_SLAVES*DATA_WIDTH-1:0]    m_axil_wdata,
    output wire [NUM_SLAVES*STRB_WIDTH-1:0]    m_axil_wstrb,
    output wire [NUM_SLAVES-1:0]               m_axil_wvalid,
    input  wire [NUM_SLAVES-1:0]               m_axil_wready,

    input  wire [NUM_SLAVES*2-1:0]             m_axil_bresp,
    input  wire [NUM_SLAVES-1:0]               m_axil_bvalid,
    output wire [NUM_SLAVES-1:0]               m_axil_bready,

    output wire [NUM_SLAVES*ADDR_WIDTH-1:0]    m_axil_araddr,
    output wire [NUM_SLAVES*3-1:0]             m_axil_arprot,
    output wire [NUM_SLAVES-1:0]               m_axil_arvalid,
    input  wire [NUM_SLAVES-1:0]               m_axil_arready,

    input  wire [NUM_SLAVES*DATA_WIDTH-1:0]    m_axil_rdata,
    input  wire [NUM_SLAVES*2-1:0]             m_axil_rresp,
    input  wire [NUM_SLAVES-1:0]               m_axil_rvalid,
    output wire [NUM_SLAVES-1:0]               m_axil_rready
);

    // Instantiate DUT
    axil_xbar #(
        .DATA_WIDTH (DATA_WIDTH),
        .ADDR_WIDTH (ADDR_WIDTH),
        .STRB_WIDTH (STRB_WIDTH),
        .NUM_MASTERS(NUM_MASTERS),
        .NUM_SLAVES (NUM_SLAVES)
    ) dut (
        .clk            (clk),
        .rst_n          (rst_n),
        .s_axil_awaddr  (s_axil_awaddr),
        .s_axil_awprot  (s_axil_awprot),
        .s_axil_awvalid (s_axil_awvalid),
        .s_axil_awready (s_axil_awready),
        .s_axil_wdata   (s_axil_wdata),
        .s_axil_wstrb   (s_axil_wstrb),
        .s_axil_wvalid  (s_axil_wvalid),
        .s_axil_wready  (s_axil_wready),
        .s_axil_bresp   (s_axil_bresp),
        .s_axil_bvalid  (s_axil_bvalid),
        .s_axil_bready  (s_axil_bready),
        .s_axil_araddr  (s_axil_araddr),
        .s_axil_arprot  (s_axil_arprot),
        .s_axil_arvalid (s_axil_arvalid),
        .s_axil_arready (s_axil_arready),
        .s_axil_rdata   (s_axil_rdata),
        .s_axil_rresp   (s_axil_rresp),
        .s_axil_rvalid  (s_axil_rvalid),
        .s_axil_rready  (s_axil_rready),
        .m_axil_awaddr  (m_axil_awaddr),
        .m_axil_awprot  (m_axil_awprot),
        .m_axil_awvalid (m_axil_awvalid),
        .m_axil_awready (m_axil_awready),
        .m_axil_wdata   (m_axil_wdata),
        .m_axil_wstrb   (m_axil_wstrb),
        .m_axil_wvalid  (m_axil_wvalid),
        .m_axil_wready  (m_axil_wready),
        .m_axil_bresp   (m_axil_bresp),
        .m_axil_bvalid  (m_axil_bvalid),
        .m_axil_bready  (m_axil_bready),
        .m_axil_araddr  (m_axil_araddr),
        .m_axil_arprot  (m_axil_arprot),
        .m_axil_arvalid (m_axil_arvalid),
        .m_axil_arready (m_axil_arready),
        .m_axil_rdata   (m_axil_rdata),
        .m_axil_rresp   (m_axil_rresp),
        .m_axil_rvalid  (m_axil_rvalid),
        .m_axil_rready  (m_axil_rready)
    );

    // Initial reset assumptions
    reg f_past_valid;
    initial f_past_valid = 1'b0;

    always @(posedge clk) begin
        f_past_valid <= 1'b1;
    end

    always @(*) begin
        if (!f_past_valid)
            assume (!rst_n);
        else
            assume (rst_n);

        if (!rst_n) begin
            assume (s_axil_awvalid == {NUM_MASTERS{1'b0}});
            assume (s_axil_wvalid  == {NUM_MASTERS{1'b0}});
            assume (s_axil_arvalid == {NUM_MASTERS{1'b0}});
            assume (m_axil_bvalid  == {NUM_SLAVES{1'b0}});
            assume (m_axil_rvalid  == {NUM_SLAVES{1'b0}});
        end
    end

    // Master assumptions
    genvar m;
    generate
        for (m = 0; m < NUM_MASTERS; m = m + 1) begin : gen_m_assumptions
            always @(posedge clk) begin
                if (f_past_valid && $past(rst_n) && rst_n) begin
                    // AW channel stability
                    if ($past(s_axil_awvalid[m]) && !$past(s_axil_awready[m])) begin
                        assume (s_axil_awvalid[m]);
                        assume (s_axil_awaddr[m*ADDR_WIDTH +: ADDR_WIDTH] == $past(s_axil_awaddr[m*ADDR_WIDTH +: ADDR_WIDTH]));
                        assume (s_axil_awprot[m*3 +: 3] == $past(s_axil_awprot[m*3 +: 3]));
                    end
                    // W channel stability
                    if ($past(s_axil_wvalid[m]) && !$past(s_axil_wready[m])) begin
                        assume (s_axil_wvalid[m]);
                        assume (s_axil_wdata[m*DATA_WIDTH +: DATA_WIDTH] == $past(s_axil_wdata[m*DATA_WIDTH +: DATA_WIDTH]));
                        assume (s_axil_wstrb[m*STRB_WIDTH +: STRB_WIDTH] == $past(s_axil_wstrb[m*STRB_WIDTH +: STRB_WIDTH]));
                    end
                    // AR channel stability
                    if ($past(s_axil_arvalid[m]) && !$past(s_axil_arready[m])) begin
                        assume (s_axil_arvalid[m]);
                        assume (s_axil_araddr[m*ADDR_WIDTH +: ADDR_WIDTH] == $past(s_axil_araddr[m*ADDR_WIDTH +: ADDR_WIDTH]));
                        assume (s_axil_arprot[m*3 +: 3] == $past(s_axil_arprot[m*3 +: 3]));
                    end
                end
            end
        end
    endgenerate

    // Slave assumptions: well-behaved responders
    genvar s;
    generate
        for (s = 0; s < NUM_SLAVES; s = s + 1) begin : gen_s_assumptions
            always @(posedge clk) begin
                if (f_past_valid && $past(rst_n) && rst_n) begin
                    // B channel stability
                    if ($past(m_axil_bvalid[s]) && !$past(m_axil_bready[s])) begin
                        assume (m_axil_bvalid[s]);
                        assume (m_axil_bresp[s*2 +: 2] == $past(m_axil_bresp[s*2 +: 2]));
                    end
                    // R channel stability
                    if ($past(m_axil_rvalid[s]) && !$past(m_axil_rready[s])) begin
                        assume (m_axil_rvalid[s]);
                        assume (m_axil_rdata[s*DATA_WIDTH +: DATA_WIDTH] == $past(m_axil_rdata[s*DATA_WIDTH +: DATA_WIDTH]));
                        assume (m_axil_rresp[s*2 +: 2] == $past(m_axil_rresp[s*2 +: 2]));
                    end
                end
            end

            // Legal response codes from slaves
            always @(*) begin
                if (m_axil_bvalid[s]) assume (m_axil_bresp[s*2 +: 2] != 2'b01);
                if (m_axil_rvalid[s]) assume (m_axil_rresp[s*2 +: 2] != 2'b01);
            end
        end
    endgenerate

    // -------------------------------------------------------------
    // Formal Invariants and Assertions
    // -------------------------------------------------------------
    always @(posedge clk) begin
        if (!rst_n) begin
            assert (s_axil_bvalid == {NUM_MASTERS{1'b0}});
            assert (s_axil_rvalid == {NUM_MASTERS{1'b0}});
            assert (m_axil_awvalid == {NUM_SLAVES{1'b0}});
            assert (m_axil_wvalid == {NUM_SLAVES{1'b0}});
            assert (m_axil_arvalid == {NUM_SLAVES{1'b0}});
        end else begin
            // 1. Response validity: response codes never EXOKAY (2'b01)
            if (s_axil_bvalid[0]) assert (s_axil_bresp[1:0] != 2'b01);
            if (s_axil_bvalid[1]) assert (s_axil_bresp[3:2] != 2'b01);
            if (s_axil_rvalid[0]) assert (s_axil_rresp[1:0] != 2'b01);
            if (s_axil_rvalid[1]) assert (s_axil_rresp[3:2] != 2'b01);

            // 2. Decode isolation: Master 0 targeting S1 (RAM 0x5000_0000) only activates S1
            if (s_axil_awvalid[0] && (s_axil_awaddr[31:16] == 16'h5000) && !s_axil_awvalid[1]) begin
                assert (!m_axil_awvalid[0]); // Not APB
                assert (!m_axil_awvalid[2]); // Not CSR
                assert (!m_axil_awvalid[3]); // Not CDC
            end

            // 3. Decode isolation: Master 1 targeting S2 (CSR 0x6000_0000) only activates S2
            if (s_axil_awvalid[1] && (s_axil_awaddr[63:48] == 16'h6000) && !s_axil_awvalid[0]) begin
                assert (!m_axil_awvalid[0]); // Not APB
                assert (!m_axil_awvalid[1]); // Not RAM
                assert (!m_axil_awvalid[3]); // Not CDC
            end

            // 4. Default slave isolation: Unmapped addresses (e.g. 0x1000_xxxx) never assert external slaves
            if (s_axil_awvalid[0] && (s_axil_awaddr[31:28] == 4'h1) && !s_axil_awvalid[1]) begin
                assert (m_axil_awvalid == 4'b0000);
            end
            if (s_axil_arvalid[0] && (s_axil_araddr[31:28] == 4'h1) && !s_axil_arvalid[1]) begin
                assert (m_axil_arvalid == 4'b0000);
            end

            // 5. Response stability
            if (f_past_valid && $past(rst_n)) begin
                if ($past(s_axil_bvalid[0]) && !$past(s_axil_bready[0])) begin
                    assert (s_axil_bvalid[0]);
                    assert (s_axil_bresp[1:0] == $past(s_axil_bresp[1:0]));
                end
                if ($past(s_axil_bvalid[1]) && !$past(s_axil_bready[1])) begin
                    assert (s_axil_bvalid[1]);
                    assert (s_axil_bresp[3:2] == $past(s_axil_bresp[3:2]));
                end
                if ($past(s_axil_rvalid[0]) && !$past(s_axil_rready[0])) begin
                    assert (s_axil_rvalid[0]);
                    assert (s_axil_rresp[1:0] == $past(s_axil_rresp[1:0]));
                    assert (s_axil_rdata[31:0] == $past(s_axil_rdata[31:0]));
                end
                if ($past(s_axil_rvalid[1]) && !$past(s_axil_rready[1])) begin
                    assert (s_axil_rvalid[1]);
                    assert (s_axil_rresp[3:2] == $past(s_axil_rresp[3:2]));
                    assert (s_axil_rdata[63:32] == $past(s_axil_rdata[63:32]));
                end
            end
        end
    end

    // -------------------------------------------------------------
    // Cover Scenarios
    // -------------------------------------------------------------
    always @(posedge clk) begin
        if (rst_n && f_past_valid) begin
            // Contention: both masters assert AW targeting S1 RAM simultaneously
            cover (s_axil_awvalid[0] && (s_axil_awaddr[31:16] == 16'h5000) &&
                   s_axil_awvalid[1] && (s_axil_awaddr[63:48] == 16'h5000));

            // Parallel write: M0 writes S1 RAM while M1 writes S2 CSR
            cover (m_axil_awvalid[1] && m_axil_awvalid[2]);

            // Parallel mixed: M0 writes S1 RAM while M1 reads S2 CSR
            cover (m_axil_awvalid[1] && m_axil_arvalid[2]);

            // Unmapped address yields DECERR (2'b11) to M0
            cover (s_axil_bvalid[0] && s_axil_bresp[1:0] == 2'b11);
            cover (s_axil_rvalid[0] && s_axil_rresp[1:0] == 2'b11);
        end
    end

endmodule
