// Formal property specification for rr_arbiter
`timescale 1ns/1ps

module rr_arbiter_props #(
    parameter integer NUM_REQS = 2
) (
    input wire                clk,
    input wire                rst_n,
    input wire [NUM_REQS-1:0] req,
    input wire                lock
);

    wire [NUM_REQS-1:0] grant;
    wire                grant_valid;

    // Instantiate DUT
    rr_arbiter #(
        .NUM_REQS(NUM_REQS)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .req(req),
        .lock(lock),
        .grant(grant),
        .grant_valid(grant_valid)
    );

    // Initial reset sequence assumption
    reg f_past_valid;
    initial f_past_valid = 1'b0;

    always @(posedge clk) begin
        f_past_valid <= 1'b1;
    end

    always @(*) begin
        if (!f_past_valid)
            assume (!rst_n);
    end

    // Reset cycle counter
    reg [2:0] f_cycles_active = 0;
    always @(posedge clk) begin
        if (!rst_n)
            f_cycles_active <= 0;
        else if (f_cycles_active < 4)
            f_cycles_active <= f_cycles_active + 1;
    end

    // Inductive invariants and properties
    always @(posedge clk) begin
        if (!rst_n) begin
            assert (grant == {NUM_REQS{1'b0}});
            assert (grant_valid == 1'b0);
        end else begin
            // 1. One-hot or zero grant
            assert (grant == {NUM_REQS{1'b0}} || $onehot(grant));

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

    // Bounded fairness: under persistent contention with lock deasserted, every
    // active requester is granted within NUM_REQS clock edges (no starvation).
    reg [3:0] f_wait_cnt [0:NUM_REQS-1];
    integer fk;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (fk = 0; fk < NUM_REQS; fk = fk + 1) begin
                f_wait_cnt[fk] <= 4'd0;
            end
        end else begin
            for (fk = 0; fk < NUM_REQS; fk = fk + 1) begin
                if (grant[fk] || !req[fk] || lock) begin
                    f_wait_cnt[fk] <= 4'd0;
                end else begin
                    f_wait_cnt[fk] <= f_wait_cnt[fk] + 4'd1;
                    assert (f_wait_cnt[fk] < NUM_REQS[3:0]);
                end
            end
        end
    end

    // Cover scenarios
    always @(posedge clk) begin
        if (rst_n && f_cycles_active >= 2) begin
            cover (grant == 2'b01);
            cover (grant == 2'b10);
            cover ($past(grant) == 2'b01 && grant == 2'b10);
            cover ($past(grant) == 2'b10 && grant == 2'b01);
            cover (lock && grant_valid);
            cover (req == 2'b11 && !lock && $past(grant) == 2'b01 && grant == 2'b10);
        end
    end

endmodule
