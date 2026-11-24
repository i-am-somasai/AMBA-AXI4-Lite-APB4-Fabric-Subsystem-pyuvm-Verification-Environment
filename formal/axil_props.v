// formal/axil_props.v
// Shared AXI4-Lite Protocol Property Checker
// Checks handshake stability, response causality, and protocol conformance.
// Parameter IS_SLAVE:
//   1: DUT is Slave  -> Assumes master inputs (AW/W/AR), asserts slave responses (B/R, ready).
//   0: DUT is Master -> Assumes slave responses (B/R), asserts master requests (AW/W/AR).
`timescale 1ns / 1ps

module axil_props #(
    parameter ADDR_WIDTH          = 32,
    parameter DATA_WIDTH          = 32,
    parameter STRB_WIDTH          = DATA_WIDTH / 8,
    parameter IS_SLAVE            = 1,
    parameter SINGLE_OUTSTANDING  = 1,
    parameter CHECK_CAUSALITY     = 1
)(
    input wire                  clk,
    input wire                  rst_n,

    // Write Address Channel
    input wire [ADDR_WIDTH-1:0] awaddr,
    input wire [2:0]            awprot,
    input wire                  awvalid,
    input wire                  awready,

    // Write Data Channel
    input wire [DATA_WIDTH-1:0] wdata,
    input wire [STRB_WIDTH-1:0] wstrb,
    input wire                  wvalid,
    input wire                  wready,

    // Write Response Channel
    input wire [1:0]            bresp,
    input wire                  bvalid,
    input wire                  bready,

    // Read Address Channel
    input wire [ADDR_WIDTH-1:0] araddr,
    input wire [2:0]            arprot,
    input wire                  arvalid,
    input wire                  arready,

    // Read Data Channel
    input wire [DATA_WIDTH-1:0] rdata,
    input wire [1:0]            rresp,
    input wire                  rvalid,
    input wire                  rready
);

`ifdef FORMAL
    reg f_past_valid;
    initial f_past_valid = 1'b0;

    always @(posedge clk) begin
        f_past_valid <= 1'b1;
    end

    // -------------------------------------------------------------
    // 1. Handshake Stability Rules
    // Once VALID is asserted, payload and VALID must remain stable
    // until READY is asserted by the receiver.
    // -------------------------------------------------------------
    always @(posedge clk) begin
        if (f_past_valid && $past(rst_n) && rst_n) begin
            // Master-driven channels (AW, W, AR)
            if ($past(awvalid) && !$past(awready)) begin
                if (IS_SLAVE) begin
                    assume(awvalid);
                    assume(awaddr == $past(awaddr));
                    assume(awprot == $past(awprot));
                end else begin
                    assert(awvalid);
                    assert(awaddr == $past(awaddr));
                    assert(awprot == $past(awprot));
                end
            end

            if ($past(wvalid) && !$past(wready)) begin
                if (IS_SLAVE) begin
                    assume(wvalid);
                    assume(wdata == $past(wdata));
                    assume(wstrb == $past(wstrb));
                end else begin
                    assert(wvalid);
                    assert(wdata == $past(wdata));
                    assert(wstrb == $past(wstrb));
                end
            end

            if ($past(arvalid) && !$past(arready)) begin
                if (IS_SLAVE) begin
                    assume(arvalid);
                    assume(araddr == $past(araddr));
                    assume(arprot == $past(arprot));
                end else begin
                    assert(arvalid);
                    assert(araddr == $past(araddr));
                    assert(arprot == $past(arprot));
                end
            end

            // Slave-driven channels (B, R)
            if ($past(bvalid) && !$past(bready)) begin
                if (IS_SLAVE) begin
                    assert(bvalid);
                    assert(bresp == $past(bresp));
                end else begin
                    assume(bvalid);
                    assume(bresp == $past(bresp));
                end
            end

            if ($past(rvalid) && !$past(rready)) begin
                if (IS_SLAVE) begin
                    assert(rvalid);
                    assert(rdata == $past(rdata));
                    assert(rresp == $past(rresp));
                end else begin
                    assume(rvalid);
                    assume(rdata == $past(rdata));
                    assume(rresp == $past(rresp));
                end
            end
        end
    end

    // -------------------------------------------------------------
    // 2. Legal Response Codes
    // In AXI4-Lite: 2'b00 = OKAY, 2'b10 = SLVERR, 2'b11 = DECERR.
    // 2'b01 (EXOKAY) is prohibited.
    // -------------------------------------------------------------
    always @(posedge clk) begin
        if (rst_n) begin
            if (bvalid) begin
                if (IS_SLAVE) assert(bresp != 2'b01);
                else assume(bresp != 2'b01);
            end
            if (rvalid) begin
                if (IS_SLAVE) assert(rresp != 2'b01);
                else assume(rresp != 2'b01);
            end
        end
    end

    // -------------------------------------------------------------
    // 3. Reset Semantics
    // During active-low reset, VALID signals must be 0.
    // -------------------------------------------------------------
    always @(posedge clk) begin
        if (!rst_n) begin
            if (IS_SLAVE) begin
                assert(!bvalid);
                assert(!rvalid);
            end else begin
                assert(!awvalid);
                assert(!wvalid);
                assert(!arvalid);
            end
        end
    end

    // -------------------------------------------------------------
    // Combinational Input Protocol Constraints
    // -------------------------------------------------------------
    always @(*) begin
        if (rst_n) begin
            if (IS_SLAVE) begin
                if (rvalid && !rready) assume(!arvalid);
                if (bvalid && !bready) begin
                    assume(!awvalid);
                    assume(!wvalid);
                end
            end
        end
    end

    // -------------------------------------------------------------
    // 4. Request-Response Causality Tracking
    // Responses cannot exceed accepted requests.
    // -------------------------------------------------------------
    reg [7:0] f_aw_handshakes;
    reg [7:0] f_w_handshakes;
    reg [7:0] f_b_handshakes;
    reg [7:0] f_ar_handshakes;
    reg [7:0] f_r_handshakes;

    always @(posedge clk) begin
        if (!rst_n) begin
            f_aw_handshakes <= 8'd0;
            f_w_handshakes  <= 8'd0;
            f_b_handshakes  <= 8'd0;
            f_ar_handshakes <= 8'd0;
            f_r_handshakes  <= 8'd0;
        end else if (CHECK_CAUSALITY) begin
            if (awvalid && awready) f_aw_handshakes <= f_aw_handshakes + 1'b1;
            if (wvalid  && wready)  f_w_handshakes  <= f_w_handshakes + 1'b1;
            if (bvalid  && bready)  f_b_handshakes  <= f_b_handshakes + 1'b1;
            if (arvalid && arready) f_ar_handshakes <= f_ar_handshakes + 1'b1;
            if (rvalid  && rready)  f_r_handshakes  <= f_r_handshakes + 1'b1;
        end
    end

    always @(posedge clk) begin
        if (rst_n && CHECK_CAUSALITY) begin
            // Single outstanding transaction constraints
            if (SINGLE_OUTSTANDING) begin
                if (IS_SLAVE) begin
                    // Master must not issue new request while one is outstanding
                    if (f_aw_handshakes > f_b_handshakes) assume(!awvalid);
                    if (f_w_handshakes  > f_b_handshakes) assume(!wvalid);
                    if (f_ar_handshakes > f_r_handshakes) assume(!arvalid);

                    // Slave must not respond without prior completed request
                    if (f_aw_handshakes <= f_b_handshakes || f_w_handshakes <= f_b_handshakes) assert(!bvalid);
                    if (f_ar_handshakes <= f_r_handshakes) assert(!rvalid);
                end else begin
                    // DUT as master: must not issue new request while one is outstanding
                    if (f_aw_handshakes > f_b_handshakes) assert(!awvalid);
                    if (f_w_handshakes  > f_b_handshakes) assert(!wvalid);
                    if (f_ar_handshakes > f_r_handshakes) assert(!arvalid);

                    // Downstream slave: must not respond without prior completed request
                    if (f_aw_handshakes <= f_b_handshakes || f_w_handshakes <= f_b_handshakes) assume(!bvalid);
                    if (f_ar_handshakes <= f_r_handshakes) assume(!rvalid);
                end
            end else begin
                // Multi-outstanding causality tracking
                if (bvalid) begin
                    if (IS_SLAVE) begin
                        assert((f_aw_handshakes > f_b_handshakes) || (awvalid && awready));
                        assert((f_w_handshakes  > f_b_handshakes) || (wvalid  && wready));
                    end else begin
                        assume((f_aw_handshakes > f_b_handshakes) || (awvalid && awready));
                        assume((f_w_handshakes  > f_b_handshakes) || (wvalid  && wready));
                    end
                end
                if (rvalid) begin
                    if (IS_SLAVE) begin
                        assert((f_ar_handshakes > f_r_handshakes) || (arvalid && arready));
                    end else begin
                        assume((f_ar_handshakes > f_r_handshakes) || (arvalid && arready));
                    end
                end
            end
        end
    end

    // -------------------------------------------------------------
    // 5. Precondition Cover Points
    // -------------------------------------------------------------
    always @(posedge clk) begin
        if (rst_n && f_past_valid) begin
            cover(awvalid && awready && wvalid && wready);
            cover(bvalid && bready);
            cover(arvalid && arready);
            cover(rvalid && rready);
        end
    end
`endif

endmodule
