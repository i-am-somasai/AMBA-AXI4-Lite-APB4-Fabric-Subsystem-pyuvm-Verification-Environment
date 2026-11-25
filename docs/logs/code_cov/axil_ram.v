//      // verilator_coverage annotation
        // AXI4-Lite Scratchpad RAM with byte enables and out-of-range SLVERR
        `timescale 1ns/1ps
        
        module axil_ram #(
            parameter integer ADDR_WIDTH = 32,
            parameter integer DATA_WIDTH = 32,
            parameter integer RAM_DEPTH  = 256
        ) (
 935460     input  wire                  clk,
~000021     input  wire                  rst_n,
        
            // Write address channel
~022352     input  wire [ADDR_WIDTH-1:0] s_axil_awaddr,
 021549     input  wire [2:0]            s_axil_awprot,
 040047     input  wire                  s_axil_awvalid,
 028542     output reg                   s_axil_awready,
        
            // Write data channel
 021652     input  wire [DATA_WIDTH-1:0] s_axil_wdata,
 021394     input  wire [(DATA_WIDTH/8)-1:0] s_axil_wstrb,
 040047     input  wire                  s_axil_wvalid,
 022856     output reg                   s_axil_wready,
        
            // Write response channel
%000002     output reg  [1:0]            s_axil_bresp,
 040047     output reg                   s_axil_bvalid,
 040047     input  wire                  s_axil_bready,
        
            // Read address channel
~021776     input  wire [ADDR_WIDTH-1:0] s_axil_araddr,
 021568     input  wire [2:0]            s_axil_arprot,
 039918     input  wire                  s_axil_arvalid,
 022729     output reg                   s_axil_arready,
        
            // Read data channel
 008661     output reg  [DATA_WIDTH-1:0] s_axil_rdata,
%000002     output reg  [1:0]            s_axil_rresp,
 039918     output reg                   s_axil_rvalid,
 039918     input  wire                  s_axil_rready
        );
        
            localparam [1:0] RESP_OKAY   = 2'b00;
            localparam [1:0] RESP_SLVERR = 2'b10;
            localparam integer RAM_ADDR_BITS = $clog2(RAM_DEPTH);
        
            // Memory array
            reg [DATA_WIDTH-1:0] mem [0:RAM_DEPTH-1];
        
            // Lint suppression for unused protocol inputs
            wire _unused_ports = &{1'b0, s_axil_awprot, s_axil_arprot, s_axil_awaddr[ADDR_WIDTH-1:12], s_axil_araddr[ADDR_WIDTH-1:12], s_axil_awaddr[1:0], s_axil_araddr[1:0]};
        
            // Write channel registers
~010062     reg [9:0] awaddr_word_q;
 013231     reg       aw_done;
 010143     reg [DATA_WIDTH-1:0] wdata_q;
 009990     reg [(DATA_WIDTH/8)-1:0] wstrb_q;
%000000     reg       w_done;
        
~6049070     wire [9:0] write_word_active = aw_done ? awaddr_word_q : s_axil_awaddr[11:2];
~6139802     wire [DATA_WIDTH-1:0] write_data_active = w_done ? wdata_q : s_axil_wdata;
~6139802     wire [(DATA_WIDTH/8)-1:0] write_strb_active = w_done ? wstrb_q : s_axil_wstrb;
        
~021456     wire [31:0] write_word_idx = {22'b0, write_word_active};
~000023     wire        write_in_bounds = (write_word_idx < RAM_DEPTH);
 021456     wire [RAM_ADDR_BITS-1:0] write_ram_addr = write_word_active[RAM_ADDR_BITS-1:0];
        
            // --- Write Channel ---
 935460     always @(posedge clk or negedge rst_n) begin
 935207         if (!rst_n) begin
 000253             s_axil_awready <= 1'b0;
 000253             s_axil_wready  <= 1'b0;
 000253             s_axil_bvalid  <= 1'b0;
 000253             s_axil_bresp   <= 2'b00;
 000253             aw_done        <= 1'b0;
 000253             w_done         <= 1'b0;
 000253             awaddr_word_q  <= 10'b0;
 000253             wdata_q        <= {DATA_WIDTH{1'b0}};
 000253             wstrb_q        <= {(DATA_WIDTH/8){1'b0}};
 935207         end else begin
 935207             s_axil_awready <= (!s_axil_bvalid || s_axil_bready) && !aw_done;
~935207             s_axil_wready  <= (!s_axil_bvalid || s_axil_bready) && !w_done;
        
 895160             if (s_axil_awvalid && s_axil_awready) begin
 040047                 awaddr_word_q <= s_axil_awaddr[11:2];
 040047                 aw_done       <= 1'b1;
                    end
        
 895160             if (s_axil_wvalid && s_axil_wready) begin
 040047                 wdata_q       <= s_axil_wdata;
 040047                 wstrb_q       <= s_axil_wstrb;
 040047                 w_done        <= 1'b1;
                    end
        
                    // When both address and data are latched/arriving
 040047             if ((s_axil_awvalid && s_axil_awready || aw_done) &&
~895160                 (s_axil_wvalid && s_axil_wready || w_done) &&
 040047                 (!s_axil_bvalid || s_axil_bready)) begin
 040047                 s_axil_bvalid <= 1'b1;
 040047                 aw_done       <= 1'b0;
 040047                 w_done        <= 1'b0;
        
~040045                 if (write_in_bounds) begin
 040045                     s_axil_bresp <= RESP_OKAY;
 022250                     if (write_strb_active[0]) mem[write_ram_addr][7:0]   <= write_data_active[7:0];
 022211                     if (write_strb_active[1]) mem[write_ram_addr][15:8]  <= write_data_active[15:8];
 022272                     if (write_strb_active[2]) mem[write_ram_addr][23:16] <= write_data_active[23:16];
 022337                     if (write_strb_active[3]) mem[write_ram_addr][31:24] <= write_data_active[31:24];
%000002                 end else begin
%000002                     s_axil_bresp <= RESP_SLVERR;
                        end
 855113             end else if (s_axil_bvalid && s_axil_bready) begin
 040047                 s_axil_bvalid <= 1'b0;
                    end
                end
            end
        
            // --- Read Channel ---
~021071     wire [9:0]  read_word_idx  = s_axil_araddr[11:2];
~021071     wire [31:0] read_word_full = {22'b0, read_word_idx};
~000023     wire        read_in_bounds = (read_word_full < RAM_DEPTH);
 021071     wire [RAM_ADDR_BITS-1:0] read_ram_addr = read_word_idx[RAM_ADDR_BITS-1:0];
        
 935460     always @(posedge clk or negedge rst_n) begin
 935207         if (!rst_n) begin
 000253             s_axil_arready <= 1'b0;
 000253             s_axil_rvalid  <= 1'b0;
 000253             s_axil_rresp   <= 2'b00;
 000253             s_axil_rdata   <= {DATA_WIDTH{1'b0}};
 935207         end else begin
 935207             s_axil_arready <= !s_axil_rvalid || s_axil_rready;
        
 895289             if (s_axil_arvalid && s_axil_arready) begin
 039918                 s_axil_rvalid <= 1'b1;
~039916                 if (read_in_bounds) begin
 039916                     s_axil_rdata <= mem[read_ram_addr];
 039916                     s_axil_rresp <= RESP_OKAY;
%000002                 end else begin
%000002                     s_axil_rdata <= {DATA_WIDTH{1'b0}};
%000002                     s_axil_rresp <= RESP_SLVERR;
                        end
 855371             end else if (s_axil_rvalid && s_axil_rready) begin
 039918                 s_axil_rvalid <= 1'b0;
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
        
            // Shared Protocol Checker
            axil_props #(
                .ADDR_WIDTH(ADDR_WIDTH),
                .DATA_WIDTH(DATA_WIDTH),
                .STRB_WIDTH(DATA_WIDTH / 8),
                .IS_SLAVE(1),
                .SINGLE_OUTSTANDING(1)
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
        
