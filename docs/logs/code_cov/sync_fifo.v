//      // verilator_coverage annotation
        // Synchronous FIFO with count, overflow, underflow flags
        `timescale 1ns/1ps
        
        module sync_fifo #(
            parameter integer WIDTH = 8,
            parameter integer DEPTH = 8
        ) (
 1870920     input  wire                      clk,
~000042     input  wire                      rst_n,
 000248     input  wire                      push,
 003814     input  wire [WIDTH-1:0]          wdata,
 000088     input  wire                      pop,
~000039     output reg  [WIDTH-1:0]          rdata,
~000027     output wire                      full,
 000074     output wire                      empty,
~000168     output reg  [$clog2(DEPTH):0]    count,
%000000     output reg                       overflow,
%000000     output reg                       underflow
        );
        
            localparam integer ADDR_WIDTH = $clog2(DEPTH);
            localparam [ADDR_WIDTH:0] DEPTH_VAL = DEPTH[ADDR_WIDTH:0];
        
~000020     reg [WIDTH-1:0] mem [0:DEPTH-1];
 000133     reg [ADDR_WIDTH-1:0] wptr;
~000053     reg [ADDR_WIDTH-1:0] rptr;
        
            assign full  = (count == DEPTH_VAL);
            assign empty = (count == { (ADDR_WIDTH+1){1'b0} });
        
 1870920     always @(posedge clk or negedge rst_n) begin
 1870414         if (!rst_n) begin
 000506             wptr      <= {ADDR_WIDTH{1'b0}};
 000506             rptr      <= {ADDR_WIDTH{1'b0}};
 000506             count     <= {(ADDR_WIDTH+1){1'b0}};
 000506             rdata     <= {WIDTH{1'b0}};
 000506             overflow  <= 1'b0;
 000506             underflow <= 1'b0;
 1870414         end else begin
 1870414             overflow  <= 1'b0;
 1870414             underflow <= 1'b0;
        
 1870414             case ({push, pop})
 000248                 2'b10: begin // Push only
~000248                     if (!full) begin
 000248                         mem[wptr] <= wdata;
 000248                         wptr      <= wptr + 1'b1;
 000248                         count     <= count + 1'b1;
%000000                     end else begin
%000000                         overflow  <= 1'b1;
                            end
                        end
        
 000088                 2'b01: begin // Pop only
~000088                     if (!empty) begin
 000088                         rdata     <= mem[rptr];
 000088                         rptr      <= rptr + 1'b1;
 000088                         count     <= count - 1'b1;
%000000                     end else begin
%000000                         underflow <= 1'b1;
                            end
                        end
        
%000000                 2'b11: begin // Push and Pop simultaneously
%000000                     if (empty) begin
%000000                         mem[wptr] <= wdata;
%000000                         wptr      <= wptr + 1'b1;
%000000                         count     <= count + 1'b1;
%000000                         underflow <= 1'b1;
%000000                     end else if (full) begin
%000000                         mem[wptr] <= wdata;
%000000                         wptr      <= wptr + 1'b1;
%000000                         rdata     <= mem[rptr];
%000000                         rptr      <= rptr + 1'b1;
%000000                     end else begin
%000000                         mem[wptr] <= wdata;
%000000                         wptr      <= wptr + 1'b1;
%000000                         rdata     <= mem[rptr];
%000000                         rptr      <= rptr + 1'b1;
                            end
                        end
        
 1870078                 default: begin
                            // Idle
                        end
                    endcase
                end
            end
        
        `ifdef FORMAL
            reg f_past_valid = 1'b0;
            always @(posedge clk) f_past_valid <= 1'b1;
        
            always @(*) begin
                if (!f_past_valid) assume (!rst_n);
            end
        
            // Inductive FIFO Data Integrity & Strict Ordering via (* anyconst *) Magic Value
            (* anyconst *) reg [WIDTH-1:0] f_magic_val;
            reg                f_armed = 1'b0;
            reg [ADDR_WIDTH:0] f_pos   = {(ADDR_WIDTH+1){1'b0}};
        
            wire f_will_push = push && (!full || pop);
            wire f_will_pop  = pop  && !empty;
            wire [ADDR_WIDTH-1:0] f_magic_idx = rptr + f_pos[ADDR_WIDTH-1:0];
        
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    f_armed <= 1'b0;
                    f_pos   <= {(ADDR_WIDTH+1){1'b0}};
                end else begin
                    if (!f_armed) begin
                        if (f_will_push && (wdata == f_magic_val)) begin
                            f_armed <= 1'b1;
                            f_pos   <= f_will_pop ? (count - {{ADDR_WIDTH{1'b0}}, 1'b1}) : count;
                        end
                    end else if (f_will_pop) begin
                        if (f_pos == {(ADDR_WIDTH+1){1'b0}}) begin
                            if (f_will_push && (wdata == f_magic_val)) begin
                                f_armed <= 1'b1;
                                f_pos   <= count - {{ADDR_WIDTH{1'b0}}, 1'b1};
                            end else begin
                                f_armed <= 1'b0;
                                f_pos   <= {(ADDR_WIDTH+1){1'b0}};
                            end
                        end else begin
                            f_pos <= f_pos - {{ADDR_WIDTH{1'b0}}, 1'b1};
                        end
                    end
                end
            end
        
            always @(posedge clk) begin
                if (rst_n) begin
                    assert (count <= DEPTH_VAL);
                    assert (wptr == (rptr + count[ADDR_WIDTH-1:0]));
                    if (f_armed) begin
                        assert (f_pos < count);
                        assert (mem[f_magic_idx] == f_magic_val);
                    end
                    if (f_past_valid && $past(rst_n) && $past(f_armed) && ($past(f_pos) == {(ADDR_WIDTH+1){1'b0}}) && $past(f_will_pop)) begin
                        assert (rdata == f_magic_val);
                    end
                end
            end
        
        `ifndef NO_INTERNAL_FIFO_COVERS
            always @(posedge clk) begin
                if (rst_n && f_past_valid) begin
                    cover (f_armed && f_pos > 0);
                    cover ($past(rst_n) && $past(f_armed) && ($past(f_pos) == 0) && $past(f_will_pop) && (rdata == f_magic_val));
                end
            end
        `endif
        `endif
        
        endmodule
        
