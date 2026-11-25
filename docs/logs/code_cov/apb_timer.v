//      // verilator_coverage annotation
        // rtl/apb/apb_timer.v
        // APB4 Timer Peripheral
        // Down-counter with LOAD reload, periodic/one-shot modes, and interrupt generation.
        `timescale 1ns / 1ps
        
        module apb_timer #(
            parameter ADDR_WIDTH = 12,
            parameter DATA_WIDTH = 32
        )(
 935460     input  wire                  clk,
~000021     input  wire                  rst_n,
        
            // APB4 Slave Interface
~006582     input  wire [ADDR_WIDTH-1:0] paddr,
 007481     input  wire [2:0]            pprot,
 007496     input  wire                  psel,
 030066     input  wire                  penable,
 007527     input  wire                  pwrite,
 003816     input  wire [DATA_WIDTH-1:0] pwdata,
 005273     input  wire [3:0]            pstrb,
 007496     output reg                   pready,
 001543     output reg  [DATA_WIDTH-1:0] prdata,
%000000     output reg                   pslverr,
        
            // Interrupt Output
 000010     output wire                  timer_irq
        );
        
            // Suppress lint for unused ports
~6139802     wire _unused = &{1'b0, pprot, pstrb, paddr[ADDR_WIDTH-1:4], paddr[1:0]};
        
            // Registers
            // 0x00: CTRL    [0] EN, [1] PERIODIC, [2] IRQ_EN
            // 0x04: LOAD    [31:0] Reload value
            // 0x08: VALUE   [31:0] Current countdown value
            // 0x0C: STATUS  [0] TIMEOUT (W1C)
 000252     reg [2:0]  reg_ctrl;
 000265     reg [31:0] reg_load;
 226817     reg [31:0] reg_value;
%000007     reg        reg_timeout;
        
            // Interrupt is active when IRQ_EN is set and TIMEOUT is asserted
 6036575     assign timer_irq = reg_ctrl[2] & reg_timeout;
        
            // Timer countdown logic
 935460     always @(posedge clk or negedge rst_n) begin
 935207         if (!rst_n) begin
 000253             reg_ctrl    <= 3'b000;
 000253             reg_load    <= 32'd0;
 000253             reg_value   <= 32'd0;
 000253             reg_timeout <= 1'b0;
 935207         end else begin
                    // Down-counter operation
 480118             if (reg_ctrl[0]) begin // EN
 453484                 if (reg_value == 32'd0) begin
 001605                     reg_timeout <= 1'b1;
~001601                     if (reg_ctrl[1]) begin // PERIODIC
 001601                         reg_value <= reg_load;
%000004                     end else begin
%000004                         reg_ctrl[0] <= 1'b0; // Stop one-shot
                            end
 453484                 end else begin
 453484                     reg_value <= reg_value - 1'b1;
                        end
                    end
        
                    // APB Register Writes (evaluated during ACCESS phase: psel && penable && pwrite)
 931392             if (psel && penable && pwrite) begin
 003815                 case (paddr[3:2])
 000929                     2'b00: begin // 0x00: CTRL
 000929                         reg_ctrl <= pwdata[2:0];
                                // If transitioning from disabled to enabled, load VALUE from LOAD
 000677                         if (pwdata[0] && !reg_ctrl[0]) begin
 000252                             reg_value <= reg_load;
                                end
                            end
 000975                     2'b01: begin // 0x04: LOAD
 000975                         reg_load <= pwdata;
                            end
 000950                     2'b10: begin // 0x08: VALUE is RO
                            end
 000961                     2'b11: begin // 0x0C: STATUS (W1C on bit 0)
 000501                         if (pwdata[0]) begin
 000460                             reg_timeout <= 1'b0;
                                end
                            end
                        endcase
                    end
                end
            end
        
            // APB Read Response & Handshake (1-cycle access)
 935460     always @(posedge clk or negedge rst_n) begin
 935207         if (!rst_n) begin
 000253             pready  <= 1'b0;
 000253             prdata  <= 32'd0;
 000253             pslverr <= 1'b0;
 935207         end else begin
 920215             if (psel && !penable) begin
                        // SETUP phase: assert pready for next cycle
 007496                 pready  <= 1'b1;
 007496                 pslverr <= 1'b0;
 007496                 case (paddr[3:2])
 001837                     2'b00:   prdata <= {29'd0, reg_ctrl};
 001872                     2'b01:   prdata <= reg_load;
 001884                     2'b10:   prdata <= reg_value;
 001903                     2'b11:   prdata <= {31'd0, reg_timeout};
%000000                     default: prdata <= 32'd0;
                        endcase
 920215             end else if (psel && penable) begin
                        // End of ACCESS phase
 007496                 pready <= 1'b0;
 920215             end else begin
 920215                 pready <= 1'b0;
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
        
