//      // verilator_coverage annotation
        // rtl/axil/axil_xbar.v
        // AXI4-Lite 2-Master x 4-Slave Crossbar with internal Default Slave
        // Features: Address decoding, per-target round-robin arbitration, transaction locking, 0-cycle added latency
        `timescale 1ns / 1ps
        
        module axil_xbar #(
            parameter DATA_WIDTH  = 32,
            parameter ADDR_WIDTH  = 32,
            parameter STRB_WIDTH  = DATA_WIDTH / 8,
            parameter NUM_MASTERS = 2,
            parameter NUM_SLAVES  = 4
        )(
 935460     input  wire                                clk,
~000021     input  wire                                rst_n,
        
            // Master Ports (flattened for 2 masters: [0] = M0, [1] = M1)
~012659     input  wire [NUM_MASTERS*ADDR_WIDTH-1:0]   s_axil_awaddr,
 012576     input  wire [NUM_MASTERS*3-1:0]            s_axil_awprot,
 050398     input  wire [NUM_MASTERS-1:0]              s_axil_awvalid,
 050398     output reg  [NUM_MASTERS-1:0]              s_axil_awready,
        
 012759     input  wire [NUM_MASTERS*DATA_WIDTH-1:0]   s_axil_wdata,
 012518     input  wire [NUM_MASTERS*STRB_WIDTH-1:0]   s_axil_wstrb,
 050398     input  wire [NUM_MASTERS-1:0]              s_axil_wvalid,
 050398     output reg  [NUM_MASTERS-1:0]              s_axil_wready,
        
 009618     output reg  [NUM_MASTERS*2-1:0]            s_axil_bresp,
 050398     output reg  [NUM_MASTERS-1:0]              s_axil_bvalid,
 050398     input  wire [NUM_MASTERS-1:0]              s_axil_bready,
        
~012202     input  wire [NUM_MASTERS*ADDR_WIDTH-1:0]   s_axil_araddr,
 012533     input  wire [NUM_MASTERS*3-1:0]            s_axil_arprot,
 050252     input  wire [NUM_MASTERS-1:0]              s_axil_arvalid,
 050252     output reg  [NUM_MASTERS-1:0]              s_axil_arready,
        
 021506     output reg  [NUM_MASTERS*DATA_WIDTH-1:0]   s_axil_rdata,
 009576     output reg  [NUM_MASTERS*2-1:0]            s_axil_rresp,
 050252     output reg  [NUM_MASTERS-1:0]              s_axil_rvalid,
 050252     input  wire [NUM_MASTERS-1:0]              s_axil_rready,
        
            // Slave Ports (flattened for 4 slaves: S0..S3)
~022352     output reg  [NUM_SLAVES*ADDR_WIDTH-1:0]    m_axil_awaddr,
 021549     output reg  [NUM_SLAVES*3-1:0]             m_axil_awprot,
 040047     output reg  [NUM_SLAVES-1:0]               m_axil_awvalid,
 028542     input  wire [NUM_SLAVES-1:0]               m_axil_awready,
        
 021652     output reg  [NUM_SLAVES*DATA_WIDTH-1:0]    m_axil_wdata,
 021394     output reg  [NUM_SLAVES*STRB_WIDTH-1:0]    m_axil_wstrb,
 040047     output reg  [NUM_SLAVES-1:0]               m_axil_wvalid,
 022856     input  wire [NUM_SLAVES-1:0]               m_axil_wready,
        
~002781     input  wire [NUM_SLAVES*2-1:0]             m_axil_bresp,
 040047     input  wire [NUM_SLAVES-1:0]               m_axil_bvalid,
 040047     output reg  [NUM_SLAVES-1:0]               m_axil_bready,
        
~021776     output reg  [NUM_SLAVES*ADDR_WIDTH-1:0]    m_axil_araddr,
 021568     output reg  [NUM_SLAVES*3-1:0]             m_axil_arprot,
 039918     output reg  [NUM_SLAVES-1:0]               m_axil_arvalid,
 022729     input  wire [NUM_SLAVES-1:0]               m_axil_arready,
        
 008661     input  wire [NUM_SLAVES*DATA_WIDTH-1:0]    m_axil_rdata,
~002807     input  wire [NUM_SLAVES*2-1:0]             m_axil_rresp,
 039918     input  wire [NUM_SLAVES-1:0]               m_axil_rvalid,
 039918     output reg  [NUM_SLAVES-1:0]               m_axil_rready
        `ifdef FORMAL
            ,output wire [NUM_SLAVES:0]                f_wr_prio_o,
            output wire [NUM_SLAVES:0]                 f_rd_prio_o,
            output wire [NUM_SLAVES:0]                 f_wr_locked_o,
            output wire [NUM_SLAVES:0]                 f_wr_owner_o,
            output wire [NUM_SLAVES:0]                 f_rd_locked_o,
            output wire [NUM_SLAVES:0]                 f_rd_owner_o,
            output wire [NUM_SLAVES:0]                 f_wr_req0_o,
            output wire [NUM_SLAVES:0]                 f_wr_req1_o,
            output wire [NUM_SLAVES:0]                 f_rd_req0_o,
            output wire [NUM_SLAVES:0]                 f_rd_req1_o
        `endif
        );
        
            localparam NUM_TARGETS = NUM_SLAVES + 1; // 4 external slaves + 1 default slave
        
            // Unpack Master Channels
~012659     wire [ADDR_WIDTH-1:0] m_awaddr  [0:NUM_MASTERS-1];
 012576     wire [2:0]            m_awprot  [0:NUM_MASTERS-1];
 012759     wire [DATA_WIDTH-1:0] m_wdata   [0:NUM_MASTERS-1];
 012518     wire [STRB_WIDTH-1:0] m_wstrb   [0:NUM_MASTERS-1];
~012202     wire [ADDR_WIDTH-1:0] m_araddr  [0:NUM_MASTERS-1];
 012533     wire [2:0]            m_arprot  [0:NUM_MASTERS-1];
        
            genvar gm;
            generate
                for (gm = 0; gm < NUM_MASTERS; gm = gm + 1) begin : gen_unpack_m
                    assign m_awaddr[gm] = s_axil_awaddr[gm*ADDR_WIDTH +: ADDR_WIDTH];
                    assign m_awprot[gm] = s_axil_awprot[gm*3 +: 3];
                    assign m_wdata[gm]  = s_axil_wdata[gm*DATA_WIDTH +: DATA_WIDTH];
                    assign m_wstrb[gm]  = s_axil_wstrb[gm*STRB_WIDTH +: STRB_WIDTH];
                    assign m_araddr[gm] = s_axil_araddr[gm*ADDR_WIDTH +: ADDR_WIDTH];
                    assign m_arprot[gm] = s_axil_arprot[gm*3 +: 3];
                end
            endgenerate
        
            // Address Decoders for Masters
 012145     wire [3:0] dec_aw_sel [0:NUM_MASTERS-1];
 004529     wire       dec_aw_err [0:NUM_MASTERS-1];
 012057     wire [3:0] dec_ar_sel [0:NUM_MASTERS-1];
 004510     wire       dec_ar_err [0:NUM_MASTERS-1];
        
 012145     wire [NUM_TARGETS-1:0] m_aw_tgt [0:NUM_MASTERS-1];
 012057     wire [NUM_TARGETS-1:0] m_ar_tgt [0:NUM_MASTERS-1];
        
            generate
                for (gm = 0; gm < NUM_MASTERS; gm = gm + 1) begin : gen_dec
                    axil_decoder u_dec_aw (
                        .addr       (m_awaddr[gm]),
                        .slave_sel  (dec_aw_sel[gm]),
                        .decode_err (dec_aw_err[gm])
                    );
                    assign m_aw_tgt[gm] = {dec_aw_err[gm], dec_aw_sel[gm]};
        
                    axil_decoder u_dec_ar (
                        .addr       (m_araddr[gm]),
                        .slave_sel  (dec_ar_sel[gm]),
                        .decode_err (dec_ar_err[gm])
                    );
                    assign m_ar_tgt[gm] = {dec_ar_err[gm], dec_ar_sel[gm]};
                end
            endgenerate
        
            // Internal Default Slave Signals (Target 4)
~015319     wire [ADDR_WIDTH-1:0] def_awaddr;
 014753     wire [2:0]            def_awprot;
 009991     wire                  def_awvalid;
 007190     wire                  def_awready;
 014844     wire [DATA_WIDTH-1:0] def_wdata;
 014653     wire [STRB_WIDTH-1:0] def_wstrb;
 009991     wire                  def_wvalid;
 005756     wire                  def_wready;
~000021     wire [1:0]            def_bresp;
 009991     wire                  def_bvalid;
 009991     wire                  def_bready;
~014456     wire [ADDR_WIDTH-1:0] def_araddr;
 014712     wire [2:0]            def_arprot;
 009856     wire                  def_arvalid;
 005653     wire                  def_arready;
%000000     wire [DATA_WIDTH-1:0] def_rdata;
~000021     wire [1:0]            def_rresp;
 009856     wire                  def_rvalid;
 009856     wire                  def_rready;
        
            axil_default_slave #(
                .DATA_WIDTH (DATA_WIDTH),
                .ADDR_WIDTH (ADDR_WIDTH)
            ) u_default_slave (
                .clk          (clk),
                .rst_n        (rst_n),
                .s_axil_awaddr(def_awaddr),
                .s_axil_awprot(def_awprot),
                .s_axil_awvalid(def_awvalid),
                .s_axil_awready(def_awready),
                .s_axil_wdata (def_wdata),
                .s_axil_wstrb (def_wstrb),
                .s_axil_wvalid(def_wvalid),
                .s_axil_wready(def_wready),
                .s_axil_bresp (def_bresp),
                .s_axil_bvalid(def_bvalid),
                .s_axil_bready(def_bready),
                .s_axil_araddr(def_araddr),
                .s_axil_arprot(def_arprot),
                .s_axil_arvalid(def_arvalid),
                .s_axil_arready(def_arready),
                .s_axil_rdata (def_rdata),
                .s_axil_rresp (def_rresp),
                .s_axil_rvalid(def_rvalid),
                .s_axil_rready(def_rready)
            );
        
            // Target Signals Muxing/Demuxing Arrays
~022352     wire [ADDR_WIDTH-1:0] tgt_awaddr  [0:NUM_TARGETS-1];
 021549     wire [2:0]            tgt_awprot  [0:NUM_TARGETS-1];
 040047     wire                  tgt_awvalid [0:NUM_TARGETS-1];
 028542     wire                  tgt_awready [0:NUM_TARGETS-1];
 021652     wire [DATA_WIDTH-1:0] tgt_wdata   [0:NUM_TARGETS-1];
 021394     wire [STRB_WIDTH-1:0] tgt_wstrb   [0:NUM_TARGETS-1];
 040047     wire                  tgt_wvalid  [0:NUM_TARGETS-1];
 022856     wire                  tgt_wready  [0:NUM_TARGETS-1];
~002781     wire [1:0]            tgt_bresp   [0:NUM_TARGETS-1];
 040047     wire                  tgt_bvalid  [0:NUM_TARGETS-1];
 040047     wire                  tgt_bready  [0:NUM_TARGETS-1];
        
~021776     wire [ADDR_WIDTH-1:0] tgt_araddr  [0:NUM_TARGETS-1];
 021568     wire [2:0]            tgt_arprot  [0:NUM_TARGETS-1];
 039918     wire                  tgt_arvalid [0:NUM_TARGETS-1];
 022729     wire                  tgt_arready [0:NUM_TARGETS-1];
~008661     wire [DATA_WIDTH-1:0] tgt_rdata   [0:NUM_TARGETS-1];
~002807     wire [1:0]            tgt_rresp   [0:NUM_TARGETS-1];
 039918     wire                  tgt_rvalid  [0:NUM_TARGETS-1];
 039918     wire                  tgt_rready  [0:NUM_TARGETS-1];
        
            // Connect Slaves 0..3 to External Ports
            genvar gs;
            generate
 000084         for (gs = 0; gs < NUM_SLAVES; gs = gs + 1) begin : gen_slaves
 000084             always @(*) begin
 000084                 m_axil_awaddr[gs*ADDR_WIDTH +: ADDR_WIDTH] = tgt_awaddr[gs];
 000084                 m_axil_awprot[gs*3 +: 3]                   = tgt_awprot[gs];
 000084                 m_axil_awvalid[gs]                         = tgt_awvalid[gs];
 000084                 m_axil_wdata[gs*DATA_WIDTH +: DATA_WIDTH]  = tgt_wdata[gs];
 000084                 m_axil_wstrb[gs*STRB_WIDTH +: STRB_WIDTH]  = tgt_wstrb[gs];
 000084                 m_axil_wvalid[gs]                          = tgt_wvalid[gs];
 000084                 m_axil_bready[gs]                          = tgt_bready[gs];
 000084                 m_axil_araddr[gs*ADDR_WIDTH +: ADDR_WIDTH] = tgt_araddr[gs];
 000084                 m_axil_arprot[gs*3 +: 3]                   = tgt_arprot[gs];
 000084                 m_axil_arvalid[gs]                         = tgt_arvalid[gs];
 000084                 m_axil_rready[gs]                          = tgt_rready[gs];
                    end
                    assign tgt_awready[gs] = m_axil_awready[gs];
                    assign tgt_wready[gs]  = m_axil_wready[gs];
                    assign tgt_bresp[gs]   = m_axil_bresp[gs*2 +: 2];
                    assign tgt_bvalid[gs]  = m_axil_bvalid[gs];
                    assign tgt_arready[gs] = m_axil_arready[gs];
                    assign tgt_rdata[gs]   = m_axil_rdata[gs*DATA_WIDTH +: DATA_WIDTH];
                    assign tgt_rresp[gs]   = m_axil_rresp[gs*2 +: 2];
                    assign tgt_rvalid[gs]  = m_axil_rvalid[gs];
                end
            endgenerate
        
            // Connect Target 4 to Internal Default Slave
            assign def_awaddr      = tgt_awaddr[4];
            assign def_awprot      = tgt_awprot[4];
            assign def_awvalid     = tgt_awvalid[4];
            assign tgt_awready[4]  = def_awready;
            assign def_wdata       = tgt_wdata[4];
            assign def_wstrb       = tgt_wstrb[4];
            assign def_wvalid      = tgt_wvalid[4];
            assign tgt_wready[4]   = def_wready;
            assign tgt_bresp[4]    = def_bresp;
            assign tgt_bvalid[4]   = def_bvalid;
            assign def_bready      = tgt_bready[4];
            assign def_araddr      = tgt_araddr[4];
            assign def_arprot      = tgt_arprot[4];
            assign def_arvalid     = tgt_arvalid[4];
            assign tgt_arready[4]  = def_arready;
            assign tgt_rdata[4]    = def_rdata;
            assign tgt_rresp[4]    = def_rresp;
            assign tgt_rvalid[4]   = def_rvalid;
            assign def_rready      = tgt_rready[4];
        
            // Master In-Flight Status
 040047     reg [NUM_TARGETS-1:0] wr_locked;
 009188     reg                   wr_owner [0:NUM_TARGETS-1];
 040047     reg [NUM_TARGETS-1:0] aw_done;
 040047     reg [NUM_TARGETS-1:0] w_done;
 009189     reg [NUM_TARGETS-1:0] wr_prio;
        
 039918     reg [NUM_TARGETS-1:0] rd_locked;
 009047     reg                   rd_owner [0:NUM_TARGETS-1];
 039918     reg [NUM_TARGETS-1:0] ar_done;
 009043     reg [NUM_TARGETS-1:0] rd_prio;
        
 050005     wire m0_wr_busy = (wr_locked[0] && wr_owner[0] == 0) ||
                              (wr_locked[1] && wr_owner[1] == 0) ||
                              (wr_locked[2] && wr_owner[2] == 0) ||
                              (wr_locked[3] && wr_owner[3] == 0) ||
                              (wr_locked[4] && wr_owner[4] == 0);
        
 050398     wire m1_wr_busy = (wr_locked[0] && wr_owner[0] == 1) ||
                              (wr_locked[1] && wr_owner[1] == 1) ||
                              (wr_locked[2] && wr_owner[2] == 1) ||
                              (wr_locked[3] && wr_owner[3] == 1) ||
                              (wr_locked[4] && wr_owner[4] == 1);
        
 050252     wire m0_rd_busy = (rd_locked[0] && rd_owner[0] == 0) ||
                              (rd_locked[1] && rd_owner[1] == 0) ||
                              (rd_locked[2] && rd_owner[2] == 0) ||
                              (rd_locked[3] && rd_owner[3] == 0) ||
                              (rd_locked[4] && rd_owner[4] == 0);
        
 049704     wire m1_rd_busy = (rd_locked[0] && rd_owner[0] == 1) ||
                              (rd_locked[1] && rd_owner[1] == 1) ||
                              (rd_locked[2] && rd_owner[2] == 1) ||
                              (rd_locked[3] && rd_owner[3] == 1) ||
                              (rd_locked[4] && rd_owner[4] == 1);
        
            // =========================================================================
            // WRITE PATH LOGIC (Per Target)
            // =========================================================================
 020100     wire [1:0] wr_req   [0:NUM_TARGETS-1];
 020100     wire [1:0] wr_grant [0:NUM_TARGETS-1];
 020100     wire       active_wr_owner [0:NUM_TARGETS-1];
 037101     wire       wr_active       [0:NUM_TARGETS-1];
        
            genvar gt;
            generate
 4814803         for (gt = 0; gt < NUM_TARGETS; gt = gt + 1) begin : gen_wr_target
                    // Request vector: only valid if master is not currently locked on another transaction
 26084205             assign wr_req[gt][0] = s_axil_awvalid[0] && m_aw_tgt[0][gt] && (!m0_wr_busy || (wr_locked[gt] && wr_owner[gt] == 0));
 26030170             assign wr_req[gt][1] = s_axil_awvalid[1] && m_aw_tgt[1][gt] && (!m1_wr_busy || (wr_locked[gt] && wr_owner[gt] == 1));
        
                    // Round-robin arbitration between M0 and M1
 6104080             assign wr_grant[gt][0] = wr_req[gt][0] && (!wr_req[gt][1] || (wr_prio[gt] == 1'b0));
 6104412             assign wr_grant[gt][1] = wr_req[gt][1] && (!wr_req[gt][0] || (wr_prio[gt] == 1'b1));
        
 25884207             assign active_wr_owner[gt] = wr_locked[gt] ? wr_owner[gt] : (wr_grant[gt][1] ? 1'b1 : 1'b0);
 5873567             assign wr_active[gt]       = wr_locked[gt] || (|wr_grant[gt]);
        
                    // Drive target AW signals
                    assign tgt_awaddr[gt]  = m_awaddr[active_wr_owner[gt]];
                    assign tgt_awprot[gt]  = m_awprot[active_wr_owner[gt]];
 5873567             assign tgt_awvalid[gt] = wr_active[gt] && !aw_done[gt] && s_axil_awvalid[active_wr_owner[gt]];
        
                    // Drive target W signals
                    assign tgt_wdata[gt]   = m_wdata[active_wr_owner[gt]];
                    assign tgt_wstrb[gt]   = m_wstrb[active_wr_owner[gt]];
 5873567             assign tgt_wvalid[gt]  = wr_active[gt] && !w_done[gt] && s_axil_wvalid[active_wr_owner[gt]];
        
                    // B channel response ready
 25884207             assign tgt_bready[gt]  = wr_locked[gt] ? s_axil_bready[active_wr_owner[gt]] : 1'b0;
        
 6081999             wire aw_hs = tgt_awvalid[gt] && tgt_awready[gt];
 6081806             wire w_hs  = tgt_wvalid[gt]  && tgt_wready[gt];
 6081673             wire b_hs  = tgt_bvalid[gt]  && tgt_bready[gt];
        
 4677300             always @(posedge clk or negedge rst_n) begin
 4676035                 if (!rst_n) begin
 001265                     wr_locked[gt] <= 1'b0;
 001265                     wr_owner[gt]  <= 1'b0;
 001265                     aw_done[gt]   <= 1'b0;
 001265                     w_done[gt]    <= 1'b0;
 001265                     wr_prio[gt]   <= 1'b0;
 4676035                 end else begin
                            // Lock target to granted master as soon as transfer begins
 4575632                     if (wr_active[gt] && !wr_locked[gt]) begin
 100403                         wr_locked[gt] <= 1'b1;
 100403                         wr_owner[gt]  <= active_wr_owner[gt];
                            end
        
                            // AW tracking
 4575632                     if (aw_hs) begin
 100403                         aw_done[gt] <= 1'b1;
                            end
        
                            // W tracking
 4575632                     if (w_hs) begin
 100403                         w_done[gt]  <= 1'b1;
                            end
        
                            // B completion & lock release
 4575632                     if (b_hs) begin
 100403                         wr_locked[gt] <= 1'b0;
 100403                         aw_done[gt]   <= 1'b0;
 100403                         w_done[gt]    <= 1'b0;
 100403                         wr_prio[gt]   <= ~active_wr_owner[gt]; // Rotate priority
                            end
                        end
                    end
                end
            endgenerate
        
            // Aggregate Master Write Feedback
            integer im;
 6139802     always @(*) begin
 6139802         s_axil_awready = {NUM_MASTERS{1'b0}};
 6139802         s_axil_wready  = {NUM_MASTERS{1'b0}};
 6139802         s_axil_bvalid  = {NUM_MASTERS{1'b0}};
 6139802         s_axil_bresp   = {NUM_MASTERS*2{1'b0}};
        
 12279604         for (im = 0; im < NUM_MASTERS; im = im + 1) begin
                    // M0
 6139802             if (im == 0) begin
                        // AWREADY
 5415010                 if (wr_active[0] && active_wr_owner[0] == 0 && !aw_done[0] && m_aw_tgt[0][0]) s_axil_awready[0] = tgt_awready[0];
 4986567                 else if (wr_active[1] && active_wr_owner[1] == 0 && !aw_done[1] && m_aw_tgt[0][1]) s_axil_awready[0] = tgt_awready[1];
 5401155                 else if (wr_active[2] && active_wr_owner[2] == 0 && !aw_done[2] && m_aw_tgt[0][2]) s_axil_awready[0] = tgt_awready[2];
 3789709                 else if (wr_active[3] && active_wr_owner[3] == 0 && !aw_done[3] && m_aw_tgt[0][3]) s_axil_awready[0] = tgt_awready[3];
 5524740                 else if (wr_active[4] && active_wr_owner[4] == 0 && !aw_done[4] && m_aw_tgt[0][4]) s_axil_awready[0] = tgt_awready[4];
        
                        // WREADY
 5415010                 if      (wr_active[0] && !w_done[0] && (wr_locked[0] ? (wr_owner[0] == 0) : (active_wr_owner[0] == 0 && m_aw_tgt[0][0]))) s_axil_wready[0] = tgt_wready[0];
 4958184                 else if (wr_active[1] && !w_done[1] && (wr_locked[1] ? (wr_owner[1] == 0) : (active_wr_owner[1] == 0 && m_aw_tgt[0][1]))) s_axil_wready[0] = tgt_wready[1];
 5328336                 else if (wr_active[2] && !w_done[2] && (wr_locked[2] ? (wr_owner[2] == 0) : (active_wr_owner[2] == 0 && m_aw_tgt[0][2]))) s_axil_wready[0] = tgt_wready[2];
 3058924                 else if (wr_active[3] && !w_done[3] && (wr_locked[3] ? (wr_owner[3] == 0) : (active_wr_owner[3] == 0 && m_aw_tgt[0][3]))) s_axil_wready[0] = tgt_wready[3];
 5382159                 else if (wr_active[4] && !w_done[4] && (wr_locked[4] ? (wr_owner[4] == 0) : (active_wr_owner[4] == 0 && m_aw_tgt[0][4]))) s_axil_wready[0] = tgt_wready[4];
        
                        // BVALID & BRESP
 5503151                 if (wr_locked[0] && wr_owner[0] == 0) begin s_axil_bvalid[0] = tgt_bvalid[0]; s_axil_bresp[0*2 +: 2] = tgt_bresp[0]; end
 5015894                 else if (wr_locked[1] && wr_owner[1] == 0) begin s_axil_bvalid[0] = tgt_bvalid[1]; s_axil_bresp[0*2 +: 2] = tgt_bresp[1]; end
 5021398                 else if (wr_locked[2] && wr_owner[2] == 0) begin s_axil_bvalid[0] = tgt_bvalid[2]; s_axil_bresp[0*2 +: 2] = tgt_bresp[2]; end
 2753861                 else if (wr_locked[3] && wr_owner[3] == 0) begin s_axil_bvalid[0] = tgt_bvalid[3]; s_axil_bresp[0*2 +: 2] = tgt_bresp[3]; end
 3753080                 else if (wr_locked[4] && wr_owner[4] == 0) begin s_axil_bvalid[0] = tgt_bvalid[4]; s_axil_bresp[0*2 +: 2] = tgt_bresp[4]; end
                    end
                    // M1
~6139802             else if (im == 1) begin
                        // AWREADY
 5776671                 if (wr_active[0] && active_wr_owner[0] == 1 && !aw_done[0] && m_aw_tgt[1][0]) s_axil_awready[1] = tgt_awready[0];
 5505677                 else if (wr_active[1] && active_wr_owner[1] == 1 && !aw_done[1] && m_aw_tgt[1][1]) s_axil_awready[1] = tgt_awready[1];
 5653528                 else if (wr_active[2] && active_wr_owner[2] == 1 && !aw_done[2] && m_aw_tgt[1][2]) s_axil_awready[1] = tgt_awready[2];
 4439001                 else if (wr_active[3] && active_wr_owner[3] == 1 && !aw_done[3] && m_aw_tgt[1][3]) s_axil_awready[1] = tgt_awready[3];
 5504518                 else if (wr_active[4] && active_wr_owner[4] == 1 && !aw_done[4] && m_aw_tgt[1][4]) s_axil_awready[1] = tgt_awready[4];
        
                        // WREADY
 5415010                 if      (wr_active[0] && !w_done[0] && (wr_locked[0] ? (wr_owner[0] == 1) : (active_wr_owner[0] == 1 && m_aw_tgt[1][0]))) s_axil_wready[1] = tgt_wready[0];
 4957730                 else if (wr_active[1] && !w_done[1] && (wr_locked[1] ? (wr_owner[1] == 1) : (active_wr_owner[1] == 1 && m_aw_tgt[1][1]))) s_axil_wready[1] = tgt_wready[1];
 5326224                 else if (wr_active[2] && !w_done[2] && (wr_locked[2] ? (wr_owner[2] == 1) : (active_wr_owner[2] == 1 && m_aw_tgt[1][2]))) s_axil_wready[1] = tgt_wready[2];
 3054782                 else if (wr_active[3] && !w_done[3] && (wr_locked[3] ? (wr_owner[3] == 1) : (active_wr_owner[3] == 1 && m_aw_tgt[1][3]))) s_axil_wready[1] = tgt_wready[3];
 5358390                 else if (wr_active[4] && !w_done[4] && (wr_locked[4] ? (wr_owner[4] == 1) : (active_wr_owner[4] == 1 && m_aw_tgt[1][4]))) s_axil_wready[1] = tgt_wready[4];
        
                        // BVALID & BRESP
 5503151                 if (wr_locked[0] && wr_owner[0] == 1) begin s_axil_bvalid[1] = tgt_bvalid[0]; s_axil_bresp[1*2 +: 2] = tgt_bresp[0]; end
 5014255                 else if (wr_locked[1] && wr_owner[1] == 1) begin s_axil_bvalid[1] = tgt_bvalid[1]; s_axil_bresp[1*2 +: 2] = tgt_bresp[1]; end
 5012033                 else if (wr_locked[2] && wr_owner[2] == 1) begin s_axil_bvalid[1] = tgt_bvalid[2]; s_axil_bresp[1*2 +: 2] = tgt_bresp[2]; end
 2742115                 else if (wr_locked[3] && wr_owner[3] == 1) begin s_axil_bvalid[1] = tgt_bvalid[3]; s_axil_bresp[1*2 +: 2] = tgt_bresp[3]; end
 3711721                 else if (wr_locked[4] && wr_owner[4] == 1) begin s_axil_bvalid[1] = tgt_bvalid[4]; s_axil_bresp[1*2 +: 2] = tgt_bresp[4]; end
                    end
                end
            end
        
            // =========================================================================
            // READ PATH LOGIC (Per Target)
            // =========================================================================
 020215     wire [1:0] rd_req   [0:NUM_TARGETS-1];
 020215     wire [1:0] rd_grant [0:NUM_TARGETS-1];
 019703     wire       active_rd_owner [0:NUM_TARGETS-1];
 037247     wire       rd_active       [0:NUM_TARGETS-1];
        
            generate
 4366691         for (gt = 0; gt < NUM_TARGETS; gt = gt + 1) begin : gen_rd_target
 26556600             assign rd_req[gt][0] = s_axil_arvalid[0] && m_ar_tgt[0][gt] && (!m0_rd_busy || (rd_locked[gt] && rd_owner[gt] == 0));
 26612970             assign rd_req[gt][1] = s_axil_arvalid[1] && m_ar_tgt[1][gt] && (!m1_rd_busy || (rd_locked[gt] && rd_owner[gt] == 1));
        
 6104570             assign rd_grant[gt][0] = rd_req[gt][0] && (!rd_req[gt][1] || (rd_prio[gt] == 1'b0));
 6105114             assign rd_grant[gt][1] = rd_req[gt][1] && (!rd_req[gt][0] || (rd_prio[gt] == 1'b1));
        
 26332319             assign active_rd_owner[gt] = rd_locked[gt] ? rd_owner[gt] : (rd_grant[gt][1] ? 1'b1 : 1'b0);
 5899460             assign rd_active[gt]       = rd_locked[gt] || (|rd_grant[gt]);
        
                    // Drive target AR signals
                    assign tgt_araddr[gt]  = m_araddr[active_rd_owner[gt]];
                    assign tgt_arprot[gt]  = m_arprot[active_rd_owner[gt]];
 5899460             assign tgt_arvalid[gt] = rd_active[gt] && !ar_done[gt] && s_axil_arvalid[active_rd_owner[gt]];
        
                    // R channel response ready
 26332319             assign tgt_rready[gt]  = rd_locked[gt] ? s_axil_rready[active_rd_owner[gt]] : 1'b0;
        
 6082692             wire ar_hs = tgt_arvalid[gt] && tgt_arready[gt];
 6082390             wire r_hs  = tgt_rvalid[gt]  && tgt_rready[gt];
        
 4677300             always @(posedge clk or negedge rst_n) begin
 4676035                 if (!rst_n) begin
 001265                     rd_locked[gt] <= 1'b0;
 001265                     rd_owner[gt]  <= 1'b0;
 001265                     ar_done[gt]   <= 1'b0;
 001265                     rd_prio[gt]   <= 1'b0;
 4676035                 end else begin
                            // Lock target to granted master as soon as transfer begins
 4576079                     if (rd_active[gt] && !rd_locked[gt]) begin
 099956                         rd_locked[gt] <= 1'b1;
 099956                         rd_owner[gt]  <= active_rd_owner[gt];
                            end
        
                            // AR handshake tracking
 4576079                     if (ar_hs) begin
 099956                         ar_done[gt] <= 1'b1;
                            end
        
                            // R completion & lock release
 4576079                     if (r_hs) begin
 099956                         rd_locked[gt] <= 1'b0;
 099956                         ar_done[gt]   <= 1'b0;
 099956                         rd_prio[gt]   <= ~active_rd_owner[gt]; // Rotate priority
                            end
                        end
                    end
                end
            endgenerate
        
            // Aggregate Master Read Feedback
 6139802     always @(*) begin
 6139802         s_axil_arready = {NUM_MASTERS{1'b0}};
 6139802         s_axil_rvalid  = {NUM_MASTERS{1'b0}};
 6139802         s_axil_rdata   = {NUM_MASTERS*DATA_WIDTH{1'b0}};
 6139802         s_axil_rresp   = {NUM_MASTERS*2{1'b0}};
        
 12279604         for (im = 0; im < NUM_MASTERS; im = im + 1) begin
                    // M0
 6139802             if (im == 0) begin
                        // ARREADY
 5465143                 if (rd_active[0] && active_rd_owner[0] == 0 && !ar_done[0] && m_ar_tgt[0][0]) s_axil_arready[0] = tgt_arready[0];
 5071446                 else if (rd_active[1] && active_rd_owner[1] == 0 && !ar_done[1] && m_ar_tgt[0][1]) s_axil_arready[0] = tgt_arready[1];
 5435081                 else if (rd_active[2] && active_rd_owner[2] == 0 && !ar_done[2] && m_ar_tgt[0][2]) s_axil_arready[0] = tgt_arready[2];
 3870995                 else if (rd_active[3] && active_rd_owner[3] == 0 && !ar_done[3] && m_ar_tgt[0][3]) s_axil_arready[0] = tgt_arready[3];
 5583121                 else if (rd_active[4] && active_rd_owner[4] == 0 && !ar_done[4] && m_ar_tgt[0][4]) s_axil_arready[0] = tgt_arready[4];
        
                        // RVALID, RDATA, RRESP
 5553180                 if (rd_locked[0] && rd_owner[0] == 0) begin s_axil_rvalid[0] = tgt_rvalid[0]; s_axil_rdata[0*DATA_WIDTH +: DATA_WIDTH] = tgt_rdata[0]; s_axil_rresp[0*2 +: 2] = tgt_rresp[0]; end
 5127193                 else if (rd_locked[1] && rd_owner[1] == 0) begin s_axil_rvalid[0] = tgt_rvalid[1]; s_axil_rdata[0*DATA_WIDTH +: DATA_WIDTH] = tgt_rdata[1]; s_axil_rresp[0*2 +: 2] = tgt_rresp[1]; end
 5122371                 else if (rd_locked[2] && rd_owner[2] == 0) begin s_axil_rvalid[0] = tgt_rvalid[2]; s_axil_rdata[0*DATA_WIDTH +: DATA_WIDTH] = tgt_rdata[2]; s_axil_rresp[0*2 +: 2] = tgt_rresp[2]; end
 3016328                 else if (rd_locked[3] && rd_owner[3] == 0) begin s_axil_rvalid[0] = tgt_rvalid[3]; s_axil_rdata[0*DATA_WIDTH +: DATA_WIDTH] = tgt_rdata[3]; s_axil_rresp[0*2 +: 2] = tgt_rresp[3]; end
 3948672                 else if (rd_locked[4] && rd_owner[4] == 0) begin s_axil_rvalid[0] = tgt_rvalid[4]; s_axil_rdata[0*DATA_WIDTH +: DATA_WIDTH] = tgt_rdata[4]; s_axil_rresp[0*2 +: 2] = tgt_rresp[4]; end
                    end
                    // M1
~6139802             else if (im == 1) begin
                        // ARREADY
 5804740                 if (rd_active[0] && active_rd_owner[0] == 1 && !ar_done[0] && m_ar_tgt[1][0]) s_axil_arready[1] = tgt_arready[0];
 5553629                 else if (rd_active[1] && active_rd_owner[1] == 1 && !ar_done[1] && m_ar_tgt[1][1]) s_axil_arready[1] = tgt_arready[1];
 5674574                 else if (rd_active[2] && active_rd_owner[2] == 1 && !ar_done[2] && m_ar_tgt[1][2]) s_axil_arready[1] = tgt_arready[2];
 4571646                 else if (rd_active[3] && active_rd_owner[3] == 1 && !ar_done[3] && m_ar_tgt[1][3]) s_axil_arready[1] = tgt_arready[3];
 5586586                 else if (rd_active[4] && active_rd_owner[4] == 1 && !ar_done[4] && m_ar_tgt[1][4]) s_axil_arready[1] = tgt_arready[4];
        
                        // RVALID, RDATA, RRESP
 5553180                 if (rd_locked[0] && rd_owner[0] == 1) begin s_axil_rvalid[1] = tgt_rvalid[0]; s_axil_rdata[1*DATA_WIDTH +: DATA_WIDTH] = tgt_rdata[0]; s_axil_rresp[1*2 +: 2] = tgt_rresp[0]; end
 5130371                 else if (rd_locked[1] && rd_owner[1] == 1) begin s_axil_rvalid[1] = tgt_rvalid[1]; s_axil_rdata[1*DATA_WIDTH +: DATA_WIDTH] = tgt_rdata[1]; s_axil_rresp[1*2 +: 2] = tgt_rresp[1]; end
 5131495                 else if (rd_locked[2] && rd_owner[2] == 1) begin s_axil_rvalid[1] = tgt_rvalid[2]; s_axil_rdata[1*DATA_WIDTH +: DATA_WIDTH] = tgt_rdata[2]; s_axil_rresp[1*2 +: 2] = tgt_rresp[2]; end
 3026199                 else if (rd_locked[3] && rd_owner[3] == 1) begin s_axil_rvalid[1] = tgt_rvalid[3]; s_axil_rdata[1*DATA_WIDTH +: DATA_WIDTH] = tgt_rdata[3]; s_axil_rresp[1*2 +: 2] = tgt_rresp[3]; end
 3964241                 else if (rd_locked[4] && rd_owner[4] == 1) begin s_axil_rvalid[1] = tgt_rvalid[4]; s_axil_rdata[1*DATA_WIDTH +: DATA_WIDTH] = tgt_rdata[4]; s_axil_rresp[1*2 +: 2] = tgt_rresp[4]; end
                    end
                end
            end
        
        `ifdef FORMAL
            assign f_wr_prio_o   = wr_prio;
            assign f_rd_prio_o   = rd_prio;
            assign f_wr_locked_o = wr_locked;
            assign f_rd_locked_o = rd_locked;
            genvar fg;
            generate
                for (fg = 0; fg < NUM_TARGETS; fg = fg + 1) begin : gen_f_obs
                    assign f_wr_owner_o[fg] = wr_owner[fg];
                    assign f_rd_owner_o[fg] = rd_owner[fg];
                    assign f_wr_req0_o[fg]  = wr_req[fg][0];
                    assign f_wr_req1_o[fg]  = wr_req[fg][1];
                    assign f_rd_req0_o[fg]  = rd_req[fg][0];
                    assign f_rd_req1_o[fg]  = rd_req[fg][1];
                end
            endgenerate
        `endif
        
        endmodule
        
