//      // verilator_coverage annotation
        // rtl/apb/axil2apb_bridge.v
        // AXI4-Lite to APB4 Bridge
        // Adheres strictly to AMBA APB4 protocol (Setup phase, Access phase with wait-states, PSLVERR mapping to SLVERR)
        `timescale 1ns / 1ps
        
        module axil2apb_bridge #(
            parameter DATA_WIDTH = 32,
            parameter ADDR_WIDTH = 32,
            parameter STRB_WIDTH = DATA_WIDTH / 8
        )(
 100022     input  wire                  clk,
~000014     input  wire                  rst_n,
        
            // AXI4-Lite Slave Interface
~002091     input  wire [ADDR_WIDTH-1:0] s_axil_awaddr,
 001935     input  wire [2:0]            s_axil_awprot,
 001922     input  wire                  s_axil_awvalid,
 001922     output reg                   s_axil_awready,
        
 001999     input  wire [DATA_WIDTH-1:0] s_axil_wdata,
 001964     input  wire [STRB_WIDTH-1:0] s_axil_wstrb,
 001922     input  wire                  s_axil_wvalid,
 001922     output reg                   s_axil_wready,
        
~000347     output reg  [1:0]            s_axil_bresp,
 001922     output reg                   s_axil_bvalid,
 001922     input  wire                  s_axil_bready,
        
~002076     input  wire [ADDR_WIDTH-1:0] s_axil_araddr,
 001963     input  wire [2:0]            s_axil_arprot,
 001977     input  wire                  s_axil_arvalid,
 001977     output reg                   s_axil_arready,
        
 000365     output reg  [DATA_WIDTH-1:0] s_axil_rdata,
~000362     output reg  [1:0]            s_axil_rresp,
 001977     output reg                   s_axil_rvalid,
 001977     input  wire                  s_axil_rready,
        
            // APB4 Master Interface
~000946     output reg  [ADDR_WIDTH-1:0] m_apb_paddr,
 000996     output reg  [2:0]            m_apb_pprot,
 003899     output reg                   m_apb_psel,
 003899     output reg                   m_apb_penable,
 001004     output reg                   m_apb_pwrite,
 000488     output reg  [DATA_WIDTH-1:0] m_apb_pwdata,
 000697     output reg  [STRB_WIDTH-1:0] m_apb_pstrb,
 003899     input  wire                  m_apb_pready,
 000986     input  wire [DATA_WIDTH-1:0] m_apb_prdata,
 000957     input  wire                  m_apb_pslverr
        );
        
            localparam [2:0] ST_IDLE    = 3'b000,
                             ST_WAIT_W  = 3'b001,
                             ST_WAIT_AW = 3'b010,
                             ST_SETUP   = 3'b011,
                             ST_ACCESS  = 3'b100,
                             ST_BRESP   = 3'b101,
                             ST_RRESP   = 3'b110;
        
 005876     reg [2:0]            state;
~000946     reg [ADDR_WIDTH-1:0] reg_addr;
 000996     reg [2:0]            reg_prot;
 000488     reg [DATA_WIDTH-1:0] reg_wdata;
 000489     reg [STRB_WIDTH-1:0] reg_wstrb;
 001004     reg                  reg_is_write;
        
 100030     always @(posedge clk or negedge rst_n) begin
 099859         if (!rst_n) begin
 000171             state          <= ST_IDLE;
 000171             reg_addr       <= {ADDR_WIDTH{1'b0}};
 000171             reg_prot       <= 3'b000;
 000171             reg_wdata      <= {DATA_WIDTH{1'b0}};
 000171             reg_wstrb      <= {STRB_WIDTH{1'b0}};
 000171             reg_is_write   <= 1'b0;
 000171             s_axil_awready <= 1'b0;
 000171             s_axil_wready  <= 1'b0;
 000171             s_axil_bvalid  <= 1'b0;
 000171             s_axil_bresp   <= 2'b00;
 000171             s_axil_arready <= 1'b0;
 000171             s_axil_rvalid  <= 1'b0;
 000171             s_axil_rresp   <= 2'b00;
 000171             s_axil_rdata   <= {DATA_WIDTH{1'b0}};
 000171             m_apb_paddr    <= {ADDR_WIDTH{1'b0}};
 000171             m_apb_pprot    <= 3'b000;
 000171             m_apb_psel     <= 1'b0;
 000171             m_apb_penable  <= 1'b0;
 000171             m_apb_pwrite   <= 1'b0;
 000171             m_apb_pwdata   <= {DATA_WIDTH{1'b0}};
 000171             m_apb_pstrb    <= {STRB_WIDTH{1'b0}};
 099859         end else begin
                    // Default pulse signals
 099859             s_axil_awready <= 1'b0;
 099859             s_axil_wready  <= 1'b0;
 099859             s_axil_arready <= 1'b0;
        
 099859             case (state)
 083065                 ST_IDLE: begin
 083065                     m_apb_psel    <= 1'b0;
 083065                     m_apb_penable <= 1'b0;
        
                            // Write has priority or read
 081742                     if (s_axil_awvalid && s_axil_wvalid) begin
 001323                         reg_addr       <= s_axil_awaddr;
 001323                         reg_prot       <= s_axil_awprot;
 001323                         reg_wdata      <= s_axil_wdata;
 001323                         reg_wstrb      <= s_axil_wstrb;
 001323                         reg_is_write   <= 1'b1;
 001323                         s_axil_awready <= 1'b1;
 001323                         s_axil_wready  <= 1'b1;
 001323                         state          <= ST_SETUP;
 000599                     end else if (s_axil_awvalid) begin
 000599                         reg_addr       <= s_axil_awaddr;
 000599                         reg_prot       <= s_axil_awprot;
 000599                         reg_is_write   <= 1'b1;
 000599                         s_axil_awready <= 1'b1;
 000599                         state          <= ST_WAIT_W;
%000000                     end else if (s_axil_wvalid) begin
%000000                         reg_wdata      <= s_axil_wdata;
%000000                         reg_wstrb      <= s_axil_wstrb;
%000000                         reg_is_write   <= 1'b1;
%000000                         s_axil_wready  <= 1'b1;
%000000                         state          <= ST_WAIT_AW;
 079166                     end else if (s_axil_arvalid) begin
 001977                         reg_addr       <= s_axil_araddr;
 001977                         reg_prot       <= s_axil_arprot;
 001977                         reg_is_write   <= 1'b0;
 001977                         s_axil_arready <= 1'b1;
 001977                         state          <= ST_SETUP;
                            end
                        end
        
 001198                 ST_WAIT_W: begin
 000599                     if (s_axil_wvalid) begin
 000599                         reg_wdata     <= s_axil_wdata;
 000599                         reg_wstrb     <= s_axil_wstrb;
 000599                         s_axil_wready <= 1'b1;
 000599                         state         <= ST_SETUP;
                            end
                        end
        
%000000                 ST_WAIT_AW: begin
%000000                     if (s_axil_awvalid) begin
%000000                         reg_addr       <= s_axil_awaddr;
%000000                         reg_prot       <= s_axil_awprot;
%000000                         s_axil_awready <= 1'b1;
%000000                         state          <= ST_SETUP;
                            end
                        end
        
 003899                 ST_SETUP: begin
 003899                     m_apb_paddr   <= reg_addr;
 003899                     m_apb_pprot   <= reg_prot;
 003899                     m_apb_pwrite  <= reg_is_write;
 003899                     m_apb_pwdata  <= reg_wdata;
 003899                     m_apb_pstrb   <= reg_is_write ? reg_wstrb : {STRB_WIDTH{1'b0}};
 003899                     m_apb_psel    <= 1'b1;
 003899                     m_apb_penable <= 1'b0;
 003899                     state         <= ST_ACCESS;
                        end
        
 007798                 ST_ACCESS: begin
 007798                     m_apb_penable <= 1'b1;
 003899                     if (m_apb_penable && m_apb_pready) begin
 003899                         m_apb_psel    <= 1'b0;
 003899                         m_apb_penable <= 1'b0;
        
 001977                         if (reg_is_write) begin
 001922                             s_axil_bvalid <= 1'b1;
 001922                             s_axil_bresp  <= m_apb_pslverr ? 2'b10 : 2'b00;
 001922                             state         <= ST_BRESP;
 001977                         end else begin
 001977                             s_axil_rvalid <= 1'b1;
 001977                             s_axil_rdata  <= m_apb_prdata;
 001977                             s_axil_rresp  <= m_apb_pslverr ? 2'b10 : 2'b00;
 001977                             state         <= ST_RRESP;
                                end
                            end
                        end
        
 001922                 ST_BRESP: begin
~001922                     if (s_axil_bready) begin
 001922                         s_axil_bvalid <= 1'b0;
 001922                         state         <= ST_IDLE;
                            end
                        end
        
 001977                 ST_RRESP: begin
~001977                     if (s_axil_rready) begin
 001977                         s_axil_rvalid <= 1'b0;
 001977                         state         <= ST_IDLE;
                            end
                        end
        
%000000                 default: state <= ST_IDLE;
                    endcase
                end
            end
        
        endmodule
        
