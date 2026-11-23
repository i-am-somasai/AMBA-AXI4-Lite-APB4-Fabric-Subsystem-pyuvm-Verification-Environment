// formal/axil_props.v
// Shared AXI4-Lite Protocol Property Checker
// Checks handshake stability, response causality, and protocol conformance.
`timescale 1ns / 1ps

module axil_props #(
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 32,
    parameter STRB_WIDTH = DATA_WIDTH / 8
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
            // AW Channel Stability
            if ($past(awvalid) && !$past(awready)) begin
                assert(awvalid);
                assert(awaddr == $past(awaddr));
                assert(awprot == $past(awprot));
            end

            // W Channel Stability
            if ($past(wvalid) && !$past(wready)) begin
                assert(wvalid);
                assert(wdata == $past(wdata));
                assert(wstrb == $past(wstrb));
            end

            // AR Channel Stability
            if ($past(arvalid) && !$past(arready)) begin
                assert(arvalid);
                assert(araddr == $past(araddr));
                assert(arprot == $past(arprot));
            end

            // B Channel Stability
            if ($past(bvalid) && !$past(bready)) begin
                assert(bvalid);
                assert(bresp == $past(bresp));
            end

            // R Channel Stability
            if ($past(rvalid) && !$past(rready)) begin
                assert(rvalid);
                assert(rdata == $past(rdata));
                assert(rresp == $past(rresp));
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
                assert(bresp != 2'b01);
            end
            if (rvalid) begin
                assert(rresp != 2'b01);
            end
        end
    end

    // -------------------------------------------------------------
    // 3. Reset Semantics
    // During active-low reset, all VALID signals must be driven 0.
    // -------------------------------------------------------------
    always @(posedge clk) begin
        if (!rst_n) begin
            assert(!bvalid);
            assert(!rvalid);
        end
    end

    // -------------------------------------------------------------
    // 4. Request-Response Causality Tracking
    // -------------------------------------------------------------
    reg [7:0] f_aw_handshakes = 0;
    reg [7:0] f_w_handshakes  = 0;
    reg [7:0] f_b_handshakes  = 0;
    reg [7:0] f_ar_handshakes = 0;
    reg [7:0] f_r_handshakes  = 0;

    always @(posedge clk) begin
        if (!rst_n) begin
            f_aw_handshakes <= 0;
            f_w_handshakes  <= 0;
            f_b_handshakes  <= 0;
            f_ar_handshakes <= 0;
            f_r_handshakes  <= 0;
        end else begin
            if (awvalid && awready) f_aw_handshakes <= f_aw_handshakes + 1'b1;
            if (wvalid  && wready)  f_w_handshakes  <= f_w_handshakes + 1'b1;
            if (bvalid  && bready)  f_b_handshakes  <= f_b_handshakes + 1'b1;
            if (arvalid && arready) f_ar_handshakes <= f_ar_handshakes + 1'b1;
            if (rvalid  && rready)  f_r_handshakes  <= f_r_handshakes + 1'b1;
        end
    end

    // Responses cannot exceed accepted requests
    always @(posedge clk) begin
        if (rst_n) begin
            // Cannot produce BVALID unless at least one request handshake has occurred
            if (bvalid) begin
                assert((f_aw_handshakes > f_b_handshakes) || (awvalid && awready));
                assert((f_w_handshakes  > f_b_handshakes) || (wvalid  && wready));
            end
            // Cannot produce RVALID unless at least one read request has occurred
            if (rvalid) begin
                assert((f_ar_handshakes > f_r_handshakes) || (arvalid && arready));
            end
        end
    end
`endif

endmodule
