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
 935460     input  wire                  clk,
~000021     input  wire                  rst_n,
        
            // AXI4-Lite Slave Interface
~016433     input  wire [ADDR_WIDTH-1:0] s_axil_awaddr,
~015607     input  wire [2:0]            s_axil_awprot,
 015085     input  wire                  s_axil_awvalid,
 015085     output reg                   s_axil_awready,
        
~015674     input  wire [DATA_WIDTH-1:0] s_axil_wdata,
~015455     input  wire [STRB_WIDTH-1:0] s_axil_wstrb,
 015085     input  wire                  s_axil_wvalid,
 015085     output reg                   s_axil_wready,
        
~002781     output reg  [1:0]            s_axil_bresp,
 015085     output reg                   s_axil_bvalid,
 015085     input  wire                  s_axil_bready,
        
~016298     input  wire [ADDR_WIDTH-1:0] s_axil_araddr,
~015614     input  wire [2:0]            s_axil_arprot,
 014981     input  wire                  s_axil_arvalid,
 014981     output reg                   s_axil_arready,
        
~002703     output reg  [DATA_WIDTH-1:0] s_axil_rdata,
~002807     output reg  [1:0]            s_axil_rresp,
 014981     output reg                   s_axil_rvalid,
 014981     input  wire                  s_axil_rready,
        
            // APB4 Master Interface
~007436     output reg  [ADDR_WIDTH-1:0] m_apb_paddr,
 007481     output reg  [2:0]            m_apb_pprot,
 030066     output reg                   m_apb_psel,
 030066     output reg                   m_apb_penable,
 007527     output reg                   m_apb_pwrite,
~003816     output reg  [DATA_WIDTH-1:0] m_apb_pwdata,
 005273     output reg  [STRB_WIDTH-1:0] m_apb_pstrb,
 030066     input  wire                  m_apb_pready,
~008155     input  wire [DATA_WIDTH-1:0] m_apb_prdata,
 007437     input  wire                  m_apb_pslverr
        );
        
            localparam [2:0] ST_IDLE    = 3'b000,
                             ST_WAIT_W  = 3'b001,
                             ST_WAIT_AW = 3'b010,
                             ST_SETUP   = 3'b011,
                             ST_ACCESS  = 3'b100,
                             ST_BRESP   = 3'b101,
                             ST_RRESP   = 3'b110;
        
 045151     reg [2:0]            state;
~007436     reg [ADDR_WIDTH-1:0] reg_addr;
 007481     reg [2:0]            reg_prot;
