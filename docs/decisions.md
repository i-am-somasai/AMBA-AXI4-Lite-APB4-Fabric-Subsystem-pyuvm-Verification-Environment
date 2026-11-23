# Architectural Decisions & Deviations Log

This document records all architectural decisions, clarifications, and intentional deviations from the specification.
Any modification made to the frozen interface (`docs/interfaces.md`) must be logged here.

| Decision ID | Date | Subject / Issue | Decision Taken | Rationale | Approved By |
|---|---|---|---|---|---|
| **DEC-001** | 2026-11-23 | Environment Isolation | Utilize `scripts/env.sh` to source `oss-cad-suite` and link OpenSTA 2.6.0 without modifying host system packages | Respects host constraints and avoids root/sudo operations while keeping tool versions strictly reproducible | Orchestrator |
| **DEC-002** | 2026-11-23 | Python Environment | Use Python 3.11 provided with `oss-cad-suite` for cocotb simulator VPI execution to match `tabbypy3` interpreter | Prevents C VPI ABI mismatch while retaining complete pip support for pyuvm and cocotb-coverage | Orchestrator |
| **DEC-003** | 2026-11-23 | Interface Freeze | All top-level and sub-block port lists, parameter sets, and memory maps in `docs/interfaces.md` marked FROZEN at end of Phase 0 | Ensures parallel agents (RTL, DV, Formal) can develop against a stable contract without interface churn | Orchestrator |
| **DEC-004** | 2026-11-23 | AXI-Lite W-First Ordering on Multi-Slave Crossbar | In multi-slave AXI4-Lite crossbar without per-master write data buffering, slave routing for W channel is established by address decoding `AWADDR`. In W-first transactions, master must drive `WVALID=1`, followed by `AWVALID=1` after staggered cycles without deadlocking waiting for `WREADY`. | AXI-Lite crossbars route W based on the addressed target slave decoded from `AWADDR`. Slaves cannot assert `WREADY` before receiving write routing. Driving `AWVALID` concurrently or with slight stagger allows crossbar to route both channels without requiring complex multi-entry store-and-forward data FIFOs. | Orchestrator |

