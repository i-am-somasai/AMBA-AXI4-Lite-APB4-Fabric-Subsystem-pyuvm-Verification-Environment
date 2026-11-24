//      // verilator_coverage annotation
        // AXI4-Lite Default Slave returning DECERR
        `timescale 1ns/1ps
        
        module axil_default_slave #(
            parameter integer ADDR_WIDTH = 32,
            parameter integer DATA_WIDTH = 32
        ) (
 100022     input  wire                  clk,
~000014     input  wire                  rst_n,
        
            // Write address channel
~001944     input  wire [ADDR_WIDTH-1:0] s_axil_awaddr,
 001873     input  wire [2:0]            s_axil_awprot,
 001261     input  wire                  s_axil_awvalid,
 000457     output reg                   s_axil_awready,
        
            // Write data channel
 001898     input  wire [DATA_WIDTH-1:0] s_axil_wdata,
 001878     input  wire [(DATA_WIDTH/8)-1:0] s_axil_wstrb,
 001261     input  wire                  s_axil_wvalid,
~000014     output reg                   s_axil_wready,
        
            // Write response channel
%000006     output reg  [1:0]            s_axil_bresp,
 001261     output reg                   s_axil_bvalid,
 001261     input  wire                  s_axil_bready,
        
            // Read address channel
~001828     input  wire [ADDR_WIDTH-1:0] s_axil_araddr,
 001885     input  wire [2:0]            s_axil_arprot,
 001220     input  wire                  s_axil_arvalid,
~000014     output reg                   s_axil_arready,
        
            // Read data channel
%000000     output reg  [DATA_WIDTH-1:0] s_axil_rdata,
%000006     output reg  [1:0]            s_axil_rresp,
 001220     output reg                   s_axil_rvalid,
 001220     input  wire                  s_axil_rready
        );
        
            localparam [1:0] RESP_DECERR = 2'b11;
        
            // Lint suppression for consumed but unused payload inputs
            wire _unused_inputs = &{1'b0, s_axil_awaddr, s_axil_awprot, s_axil_wdata, s_axil_wstrb, s_axil_araddr, s_axil_arprot};
        
            // Track write handshake completion
 000443     reg aw_done;
%000000     reg w_done;
        
            // --- Write Channel Logic ---
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             s_axil_awready <= 1'b0;
 000171             s_axil_wready  <= 1'b0;
 000171             s_axil_bvalid  <= 1'b0;
 000171             s_axil_bresp   <= 2'b00;
 000171             aw_done        <= 1'b0;
 000171             w_done         <= 1'b0;
 099859         end else begin
~099859             s_axil_awready <= (!s_axil_bvalid || s_axil_bready) && !aw_done;
~099859             s_axil_wready  <= (!s_axil_bvalid || s_axil_bready) && !w_done;
        
 098598             if (s_axil_awvalid && s_axil_awready) begin
 001261                 aw_done <= 1'b1;
                    end
        
 098598             if (s_axil_wvalid && s_axil_wready) begin
 001261                 w_done <= 1'b1;
                    end
        
                    // When both AW and W are collected, generate DECERR response
 001261             if ((s_axil_awvalid && s_axil_awready || aw_done) &&
~098598                 (s_axil_wvalid && s_axil_wready || w_done) &&
 001261                 (!s_axil_bvalid || s_axil_bready)) begin
 001261                 s_axil_bvalid <= 1'b1;
 001261                 s_axil_bresp  <= RESP_DECERR;
 001261                 aw_done       <= 1'b0;
 001261                 w_done        <= 1'b0;
 097337             end else if (s_axil_bvalid && s_axil_bready) begin
 001261                 s_axil_bvalid <= 1'b0;
                    end
                end
            end
        
            // --- Read Channel Logic ---
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             s_axil_arready <= 1'b0;
 000171             s_axil_rvalid  <= 1'b0;
 000171             s_axil_rresp   <= 2'b00;
 000171             s_axil_rdata   <= {DATA_WIDTH{1'b0}};
 099859         end else begin
~099859             s_axil_arready <= !s_axil_rvalid || s_axil_rready;
        
 098639             if (s_axil_arvalid && s_axil_arready) begin
 001220                 s_axil_rvalid <= 1'b1;
 001220                 s_axil_rresp  <= RESP_DECERR;
 001220                 s_axil_rdata  <= {DATA_WIDTH{1'b0}};
 097419             end else if (s_axil_rvalid && s_axil_rready) begin
 001220                 s_axil_rvalid <= 1'b0;
                    end
                end
            end
        
        endmodule
        
