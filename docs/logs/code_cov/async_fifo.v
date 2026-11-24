//      // verilator_coverage annotation
        // Dual-clock Asynchronous FIFO (Cummings design) with Gray code pointers
        `timescale 1ns/1ps
        
        module async_fifo #(
            parameter integer WIDTH = 32,
            parameter integer DEPTH = 4,
            parameter integer ASYNC_STAGES = 2
        ) (
            // Write clock domain
 100022     input  wire             wclk,
~000014     input  wire             wrst_n,
 003921     input  wire             winc,
~001273     input  wire [WIDTH-1:0] wdata,
%000000     output reg              wfull,
        
            // Read clock domain
 100022     input  wire             rclk,
~000014     input  wire             rrst_n,
 003921     input  wire             rinc,
~001969     output wire [WIDTH-1:0] rdata,
 003927     output reg              rempty
        );
        
            localparam integer ADDR_WIDTH = $clog2(DEPTH);
            localparam integer PTR_WIDTH  = ADDR_WIDTH + 1;
        
            // Lint check helper for ASYNC_STAGES
            wire _unused_stages = &{1'b0, ASYNC_STAGES};
        
            // Dual-port memory
~000251     reg [WIDTH-1:0] mem [0:DEPTH-1];
        
            // Pointers
 001962     reg [PTR_WIDTH-1:0] wbin;
 000984     reg [PTR_WIDTH-1:0] wptr_gray;
 001962     reg [PTR_WIDTH-1:0] rbin;
 000984     reg [PTR_WIDTH-1:0] rptr_gray;
        
            // Synchronizer registers (specifically named for CDC / STA constraints)
 000984     reg [PTR_WIDTH-1:0] sync_w2r_q1;
 000984     reg [PTR_WIDTH-1:0] sync_w2r_q2;
 000984     reg [PTR_WIDTH-1:0] sync_r2w_q1;
 000984     reg [PTR_WIDTH-1:0] sync_r2w_q2;
        
            // Next pointer values
~605159     wire [PTR_WIDTH-1:0] wbin_next  = (winc && !wfull) ? (wbin + 1'b1) : wbin;
 000984     wire [PTR_WIDTH-1:0] wgray_next = (wbin_next >> 1) ^ wbin_next;
 606006     wire [PTR_WIDTH-1:0] rbin_next  = (rinc && !rempty) ? (rbin + 1'b1) : rbin;
 000984     wire [PTR_WIDTH-1:0] rgray_next = (rbin_next >> 1) ^ rbin_next;
        
            // Full condition (Cummings registered full)
%000000     wire wfull_val = (wgray_next == {~sync_r2w_q2[PTR_WIDTH-1:PTR_WIDTH-2], sync_r2w_q2[PTR_WIDTH-3:0]});
        
 100030     always @(posedge wclk or negedge wrst_n) begin
 099859         if (!wrst_n) begin
 000171             wbin      <= {PTR_WIDTH{1'b0}};
 000171             wptr_gray <= {PTR_WIDTH{1'b0}};
 000171             wfull     <= 1'b0;
 099859         end else begin
 099859             wbin      <= wbin_next;
 099859             wptr_gray <= wgray_next;
 099859             wfull     <= wfull_val;
~095938             if (winc && !wfull) begin
 003921                 mem[wbin[ADDR_WIDTH-1:0]] <= wdata;
                    end
                end
            end
        
            // Synchronize rptr_gray -> wclk domain
 100030     always @(posedge wclk or negedge wrst_n) begin
 099859         if (!wrst_n) begin
 000171             sync_r2w_q1 <= {PTR_WIDTH{1'b0}};
 000171             sync_r2w_q2 <= {PTR_WIDTH{1'b0}};
 099859         end else begin
 099859             sync_r2w_q1 <= rptr_gray;
 099859             sync_r2w_q2 <= sync_r2w_q1;
                end
            end
        
            // --- Read Domain Logic ---
            // Empty condition (Cummings registered empty)
 003927     wire rempty_val = (rgray_next == sync_w2r_q2);
        
 100030     always @(posedge rclk or negedge rrst_n) begin
 099859         if (!rrst_n) begin
 000171             rbin      <= {PTR_WIDTH{1'b0}};
 000171             rptr_gray <= {PTR_WIDTH{1'b0}};
 000171             rempty    <= 1'b1;
 099859         end else begin
 099859             rbin      <= rbin_next;
 099859             rptr_gray <= rgray_next;
 099859             rempty    <= rempty_val;
                end
            end
        
            // Asynchronous read data output
            assign rdata = mem[rbin[ADDR_WIDTH-1:0]];
        
            // Synchronize wptr_gray -> rclk domain
 100030     always @(posedge rclk or negedge rrst_n) begin
 099859         if (!rrst_n) begin
 000171             sync_w2r_q1 <= {PTR_WIDTH{1'b0}};
 000171             sync_w2r_q2 <= {PTR_WIDTH{1'b0}};
 099859         end else begin
 099859             sync_w2r_q1 <= wptr_gray;
 099859             sync_w2r_q2 <= sync_w2r_q1;
                end
            end
        
        `ifdef FORMAL
            // Initial reset sequence: reset initially, stable active-high afterwards
            reg f_w_past_valid = 1'b0;
            reg f_r_past_valid = 1'b0;
        
            always @(posedge wclk) f_w_past_valid <= 1'b1;
            always @(posedge rclk) f_r_past_valid <= 1'b1;
        
            always @(*) begin
                if (!f_w_past_valid) assume (!wrst_n);
                else assume (wrst_n);
        
                if (!f_r_past_valid) assume (!rrst_n);
                else assume (rrst_n);
            end
        
            // Protocol assumptions: never write when full, never read when empty
            always @(posedge wclk) begin
                if (wrst_n && wfull) assume (!winc);
            end
        
            always @(posedge rclk) begin
                if (rrst_n && rempty) assume (!rinc);
            end
        
            // 1. Gray pointer properties: Gray pointer matches binary pointer
            // and changes by at most 1 bit per clock edge
            always @(posedge wclk) begin
                if (wrst_n) begin
                    assert (wptr_gray == ((wbin >> 1) ^ wbin));
                    assert ($onehot0(wgray_next ^ wptr_gray));
                end
            end
        
            // 2. Gray pointer properties on read domain
            always @(posedge rclk) begin
                if (rrst_n) begin
                    assert (rptr_gray == ((rbin >> 1) ^ rbin));
                    assert ($onehot0(rgray_next ^ rptr_gray));
                end
            end
        
            // 3. Data Integrity via Formal Magic Value Tracking
            (* anyconst *) reg [WIDTH-1:0] f_magic_val;
            reg f_magic_written = 1'b0;
            reg [PTR_WIDTH-1:0] f_magic_ptr = {PTR_WIDTH{1'b0}};
            reg f_magic_read = 1'b0;
        
            always @(posedge wclk) begin
                if (!wrst_n) begin
                    f_magic_written <= 1'b0;
                    f_magic_ptr     <= {PTR_WIDTH{1'b0}};
                end else if (winc && !wfull && (wdata == f_magic_val) && !f_magic_written) begin
                    f_magic_written <= 1'b1;
                    f_magic_ptr     <= wbin;
                end
            end
        
            always @(posedge rclk) begin
                if (!rrst_n) begin
                    f_magic_read <= 1'b0;
                end else if (f_magic_written && !f_magic_read) begin
                    if ((rbin == f_magic_ptr) && !rempty) begin
                        assert (rdata == f_magic_val);
                        if (rinc) begin
                            f_magic_read <= 1'b1;
                        end
                    end
                end
            end
        
            // 4. Cover statements
            always @(posedge wclk) begin
                if (wrst_n && f_w_past_valid) begin
                    cover (wfull);
                end
            end
        
            always @(posedge rclk) begin
                if (rrst_n && f_r_past_valid) begin
                    cover (!rempty);
                    cover (rinc && !rempty);
                    cover (f_magic_read);
                end
            end
        `endif
        
        endmodule
        
