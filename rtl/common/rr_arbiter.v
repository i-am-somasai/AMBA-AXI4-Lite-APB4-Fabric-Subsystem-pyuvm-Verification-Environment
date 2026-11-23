// Round-Robin Arbiter with transaction lock
`timescale 1ns/1ps

module rr_arbiter #(
    parameter integer NUM_REQS = 2
) (
    input  wire                clk,
    input  wire                rst_n,
    input  wire [NUM_REQS-1:0] req,
    input  wire                lock,
    output reg  [NUM_REQS-1:0] grant,
    output wire                grant_valid
);

    reg [NUM_REQS-1:0] grant_q;
    assign grant_valid = |grant;

    reg [NUM_REQS-1:0] next_grant;
    integer i, j;
    reg found;

    always @(*) begin
        found = 1'b0;
        next_grant = {NUM_REQS{1'b0}};

        // If locked and current grant is still active and requesting, hold grant
        if (lock && (|grant_q) && (|(grant_q & req))) begin
            next_grant = grant_q;
            found = 1'b1;
        end else if (|req) begin
            // Round-robin selection starting from index after grant_q
            for (i = 0; i < NUM_REQS; i = i + 1) begin
                if (grant_q[i]) begin
                    for (j = 1; j < NUM_REQS; j = j + 1) begin
                        if (!found && req[(i + j) % NUM_REQS]) begin
                            next_grant[(i + j) % NUM_REQS] = 1'b1;
                            found = 1'b1;
                        end
                    end
                end
            end

            // If no previous grant or no higher wrap-around request found
            if (!found) begin
                for (i = 0; i < NUM_REQS; i = i + 1) begin
                    if (!found && req[i]) begin
                        next_grant[i] = 1'b1;
                        found = 1'b1;
                    end
                end
            end
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            grant_q <= {NUM_REQS{1'b0}};
            grant   <= {NUM_REQS{1'b0}};
        end else begin
            grant   <= next_grant;
            if (|next_grant) begin
                grant_q <= next_grant;
            end
        end
    end

`ifdef FORMAL
    reg f_past_valid;
    initial f_past_valid = 1'b0;

    always @(posedge clk) begin
        f_past_valid <= 1'b1;
    end

    always @(*) begin
        if (!f_past_valid)
            assume (!rst_n);
    end

    reg [2:0] f_cycles_active = 0;
    always @(posedge clk) begin
        if (!rst_n)
            f_cycles_active <= 0;
        else if (f_cycles_active < 4)
            f_cycles_active <= f_cycles_active + 1;
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            assert (grant == {NUM_REQS{1'b0}});
            assert (grant_q == {NUM_REQS{1'b0}});
            assert (grant_valid == 1'b0);
        end else begin
            // 1. One-hot or zero grant
            assert (grant == {NUM_REQS{1'b0}} || $onehot(grant));
            assert (grant_q == {NUM_REQS{1'b0}} || $onehot(grant_q));

            // 2. grant_valid matches reduction OR of grant
            assert (grant_valid == (|grant));

            if (f_cycles_active >= 2) begin
                // 3. Grant only given to requesters active in the previous cycle
                assert ((grant & $past(req)) == grant);

                // 4. No grant if no request in previous cycle
                if ($past(req) == {NUM_REQS{1'b0}}) begin
                    assert (grant == {NUM_REQS{1'b0}});
                end

                // 5. Transaction lock: if lock was asserted and locked requester still requested, hold grant
                if ($past(lock) && $past(grant_valid) && (|($past(grant) & $past(req)))) begin
                    assert (grant == $past(grant));
                end
            end
        end
    end

    // Cover statements
    always @(posedge clk) begin
        if (rst_n && f_cycles_active >= 2) begin
            cover (grant == 2'b01);
            cover (grant == 2'b10);
            cover ($past(grant) == 2'b01 && grant == 2'b10);
            cover ($past(grant) == 2'b10 && grant == 2'b01);
            cover (lock && grant_valid);
        end
    end
`endif

endmodule
