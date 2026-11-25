//      // verilator_coverage annotation
        // AXI4-Lite CSR Block with RO, RW, W1C registers and IRQ aggregation
        `timescale 1ns/1ps
        
        module axil_csr #(
            parameter integer ADDR_WIDTH = 32,
            parameter integer DATA_WIDTH = 32
        ) (
 935460     input  wire                  clk,
~000021     input  wire                  rst_n,
        
            // AXI4-Lite Slave Interface
~018379     input  wire [ADDR_WIDTH-1:0] s_axil_awaddr,
 017057     input  wire [2:0]            s_axil_awprot,
 020070     input  wire                  s_axil_awvalid,
 014341     output reg                   s_axil_awready,
        
 017172     input  wire [DATA_WIDTH-1:0] s_axil_wdata,
 017021     input  wire [(DATA_WIDTH/8)-1:0] s_axil_wstrb,
 020070     input  wire                  s_axil_wvalid,
 011529     output reg                   s_axil_wready,
        
%000002     output reg  [1:0]            s_axil_bresp,
 020070     output reg                   s_axil_bvalid,
 020070     input  wire                  s_axil_bready,
        
~018238     input  wire [ADDR_WIDTH-1:0] s_axil_araddr,
 017157     input  wire [2:0]            s_axil_arprot,
 020039     input  wire                  s_axil_arvalid,
 011405     output reg                   s_axil_arready,
        
 004604     output reg  [DATA_WIDTH-1:0] s_axil_rdata,
%000002     output reg  [1:0]            s_axil_rresp,
 020039     output reg                   s_axil_rvalid,
 020039     input  wire                  s_axil_rready,
        
            // Interrupt subsystem
~000010     input  wire [2:0]            irq_sources, // [0] UART, [1] Timer, [2] GPIO
 000020     output wire                  irq_o
        );
        
            localparam [1:0] RESP_OKAY   = 2'b00;
            localparam [1:0] RESP_SLVERR = 2'b10;
        
            localparam [31:0] CONST_ID      = 32'hA3BA_0001;
            localparam [31:0] CONST_VERSION = 32'h0001_0000;
        
            // Lint suppression for unused bits
            wire _unused_bits = &{1'b0, s_axil_awprot, s_axil_arprot, s_axil_awaddr[ADDR_WIDTH-1:8], s_axil_araddr[ADDR_WIDTH-1:8], s_axil_awaddr[1:0], s_axil_araddr[1:0]};
        
            // Registers
 000865     reg [31:0] reg_scratch;
 000589     reg [31:0] reg_scratch2;
 001254     reg [2:0]  reg_irq_mask;
 000859     reg [31:0] reg_w1c_test;
        
~000010     wire [31:0] reg_irq_raw    = {29'b0, irq_sources};
~000017     wire [31:0] reg_irq_status = {29'b0, irq_sources & reg_irq_mask};
        
~6085605     assign irq_o = |(reg_irq_status[2:0]);
        
            // Latch channels (Rule 6: address bits [1:0] ignored -> decode word offset [7:2])
~004913     reg [5:0] awoffset_q;
 006626     reg       aw_done;
 005071     reg [DATA_WIDTH-1:0] wdata_q;
 004985     reg [(DATA_WIDTH/8)-1:0] wstrb_q;
%000000     reg       w_done;
        
 6094364     wire [5:0] write_word = (aw_done ? awoffset_q : s_axil_awaddr[7:2]);
~6139802     wire [DATA_WIDTH-1:0] write_data = (w_done ? wdata_q : s_axil_wdata);
~6139802     wire [(DATA_WIDTH/8)-1:0] write_strb = (w_done ? wstrb_q : s_axil_wstrb);
        
            // --- Write Channel ---
 935460     always @(posedge clk or negedge rst_n) begin
 935207         if (!rst_n) begin
 000253             s_axil_awready <= 1'b0;
 000253             s_axil_wready  <= 1'b0;
 000253             s_axil_bvalid  <= 1'b0;
 000253             s_axil_bresp   <= 2'b00;
 000253             aw_done        <= 1'b0;
 000253             w_done         <= 1'b0;
 000253             awoffset_q     <= 6'h00;
 000253             wdata_q        <= {DATA_WIDTH{1'b0}};
 000253             wstrb_q        <= {(DATA_WIDTH/8){1'b0}};
        
 000253             reg_scratch    <= 32'h0;
 000253             reg_scratch2   <= 32'h0;
 000253             reg_irq_mask   <= 3'b0;
 000253             reg_w1c_test   <= 32'h0;
 935207         end else begin
 935207             s_axil_awready <= (!s_axil_bvalid || s_axil_bready) && !aw_done;
~935207             s_axil_wready  <= (!s_axil_bvalid || s_axil_bready) && !w_done;
        
 915137             if (s_axil_awvalid && s_axil_awready) begin
 020070                 awoffset_q <= s_axil_awaddr[7:2];
 020070                 aw_done    <= 1'b1;
                    end
        
 915137             if (s_axil_wvalid && s_axil_wready) begin
 020070                 wdata_q    <= s_axil_wdata;
 020070                 wstrb_q    <= s_axil_wstrb;
 020070                 w_done     <= 1'b1;
                    end
        
 020070             if ((s_axil_awvalid && s_axil_awready || aw_done) &&
~915137                 (s_axil_wvalid && s_axil_wready || w_done) &&
 020070                 (!s_axil_bvalid || s_axil_bready)) begin
 020070                 s_axil_bvalid <= 1'b1;
 020070                 aw_done       <= 1'b0;
 020070                 w_done        <= 1'b0;
        
 020070                 case (write_word)
%000000                     6'h00: begin // 0x00 ID: Read-Only, writes ignored with OKAY
%000000                         s_axil_bresp <= RESP_OKAY;
                            end
%000000                     6'h01: begin // 0x04 VERSION: Read-Only, writes ignored with OKAY
%000000                         s_axil_bresp <= RESP_OKAY;
                            end
 003376                     6'h02: begin // 0x08 SCRATCH: Full-word RW
 003376                         s_axil_bresp <= RESP_OKAY;
 003376                         reg_scratch  <= write_data;
                            end
 005064                     6'h03: begin // 0x0C SCRATCH2: Byte-writable via WSTRB
 005064                         s_axil_bresp <= RESP_OKAY;
 002860                         if (write_strb[0]) reg_scratch2[7:0]   <= write_data[7:0];
 002838                         if (write_strb[1]) reg_scratch2[15:8]  <= write_data[15:8];
 002803                         if (write_strb[2]) reg_scratch2[23:16] <= write_data[23:16];
 002836                         if (write_strb[3]) reg_scratch2[31:24] <= write_data[31:24];
                            end
%000000                     6'h04: begin // 0x10 IRQ_RAW: RO
%000000                         s_axil_bresp <= RESP_OKAY;
                            end
 005054                     6'h05: begin // 0x14 IRQ_MASK: RW
 005054                         s_axil_bresp <= RESP_OKAY;
 005054                         reg_irq_mask <= write_data[2:0];
                            end
%000000                     6'h06: begin // 0x18 IRQ_STATUS: RO
%000000                         s_axil_bresp <= RESP_OKAY;
                            end
 003301                     6'h07: begin // 0x1C W1C_TEST: writing 1 clears bit
 003301                         s_axil_bresp <= RESP_OKAY;
 003301                         reg_w1c_test <= reg_w1c_test & ~write_data;
                            end
 003273                     6'h08: begin // 0x20 W1C_SET: WO test hook, sets bit in W1C_TEST
 003273                         s_axil_bresp <= RESP_OKAY;
 003273                         reg_w1c_test <= reg_w1c_test | write_data;
                            end
%000002                     default: begin // Undefined word offset -> SLVERR
%000002                         s_axil_bresp <= RESP_SLVERR;
                            end
                        endcase
 895067             end else if (s_axil_bvalid && s_axil_bready) begin
 020070                 s_axil_bvalid <= 1'b0;
                    end
                end
            end
        
            // --- Read Channel ---
 016721     wire [5:0] read_word = s_axil_araddr[7:2];
        
 935460     always @(posedge clk or negedge rst_n) begin
 935207         if (!rst_n) begin
 000253             s_axil_arready <= 1'b0;
 000253             s_axil_rvalid  <= 1'b0;
 000253             s_axil_rresp   <= 2'b00;
 000253             s_axil_rdata   <= {DATA_WIDTH{1'b0}};
 935207         end else begin
 935207             s_axil_arready <= !s_axil_rvalid || s_axil_rready;
        
 915168             if (s_axil_arvalid && s_axil_arready) begin
 020039                 s_axil_rvalid <= 1'b1;
 020039                 case (read_word)
 004044                     6'h00: begin // 0x00 ID
 004044                         s_axil_rdata <= CONST_ID;
 004044                         s_axil_rresp <= RESP_OKAY;
                            end
 003977                     6'h01: begin // 0x04 VERSION
 003977                         s_axil_rdata <= CONST_VERSION;
 003977                         s_axil_rresp <= RESP_OKAY;
                            end
 002089                     6'h02: begin // 0x08 SCRATCH
 002089                         s_axil_rdata <= reg_scratch;
 002089                         s_axil_rresp <= RESP_OKAY;
                            end
 002070                     6'h03: begin // 0x0C SCRATCH2
 002070                         s_axil_rdata <= reg_scratch2;
 002070                         s_axil_rresp <= RESP_OKAY;
                            end
 001967                     6'h04: begin // 0x10 IRQ_RAW
 001967                         s_axil_rdata <= reg_irq_raw;
 001967                         s_axil_rresp <= RESP_OKAY;
                            end
 001937                     6'h05: begin // 0x14 IRQ_MASK
 001937                         s_axil_rdata <= {29'b0, reg_irq_mask};
 001937                         s_axil_rresp <= RESP_OKAY;
                            end
 002004                     6'h06: begin // 0x18 IRQ_STATUS
 002004                         s_axil_rdata <= reg_irq_status;
 002004                         s_axil_rresp <= RESP_OKAY;
                            end
 001949                     6'h07: begin // 0x1C W1C_TEST
 001949                         s_axil_rdata <= reg_w1c_test;
 001949                         s_axil_rresp <= RESP_OKAY;
                            end
%000000                     6'h08: begin // 0x20 W1C_SET is WO, returns 0 on read
%000000                         s_axil_rdata <= 32'h0;
%000000                         s_axil_rresp <= RESP_OKAY;
                            end
%000002                     default: begin // Undefined word offset -> SLVERR
%000002                         s_axil_rdata <= 32'h0;
%000002                         s_axil_rresp <= RESP_SLVERR;
                            end
                        endcase
 895129             end else if (s_axil_rvalid && s_axil_rready) begin
 020039                 s_axil_rvalid <= 1'b0;
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
                    // Constant identifiers & Rule 6 (address bits [1:0] ignored -> unaligned bytes resolve to word offset)
                    if ($past(rst_n) && $past(s_axil_arvalid && s_axil_arready)) begin
                        if ($past(read_word == 6'h00)) begin
                            assert (s_axil_rvalid && s_axil_rresp == RESP_OKAY && s_axil_rdata == CONST_ID);
                        end else if ($past(read_word == 6'h01)) begin
                            assert (s_axil_rvalid && s_axil_rresp == RESP_OKAY && s_axil_rdata == CONST_VERSION);
                        end else if ($past(read_word <= 6'h08)) begin
                            assert (s_axil_rvalid && s_axil_rresp == RESP_OKAY);
                        end else begin
                            assert (s_axil_rvalid && s_axil_rresp == RESP_SLVERR && s_axil_rdata == 32'h0);
                        end
                    end
        
                    // Write Rule 6 response check: word offsets 0..8 -> OKAY, undefined word offsets -> SLVERR
                    if ($past(rst_n) && $past((s_axil_awvalid && s_axil_awready || aw_done) &&
                                              (s_axil_wvalid && s_axil_wready || w_done) &&
                                              (!s_axil_bvalid || s_axil_bready))) begin
                        if ($past(write_word <= 6'h08)) begin
                            assert (s_axil_bvalid && s_axil_bresp == RESP_OKAY);
                        end else begin
                            assert (s_axil_bvalid && s_axil_bresp == RESP_SLVERR);
                        end
                    end
        
                    // IRQ aggregation
                    assert (irq_o == |reg_irq_status[2:0]);
                    assert (reg_irq_raw == {29'b0, irq_sources});
                end
            end
        
            // Shared Protocol Checker (`FORMAL_CAUSALITY` enabled in bounded BMC;
            // disabled in unbounded k-induction because axil_props uses 8-bit wrapping counters)
            axil_props #(
                .ADDR_WIDTH(ADDR_WIDTH),
                .DATA_WIDTH(DATA_WIDTH),
                .STRB_WIDTH(DATA_WIDTH / 8),
                .IS_SLAVE(1),
                .SINGLE_OUTSTANDING(1),
        `ifdef FORMAL_CAUSALITY
                .CHECK_CAUSALITY(1)
        `else
                .CHECK_CAUSALITY(0)
        `endif
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
        
