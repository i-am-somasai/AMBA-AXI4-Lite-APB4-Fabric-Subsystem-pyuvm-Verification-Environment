// rtl/apb/apb_timer.v
// APB4 Timer Peripheral
// Down-counter with LOAD reload, periodic/one-shot modes, and interrupt generation.
`timescale 1ns / 1ps

module apb_timer #(
    parameter ADDR_WIDTH = 12,
    parameter DATA_WIDTH = 32
)(
    input  wire                  clk,
    input  wire                  rst_n,

    // APB4 Slave Interface
    input  wire [ADDR_WIDTH-1:0] paddr,
    input  wire [2:0]            pprot,
    input  wire                  psel,
    input  wire                  penable,
    input  wire                  pwrite,
    input  wire [DATA_WIDTH-1:0] pwdata,
    input  wire [3:0]            pstrb,
    output reg                   pready,
    output reg  [DATA_WIDTH-1:0] prdata,
    output reg                   pslverr,

    // Interrupt Output
    output wire                  timer_irq
);

    // Suppress lint for unused ports
    wire _unused = &{1'b0, pprot, pstrb, paddr[ADDR_WIDTH-1:4], paddr[1:0]};

    // Registers
    // 0x00: CTRL    [0] EN, [1] PERIODIC, [2] IRQ_EN
    // 0x04: LOAD    [31:0] Reload value
    // 0x08: VALUE   [31:0] Current countdown value
    // 0x0C: STATUS  [0] TIMEOUT (W1C)
    reg [2:0]  reg_ctrl;
    reg [31:0] reg_load;
    reg [31:0] reg_value;
    reg        reg_timeout;

    // Interrupt is active when IRQ_EN is set and TIMEOUT is asserted
    assign timer_irq = reg_ctrl[2] & reg_timeout;

    // Timer countdown logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            reg_ctrl    <= 3'b000;
            reg_load    <= 32'd0;
            reg_value   <= 32'd0;
            reg_timeout <= 1'b0;
        end else begin
            // Down-counter operation
            if (reg_ctrl[0]) begin // EN
                if (reg_value == 32'd0) begin
                    reg_timeout <= 1'b1;
                    if (reg_ctrl[1]) begin // PERIODIC
                        reg_value <= reg_load;
                    end else begin
                        reg_ctrl[0] <= 1'b0; // Stop one-shot
                    end
                end else begin
                    reg_value <= reg_value - 1'b1;
                end
            end

            // APB Register Writes (evaluated during ACCESS phase: psel && penable && pwrite)
            if (psel && penable && pwrite) begin
                case (paddr[3:2])
                    2'b00: begin // 0x00: CTRL
                        reg_ctrl <= pwdata[2:0];
                        // If transitioning from disabled to enabled, load VALUE from LOAD
                        if (pwdata[0] && !reg_ctrl[0]) begin
                            reg_value <= reg_load;
                        end
                    end
                    2'b01: begin // 0x04: LOAD
                        reg_load <= pwdata;
                    end
                    2'b10: begin // 0x08: VALUE is RO
                    end
                    2'b11: begin // 0x0C: STATUS (W1C on bit 0)
                        if (pwdata[0]) begin
                            reg_timeout <= 1'b0;
                        end
                    end
                endcase
            end
        end
    end

    // APB Read Response & Handshake (1-cycle access)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pready  <= 1'b0;
            prdata  <= 32'd0;
            pslverr <= 1'b0;
        end else begin
            if (psel && !penable) begin
                // SETUP phase: assert pready for next cycle
                pready  <= 1'b1;
                pslverr <= 1'b0;
                case (paddr[3:2])
                    2'b00:   prdata <= {29'd0, reg_ctrl};
                    2'b01:   prdata <= reg_load;
                    2'b10:   prdata <= reg_value;
                    2'b11:   prdata <= {31'd0, reg_timeout};
                    default: prdata <= 32'd0;
                endcase
            end else if (psel && penable) begin
                // End of ACCESS phase
                pready <= 1'b0;
            end else begin
                pready <= 1'b0;
            end
        end
    end

`ifdef FORMAL
    wire apb_write = psel && penable && pwrite;
    reg f_past_valid = 0;
    always @(posedge clk) f_past_valid <= 1;

    always @(*) begin
        if (!f_past_valid) assume (!rst_n);
    end

    // APB protocol assumptions
    always @(posedge clk) begin
        if (f_past_valid && $past(rst_n) && rst_n) begin
            if ($past(psel) && !$past(penable)) begin
                assume (psel);
                assume (penable);
                assume ($stable(paddr));
                assume ($stable(pwrite));
                assume ($stable(pwdata));
                assume ($stable(pstrb));
                assume ($stable(pprot));
            end
            if ($past(psel) && $past(penable) && $past(pready)) begin
                if (psel) assume (!penable);
            end
        end
    end

    // Functional assertions
    always @(posedge clk) begin
        if (rst_n) begin
            assert (pslverr == 1'b0);
            assert (timer_irq == (reg_ctrl[2] & reg_timeout));
        end
    end

    always @(posedge clk) begin
        if (f_past_valid && $past(rst_n) && rst_n) begin
            // Down-counting when enabled, value > 0, and not written by APB
            if ($past(reg_ctrl[0]) && ($past(reg_value) > 0) && !$past(apb_write && (paddr[3:2] == 2'b10))) begin
                assert (reg_value == $past(reg_value) - 1'b1);
            end
            // Timeout event when value reaches 0
            if ($past(reg_ctrl[0]) && ($past(reg_value) == 0)) begin
                if (!$past(apb_write && (paddr[3:2] == 2'b11) && pwdata[0])) begin
                    assert (reg_timeout == 1'b1);
                end
                if ($past(reg_ctrl[1])) begin
                    if (!$past(apb_write && (paddr[3:2] == 2'b10))) begin
                        assert (reg_value == $past(reg_load));
                    end
                    if (!$past(apb_write && (paddr[3:2] == 2'b00))) begin
                        assert (reg_ctrl[0] == 1'b1);
                    end
                end else begin
                    if (!$past(apb_write && (paddr[3:2] == 2'b00))) begin
                        assert (reg_ctrl[0] == 1'b0);
                    end
                end
            end
            // Clear timeout on write-1-to-clear to STATUS
            if ($past(apb_write && (paddr[3:2] == 2'b11) && pwdata[0])) begin
                assert (reg_timeout == 1'b0);
            end
        end
    end

    // Covers
    always @(posedge clk) begin
        if (rst_n) begin
            cover (timer_irq);
            cover (reg_ctrl[0] && reg_timeout);
            cover (reg_ctrl[1] && (reg_value == reg_load) && reg_timeout);
            cover (psel && penable && pwrite && (paddr[3:2] == 2'b11) && pwdata[0]);
        end
    end
`endif

endmodule
