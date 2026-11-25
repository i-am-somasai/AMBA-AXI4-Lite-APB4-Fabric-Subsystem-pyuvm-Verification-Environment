//      // verilator_coverage annotation
        // Reset synchronizer (2-FF, async assert, sync deassert)
        `timescale 1ns/1ps
        
        module rst_sync (
 1325018     input  wire clk,
~000042     input  wire rst_n_in,
~000042     output wire rst_n_out
        );
        
~000042     reg sync_q1;
~000042     reg sync_q2;
        
 1325018     always @(posedge clk or negedge rst_n_in) begin
 1324710         if (!rst_n_in) begin
 000308             sync_q1 <= 1'b0;
 000308             sync_q2 <= 1'b0;
 1324710         end else begin
 1324710             sync_q1 <= 1'b1;
 1324710             sync_q2 <= sync_q1;
                end
            end
        
            assign rst_n_out = sync_q2;
        
        endmodule
        
