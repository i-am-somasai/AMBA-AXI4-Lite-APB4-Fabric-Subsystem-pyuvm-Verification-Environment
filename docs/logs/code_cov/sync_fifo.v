//      // verilator_coverage annotation
        // Synchronous FIFO with count, overflow, underflow flags
        `timescale 1ns/1ps
        
        module sync_fifo #(
            parameter integer WIDTH = 8,
            parameter integer DEPTH = 8
        ) (
 200044     input  wire                      clk,
 000028     input  wire                      rst_n,
 000048     input  wire                      push,
 000486     input  wire [WIDTH-1:0]          wdata,
%000008     input  wire                      pop,
%000005     output reg  [WIDTH-1:0]          rdata,
%000005     output wire                      full,
 000018     output wire                      empty,
~000028     output reg  [$clog2(DEPTH):0]    count,
%000000     output reg                       overflow,
%000000     output reg                       underflow
        );
        
            localparam integer ADDR_WIDTH = $clog2(DEPTH);
            localparam [ADDR_WIDTH:0] DEPTH_VAL = DEPTH[ADDR_WIDTH:0];
        
%000005     reg [WIDTH-1:0] mem [0:DEPTH-1];
~000026     reg [ADDR_WIDTH-1:0] wptr;
%000006     reg [ADDR_WIDTH-1:0] rptr;
        
            assign full  = (count == DEPTH_VAL);
            assign empty = (count == { (ADDR_WIDTH+1){1'b0} });
        
 200060     always @(posedge clk or negedge rst_n) begin
 199718         if (!rst_n) begin
 000342             wptr      <= {ADDR_WIDTH{1'b0}};
 000342             rptr      <= {ADDR_WIDTH{1'b0}};
 000342             count     <= {(ADDR_WIDTH+1){1'b0}};
 000342             rdata     <= {WIDTH{1'b0}};
 000342             overflow  <= 1'b0;
 000342             underflow <= 1'b0;
 199718         end else begin
 199718             overflow  <= 1'b0;
 199718             underflow <= 1'b0;
        
 199718             case ({push, pop})
 000048                 2'b10: begin // Push only
~000048                     if (!full) begin
 000048                         mem[wptr] <= wdata;
 000048                         wptr      <= wptr + 1'b1;
 000048                         count     <= count + 1'b1;
%000000                     end else begin
%000000                         overflow  <= 1'b1;
                            end
                        end
        
%000008                 2'b01: begin // Pop only
%000008                     if (!empty) begin
%000008                         rdata     <= mem[rptr];
%000008                         rptr      <= rptr + 1'b1;
%000008                         count     <= count - 1'b1;
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
        
 199662                 default: begin
                            // Idle
                        end
                    endcase
                end
            end
        
        endmodule
        
