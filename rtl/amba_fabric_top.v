// rtl/amba_fabric_top.v
// Top-Level AMBA Fabric Subsystem Integration
// 2-Master AXI4-Lite Crossbar + APB Peripherals (UART, Timer, GPIO) + RAM + CSR + CDC Bridge
`timescale 1ns / 1ps

module amba_fabric_top #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 32,
    parameter STRB_WIDTH = DATA_WIDTH / 8,
    parameter RAM_DEPTH  = 256,
    parameter GPIO_WIDTH = 16
)(
    // Clocks and External Reset
    input  wire                   clk_sys,
    input  wire                   clk_slow,
    input  wire                   rst_n,

    // AXI4-Lite Master 0 Interface
    input  wire [ADDR_WIDTH-1:0]  s0_axil_awaddr,
    input  wire [2:0]             s0_axil_awprot,
    input  wire                   s0_axil_awvalid,
    output wire                   s0_axil_awready,
    input  wire [DATA_WIDTH-1:0]  s0_axil_wdata,
    input  wire [STRB_WIDTH-1:0]  s0_axil_wstrb,
    input  wire                   s0_axil_wvalid,
    output wire                   s0_axil_wready,
    output wire [1:0]             s0_axil_bresp,
    output wire                   s0_axil_bvalid,
    input  wire                   s0_axil_bready,
    input  wire [ADDR_WIDTH-1:0]  s0_axil_araddr,
    input  wire [2:0]             s0_axil_arprot,
    input  wire                   s0_axil_arvalid,
    output wire                   s0_axil_arready,
    output wire [DATA_WIDTH-1:0]  s0_axil_rdata,
    output wire [1:0]             s0_axil_rresp,
    output wire                   s0_axil_rvalid,
    input  wire                   s0_axil_rready,

    // AXI4-Lite Master 1 Interface
    input  wire [ADDR_WIDTH-1:0]  s1_axil_awaddr,
    input  wire [2:0]             s1_axil_awprot,
    input  wire                   s1_axil_awvalid,
    output wire                   s1_axil_awready,
    input  wire [DATA_WIDTH-1:0]  s1_axil_wdata,
    input  wire [STRB_WIDTH-1:0]  s1_axil_wstrb,
    input  wire                   s1_axil_wvalid,
    output wire                   s1_axil_wready,
    output wire [1:0]             s1_axil_bresp,
    output wire                   s1_axil_bvalid,
    input  wire                   s1_axil_bready,
    input  wire [ADDR_WIDTH-1:0]  s1_axil_araddr,
    input  wire [2:0]             s1_axil_arprot,
    input  wire                   s1_axil_arvalid,
    output wire                   s1_axil_arready,
    output wire [DATA_WIDTH-1:0]  s1_axil_rdata,
    output wire [1:0]             s1_axil_rresp,
    output wire                   s1_axil_rvalid,
    input  wire                   s1_axil_rready,

    // Peripheral I/O Pins
    input  wire                   uart_rx,
    output wire                   uart_tx,
    input  wire [GPIO_WIDTH-1:0]  gpio_i,
    output wire [GPIO_WIDTH-1:0]  gpio_o,
    output wire [GPIO_WIDTH-1:0]  gpio_dir,
    output wire                   irq_o
);

    // -------------------------------------------------------------
    // Reset Synchronizers (Assert Asynchronous, Deassert Synchronous)
    // -------------------------------------------------------------
    wire rst_sys_n;
    wire rst_slow_n;

    rst_sync u_rst_sync_sys (
        .clk       (clk_sys),
        .rst_n_in  (rst_n),
        .rst_n_out (rst_sys_n)
    );

    rst_sync u_rst_sync_slow (
        .clk       (clk_slow),
        .rst_n_in  (rst_n),
        .rst_n_out (rst_slow_n)
    );

    // -------------------------------------------------------------
    // Crossbar Slave Port Interconnect Signals
    // Slaves: S0=APB, S1=RAM, S2=CSR, S3=CDC
    // -------------------------------------------------------------
    wire [4*ADDR_WIDTH-1:0] xbar_s_awaddr;
    wire [4*3-1:0]          xbar_s_awprot;
    wire [3:0]              xbar_s_awvalid;
    wire [3:0]              xbar_s_awready;

    wire [4*DATA_WIDTH-1:0] xbar_s_wdata;
    wire [4*STRB_WIDTH-1:0] xbar_s_wstrb;
    wire [3:0]              xbar_s_wvalid;
    wire [3:0]              xbar_s_wready;

    wire [4*2-1:0]          xbar_s_bresp;
    wire [3:0]              xbar_s_bvalid;
    wire [3:0]              xbar_s_bready;

    wire [4*ADDR_WIDTH-1:0] xbar_s_araddr;
    wire [4*3-1:0]          xbar_s_arprot;
    wire [3:0]              xbar_s_arvalid;
    wire [3:0]              xbar_s_arready;

    wire [4*DATA_WIDTH-1:0] xbar_s_rdata;
    wire [4*2-1:0]          xbar_s_rresp;
    wire [3:0]              xbar_s_rvalid;
    wire [3:0]              xbar_s_rready;

    // Instantiate 2-Master x 4-Slave Crossbar
    axil_xbar #(
        .DATA_WIDTH (DATA_WIDTH),
        .ADDR_WIDTH (ADDR_WIDTH),
        .STRB_WIDTH (STRB_WIDTH),
        .NUM_MASTERS(2),
        .NUM_SLAVES (4)
    ) u_xbar (
        .clk            (clk_sys),
        .rst_n          (rst_sys_n),

        // Masters
        .s_axil_awaddr  ({s1_axil_awaddr,  s0_axil_awaddr}),
        .s_axil_awprot  ({s1_axil_awprot,  s0_axil_awprot}),
        .s_axil_awvalid ({s1_axil_awvalid, s0_axil_awvalid}),
        .s_axil_awready ({s1_axil_awready, s0_axil_awready}),

        .s_axil_wdata   ({s1_axil_wdata,   s0_axil_wdata}),
        .s_axil_wstrb   ({s1_axil_wstrb,   s0_axil_wstrb}),
        .s_axil_wvalid  ({s1_axil_wvalid,  s0_axil_wvalid}),
        .s_axil_wready  ({s1_axil_wready,  s0_axil_wready}),

        .s_axil_bresp   ({s1_axil_bresp,   s0_axil_bresp}),
        .s_axil_bvalid  ({s1_axil_bvalid,  s0_axil_bvalid}),
        .s_axil_bready  ({s1_axil_bready,  s0_axil_bready}),

        .s_axil_araddr  ({s1_axil_araddr,  s0_axil_araddr}),
        .s_axil_arprot  ({s1_axil_arprot,  s0_axil_arprot}),
        .s_axil_arvalid ({s1_axil_arvalid, s0_axil_arvalid}),
        .s_axil_arready ({s1_axil_arready, s0_axil_arready}),

        .s_axil_rdata   ({s1_axil_rdata,   s0_axil_rdata}),
        .s_axil_rresp   ({s1_axil_rresp,   s0_axil_rresp}),
        .s_axil_rvalid  ({s1_axil_rvalid,  s0_axil_rvalid}),
        .s_axil_rready  ({s1_axil_rready,  s0_axil_rready}),

        // Slaves: [0]=APB, [1]=RAM, [2]=CSR, [3]=CDC
        .m_axil_awaddr  (xbar_s_awaddr),
        .m_axil_awprot  (xbar_s_awprot),
        .m_axil_awvalid (xbar_s_awvalid),
        .m_axil_awready (xbar_s_awready),

        .m_axil_wdata   (xbar_s_wdata),
        .m_axil_wstrb   (xbar_s_wstrb),
        .m_axil_wvalid  (xbar_s_wvalid),
        .m_axil_wready  (xbar_s_wready),

        .m_axil_bresp   (xbar_s_bresp),
        .m_axil_bvalid  (xbar_s_bvalid),
        .m_axil_bready  (xbar_s_bready),

        .m_axil_araddr  (xbar_s_araddr),
        .m_axil_arprot  (xbar_s_arprot),
        .m_axil_arvalid (xbar_s_arvalid),
        .m_axil_arready (xbar_s_arready),

        .m_axil_rdata   (xbar_s_rdata),
        .m_axil_rresp   (xbar_s_rresp),
        .m_axil_rvalid  (xbar_s_rvalid),
        .m_axil_rready  (xbar_s_rready)
    );

    // -------------------------------------------------------------
    // Slave 0: APB Subsystem (Bridge + Decoder + UART + Timer + GPIO)
    // -------------------------------------------------------------
    // APB master interface from bridge
    wire [ADDR_WIDTH-1:0] apb_paddr;
    wire [2:0]            apb_pprot;
    wire                  apb_psel;
    wire                  apb_penable;
    wire                  apb_pwrite;
    wire [DATA_WIDTH-1:0] apb_pwdata;
    wire [STRB_WIDTH-1:0] apb_pstrb;
    wire                  apb_pready;
    wire [DATA_WIDTH-1:0] apb_prdata;
    wire                  apb_pslverr;

    axil2apb_bridge #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
    ) u_apb_bridge (
        .clk            (clk_sys),
        .rst_n          (rst_sys_n),

        .s_axil_awaddr  (xbar_s_awaddr[0*ADDR_WIDTH +: ADDR_WIDTH]),
        .s_axil_awprot  (xbar_s_awprot[0*3 +: 3]),
        .s_axil_awvalid (xbar_s_awvalid[0]),
        .s_axil_awready (xbar_s_awready[0]),

        .s_axil_wdata   (xbar_s_wdata[0*DATA_WIDTH +: DATA_WIDTH]),
        .s_axil_wstrb   (xbar_s_wstrb[0*STRB_WIDTH +: STRB_WIDTH]),
        .s_axil_wvalid  (xbar_s_wvalid[0]),
        .s_axil_wready  (xbar_s_wready[0]),

        .s_axil_bresp   (xbar_s_bresp[0*2 +: 2]),
        .s_axil_bvalid  (xbar_s_bvalid[0]),
        .s_axil_bready  (xbar_s_bready[0]),

        .s_axil_araddr  (xbar_s_araddr[0*ADDR_WIDTH +: ADDR_WIDTH]),
        .s_axil_arprot  (xbar_s_arprot[0*3 +: 3]),
        .s_axil_arvalid (xbar_s_arvalid[0]),
        .s_axil_arready (xbar_s_arready[0]),

        .s_axil_rdata   (xbar_s_rdata[0*DATA_WIDTH +: DATA_WIDTH]),
        .s_axil_rresp   (xbar_s_rresp[0*2 +: 2]),
        .s_axil_rvalid  (xbar_s_rvalid[0]),
        .s_axil_rready  (xbar_s_rready[0]),

        .m_apb_paddr    (apb_paddr),
        .m_apb_pprot    (apb_pprot),
        .m_apb_psel     (apb_psel),
        .m_apb_penable  (apb_penable),
        .m_apb_pwrite   (apb_pwrite),
        .m_apb_pwdata   (apb_pwdata),
        .m_apb_pstrb    (apb_pstrb),
        .m_apb_pready   (apb_pready),
        .m_apb_prdata   (apb_prdata),
        .m_apb_pslverr  (apb_pslverr)
    );

    // APB Peripherals: UART (0), Timer (1), GPIO (2)
    wire                  psel_uart;
    wire                  pready_uart;
    wire [DATA_WIDTH-1:0] prdata_uart;
    wire                  pslverr_uart;

    wire                  psel_timer;
    wire                  pready_timer;
    wire [DATA_WIDTH-1:0] prdata_timer;
    wire                  pslverr_timer;

    wire                  psel_gpio;
    wire                  pready_gpio;
    wire [DATA_WIDTH-1:0] prdata_gpio;
    wire                  pslverr_gpio;

    apb_decoder #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
    ) u_apb_decoder (
        .paddr         (apb_paddr),
        .psel          (apb_psel),
        .penable       (apb_penable),
        .pready        (apb_pready),
        .prdata        (apb_prdata),
        .pslverr       (apb_pslverr),

        .psel_uart     (psel_uart),
        .pready_uart   (pready_uart),
        .prdata_uart   (prdata_uart),
        .pslverr_uart  (pslverr_uart),

        .psel_timer    (psel_timer),
        .pready_timer  (pready_timer),
        .prdata_timer  (prdata_timer),
        .pslverr_timer (pslverr_timer),

        .psel_gpio     (psel_gpio),
        .pready_gpio   (pready_gpio),
        .prdata_gpio   (prdata_gpio),
        .pslverr_gpio  (pslverr_gpio)
    );

    // Peripheral 0: UART (0x4000_0000)
    wire uart_irq;
    apb_uart #(
        .FIFO_DEPTH(8),
        .ADDR_WIDTH(12),
        .DATA_WIDTH(DATA_WIDTH)
    ) u_uart (
        .clk      (clk_sys),
        .rst_n    (rst_sys_n),

        .paddr    (apb_paddr[11:0]),
        .pprot    (apb_pprot),
        .psel     (psel_uart),
        .penable  (apb_penable),
        .pwrite   (apb_pwrite),
        .pwdata   (apb_pwdata),
        .pstrb    (apb_pstrb),
        .pready   (pready_uart),
        .prdata   (prdata_uart),
        .pslverr  (pslverr_uart),

        .uart_rx  (uart_rx),
        .uart_tx  (uart_tx),
        .uart_irq (uart_irq)
    );

    // Peripheral 1: Timer (0x4000_1000)
    wire timer_irq;
    apb_timer #(
        .ADDR_WIDTH(12),
        .DATA_WIDTH(DATA_WIDTH)
    ) u_timer (
        .clk       (clk_sys),
        .rst_n     (rst_sys_n),

        .paddr     (apb_paddr[11:0]),
        .pprot     (apb_pprot),
        .psel      (psel_timer),
        .penable   (apb_penable),
        .pwrite    (apb_pwrite),
        .pwdata    (apb_pwdata),
        .pstrb     (apb_pstrb),
        .pready    (pready_timer),
        .prdata    (prdata_timer),
        .pslverr   (pslverr_timer),

        .timer_irq (timer_irq)
    );

    // Peripheral 2: GPIO (0x4000_2000)
    wire gpio_irq;
    apb_gpio #(
        .GPIO_WIDTH(GPIO_WIDTH),
        .ADDR_WIDTH(12),
        .DATA_WIDTH(DATA_WIDTH)
    ) u_gpio (
        .clk      (clk_sys),
        .rst_n    (rst_sys_n),

        .paddr    (apb_paddr[11:0]),
        .pprot    (apb_pprot),
        .psel     (psel_gpio),
        .penable  (apb_penable),
        .pwrite   (apb_pwrite),
        .pwdata   (apb_pwdata),
        .pstrb    (apb_pstrb),
        .pready   (pready_gpio),
        .prdata   (prdata_gpio),
        .pslverr  (pslverr_gpio),

        .gpio_i   (gpio_i),
        .gpio_o   (gpio_o),
        .gpio_dir (gpio_dir),
        .gpio_irq (gpio_irq)
    );

    // -------------------------------------------------------------
    // Slave 1: Scratchpad RAM (0x5000_0000, 1 KB)
    // -------------------------------------------------------------
    axil_ram #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH),
        .RAM_DEPTH (RAM_DEPTH)
    ) u_ram (
        .clk            (clk_sys),
        .rst_n          (rst_sys_n),

        .s_axil_awaddr  (xbar_s_awaddr[1*ADDR_WIDTH +: ADDR_WIDTH]),
        .s_axil_awprot  (xbar_s_awprot[1*3 +: 3]),
        .s_axil_awvalid (xbar_s_awvalid[1]),
        .s_axil_awready (xbar_s_awready[1]),

        .s_axil_wdata   (xbar_s_wdata[1*DATA_WIDTH +: DATA_WIDTH]),
        .s_axil_wstrb   (xbar_s_wstrb[1*STRB_WIDTH +: STRB_WIDTH]),
        .s_axil_wvalid  (xbar_s_wvalid[1]),
        .s_axil_wready  (xbar_s_wready[1]),

        .s_axil_bresp   (xbar_s_bresp[1*2 +: 2]),
        .s_axil_bvalid  (xbar_s_bvalid[1]),
        .s_axil_bready  (xbar_s_bready[1]),

        .s_axil_araddr  (xbar_s_araddr[1*ADDR_WIDTH +: ADDR_WIDTH]),
        .s_axil_arprot  (xbar_s_arprot[1*3 +: 3]),
        .s_axil_arvalid (xbar_s_arvalid[1]),
        .s_axil_arready (xbar_s_arready[1]),

        .s_axil_rdata   (xbar_s_rdata[1*DATA_WIDTH +: DATA_WIDTH]),
        .s_axil_rresp   (xbar_s_rresp[1*2 +: 2]),
        .s_axil_rvalid  (xbar_s_rvalid[1]),
        .s_axil_rready  (xbar_s_rready[1])
    );

    // -------------------------------------------------------------
    // Slave 2: CSR Block & IRQ Aggregation (0x6000_0000)
    // -------------------------------------------------------------
    axil_csr #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
    ) u_csr (
        .clk            (clk_sys),
        .rst_n          (rst_sys_n),

        .s_axil_awaddr  (xbar_s_awaddr[2*ADDR_WIDTH +: ADDR_WIDTH]),
        .s_axil_awprot  (xbar_s_awprot[2*3 +: 3]),
        .s_axil_awvalid (xbar_s_awvalid[2]),
        .s_axil_awready (xbar_s_awready[2]),

        .s_axil_wdata   (xbar_s_wdata[2*DATA_WIDTH +: DATA_WIDTH]),
        .s_axil_wstrb   (xbar_s_wstrb[2*STRB_WIDTH +: STRB_WIDTH]),
        .s_axil_wvalid  (xbar_s_wvalid[2]),
        .s_axil_wready  (xbar_s_wready[2]),

        .s_axil_bresp   (xbar_s_bresp[2*2 +: 2]),
        .s_axil_bvalid  (xbar_s_bvalid[2]),
        .s_axil_bready  (xbar_s_bready[2]),

        .s_axil_araddr  (xbar_s_araddr[2*ADDR_WIDTH +: ADDR_WIDTH]),
        .s_axil_arprot  (xbar_s_arprot[2*3 +: 3]),
        .s_axil_arvalid (xbar_s_arvalid[2]),
        .s_axil_arready (xbar_s_arready[2]),

        .s_axil_rdata   (xbar_s_rdata[2*DATA_WIDTH +: DATA_WIDTH]),
        .s_axil_rresp   (xbar_s_rresp[2*2 +: 2]),
        .s_axil_rvalid  (xbar_s_rvalid[2]),
        .s_axil_rready  (xbar_s_rready[2]),

        .irq_sources    ({gpio_irq, timer_irq, uart_irq}), // [0] UART, [1] Timer, [2] GPIO
        .irq_o          (irq_o)
    );

    // -------------------------------------------------------------
    // Slave 3: CDC Bridge to clk_slow Domain (0x7000_0000)
    // -------------------------------------------------------------
    axil_cdc_bridge #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH),
        .FIFO_DEPTH(4)
    ) u_cdc_bridge (
        .clk_sys        (clk_sys),
        .rst_sys_n      (rst_sys_n),
        .clk_slow       (clk_slow),
        .rst_slow_n     (rst_slow_n),

        .s_axil_awaddr  (xbar_s_awaddr[3*ADDR_WIDTH +: ADDR_WIDTH]),
        .s_axil_awprot  (xbar_s_awprot[3*3 +: 3]),
        .s_axil_awvalid (xbar_s_awvalid[3]),
        .s_axil_awready (xbar_s_awready[3]),

        .s_axil_wdata   (xbar_s_wdata[3*DATA_WIDTH +: DATA_WIDTH]),
        .s_axil_wstrb   (xbar_s_wstrb[3*STRB_WIDTH +: STRB_WIDTH]),
        .s_axil_wvalid  (xbar_s_wvalid[3]),
        .s_axil_wready  (xbar_s_wready[3]),

        .s_axil_bresp   (xbar_s_bresp[3*2 +: 2]),
        .s_axil_bvalid  (xbar_s_bvalid[3]),
        .s_axil_bready  (xbar_s_bready[3]),

        .s_axil_araddr  (xbar_s_araddr[3*ADDR_WIDTH +: ADDR_WIDTH]),
        .s_axil_arprot  (xbar_s_arprot[3*3 +: 3]),
        .s_axil_arvalid (xbar_s_arvalid[3]),
        .s_axil_arready (xbar_s_arready[3]),

        .s_axil_rdata   (xbar_s_rdata[3*DATA_WIDTH +: DATA_WIDTH]),
        .s_axil_rresp   (xbar_s_rresp[3*2 +: 2]),
        .s_axil_rvalid  (xbar_s_rvalid[3]),
        .s_axil_rready  (xbar_s_rready[3])
    );

endmodule
