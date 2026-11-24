// AXI4-Lite Scratchpad RAM with byte enables and out-of-range SLVERR
`timescale 1ns/1ps

module axil_ram #(
    parameter integer ADDR_WIDTH = 32,
    parameter integer DATA_WIDTH = 32,
    parameter integer RAM_DEPTH  = 256
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

    localparam [1:0] RESP_OKAY   = 2'b00;
    localparam [1:0] RESP_SLVERR = 2'b10;
    localparam integer RAM_ADDR_BITS = $clog2(RAM_DEPTH);

    // Memory array
    reg [DATA_WIDTH-1:0] mem [0:RAM_DEPTH-1];

    // Lint suppression for unused protocol inputs
    wire _unused_ports = &{1'b0, s_axil_awprot, s_axil_arprot, s_axil_awaddr[ADDR_WIDTH-1:12], s_axil_araddr[ADDR_WIDTH-1:12], s_axil_awaddr[1:0], s_axil_araddr[1:0]};

    // Write channel registers
    reg [9:0] awaddr_word_q;
    reg       aw_done;
    reg [DATA_WIDTH-1:0] wdata_q;
    reg [(DATA_WIDTH/8)-1:0] wstrb_q;
    reg       w_done;

    wire [9:0] write_word_active = aw_done ? awaddr_word_q : s_axil_awaddr[11:2];
    wire [DATA_WIDTH-1:0] write_data_active = w_done ? wdata_q : s_axil_wdata;
    wire [(DATA_WIDTH/8)-1:0] write_strb_active = w_done ? wstrb_q : s_axil_wstrb;

    wire [31:0] write_word_idx = {22'b0, write_word_active};
    wire        write_in_bounds = (write_word_idx < RAM_DEPTH);
    wire [RAM_ADDR_BITS-1:0] write_ram_addr = write_word_active[RAM_ADDR_BITS-1:0];

    // --- Write Channel ---
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axil_awready <= 1'b0;
            s_axil_wready  <= 1'b0;
            s_axil_bvalid  <= 1'b0;
            s_axil_bresp   <= 2'b00;
            aw_done        <= 1'b0;
            w_done         <= 1'b0;
            awaddr_word_q  <= 10'b0;
            wdata_q        <= {DATA_WIDTH{1'b0}};
            wstrb_q        <= {(DATA_WIDTH/8){1'b0}};
        end else begin
            s_axil_awready <= (!s_axil_bvalid || s_axil_bready) && !aw_done;
            s_axil_wready  <= (!s_axil_bvalid || s_axil_bready) && !w_done;

            if (s_axil_awvalid && s_axil_awready) begin
                awaddr_word_q <= s_axil_awaddr[11:2];
                aw_done       <= 1'b1;
            end

            if (s_axil_wvalid && s_axil_wready) begin
                wdata_q       <= s_axil_wdata;
                wstrb_q       <= s_axil_wstrb;
                w_done        <= 1'b1;
            end

            // When both address and data are latched/arriving
            if ((s_axil_awvalid && s_axil_awready || aw_done) &&
                (s_axil_wvalid && s_axil_wready || w_done) &&
                (!s_axil_bvalid || s_axil_bready)) begin
                s_axil_bvalid <= 1'b1;
                aw_done       <= 1'b0;
                w_done        <= 1'b0;

                if (write_in_bounds) begin
                    s_axil_bresp <= RESP_OKAY;
                    // MUTANT: Dropped WSTRB[0]
                    if (1'b0) mem[write_ram_addr][7:0]   <= write_data_active[7:0];
                    if (write_strb_active[1]) mem[write_ram_addr][15:8]  <= write_data_active[15:8];
                    if (write_strb_active[2]) mem[write_ram_addr][23:16] <= write_data_active[23:16];
                    if (write_strb_active[3]) mem[write_ram_addr][31:24] <= write_data_active[31:24];
                end else begin
                    s_axil_bresp <= RESP_SLVERR;
                end
            end else if (s_axil_bvalid && s_axil_bready) begin
                s_axil_bvalid <= 1'b0;
            end
        end
    end

    // --- Read Channel ---
    wire [9:0]  read_word_idx  = s_axil_araddr[11:2];
    wire [31:0] read_word_full = {22'b0, read_word_idx};
    wire        read_in_bounds = (read_word_full < RAM_DEPTH);
    wire [RAM_ADDR_BITS-1:0] read_ram_addr = read_word_idx[RAM_ADDR_BITS-1:0];

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
                if (read_in_bounds) begin
                    s_axil_rdata <= mem[read_ram_addr];
                    s_axil_rresp <= RESP_OKAY;
                end else begin
                    s_axil_rdata <= {DATA_WIDTH{1'b0}};
                    s_axil_rresp <= RESP_SLVERR;
                end
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

    // AXI master protocol assumptions
    always @(posedge clk) begin
        if (f_past_valid && $past(rst_n) && rst_n) begin
            if ($past(s_axil_awvalid) && !$past(s_axil_awready)) begin
                assume (s_axil_awvalid);
                assume ($stable(s_axil_awaddr));
                assume ($stable(s_axil_awprot));
            end
            if ($past(s_axil_wvalid) && !$past(s_axil_wready)) begin
                assume (s_axil_wvalid);
                assume ($stable(s_axil_wdata));
                assume ($stable(s_axil_wstrb));
            end
            if ($past(s_axil_arvalid) && !$past(s_axil_arready)) begin
                assume (s_axil_arvalid);
                assume ($stable(s_axil_araddr));
                assume ($stable(s_axil_arprot));
            end
        end
    end

    wire write_commit = ((s_axil_awvalid && s_axil_awready || aw_done) &&
                         (s_axil_wvalid && s_axil_wready || w_done) &&
                         (!s_axil_bvalid || s_axil_bready));
    wire read_commit  = (s_axil_arvalid && s_axil_arready);

    always @(posedge clk) begin
        if (rst_n) begin
            assert (s_axil_bresp == RESP_OKAY || s_axil_bresp == RESP_SLVERR);
            assert (s_axil_rresp == RESP_OKAY || s_axil_rresp == RESP_SLVERR);

            if (f_past_valid && $past(rst_n)) begin
                if ($past(write_commit)) begin
                    assert (s_axil_bvalid);
                    assert (s_axil_bresp == ($past(write_in_bounds) ? RESP_OKAY : RESP_SLVERR));
                end else if ($past(s_axil_bvalid && !s_axil_bready)) begin
                    assert (s_axil_bvalid);
                    assert ($stable(s_axil_bresp));
                end

                if ($past(read_commit)) begin
                    assert (s_axil_rvalid);
                    assert (s_axil_rresp == ($past(read_in_bounds) ? RESP_OKAY : RESP_SLVERR));
                end else if ($past(s_axil_rvalid && !s_axil_rready)) begin
                    assert (s_axil_rvalid);
                    assert ($stable(s_axil_rdata));
                    assert ($stable(s_axil_rresp));
                end
            end
        end
    end

    // Covers
    always @(posedge clk) begin
        if (rst_n) begin
            cover (s_axil_bvalid && s_axil_bresp == RESP_OKAY);
            cover (s_axil_bvalid && s_axil_bresp == RESP_SLVERR);
            cover (s_axil_rvalid && s_axil_rresp == RESP_OKAY);
            cover (s_axil_rvalid && s_axil_rresp == RESP_SLVERR);
        end
    end
`endif

endmodule
