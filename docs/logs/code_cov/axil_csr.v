//      // verilator_coverage annotation
        // AXI4-Lite CSR Block with RO, RW, W1C registers and IRQ aggregation
        `timescale 1ns/1ps
        
        module axil_csr #(
            parameter integer ADDR_WIDTH = 32,
            parameter integer DATA_WIDTH = 32
        ) (
 100022     input  wire                  clk,
~000014     input  wire                  rst_n,
        
            // AXI4-Lite Slave Interface
~002352     input  wire [ADDR_WIDTH-1:0] s_axil_awaddr,
 002148     input  wire [2:0]            s_axil_awprot,
 002511     input  wire                  s_axil_awvalid,
 000855     output reg                   s_axil_awready,
        
 002216     input  wire [DATA_WIDTH-1:0] s_axil_wdata,
 002164     input  wire [(DATA_WIDTH/8)-1:0] s_axil_wstrb,
 002511     input  wire                  s_axil_wvalid,
~000014     output reg                   s_axil_wready,
        
%000003     output reg  [1:0]            s_axil_bresp,
 002511     output reg                   s_axil_bvalid,
 002511     input  wire                  s_axil_bready,
        
~002397     input  wire [ADDR_WIDTH-1:0] s_axil_araddr,
 002193     input  wire [2:0]            s_axil_arprot,
 002489     input  wire                  s_axil_arvalid,
~000014     output reg                   s_axil_arready,
        
 000613     output reg  [DATA_WIDTH-1:0] s_axil_rdata,
%000003     output reg  [1:0]            s_axil_rresp,
 002489     output reg                   s_axil_rvalid,
 002489     input  wire                  s_axil_rready,
        
            // Interrupt subsystem
%000002     input  wire [2:0]            irq_sources, // [0] UART, [1] Timer, [2] GPIO
%000006     output wire                  irq_o
        );
        
            localparam [1:0] RESP_OKAY   = 2'b00;
            localparam [1:0] RESP_SLVERR = 2'b10;
        
            localparam [31:0] CONST_ID      = 32'hA3BA_0001;
            localparam [31:0] CONST_VERSION = 32'h0001_0000;
        
            // Lint suppression for unused bits
            wire _unused_bits = &{1'b0, s_axil_awprot, s_axil_arprot, s_axil_awaddr[ADDR_WIDTH-1:8], s_axil_araddr[ADDR_WIDTH-1:8], s_axil_awaddr[1:0], s_axil_araddr[1:0]};
        
            // Registers
 000106     reg [31:0] reg_scratch;
 000077     reg [31:0] reg_scratch2;
 000170     reg [2:0]  reg_irq_mask;
 000119     reg [31:0] reg_w1c_test;
        
%000002     wire [31:0] reg_irq_raw    = {29'b0, irq_sources};
%000006     wire [31:0] reg_irq_status = {29'b0, irq_sources & reg_irq_mask};
        
~620189     assign irq_o = |(reg_irq_status[2:0]);
        
            // Latch channels
~000616     reg [7:0] awoffset_q;
 000841     reg       aw_done;
 000646     reg [DATA_WIDTH-1:0] wdata_q;
 000627     reg [(DATA_WIDTH/8)-1:0] wstrb_q;
%000000     reg       w_done;
        
~624103     wire [7:0] write_offset = (aw_done ? awoffset_q : s_axil_awaddr[7:0]);
~629953     wire [DATA_WIDTH-1:0] write_data = (w_done ? wdata_q : s_axil_wdata);
~629953     wire [(DATA_WIDTH/8)-1:0] write_strb = (w_done ? wstrb_q : s_axil_wstrb);
        
            // --- Write Channel ---
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             s_axil_awready <= 1'b0;
 000171             s_axil_wready  <= 1'b0;
 000171             s_axil_bvalid  <= 1'b0;
 000171             s_axil_bresp   <= 2'b00;
 000171             aw_done        <= 1'b0;
 000171             w_done         <= 1'b0;
 000171             awoffset_q     <= 8'h00;
 000171             wdata_q        <= {DATA_WIDTH{1'b0}};
 000171             wstrb_q        <= {(DATA_WIDTH/8){1'b0}};
        
 000171             reg_scratch    <= 32'h0;
 000171             reg_scratch2   <= 32'h0;
 000171             reg_irq_mask   <= 3'b0;
 000171             reg_w1c_test   <= 32'h0;
 099859         end else begin
~099859             s_axil_awready <= (!s_axil_bvalid || s_axil_bready) && !aw_done;
~099859             s_axil_wready  <= (!s_axil_bvalid || s_axil_bready) && !w_done;
        
 097348             if (s_axil_awvalid && s_axil_awready) begin
 002511                 awoffset_q <= s_axil_awaddr[7:0];
 002511                 aw_done    <= 1'b1;
                    end
        
 097348             if (s_axil_wvalid && s_axil_wready) begin
 002511                 wdata_q    <= s_axil_wdata;
 002511                 wstrb_q    <= s_axil_wstrb;
 002511                 w_done     <= 1'b1;
                    end
        
 002511             if ((s_axil_awvalid && s_axil_awready || aw_done) &&
~097348                 (s_axil_wvalid && s_axil_wready || w_done) &&
 002511                 (!s_axil_bvalid || s_axil_bready)) begin
 002511                 s_axil_bvalid <= 1'b1;
 002511                 aw_done       <= 1'b0;
 002511                 w_done        <= 1'b0;
        
 002511                 case (write_offset)
%000000                     8'h00: begin // ID: Read-Only, writes ignored with OKAY
%000000                         s_axil_bresp <= RESP_OKAY;
                            end
%000000                     8'h04: begin // VERSION: Read-Only, writes ignored with OKAY
%000000                         s_axil_bresp <= RESP_OKAY;
                            end
 000416                     8'h08: begin // SCRATCH: Full-word RW
 000416                         s_axil_bresp <= RESP_OKAY;
 000416                         reg_scratch  <= write_data;
                            end
 000600                     8'h0C: begin // SCRATCH2: Byte-writable via WSTRB
 000600                         s_axil_bresp <= RESP_OKAY;
 000342                         if (write_strb[0]) reg_scratch2[7:0]   <= write_data[7:0];
 000322                         if (write_strb[1]) reg_scratch2[15:8]  <= write_data[15:8];
 000339                         if (write_strb[2]) reg_scratch2[23:16] <= write_data[23:16];
 000346                         if (write_strb[3]) reg_scratch2[31:24] <= write_data[31:24];
                            end
%000000                     8'h10: begin // IRQ_RAW: RO
%000000                         s_axil_bresp <= RESP_OKAY;
                            end
 000632                     8'h14: begin // IRQ_MASK: RW
 000632                         s_axil_bresp <= RESP_OKAY;
 000632                         reg_irq_mask <= write_data[2:0];
                            end
%000000                     8'h18: begin // IRQ_STATUS: RO
%000000                         s_axil_bresp <= RESP_OKAY;
                            end
 000434                     8'h1C: begin // W1C_TEST: writing 1 clears bit
 000434                         s_axil_bresp <= RESP_OKAY;
 000434                         reg_w1c_test <= reg_w1c_test & ~write_data;
                            end
 000426                     8'h20: begin // W1C_SET: WO test hook, sets bit in W1C_TEST
 000426                         s_axil_bresp <= RESP_OKAY;
 000426                         reg_w1c_test <= reg_w1c_test | write_data;
                            end
%000003                     default: begin // Undefined offset -> SLVERR
%000003                         s_axil_bresp <= RESP_SLVERR;
                            end
                        endcase
 094837             end else if (s_axil_bvalid && s_axil_bready) begin
 002511                 s_axil_bvalid <= 1'b0;
                    end
                end
            end
        
            // --- Read Channel ---
~002153     wire [7:0] read_offset = s_axil_araddr[7:0];
        
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             s_axil_arready <= 1'b0;
 000171             s_axil_rvalid  <= 1'b0;
 000171             s_axil_rresp   <= 2'b00;
 000171             s_axil_rdata   <= {DATA_WIDTH{1'b0}};
 099859         end else begin
~099859             s_axil_arready <= !s_axil_rvalid || s_axil_rready;
        
 097370             if (s_axil_arvalid && s_axil_arready) begin
 002489                 s_axil_rvalid <= 1'b1;
 002489                 case (read_offset)
 000519                     8'h00: begin
 000519                         s_axil_rdata <= CONST_ID;
 000519                         s_axil_rresp <= RESP_OKAY;
                            end
 000479                     8'h04: begin
 000479                         s_axil_rdata <= CONST_VERSION;
 000479                         s_axil_rresp <= RESP_OKAY;
                            end
 000255                     8'h08: begin
 000255                         s_axil_rdata <= reg_scratch;
 000255                         s_axil_rresp <= RESP_OKAY;
                            end
 000260                     8'h0C: begin
 000260                         s_axil_rdata <= reg_scratch2;
 000260                         s_axil_rresp <= RESP_OKAY;
                            end
 000244                     8'h10: begin
 000244                         s_axil_rdata <= reg_irq_raw;
 000244                         s_axil_rresp <= RESP_OKAY;
                            end
 000251                     8'h14: begin
 000251                         s_axil_rdata <= {29'b0, reg_irq_mask};
 000251                         s_axil_rresp <= RESP_OKAY;
                            end
 000240                     8'h18: begin
 000240                         s_axil_rdata <= reg_irq_status;
 000240                         s_axil_rresp <= RESP_OKAY;
                            end
 000238                     8'h1C: begin
 000238                         s_axil_rdata <= reg_w1c_test;
 000238                         s_axil_rresp <= RESP_OKAY;
                            end
%000000                     8'h20: begin // W1C_SET is WO, returns 0 on read
%000000                         s_axil_rdata <= 32'h0;
%000000                         s_axil_rresp <= RESP_OKAY;
                            end
%000003                     default: begin // Undefined offset -> SLVERR
%000003                         s_axil_rdata <= 32'h0;
%000003                         s_axil_rresp <= RESP_SLVERR;
                            end
                        endcase
 094881             end else if (s_axil_rvalid && s_axil_rready) begin
 002489                 s_axil_rvalid <= 1'b0;
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
        
