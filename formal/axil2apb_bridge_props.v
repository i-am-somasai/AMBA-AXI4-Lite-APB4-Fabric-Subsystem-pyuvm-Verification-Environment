// formal/axil2apb_bridge_props.v
// Formal property specification for axil2apb_bridge
`timescale 1ns / 1ps

module axil2apb_bridge_props #(
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 32,
    parameter STRB_WIDTH = DATA_WIDTH / 8
)(
    input wire                  clk,
    input wire                  rst_n,

    // AXI4-Lite Slave Interface
    input wire [ADDR_WIDTH-1:0] s_axil_awaddr,
    input wire [2:0]            s_axil_awprot,
    input wire                  s_axil_awvalid,
    output wire                 s_axil_awready,

    input wire [DATA_WIDTH-1:0] s_axil_wdata,
    input wire [STRB_WIDTH-1:0] s_axil_wstrb,
    input wire                  s_axil_wvalid,
    output wire                 s_axil_wready,

    output wire [1:0]           s_axil_bresp,
    output wire                 s_axil_bvalid,
    input wire                  s_axil_bready,

    input wire [ADDR_WIDTH-1:0] s_axil_araddr,
    input wire [2:0]            s_axil_arprot,
    input wire                  s_axil_arvalid,
    output wire                 s_axil_arready,

    output wire [DATA_WIDTH-1:0] s_axil_rdata,
    output wire [1:0]           s_axil_rresp,
    output wire                 s_axil_rvalid,
    input wire                  s_axil_rready,

    // APB4 Master Interface
    output wire [ADDR_WIDTH-1:0] m_apb_paddr,
    output wire [2:0]           m_apb_pprot,
    output wire                 m_apb_psel,
    output wire                 m_apb_penable,
    output wire                 m_apb_pwrite,
    output wire [DATA_WIDTH-1:0] m_apb_pwdata,
    output wire [STRB_WIDTH-1:0] m_apb_pstrb,
    input wire                  m_apb_pready,
    input wire [DATA_WIDTH-1:0] m_apb_prdata,
    input wire                  m_apb_pslverr
);

    // Instantiate DUT
    axil2apb_bridge #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
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
        .m_apb_paddr    (m_apb_paddr),
        .m_apb_pprot    (m_apb_pprot),
        .m_apb_psel     (m_apb_psel),
        .m_apb_penable  (m_apb_penable),
        .m_apb_pwrite   (m_apb_pwrite),
        .m_apb_pwdata   (m_apb_pwdata),
        .m_apb_pstrb    (m_apb_pstrb),
        .m_apb_pready   (m_apb_pready),
        .m_apb_prdata   (m_apb_prdata),
        .m_apb_pslverr  (m_apb_pslverr)
    );

    // Shared AXI4-Lite Protocol Checker
    axil_props #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH),
        .STRB_WIDTH(STRB_WIDTH),
        .IS_SLAVE(1)
    ) u_axil_props (
        .clk     (clk),
        .rst_n   (rst_n),
        .awaddr  (s_axil_awaddr),
        .awprot  (s_axil_awprot),
        .awvalid (s_axil_awvalid),
        .awready (s_axil_awready),
        .wdata   (s_axil_wdata),
        .wstrb   (s_axil_wstrb),
        .wvalid  (s_axil_wvalid),
        .wready  (s_axil_wready),
        .bresp   (s_axil_bresp),
        .bvalid  (s_axil_bvalid),
        .bready  (s_axil_bready),
        .araddr  (s_axil_araddr),
        .arprot  (s_axil_arprot),
        .arvalid (s_axil_arvalid),
        .arready (s_axil_arready),
        .rdata   (s_axil_rdata),
        .rresp   (s_axil_rresp),
        .rvalid  (s_axil_rvalid),
        .rready  (s_axil_rready)
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
    end

    // Master assumptions (AXI4-Lite handshake rules)
    always @(posedge clk) begin
        if (f_past_valid && $past(rst_n) && rst_n) begin
            if ($past(s_axil_awvalid) && !$past(s_axil_awready)) begin
                assume (s_axil_awvalid);
                assume (s_axil_awaddr == $past(s_axil_awaddr));
                assume (s_axil_awprot == $past(s_axil_awprot));
            end
            if ($past(s_axil_wvalid) && !$past(s_axil_wready)) begin
                assume (s_axil_wvalid);
                assume (s_axil_wdata == $past(s_axil_wdata));
                assume (s_axil_wstrb == $past(s_axil_wstrb));
            end
            if ($past(s_axil_arvalid) && !$past(s_axil_arready)) begin
                assume (s_axil_arvalid);
                assume (s_axil_araddr == $past(s_axil_araddr));
                assume (s_axil_arprot == $past(s_axil_arprot));
            end
        end
    end

    // Do not issue simultaneous read and write (bridge handles write or read sequentially)
    always @(*) begin
        if (s_axil_awvalid || s_axil_wvalid)
            assume (!s_axil_arvalid);
    end

    // -------------------------------------------------------------
    // Formal Invariants and Assertions
    // -------------------------------------------------------------
    always @(posedge clk) begin
        if (!rst_n) begin
            assert (!m_apb_psel);
            assert (!m_apb_penable);
            assert (!s_axil_bvalid);
            assert (!s_axil_rvalid);
        end else begin
            // 1. APB Protocol: PENABLE only high when PSEL is high
            assert (!m_apb_penable || m_apb_psel);

            if (f_past_valid && $past(rst_n)) begin
                // 2. PENABLE is high only following a cycle where PSEL was high
                if (m_apb_penable && !$past(m_apb_penable)) begin
                    assert ($past(m_apb_psel) && !$past(m_apb_penable));
                end

                // 3. APB stability during wait states (PENABLE=1 && PREADY=0)
                if ($past(m_apb_psel) && $past(m_apb_penable) && !$past(m_apb_pready)) begin
                    assert (m_apb_psel);
                    assert (m_apb_penable);
                    assert (m_apb_paddr  == $past(m_apb_paddr));
                    assert (m_apb_pprot  == $past(m_apb_pprot));
                    assert (m_apb_pwrite == $past(m_apb_pwrite));
                    assert (m_apb_pwdata == $past(m_apb_pwdata));
                    assert (m_apb_pstrb  == $past(m_apb_pstrb));
                end

                // 4. APB transfer completion: PSEL and PENABLE drop next cycle
                if ($past(m_apb_psel) && $past(m_apb_penable) && $past(m_apb_pready)) begin
                    assert (!m_apb_penable);
                end

                // 5. PSLVERR translation: PSLVERR produces SLVERR (2'b10)
                if ($past(m_apb_psel) && $past(m_apb_penable) && $past(m_apb_pready)) begin
                    if ($past(m_apb_pwrite)) begin
                        assert (s_axil_bvalid);
                        assert (s_axil_bresp == ($past(m_apb_pslverr) ? 2'b10 : 2'b00));
                    end else begin
                        assert (s_axil_rvalid);
                        assert (s_axil_rresp == ($past(m_apb_pslverr) ? 2'b10 : 2'b00));
                        assert (s_axil_rdata == $past(m_apb_prdata));
                    end
                end

                // 6. AXI stability
                if ($past(s_axil_bvalid) && !$past(s_axil_bready)) begin
                    assert (s_axil_bvalid);
                    assert (s_axil_bresp == $past(s_axil_bresp));
                end
                if ($past(s_axil_rvalid) && !$past(s_axil_rready)) begin
                    assert (s_axil_rvalid);
                    assert (s_axil_rresp == $past(s_axil_rresp));
                    assert (s_axil_rdata == $past(s_axil_rdata));
                end
            end
        end
    end

    // -------------------------------------------------------------
    // Bounded Liveness Properties
    // Under fair slave (PREADY asserted within N cycles) and fair master
    // (BREADY/RREADY asserted within N cycles), every accepted request
    // receives its response within M cycles.
    // -------------------------------------------------------------
    reg [3:0] f_bready_wait = 0;
    reg [3:0] f_rready_wait = 0;
    reg [3:0] f_pready_wait = 0;

    always @(posedge clk) begin
        if (!rst_n) begin
            f_bready_wait <= 4'd0;
            f_rready_wait <= 4'd0;
            f_pready_wait <= 4'd0;
        end else begin
            if (s_axil_bvalid && !s_axil_bready) f_bready_wait <= f_bready_wait + 1'b1;
            else f_bready_wait <= 4'd0;

            if (s_axil_rvalid && !s_axil_rready) f_rready_wait <= f_rready_wait + 1'b1;
            else f_rready_wait <= 4'd0;

            if (m_apb_psel && m_apb_penable && !m_apb_pready) f_pready_wait <= f_pready_wait + 1'b1;
            else f_pready_wait <= 4'd0;
        end
    end

    always @(*) begin
        if (f_bready_wait >= 4'd4) assume (s_axil_bready);
        if (f_rready_wait >= 4'd4) assume (s_axil_rready);
        if (f_pready_wait >= 4'd4) assume (m_apb_pready);
    end

    reg f_aw_seen = 0;
    reg f_w_seen  = 0;
    reg       f_wr_live_active = 0;
    reg [3:0] f_wr_live_timer  = 0;
    reg       f_rd_live_active = 0;
    reg [3:0] f_rd_live_timer  = 0;

    wire f_wr_committed = (f_aw_seen || (s_axil_awvalid && s_axil_awready)) &&
                          (f_w_seen  || (s_axil_wvalid  && s_axil_wready));

    always @(posedge clk) begin
        if (!rst_n) begin
            f_aw_seen        <= 1'b0;
            f_w_seen         <= 1'b0;
            f_wr_live_active <= 1'b0;
            f_wr_live_timer  <= 4'd0;
            f_rd_live_active <= 1'b0;
            f_rd_live_timer  <= 4'd0;
        end else begin
            if (s_axil_awvalid && s_axil_awready) f_aw_seen <= 1'b1;
            if (s_axil_wvalid  && s_axil_wready)  f_w_seen  <= 1'b1;

            // Write bounded liveness starts when BOTH AW and W handshakes are committed
            if (f_wr_committed && !f_wr_live_active && !(s_axil_bvalid && s_axil_bready)) begin
                f_wr_live_active <= 1'b1;
                f_wr_live_timer  <= 4'd0;
            end else if (f_wr_live_active) begin
                if (s_axil_bvalid && s_axil_bready) begin
                    f_wr_live_active <= 1'b0;
                    f_wr_live_timer  <= 4'd0;
                    f_aw_seen        <= 1'b0;
                    f_w_seen         <= 1'b0;
                end else begin
                    f_wr_live_timer <= f_wr_live_timer + 1'b1;
                    assert (f_wr_live_timer < 4'd12);
                end
            end else if (s_axil_bvalid && s_axil_bready) begin
                f_aw_seen <= 1'b0;
                f_w_seen  <= 1'b0;
            end

            // Read bounded liveness
            if (s_axil_arvalid && s_axil_arready) begin
                f_rd_live_active <= 1'b1;
                f_rd_live_timer  <= 4'd0;
            end else if (f_rd_live_active) begin
                if (s_axil_rvalid && s_axil_rready) begin
                    f_rd_live_active <= 1'b0;
                    f_rd_live_timer  <= 4'd0;
                end else begin
                    f_rd_live_timer <= f_rd_live_timer + 1'b1;
                    assert (f_rd_live_timer < 4'd12);
                end
            end
        end
    end

    // -------------------------------------------------------------
    // Cover scenarios
    // -------------------------------------------------------------
    always @(posedge clk) begin
        if (rst_n && f_past_valid) begin
            // Bounded liveness precondition covers
            cover (f_wr_live_active && s_axil_bvalid && f_wr_live_timer > 0);
            cover (f_rd_live_active && s_axil_rvalid && f_rd_live_timer > 0);
            // 0 wait-state write transfer
            cover (m_apb_psel && m_apb_penable && m_apb_pready && m_apb_pwrite);
            // 0 wait-state read transfer
            cover (m_apb_psel && m_apb_penable && m_apb_pready && !m_apb_pwrite);
            // APB wait state (PREADY=0 during access phase)
            cover (m_apb_psel && m_apb_penable && !m_apb_pready);
            // PSLVERR on write returning SLVERR
            cover (s_axil_bvalid && s_axil_bresp == 2'b10);
            // PSLVERR on read returning SLVERR
            cover (s_axil_rvalid && s_axil_rresp == 2'b10);
        end
    end

endmodule
