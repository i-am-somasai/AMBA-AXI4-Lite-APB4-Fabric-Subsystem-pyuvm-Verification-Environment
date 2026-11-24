// AXI4-Lite CSR Block with RO, RW, W1C registers and IRQ aggregation
`timescale 1ns/1ps

module axil_csr #(
    parameter integer ADDR_WIDTH = 32,
    parameter integer DATA_WIDTH = 32
) (
    input  wire                  clk,
    input  wire                  rst_n,

    // AXI4-Lite Slave Interface
    input  wire [ADDR_WIDTH-1:0] s_axil_awaddr,
    input  wire [2:0]            s_axil_awprot,
    input  wire                  s_axil_awvalid,
    output reg                   s_axil_awready,

    input  wire [DATA_WIDTH-1:0] s_axil_wdata,
    input  wire [(DATA_WIDTH/8)-1:0] s_axil_wstrb,
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
    input  wire                  s_axil_rready,

    // Interrupt subsystem
    input  wire [2:0]            irq_sources, // [0] UART, [1] Timer, [2] GPIO
    output wire                  irq_o
);

    localparam [1:0] RESP_OKAY   = 2'b00;
    localparam [1:0] RESP_SLVERR = 2'b10;

    localparam [31:0] CONST_ID      = 32'hA3BA_0001;
    localparam [31:0] CONST_VERSION = 32'h0001_0000;

    // Lint suppression for unused bits
    wire _unused_bits = &{1'b0, s_axil_awprot, s_axil_arprot, s_axil_awaddr[ADDR_WIDTH-1:8], s_axil_araddr[ADDR_WIDTH-1:8], s_axil_awaddr[1:0], s_axil_araddr[1:0]};

    // Registers
    reg [31:0] reg_scratch;
    reg [31:0] reg_scratch2;
    reg [2:0]  reg_irq_mask;
    reg [31:0] reg_w1c_test;

    wire [31:0] reg_irq_raw    = {29'b0, irq_sources};
    wire [31:0] reg_irq_status = {29'b0, irq_sources & reg_irq_mask};

    assign irq_o = |(reg_irq_status[2:0]);

    // Latch channels
    reg [7:0] awoffset_q;
    reg       aw_done;
    reg [DATA_WIDTH-1:0] wdata_q;
    reg [(DATA_WIDTH/8)-1:0] wstrb_q;
    reg       w_done;

    wire [7:0] write_offset = (aw_done ? awoffset_q : s_axil_awaddr[7:0]);
    wire [DATA_WIDTH-1:0] write_data = (w_done ? wdata_q : s_axil_wdata);
    wire [(DATA_WIDTH/8)-1:0] write_strb = (w_done ? wstrb_q : s_axil_wstrb);

    // --- Write Channel ---
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axil_awready <= 1'b0;
            s_axil_wready  <= 1'b0;
            s_axil_bvalid  <= 1'b0;
            s_axil_bresp   <= 2'b00;
            aw_done        <= 1'b0;
            w_done         <= 1'b0;
            awoffset_q     <= 8'h00;
            wdata_q        <= {DATA_WIDTH{1'b0}};
            wstrb_q        <= {(DATA_WIDTH/8){1'b0}};

            reg_scratch    <= 32'h0;
            reg_scratch2   <= 32'h0;
            reg_irq_mask   <= 3'b0;
            reg_w1c_test   <= 32'h0;
        end else begin
            s_axil_awready <= (!s_axil_bvalid || s_axil_bready) && !aw_done;
            s_axil_wready  <= (!s_axil_bvalid || s_axil_bready) && !w_done;

            if (s_axil_awvalid && s_axil_awready) begin
                awoffset_q <= s_axil_awaddr[7:0];
                aw_done    <= 1'b1;
            end

            if (s_axil_wvalid && s_axil_wready) begin
                wdata_q    <= s_axil_wdata;
                wstrb_q    <= s_axil_wstrb;
                w_done     <= 1'b1;
            end

            if ((s_axil_awvalid && s_axil_awready || aw_done) &&
                (s_axil_wvalid && s_axil_wready || w_done) &&
                (!s_axil_bvalid || s_axil_bready)) begin
                s_axil_bvalid <= 1'b1;
                aw_done       <= 1'b0;
                w_done        <= 1'b0;

                case (write_offset)
                    8'h00: begin // ID: Read-Only, writes ignored with OKAY
                        s_axil_bresp <= RESP_OKAY;
                    end
                    8'h04: begin // VERSION: Read-Only, writes ignored with OKAY
                        s_axil_bresp <= RESP_OKAY;
                    end
                    8'h08: begin // SCRATCH: Full-word RW
                        s_axil_bresp <= RESP_OKAY;
                        reg_scratch  <= write_data;
                    end
                    8'h0C: begin // SCRATCH2: Byte-writable via WSTRB
                        s_axil_bresp <= RESP_OKAY;
                        if (write_strb[0]) reg_scratch2[7:0]   <= write_data[7:0];
                        if (write_strb[1]) reg_scratch2[15:8]  <= write_data[15:8];
                        if (write_strb[2]) reg_scratch2[23:16] <= write_data[23:16];
                        if (write_strb[3]) reg_scratch2[31:24] <= write_data[31:24];
                    end
                    8'h10: begin // IRQ_RAW: RO
                        s_axil_bresp <= RESP_OKAY;
                    end
                    8'h14: begin // IRQ_MASK: RW
                        s_axil_bresp <= RESP_OKAY;
                        reg_irq_mask <= write_data[2:0];
                    end
                    8'h18: begin // IRQ_STATUS: RO
                        s_axil_bresp <= RESP_OKAY;
                    end
                    8'h1C: begin // W1C_TEST: writing 1 clears bit
                        s_axil_bresp <= RESP_OKAY;
                        reg_w1c_test <= reg_w1c_test & ~write_data;
                    end
                    8'h20: begin // W1C_SET: WO test hook, sets bit in W1C_TEST
                        s_axil_bresp <= RESP_OKAY;
                        reg_w1c_test <= reg_w1c_test | write_data;
                    end
                    default: begin // Undefined offset -> SLVERR
                        s_axil_bresp <= RESP_SLVERR;
                    end
                endcase
            end else if (s_axil_bvalid && s_axil_bready) begin
                s_axil_bvalid <= 1'b0;
            end
        end
    end

    // --- Read Channel ---
    wire [7:0] read_offset = s_axil_araddr[7:0];

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
                case (read_offset)
                    8'h00: begin
                        s_axil_rdata <= CONST_ID;
                        s_axil_rresp <= RESP_OKAY;
                    end
                    8'h04: begin
                        s_axil_rdata <= CONST_VERSION;
                        s_axil_rresp <= RESP_OKAY;
                    end
                    8'h08: begin
                        s_axil_rdata <= reg_scratch;
                        s_axil_rresp <= RESP_OKAY;
                    end
                    8'h0C: begin
                        s_axil_rdata <= reg_scratch2;
                        s_axil_rresp <= RESP_OKAY;
                    end
                    8'h10: begin
                        s_axil_rdata <= reg_irq_raw;
                        s_axil_rresp <= RESP_OKAY;
                    end
                    8'h14: begin
                        s_axil_rdata <= {29'b0, reg_irq_mask};
                        s_axil_rresp <= RESP_OKAY;
                    end
                    8'h18: begin
                        s_axil_rdata <= reg_irq_status;
                        s_axil_rresp <= RESP_OKAY;
                    end
                    8'h1C: begin
                        s_axil_rdata <= reg_w1c_test;
                        s_axil_rresp <= RESP_OKAY;
                    end
                    8'h20: begin // W1C_SET is WO, returns 0 on read
                        s_axil_rdata <= 32'h0;
                        s_axil_rresp <= RESP_OKAY;
                    end
                    default: begin // Undefined offset -> SLVERR
                        s_axil_rdata <= 32'h0;
                        s_axil_rresp <= RESP_SLVERR;
                    end
                endcase
            end else if (s_axil_rvalid && s_axil_rready) begin
                s_axil_rvalid <= 1'b0;
            end
        end
    end

`ifdef FORMAL
    reg f_past_valid = 0;
    always @(posedge clk) f_past_valid <= 1;

    always @(*) begin
        if (!f_past_valid) assume (!rst_n);
    end

    // Master stability assumptions
    always @(posedge clk) begin
        if (f_past_valid && $past(rst_n) && rst_n) begin
            if ($past(s_axil_awvalid) && !$past(s_axil_awready)) begin
                assume (s_axil_awvalid);
                assume ($stable(s_axil_awaddr));
            end
            if ($past(s_axil_wvalid) && !$past(s_axil_wready)) begin
                assume (s_axil_wvalid);
                assume ($stable(s_axil_wdata));
                assume ($stable(s_axil_wstrb));
            end
            if ($past(s_axil_arvalid) && !$past(s_axil_arready)) begin
                assume (s_axil_arvalid);
                assume ($stable(s_axil_araddr));
            end
        end
    end

    always @(posedge clk) begin
        if (rst_n) begin
            // Constant identifiers
            if (s_axil_rvalid && s_axil_rresp == RESP_OKAY) begin
                if ($past(s_axil_arvalid && s_axil_arready && (read_offset == 8'h00)))
                    assert (s_axil_rdata == CONST_ID);
                if ($past(s_axil_arvalid && s_axil_arready && (read_offset == 8'h04)))
                    assert (s_axil_rdata == CONST_VERSION);
            end

            // IRQ aggregation
            assert (irq_o == |reg_irq_status[2:0]);
            assert (reg_irq_raw == {29'b0, irq_sources});
        end
    end

    // Shared Protocol Checker
    axil_props #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH),
        .STRB_WIDTH(DATA_WIDTH / 8),
        .IS_SLAVE(1),
        .SINGLE_OUTSTANDING(1),
        .CHECK_CAUSALITY(0)
    ) u_axil_props (
        .clk     (clk),
        .rst_n   (rst_n),
        .awaddr  (s_axil_awaddr),
        .awprot  (3'b000),
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
        .arprot  (3'b000),
        .arvalid (s_axil_arvalid),
        .arready (s_axil_arready),
        .rdata   (s_axil_rdata),
        .rresp   (s_axil_rresp),
        .rvalid  (s_axil_rvalid),
        .rready  (s_axil_rready)
    );

    // Covers
    always @(posedge clk) begin
        if (rst_n) begin
            cover (irq_o);
            cover (s_axil_bvalid && s_axil_bresp == RESP_OKAY);
            cover (s_axil_rvalid && s_axil_rresp == RESP_OKAY);
            cover (s_axil_bvalid && s_axil_bresp == RESP_SLVERR);
        end
    end
`endif

endmodule
