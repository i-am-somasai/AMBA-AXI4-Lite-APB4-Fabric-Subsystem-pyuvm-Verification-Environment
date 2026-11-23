// rtl/apb/axil2apb_bridge.v
// AXI4-Lite to APB4 Bridge
// Adheres strictly to AMBA APB4 protocol (Setup phase, Access phase with wait-states, PSLVERR mapping to SLVERR)
`timescale 1ns / 1ps

module axil2apb_bridge #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 32,
    parameter STRB_WIDTH = DATA_WIDTH / 8
)(
    input  wire                  clk,
    input  wire                  rst_n,

    // AXI4-Lite Slave Interface
    input  wire [ADDR_WIDTH-1:0] s_axil_awaddr,
    input  wire [2:0]            s_axil_awprot,
    input  wire                  s_axil_awvalid,
    output reg                   s_axil_awready,

    input  wire [DATA_WIDTH-1:0] s_axil_wdata,
    input  wire [STRB_WIDTH-1:0] s_axil_wstrb,
    input  wire                  s_axil_wvalid,
    output reg                   s_axil_wready,

    output reg  [1:0]            s_axil_bresp,
    output reg                   s_axil_bvalid,
    input  wire                  s_axil_bready,

    input  wire [ADDR_WIDTH-1:0] s_axil_araddr,
    input  wire [2:0]            s_axil_arprot,
    input  wire                  s_axil_arvalid,
    output reg                   s_axil_arready,

    output reg  [DATA_WIDTH-1:0] s_axil_rdata,
    output reg  [1:0]            s_axil_rresp,
    output reg                   s_axil_rvalid,
    input  wire                  s_axil_rready,

    // APB4 Master Interface
    output reg  [ADDR_WIDTH-1:0] m_apb_paddr,
    output reg  [2:0]            m_apb_pprot,
    output reg                   m_apb_psel,
    output reg                   m_apb_penable,
    output reg                   m_apb_pwrite,
    output reg  [DATA_WIDTH-1:0] m_apb_pwdata,
    output reg  [STRB_WIDTH-1:0] m_apb_pstrb,
    input  wire                  m_apb_pready,
    input  wire [DATA_WIDTH-1:0] m_apb_prdata,
    input  wire                  m_apb_pslverr
);

    localparam [2:0] ST_IDLE    = 3'b000,
                     ST_WAIT_W  = 3'b001,
                     ST_WAIT_AW = 3'b010,
                     ST_SETUP   = 3'b011,
                     ST_ACCESS  = 3'b100,
                     ST_BRESP   = 3'b101,
                     ST_RRESP   = 3'b110;

    reg [2:0]            state;
    reg [ADDR_WIDTH-1:0] reg_addr;
    reg [2:0]            reg_prot;
    reg [DATA_WIDTH-1:0] reg_wdata;
    reg [STRB_WIDTH-1:0] reg_wstrb;
    reg                  reg_is_write;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state          <= ST_IDLE;
            reg_addr       <= {ADDR_WIDTH{1'b0}};
            reg_prot       <= 3'b000;
            reg_wdata      <= {DATA_WIDTH{1'b0}};
            reg_wstrb      <= {STRB_WIDTH{1'b0}};
            reg_is_write   <= 1'b0;
            s_axil_awready <= 1'b0;
            s_axil_wready  <= 1'b0;
            s_axil_bvalid  <= 1'b0;
            s_axil_bresp   <= 2'b00;
            s_axil_arready <= 1'b0;
            s_axil_rvalid  <= 1'b0;
            s_axil_rresp   <= 2'b00;
            s_axil_rdata   <= {DATA_WIDTH{1'b0}};
            m_apb_paddr    <= {ADDR_WIDTH{1'b0}};
            m_apb_pprot    <= 3'b000;
            m_apb_psel     <= 1'b0;
            m_apb_penable  <= 1'b0;
            m_apb_pwrite   <= 1'b0;
            m_apb_pwdata   <= {DATA_WIDTH{1'b0}};
            m_apb_pstrb    <= {STRB_WIDTH{1'b0}};
        end else begin
            // Default pulse signals
            s_axil_awready <= 1'b0;
            s_axil_wready  <= 1'b0;
            s_axil_arready <= 1'b0;

            case (state)
                ST_IDLE: begin
                    m_apb_psel    <= 1'b0;
                    m_apb_penable <= 1'b0;

                    // Write has priority or read
                    if (s_axil_awvalid && s_axil_wvalid) begin
                        reg_addr       <= s_axil_awaddr;
                        reg_prot       <= s_axil_awprot;
                        reg_wdata      <= s_axil_wdata;
                        reg_wstrb      <= s_axil_wstrb;
                        reg_is_write   <= 1'b1;
                        s_axil_awready <= 1'b1;
                        s_axil_wready  <= 1'b1;
                        state          <= ST_SETUP;
                    end else if (s_axil_awvalid) begin
                        reg_addr       <= s_axil_awaddr;
                        reg_prot       <= s_axil_awprot;
                        reg_is_write   <= 1'b1;
                        s_axil_awready <= 1'b1;
                        state          <= ST_WAIT_W;
                    end else if (s_axil_wvalid) begin
                        reg_wdata      <= s_axil_wdata;
                        reg_wstrb      <= s_axil_wstrb;
                        reg_is_write   <= 1'b1;
                        s_axil_wready  <= 1'b1;
                        state          <= ST_WAIT_AW;
                    end else if (s_axil_arvalid) begin
                        reg_addr       <= s_axil_araddr;
                        reg_prot       <= s_axil_arprot;
                        reg_is_write   <= 1'b0;
                        s_axil_arready <= 1'b1;
                        state          <= ST_SETUP;
                    end
                end

                ST_WAIT_W: begin
                    if (s_axil_wvalid) begin
                        reg_wdata     <= s_axil_wdata;
                        reg_wstrb     <= s_axil_wstrb;
                        s_axil_wready <= 1'b1;
                        state         <= ST_SETUP;
                    end
                end

                ST_WAIT_AW: begin
                    if (s_axil_awvalid) begin
                        reg_addr       <= s_axil_awaddr;
                        reg_prot       <= s_axil_awprot;
                        s_axil_awready <= 1'b1;
                        state          <= ST_SETUP;
                    end
                end

                ST_SETUP: begin
                    m_apb_paddr   <= reg_addr;
                    m_apb_pprot   <= reg_prot;
                    m_apb_pwrite  <= reg_is_write;
                    m_apb_pwdata  <= reg_wdata;
                    m_apb_pstrb   <= reg_is_write ? reg_wstrb : {STRB_WIDTH{1'b0}};
                    m_apb_psel    <= 1'b1;
                    m_apb_penable <= 1'b0;
                    state         <= ST_ACCESS;
                end

                ST_ACCESS: begin
                    m_apb_penable <= 1'b1;
                    if (m_apb_pready) begin
                        m_apb_psel    <= 1'b0;
                        m_apb_penable <= 1'b0;

                        if (reg_is_write) begin
                            s_axil_bvalid <= 1'b1;
                            s_axil_bresp  <= m_apb_pslverr ? 2'b10 : 2'b00;
                            state         <= ST_BRESP;
                        end else begin
                            s_axil_rvalid <= 1'b1;
                            s_axil_rdata  <= m_apb_prdata;
                            s_axil_rresp  <= m_apb_pslverr ? 2'b10 : 2'b00;
                            state         <= ST_RRESP;
                        end
                    end
                end

                ST_BRESP: begin
                    if (s_axil_bready) begin
                        s_axil_bvalid <= 1'b0;
                        state         <= ST_IDLE;
                    end
                end

                ST_RRESP: begin
                    if (s_axil_rready) begin
                        s_axil_rvalid <= 1'b0;
                        state         <= ST_IDLE;
                    end
                end

                default: state <= ST_IDLE;
            endcase
        end
    end

endmodule