~003816     reg [DATA_WIDTH-1:0] reg_wdata;
 003784     reg [STRB_WIDTH-1:0] reg_wstrb;
 007527     reg                  reg_is_write;
        
 935460     always @(posedge clk or negedge rst_n) begin
 935207         if (!rst_n) begin
 000253             state          <= ST_IDLE;
 000253             reg_addr       <= {ADDR_WIDTH{1'b0}};
 000253             reg_prot       <= 3'b000;
 000253             reg_wdata      <= {DATA_WIDTH{1'b0}};
 000253             reg_wstrb      <= {STRB_WIDTH{1'b0}};
 000253             reg_is_write   <= 1'b0;
 000253             s_axil_awready <= 1'b0;
 000253             s_axil_wready  <= 1'b0;
 000253             s_axil_bvalid  <= 1'b0;
 000253             s_axil_bresp   <= 2'b00;
 000253             s_axil_arready <= 1'b0;
 000253             s_axil_rvalid  <= 1'b0;
 000253             s_axil_rresp   <= 2'b00;
 000253             s_axil_rdata   <= {DATA_WIDTH{1'b0}};
 000253             m_apb_paddr    <= {ADDR_WIDTH{1'b0}};
 000253             m_apb_pprot    <= 3'b000;
 000253             m_apb_psel     <= 1'b0;
 000253             m_apb_penable  <= 1'b0;
 000253             m_apb_pwrite   <= 1'b0;
 000253             m_apb_pwdata   <= {DATA_WIDTH{1'b0}};
 000253             m_apb_pstrb    <= {STRB_WIDTH{1'b0}};
 935207         end else begin
                    // Default pulse signals
 935207             s_axil_awready <= 1'b0;
 935207             s_axil_wready  <= 1'b0;
 935207             s_axil_arready <= 1'b0;
        
 935207             case (state)
 754607                 ST_IDLE: begin
 754607                     m_apb_psel    <= 1'b0;
 754607                     m_apb_penable <= 1'b0;
        
                            // Write has priority or read
 744394                     if (s_axil_awvalid && s_axil_wvalid) begin
 010213                         reg_addr       <= s_axil_awaddr;
 010213                         reg_prot       <= s_axil_awprot;
 010213                         reg_wdata      <= s_axil_wdata;
 010213                         reg_wstrb      <= s_axil_wstrb;
 010213                         reg_is_write   <= 1'b1;
 010213                         s_axil_awready <= 1'b1;
 010213                         s_axil_wready  <= 1'b1;
 010213                         state          <= ST_SETUP;
 004872                     end else if (s_axil_awvalid) begin
 004872                         reg_addr       <= s_axil_awaddr;
 004872                         reg_prot       <= s_axil_awprot;
 004872                         reg_is_write   <= 1'b1;
 004872                         s_axil_awready <= 1'b1;
 004872                         state          <= ST_WAIT_W;
~000035                     end else if (s_axil_wvalid) begin
~000035                         reg_wdata      <= s_axil_wdata;
~000035                         reg_wstrb      <= s_axil_wstrb;
~000035                         reg_is_write   <= 1'b1;
~000035                         s_axil_wready  <= 1'b1;
~000035                         state          <= ST_WAIT_AW;
 724541                     end else if (s_axil_arvalid) begin
 014981                         reg_addr       <= s_axil_araddr;
 014981                         reg_prot       <= s_axil_arprot;
 014981                         reg_is_write   <= 1'b0;
 014981                         s_axil_arready <= 1'b1;
 014981                         state          <= ST_SETUP;
                            end
                        end
        
 009744                 ST_WAIT_W: begin
 004872                     if (s_axil_wvalid) begin
 004872                         reg_wdata     <= s_axil_wdata;
 004872                         reg_wstrb     <= s_axil_wstrb;
 004872                         s_axil_wready <= 1'b1;
 004872                         state         <= ST_SETUP;
                            end
                        end
        
~000076                 ST_WAIT_AW: begin
~000041                     if (s_axil_awvalid) begin
~000035                         reg_addr       <= s_axil_awaddr;
~000035                         reg_prot       <= s_axil_awprot;
~000035                         s_axil_awready <= 1'b1;
~000035                         state          <= ST_SETUP;
                            end
                        end
        
 030066                 ST_SETUP: begin
 030066                     m_apb_paddr   <= reg_addr;
 030066                     m_apb_pprot   <= reg_prot;
 030066                     m_apb_pwrite  <= reg_is_write;
 030066                     m_apb_pwdata  <= reg_wdata;
 030066                     m_apb_pstrb   <= reg_is_write ? reg_wstrb : {STRB_WIDTH{1'b0}};
 030066                     m_apb_psel    <= 1'b1;
 030066                     m_apb_penable <= 1'b0;
 030066                     state         <= ST_ACCESS;
                        end
        
 060132                 ST_ACCESS: begin
 060132                     m_apb_penable <= 1'b1;
 030066                     if (m_apb_penable && m_apb_pready) begin
 030066                         m_apb_psel    <= 1'b0;
 030066                         m_apb_penable <= 1'b0;
        
 015085                         if (reg_is_write) begin
 015085                             s_axil_bvalid <= 1'b1;
~015085                             s_axil_bresp  <= m_apb_pslverr ? 2'b10 : 2'b00;
 015085                             state         <= ST_BRESP;
 014981                         end else begin
 014981                             s_axil_rvalid <= 1'b1;
 014981                             s_axil_rdata  <= m_apb_prdata;
~014981                             s_axil_rresp  <= m_apb_pslverr ? 2'b10 : 2'b00;
 014981                             state         <= ST_RRESP;
                                end
                            end
                        end
        
 040450                 ST_BRESP: begin
 025365                     if (s_axil_bready) begin
 015085                         s_axil_bvalid <= 1'b0;
 015085                         state         <= ST_IDLE;
                            end
                        end
        
 040208                 ST_RRESP: begin
 025227                     if (s_axil_rready) begin
 014981                         s_axil_rvalid <= 1'b0;
 014981                         state         <= ST_IDLE;
                            end
                        end
        
%000000                 default: state <= ST_IDLE;
                    endcase
                end
            end
        
        endmodule
        
