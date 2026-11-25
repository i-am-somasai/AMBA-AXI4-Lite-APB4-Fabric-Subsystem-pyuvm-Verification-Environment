//      // verilator_coverage annotation
        // Dual-clock Asynchronous FIFO (Cummings design) with Gray code pointers
        `timescale 1ns/1ps
        
        module async_fifo #(
            parameter integer WIDTH = 32,
            parameter integer DEPTH = 4,
            parameter integer ASYNC_STAGES = 2
        ) (
            // Write clock domain
 935460     input  wire             wclk,
~000021     input  wire             wrst_n,
 030372     input  wire             winc,
~009290     input  wire [WIDTH-1:0] wdata,
%000000     output reg              wfull,
        
            // Read clock domain
 935460     input  wire             rclk,
~000021     input  wire             rrst_n,
 030372     input  wire             rinc,
~015281     output wire [WIDTH-1:0] rdata,
 030393     output reg              rempty
        );
        
            localparam integer ADDR_WIDTH = $clog2(DEPTH);
            localparam integer PTR_WIDTH  = ADDR_WIDTH + 1;
        
            // Lint check helper for ASYNC_STAGES
            wire _unused_stages = &{1'b0, ASYNC_STAGES};
        
            // Dual-port memory
~001916     reg [WIDTH-1:0] mem [0:DEPTH-1];
        
            // Pointers
 015191     reg [PTR_WIDTH-1:0] wbin;
 007603     reg [PTR_WIDTH-1:0] wptr_gray;
 015191     reg [PTR_WIDTH-1:0] rbin;
 007603     reg [PTR_WIDTH-1:0] rptr_gray;
        
            // Synchronizer registers (specifically named for CDC / STA constraints)
 007603     reg [PTR_WIDTH-1:0] sync_w2r_q1;
 007603     reg [PTR_WIDTH-1:0] sync_w2r_q2;
 007603     reg [PTR_WIDTH-1:0] sync_r2w_q1;
 007603     reg [PTR_WIDTH-1:0] sync_r2w_q2;
        
            // Next pointer values
~5938716     wire [PTR_WIDTH-1:0] wbin_next  = (winc && !wfull) ? (wbin + 1'b1) : wbin;
 007603     wire [PTR_WIDTH-1:0] wgray_next = (wbin_next >> 1) ^ wbin_next;
 5949715     wire [PTR_WIDTH-1:0] rbin_next  = (rinc && !rempty) ? (rbin + 1'b1) : rbin;
 007603     wire [PTR_WIDTH-1:0] rgray_next = (rbin_next >> 1) ^ rbin_next;
        
            // Full condition (Cummings registered full)
%000000     wire wfull_val = (wgray_next == {~sync_r2w_q2[PTR_WIDTH-1:PTR_WIDTH-2], sync_r2w_q2[PTR_WIDTH-3:0]});
        
 935460     always @(posedge wclk or negedge wrst_n) begin
 935145         if (!wrst_n) begin
 000315             wbin      <= {PTR_WIDTH{1'b0}};
 000315             wptr_gray <= {PTR_WIDTH{1'b0}};
 000315             wfull     <= 1'b0;
 935145         end else begin
 935145             wbin      <= wbin_next;
 935145             wptr_gray <= wgray_next;
 935145             wfull     <= wfull_val;
~904773             if (winc && !wfull) begin
 030372                 mem[wbin[ADDR_WIDTH-1:0]] <= wdata;
                    end
                end
            end
        
            // Synchronize rptr_gray -> wclk domain
 935460     always @(posedge wclk or negedge wrst_n) begin
 935145         if (!wrst_n) begin
 000315             sync_r2w_q1 <= {PTR_WIDTH{1'b0}};
 000315             sync_r2w_q2 <= {PTR_WIDTH{1'b0}};
 935145         end else begin
 935145             sync_r2w_q1 <= rptr_gray;
 935145             sync_r2w_q2 <= sync_r2w_q1;
                end
            end
        
            // --- Read Domain Logic ---
            // Empty condition (Cummings registered empty)
 030393     wire rempty_val = (rgray_next == sync_w2r_q2);
        
 935460     always @(posedge rclk or negedge rrst_n) begin
 935145         if (!rrst_n) begin
 000315             rbin      <= {PTR_WIDTH{1'b0}};
 000315             rptr_gray <= {PTR_WIDTH{1'b0}};
 000315             rempty    <= 1'b1;
 935145         end else begin
 935145             rbin      <= rbin_next;
 935145             rptr_gray <= rgray_next;
 935145             rempty    <= rempty_val;
                end
            end
        
            // Asynchronous read data output
            assign rdata = mem[rbin[ADDR_WIDTH-1:0]];
        
            // Synchronize wptr_gray -> rclk domain
 935460     always @(posedge rclk or negedge rrst_n) begin
 935145         if (!rrst_n) begin
 000315             sync_w2r_q1 <= {PTR_WIDTH{1'b0}};
 000315             sync_w2r_q2 <= {PTR_WIDTH{1'b0}};
 935145         end else begin
 935145             sync_w2r_q1 <= wptr_gray;
 935145             sync_w2r_q2 <= sync_w2r_q1;
                end
            end
        
        `ifdef FORMAL
            // Initial reset sequence: reset initially, stable active-high afterwards
            reg f_w_past_valid = 1'b0;
            reg f_r_past_valid = 1'b0;
        
            always @(posedge wclk) f_w_past_valid <= 1'b1;
            always @(posedge rclk) f_r_past_valid <= 1'b1;
        
        `ifndef NO_INTERNAL_FIFO_COVERS
            always @(*) begin
                if (!f_w_past_valid) assume (!wrst_n);
                else assume (wrst_n);
        
                if (!f_r_past_valid) assume (!rrst_n);
                else assume (rrst_n);
            end
        `endif
        
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
        `ifndef NO_INTERNAL_FIFO_COVERS
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
        `endif
        
        endmodule
        
