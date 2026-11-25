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

    wire [NUM_SLAVES:0] f_wr_prio;
    wire [NUM_SLAVES:0] f_rd_prio;
    wire [NUM_SLAVES:0] f_wr_locked;
    wire [NUM_SLAVES:0] f_wr_owner;
    wire [NUM_SLAVES:0] f_rd_locked;
    wire [NUM_SLAVES:0] f_rd_owner;
    wire [NUM_SLAVES:0] f_wr_req0;
    wire [NUM_SLAVES:0] f_wr_req1;
    wire [NUM_SLAVES:0] f_rd_req0;
    wire [NUM_SLAVES:0] f_rd_req1;

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
        .m_axil_rready  (m_axil_rready),
        .f_wr_prio_o    (f_wr_prio),
        .f_rd_prio_o    (f_rd_prio),
        .f_wr_locked_o  (f_wr_locked),
        .f_wr_owner_o   (f_wr_owner),
        .f_rd_locked_o  (f_rd_locked),
        .f_rd_owner_o   (f_rd_owner),
        .f_wr_req0_o    (f_wr_req0),
        .f_wr_req1_o    (f_wr_req1),
        .f_rd_req0_o    (f_rd_req0),
        .f_rd_req1_o    (f_rd_req1)
    );

    // Shared AXI-Lite Protocol Checker on Master Ports (DUT is slave)
    genvar pm;
    generate
        for (pm = 0; pm < NUM_MASTERS; pm = pm + 1) begin : gen_master_props
            axil_props #(
                .ADDR_WIDTH(ADDR_WIDTH),
                .DATA_WIDTH(DATA_WIDTH),
                .STRB_WIDTH(STRB_WIDTH),
                .IS_SLAVE(1)
            ) u_axil_props_m (
                .clk     (clk),
                .rst_n   (rst_n),
                .awaddr  (s_axil_awaddr[pm*ADDR_WIDTH +: ADDR_WIDTH]),
                .awprot  (s_axil_awprot[pm*3 +: 3]),
                .awvalid (s_axil_awvalid[pm]),
                .awready (s_axil_awready[pm]),
                .wdata   (s_axil_wdata[pm*DATA_WIDTH +: DATA_WIDTH]),
                .wstrb   (s_axil_wstrb[pm*STRB_WIDTH +: STRB_WIDTH]),
                .wvalid  (s_axil_wvalid[pm]),
                .wready  (s_axil_wready[pm]),
                .bresp   (s_axil_bresp[pm*2 +: 2]),
                .bvalid  (s_axil_bvalid[pm]),
                .bready  (s_axil_bready[pm]),
                .araddr  (s_axil_araddr[pm*ADDR_WIDTH +: ADDR_WIDTH]),
                .arprot  (s_axil_arprot[pm*3 +: 3]),
                .arvalid (s_axil_arvalid[pm]),
                .arready (s_axil_arready[pm]),
                .rdata   (s_axil_rdata[pm*DATA_WIDTH +: DATA_WIDTH]),
                .rresp   (s_axil_rresp[pm*2 +: 2]),
                .rvalid  (s_axil_rvalid[pm]),
                .rready  (s_axil_rready[pm])
            );
        end
    endgenerate

    // Shared AXI-Lite Protocol Checker on Slave Ports (DUT is master)
    genvar ps;
    generate
        for (ps = 0; ps < NUM_SLAVES; ps = ps + 1) begin : gen_slave_props
            axil_props #(
                .ADDR_WIDTH(ADDR_WIDTH),
                .DATA_WIDTH(DATA_WIDTH),
                .STRB_WIDTH(STRB_WIDTH),
                .IS_SLAVE(0)
            ) u_axil_props_s (
                .clk     (clk),
                .rst_n   (rst_n),
                .awaddr  (m_axil_awaddr[ps*ADDR_WIDTH +: ADDR_WIDTH]),
                .awprot  (m_axil_awprot[ps*3 +: 3]),
                .awvalid (m_axil_awvalid[ps]),
                .awready (m_axil_awready[ps]),
                .wdata   (m_axil_wdata[ps*DATA_WIDTH +: DATA_WIDTH]),
                .wstrb   (m_axil_wstrb[ps*STRB_WIDTH +: STRB_WIDTH]),
                .wvalid  (m_axil_wvalid[ps]),
                .wready  (m_axil_wready[ps]),
                .bresp   (m_axil_bresp[ps*2 +: 2]),
                .bvalid  (m_axil_bvalid[ps]),
                .bready  (m_axil_bready[ps]),
                .araddr  (m_axil_araddr[ps*ADDR_WIDTH +: ADDR_WIDTH]),
                .arprot  (m_axil_arprot[ps*3 +: 3]),
                .arvalid (m_axil_arvalid[ps]),
                .arready (m_axil_arready[ps]),
                .rdata   (m_axil_rdata[ps*DATA_WIDTH +: DATA_WIDTH]),
                .rresp   (m_axil_rresp[ps*2 +: 2]),
                .rvalid  (m_axil_rvalid[ps]),
                .rready  (m_axil_rready[ps])
            );
        end
    endgenerate

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

            // Bounded liveness precondition covers
            cover (f_m_wr_live[0] && s_axil_bvalid[0] && f_m_wr_timer[0] > 0);
            cover (f_m_rd_live[0] && s_axil_rvalid[0] && f_m_rd_timer[0] > 0);
            cover (f_m_wr_live[1] && s_axil_bvalid[1] && f_m_wr_timer[1] > 0);
            cover (f_m_rd_live[1] && s_axil_rvalid[1] && f_m_rd_timer[1] > 0);

            // Round-robin priority rotation covers under contention
            cover (f_wr_prio[1] == 1'b1);
            cover (f_rd_prio[1] == 1'b1);
        end
    end

    // -------------------------------------------------------------
    // Bounded Fairness Verification on Crossbar Inline Arbiters (wr_prio / rd_prio)
    // -------------------------------------------------------------
    genvar ft;
    generate
        for (ft = 0; ft <= NUM_SLAVES; ft = ft + 1) begin : gen_arb_fairness
            reg [1:0] f_wr_other_wins_m0;
            reg [1:0] f_wr_other_wins_m1;
            reg [1:0] f_rd_other_wins_m0;
            reg [1:0] f_rd_other_wins_m1;

            always @(posedge clk) begin
                if (!rst_n) begin
                    f_wr_other_wins_m0 <= 2'd0;
                    f_wr_other_wins_m1 <= 2'd0;
                    f_rd_other_wins_m0 <= 2'd0;
                    f_rd_other_wins_m1 <= 2'd0;
                end else if (f_past_valid && $past(rst_n)) begin
                    // Priority rotation invariant on unlock (B/R completion)
                    if (!f_wr_locked[ft] && $past(f_wr_locked[ft])) begin
                        assert (f_wr_prio[ft] == ~$past(f_wr_owner[ft]));
                    end
                    if (!f_rd_locked[ft] && $past(f_rd_locked[ft])) begin
                        assert (f_rd_prio[ft] == ~$past(f_rd_owner[ft]));
                    end

                    // Contention fairness (WR): while M0 requests target ft, M1 cannot win twice in a row
                    if (!f_wr_req0[ft] || (f_wr_locked[ft] && f_wr_owner[ft] == 1'b0)) begin
                        f_wr_other_wins_m0 <= 2'd0;
                    end else if (!f_wr_locked[ft] && $past(f_wr_locked[ft]) && ($past(f_wr_owner[ft]) != 1'b0)) begin
                        f_wr_other_wins_m0 <= f_wr_other_wins_m0 + 2'd1;
                        assert (f_wr_other_wins_m0 == 2'd0);
                    end

                    if (!f_wr_req1[ft] || (f_wr_locked[ft] && f_wr_owner[ft] == 1'b1)) begin
                        f_wr_other_wins_m1 <= 2'd0;
                    end else if (!f_wr_locked[ft] && $past(f_wr_locked[ft]) && ($past(f_wr_owner[ft]) != 1'b1)) begin
                        f_wr_other_wins_m1 <= f_wr_other_wins_m1 + 2'd1;
                        assert (f_wr_other_wins_m1 == 2'd0);
                    end

                    // Contention fairness (RD): while M0/M1 requests target ft, other master cannot win twice in a row
                    if (!f_rd_req0[ft] || (f_rd_locked[ft] && f_rd_owner[ft] == 1'b0)) begin
                        f_rd_other_wins_m0 <= 2'd0;
                    end else if (!f_rd_locked[ft] && $past(f_rd_locked[ft]) && ($past(f_rd_owner[ft]) != 1'b0)) begin
                        f_rd_other_wins_m0 <= f_rd_other_wins_m0 + 2'd1;
                        assert (f_rd_other_wins_m0 == 2'd0);
                    end

                    if (!f_rd_req1[ft] || (f_rd_locked[ft] && f_rd_owner[ft] == 1'b1)) begin
                        f_rd_other_wins_m1 <= 2'd0;
                    end else if (!f_rd_locked[ft] && $past(f_rd_locked[ft]) && ($past(f_rd_owner[ft]) != 1'b1)) begin
                        f_rd_other_wins_m1 <= f_rd_other_wins_m1 + 2'd1;
                        assert (f_rd_other_wins_m1 == 2'd0);
                    end
                end
            end
        end
    endgenerate

    // -------------------------------------------------------------
    // Bounded Liveness Verification (without over-constraining WVALID)
    // -------------------------------------------------------------
    reg [2:0] f_s_bresp_wait [NUM_SLAVES-1:0];
    reg [2:0] f_s_rresp_wait [NUM_SLAVES-1:0];
    reg [NUM_SLAVES-1:0] f_s_aw_done;
    reg [NUM_SLAVES-1:0] f_s_w_done;
    reg [NUM_SLAVES-1:0] f_s_ar_done;
    reg [2:0] f_m_bready_wait [NUM_MASTERS-1:0];
    reg [2:0] f_m_rready_wait [NUM_MASTERS-1:0];

    integer si, mi;
    always @(posedge clk) begin
        if (!rst_n) begin
            f_s_aw_done <= {NUM_SLAVES{1'b0}};
            f_s_w_done  <= {NUM_SLAVES{1'b0}};
            f_s_ar_done <= {NUM_SLAVES{1'b0}};
            for (si = 0; si < NUM_SLAVES; si = si + 1) begin
                f_s_bresp_wait[si] <= 3'd0;
                f_s_rresp_wait[si] <= 3'd0;
            end
            for (mi = 0; mi < NUM_MASTERS; mi = mi + 1) begin
                f_m_bready_wait[mi] <= 3'd0;
                f_m_rready_wait[mi] <= 3'd0;
            end
        end else begin
            for (si = 0; si < NUM_SLAVES; si = si + 1) begin
                // Track committed AW and W handshakes on slave port si so BVALID is only
                // expected after BOTH AW and W have completed.
                if (m_axil_awvalid[si] && m_axil_awready[si]) f_s_aw_done[si] <= 1'b1;
                if (m_axil_wvalid[si]  && m_axil_wready[si])  f_s_w_done[si]  <= 1'b1;

                if (m_axil_bvalid[si] && m_axil_bready[si]) begin
                    f_s_aw_done[si]    <= 1'b0;
                    f_s_w_done[si]     <= 1'b0;
                    f_s_bresp_wait[si] <= 3'd0;
                end else if ((f_s_aw_done[si] || (m_axil_awvalid[si] && m_axil_awready[si])) &&
                             (f_s_w_done[si]  || (m_axil_wvalid[si]  && m_axil_wready[si]))) begin
                    f_s_bresp_wait[si] <= f_s_bresp_wait[si] + 1'b1;
                end else begin
                    f_s_bresp_wait[si] <= 3'd0;
                end

                // Track committed AR handshake on slave port si
                if (m_axil_arvalid[si] && m_axil_arready[si]) f_s_ar_done[si] <= 1'b1;

                if (m_axil_rvalid[si] && m_axil_rready[si]) begin
                    f_s_ar_done[si]    <= 1'b0;
                    f_s_rresp_wait[si] <= 3'd0;
                end else if (f_s_ar_done[si] || (m_axil_arvalid[si] && m_axil_arready[si])) begin
                    f_s_rresp_wait[si] <= f_s_rresp_wait[si] + 1'b1;
                end else begin
                    f_s_rresp_wait[si] <= 3'd0;
                end
            end
            for (mi = 0; mi < NUM_MASTERS; mi = mi + 1) begin
                if (s_axil_bvalid[mi] && !s_axil_bready[mi]) f_m_bready_wait[mi] <= f_m_bready_wait[mi] + 1'b1;
                else f_m_bready_wait[mi] <= 3'd0;

                if (s_axil_rvalid[mi] && !s_axil_rready[mi]) f_m_rready_wait[mi] <= f_m_rready_wait[mi] + 1'b1;
                else f_m_rready_wait[mi] <= 3'd0;
            end
        end
    end

    // Slaves must respond within 3 cycles, masters must accept within 3 cycles
    always @(*) begin
        for (si = 0; si < NUM_SLAVES; si = si + 1) begin
            if (f_s_bresp_wait[si] >= 3'd3) assume (m_axil_bvalid[si]);
            if (f_s_rresp_wait[si] >= 3'd3) assume (m_axil_rvalid[si]);
        end
        for (mi = 0; mi < NUM_MASTERS; mi = mi + 1) begin
            if (f_m_bready_wait[mi] >= 3'd3) assume (s_axil_bready[mi]);
            if (f_m_rready_wait[mi] >= 3'd3) assume (s_axil_rready[mi]);
        end
    end

    // Master bounded liveness: response within 16 cycles
    reg [NUM_MASTERS-1:0] f_m_aw_seen;
    reg [NUM_MASTERS-1:0] f_m_w_seen;
    reg [NUM_MASTERS-1:0] f_m_wr_live;
    reg [4:0]             f_m_wr_timer [NUM_MASTERS-1:0];
    reg [NUM_MASTERS-1:0] f_m_rd_live;
    reg [4:0]             f_m_rd_timer [NUM_MASTERS-1:0];

    always @(posedge clk) begin
        if (!rst_n) begin
            f_m_aw_seen <= {NUM_MASTERS{1'b0}};
            f_m_w_seen  <= {NUM_MASTERS{1'b0}};
            f_m_wr_live <= {NUM_MASTERS{1'b0}};
            f_m_rd_live <= {NUM_MASTERS{1'b0}};
            for (mi = 0; mi < NUM_MASTERS; mi = mi + 1) begin
                f_m_wr_timer[mi] <= 5'd0;
                f_m_rd_timer[mi] <= 5'd0;
            end
        end else begin
            for (mi = 0; mi < NUM_MASTERS; mi = mi + 1) begin
                if (s_axil_awvalid[mi] && s_axil_awready[mi]) f_m_aw_seen[mi] <= 1'b1;
                if (s_axil_wvalid[mi]  && s_axil_wready[mi])  f_m_w_seen[mi]  <= 1'b1;

                if ((f_m_aw_seen[mi] || (s_axil_awvalid[mi] && s_axil_awready[mi])) &&
                    (f_m_w_seen[mi]  || (s_axil_wvalid[mi]  && s_axil_wready[mi])) &&
                    !f_m_wr_live[mi] && !(s_axil_bvalid[mi] && s_axil_bready[mi])) begin
                    f_m_wr_live[mi]  <= 1'b1;
                    f_m_wr_timer[mi] <= 5'd0;
                end else if (f_m_wr_live[mi]) begin
                    if (s_axil_bvalid[mi] && s_axil_bready[mi]) begin
                        f_m_wr_live[mi]  <= 1'b0;
                        f_m_wr_timer[mi] <= 5'd0;
                        f_m_aw_seen[mi]  <= 1'b0;
                        f_m_w_seen[mi]   <= 1'b0;
                    end else begin
                        f_m_wr_timer[mi] <= f_m_wr_timer[mi] + 1'b1;
                        assert (f_m_wr_timer[mi] < 5'd18);
                    end
                end else if (s_axil_bvalid[mi] && s_axil_bready[mi]) begin
                    f_m_aw_seen[mi] <= 1'b0;
                    f_m_w_seen[mi]  <= 1'b0;
                end

                if (s_axil_arvalid[mi] && s_axil_arready[mi]) begin
                    f_m_rd_live[mi]  <= 1'b1;
                    f_m_rd_timer[mi] <= 5'd0;
                end else if (f_m_rd_live[mi]) begin
                    if (s_axil_rvalid[mi] && s_axil_rready[mi]) begin
                        f_m_rd_live[mi]  <= 1'b0;
                        f_m_rd_timer[mi] <= 5'd0;
                    end else begin
                        f_m_rd_timer[mi] <= f_m_rd_timer[mi] + 1'b1;
                        assert (f_m_rd_timer[mi] < 5'd18);
                    end
                end
            end
        end
    end

endmodule
