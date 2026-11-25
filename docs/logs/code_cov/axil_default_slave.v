//      // verilator_coverage annotation
        // AXI4-Lite Default Slave returning DECERR
        `timescale 1ns/1ps
        
        module axil_default_slave #(
            parameter integer ADDR_WIDTH = 32,
            parameter integer DATA_WIDTH = 32
        ) (
 935460     input  wire                  clk,
~000021     input  wire                  rst_n,
        
            // Write address channel
~015319     input  wire [ADDR_WIDTH-1:0] s_axil_awaddr,
 014753     input  wire [2:0]            s_axil_awprot,
 009991     input  wire                  s_axil_awvalid,
 007190     output reg                   s_axil_awready,
        
            // Write data channel
 014844     input  wire [DATA_WIDTH-1:0] s_axil_wdata,
 014653     input  wire [(DATA_WIDTH/8)-1:0] s_axil_wstrb,
 009991     input  wire                  s_axil_wvalid,
 005756     output reg                   s_axil_wready,
        
            // Write response channel
~000021     output reg  [1:0]            s_axil_bresp,
 009991     output reg                   s_axil_bvalid,
 009991     input  wire                  s_axil_bready,
        
            // Read address channel
~014456     input  wire [ADDR_WIDTH-1:0] s_axil_araddr,
 014712     input  wire [2:0]            s_axil_arprot,
 009856     input  wire                  s_axil_arvalid,
 005653     output reg                   s_axil_arready,
        
            // Read data channel
%000000     output reg  [DATA_WIDTH-1:0] s_axil_rdata,
~000021     output reg  [1:0]            s_axil_rresp,
 009856     output reg                   s_axil_rvalid,
 009856     input  wire                  s_axil_rready
        );
        
            localparam [1:0] RESP_DECERR = 2'b11;
        
            // Lint suppression for consumed but unused payload inputs
            wire _unused_inputs = &{1'b0, s_axil_awaddr, s_axil_awprot, s_axil_wdata, s_axil_wstrb, s_axil_araddr, s_axil_arprot};
        
            // Track write handshake completion
 003344     reg aw_done;
%000000     reg w_done;
        
            // --- Write Channel Logic ---
 935460     always @(posedge clk or negedge rst_n) begin
 935207         if (!rst_n) begin
 000253             s_axil_awready <= 1'b0;
 000253             s_axil_wready  <= 1'b0;
 000253             s_axil_bvalid  <= 1'b0;
 000253             s_axil_bresp   <= 2'b00;
 000253             aw_done        <= 1'b0;
 000253             w_done         <= 1'b0;
 935207         end else begin
 935207             s_axil_awready <= (!s_axil_bvalid || s_axil_bready) && !aw_done;
~935207             s_axil_wready  <= (!s_axil_bvalid || s_axil_bready) && !w_done;
        
 925216             if (s_axil_awvalid && s_axil_awready) begin
 009991                 aw_done <= 1'b1;
                    end
        
 925216             if (s_axil_wvalid && s_axil_wready) begin
 009991                 w_done <= 1'b1;
                    end
        
                    // When both AW and W are collected, generate DECERR response
 009991             if ((s_axil_awvalid && s_axil_awready || aw_done) &&
~925216                 (s_axil_wvalid && s_axil_wready || w_done) &&
 009991                 (!s_axil_bvalid || s_axil_bready)) begin
 009991                 s_axil_bvalid <= 1'b1;
 009991                 s_axil_bresp  <= RESP_DECERR;
 009991                 aw_done       <= 1'b0;
 009991                 w_done        <= 1'b0;
 915225             end else if (s_axil_bvalid && s_axil_bready) begin
 009991                 s_axil_bvalid <= 1'b0;
                    end
                end
            end
        
            // --- Read Channel Logic ---
 935460     always @(posedge clk or negedge rst_n) begin
 935207         if (!rst_n) begin
 000253             s_axil_arready <= 1'b0;
 000253             s_axil_rvalid  <= 1'b0;
 000253             s_axil_rresp   <= 2'b00;
 000253             s_axil_rdata   <= {DATA_WIDTH{1'b0}};
 935207         end else begin
 935207             s_axil_arready <= !s_axil_rvalid || s_axil_rready;
        
 925351             if (s_axil_arvalid && s_axil_arready) begin
 009856                 s_axil_rvalid <= 1'b1;
 009856                 s_axil_rresp  <= RESP_DECERR;
 009856                 s_axil_rdata  <= {DATA_WIDTH{1'b0}};
 915495             end else if (s_axil_rvalid && s_axil_rready) begin
 009856                 s_axil_rvalid <= 1'b0;
                    end
                end
            end
        
        endmodule
        
