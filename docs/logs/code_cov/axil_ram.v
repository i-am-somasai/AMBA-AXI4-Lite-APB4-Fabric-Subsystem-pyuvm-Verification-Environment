//      // verilator_coverage annotation
        // AXI4-Lite Scratchpad RAM with byte enables and out-of-range SLVERR
        `timescale 1ns/1ps
        
        module axil_ram #(
            parameter integer ADDR_WIDTH = 32,
            parameter integer DATA_WIDTH = 32,
            parameter integer RAM_DEPTH  = 256
        ) (
 100022     input  wire                  clk,
~000014     input  wire                  rst_n,
        
            // Write address channel
~002975     input  wire [ADDR_WIDTH-1:0] s_axil_awaddr,
 002767     input  wire [2:0]            s_axil_awprot,
 005029     input  wire                  s_axil_awvalid,
 001700     output reg                   s_axil_awready,
        
            // Write data channel
 002824     input  wire [DATA_WIDTH-1:0] s_axil_wdata,
 002761     input  wire [(DATA_WIDTH/8)-1:0] s_axil_wstrb,
 005029     input  wire                  s_axil_wvalid,
~000014     output reg                   s_axil_wready,
        
            // Write response channel
%000003     output reg  [1:0]            s_axil_bresp,
 005029     output reg                   s_axil_bvalid,
 005029     input  wire                  s_axil_bready,
        
            // Read address channel
~002829     input  wire [ADDR_WIDTH-1:0] s_axil_araddr,
 002748     input  wire [2:0]            s_axil_arprot,
 004902     input  wire                  s_axil_arvalid,
~000014     output reg                   s_axil_arready,
        
            // Read data channel
 000927     output reg  [DATA_WIDTH-1:0] s_axil_rdata,
%000003     output reg  [1:0]            s_axil_rresp,
 004902     output reg                   s_axil_rvalid,
 004902     input  wire                  s_axil_rready
        );
        
            localparam [1:0] RESP_OKAY   = 2'b00;
            localparam [1:0] RESP_SLVERR = 2'b10;
            localparam integer RAM_ADDR_BITS = $clog2(RAM_DEPTH);
        
            // Memory array
            reg [DATA_WIDTH-1:0] mem [0:RAM_DEPTH-1];
        
            // Lint suppression for unused protocol inputs
            wire _unused_ports = &{1'b0, s_axil_awprot, s_axil_arprot, s_axil_awaddr[ADDR_WIDTH-1:12], s_axil_araddr[ADDR_WIDTH-1:12], s_axil_awaddr[1:0], s_axil_araddr[1:0]};
        
            // Write channel registers
~001259     reg [9:0] awaddr_word_q;
 001686     reg       aw_done;
 001294     reg [DATA_WIDTH-1:0] wdata_q;
 001256     reg [(DATA_WIDTH/8)-1:0] wstrb_q;
%000000     reg       w_done;
        
~618217     wire [9:0] write_word_active = aw_done ? awaddr_word_q : s_axil_awaddr[11:2];
~629953     wire [DATA_WIDTH-1:0] write_data_active = w_done ? wdata_q : s_axil_wdata;
~629953     wire [(DATA_WIDTH/8)-1:0] write_strb_active = w_done ? wstrb_q : s_axil_wstrb;
        
~002712     wire [31:0] write_word_idx = {22'b0, write_word_active};
%000009     wire        write_in_bounds = (write_word_idx < RAM_DEPTH);
 002712     wire [RAM_ADDR_BITS-1:0] write_ram_addr = write_word_active[RAM_ADDR_BITS-1:0];
        
            // --- Write Channel ---
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             s_axil_awready <= 1'b0;
 000171             s_axil_wready  <= 1'b0;
 000171             s_axil_bvalid  <= 1'b0;
 000171             s_axil_bresp   <= 2'b00;
 000171             aw_done        <= 1'b0;
 000171             w_done         <= 1'b0;
 000171             awaddr_word_q  <= 10'b0;
 000171             wdata_q        <= {DATA_WIDTH{1'b0}};
 000171             wstrb_q        <= {(DATA_WIDTH/8){1'b0}};
 099859         end else begin
~099859             s_axil_awready <= (!s_axil_bvalid || s_axil_bready) && !aw_done;
~099859             s_axil_wready  <= (!s_axil_bvalid || s_axil_bready) && !w_done;
        
 094830             if (s_axil_awvalid && s_axil_awready) begin
 005029                 awaddr_word_q <= s_axil_awaddr[11:2];
 005029                 aw_done       <= 1'b1;
                    end
        
 094830             if (s_axil_wvalid && s_axil_wready) begin
 005029                 wdata_q       <= s_axil_wdata;
 005029                 wstrb_q       <= s_axil_wstrb;
 005029                 w_done        <= 1'b1;
                    end
        
                    // When both address and data are latched/arriving
 005029             if ((s_axil_awvalid && s_axil_awready || aw_done) &&
~094830                 (s_axil_wvalid && s_axil_wready || w_done) &&
 005029                 (!s_axil_bvalid || s_axil_bready)) begin
 005029                 s_axil_bvalid <= 1'b1;
 005029                 aw_done       <= 1'b0;
 005029                 w_done        <= 1'b0;
        
~005026                 if (write_in_bounds) begin
 005026                     s_axil_bresp <= RESP_OKAY;
 002739                     if (write_strb_active[0]) mem[write_ram_addr][7:0]   <= write_data_active[7:0];
 002734                     if (write_strb_active[1]) mem[write_ram_addr][15:8]  <= write_data_active[15:8];
 002744                     if (write_strb_active[2]) mem[write_ram_addr][23:16] <= write_data_active[23:16];
 002766                     if (write_strb_active[3]) mem[write_ram_addr][31:24] <= write_data_active[31:24];
%000003                 end else begin
%000003                     s_axil_bresp <= RESP_SLVERR;
                        end
 089801             end else if (s_axil_bvalid && s_axil_bready) begin
 005029                 s_axil_bvalid <= 1'b0;
                    end
                end
            end
        
            // --- Read Channel ---
~002670     wire [9:0]  read_word_idx  = s_axil_araddr[11:2];
~002670     wire [31:0] read_word_full = {22'b0, read_word_idx};
%000009     wire        read_in_bounds = (read_word_full < RAM_DEPTH);
 002670     wire [RAM_ADDR_BITS-1:0] read_ram_addr = read_word_idx[RAM_ADDR_BITS-1:0];
        
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             s_axil_arready <= 1'b0;
 000171             s_axil_rvalid  <= 1'b0;
 000171             s_axil_rresp   <= 2'b00;
 000171             s_axil_rdata   <= {DATA_WIDTH{1'b0}};
 099859         end else begin
~099859             s_axil_arready <= !s_axil_rvalid || s_axil_rready;
        
 094957             if (s_axil_arvalid && s_axil_arready) begin
 004902                 s_axil_rvalid <= 1'b1;
~004899                 if (read_in_bounds) begin
 004899                     s_axil_rdata <= mem[read_ram_addr];
 004899                     s_axil_rresp <= RESP_OKAY;
%000003                 end else begin
%000003                     s_axil_rdata <= {DATA_WIDTH{1'b0}};
%000003                     s_axil_rresp <= RESP_SLVERR;
                        end
 090055             end else if (s_axil_rvalid && s_axil_rready) begin
 004902                 s_axil_rvalid <= 1'b0;
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
        
