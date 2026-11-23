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
            assert (dut.grant_q == {NUM_REQS{1'b0}});
            assert (grant_valid == 1'b0);
        end else begin
            // 1. One-hot or zero grant
            assert (grant == {NUM_REQS{1'b0}} || $onehot(grant));
            assert (dut.grant_q == {NUM_REQS{1'b0}} || $onehot(dut.grant_q));

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

    // Cover scenarios
    always @(posedge clk) begin
        if (rst_n && f_cycles_active >= 2) begin
            cover (grant == 2'b01);
            cover (grant == 2'b10);
            cover ($past(grant) == 2'b01 && grant == 2'b10);
            cover ($past(grant) == 2'b10 && grant == 2'b01);
            cover (lock && grant_valid);
        end
    end

endmodule
