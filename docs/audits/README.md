# Independent Verification Audits Index

This directory archives the independent adversarial audit reports, machine-readable result tables, and closure verification for AMBA-Fabric. Earlier audit rounds uncovered real defects across RTL, formal verification, coverage collection, mutation testing, synthesis/STA, and documentation; each round's remediation is documented in:

- [docs/FIX_REPORT.md](../FIX_REPORT.md) (R1 remediation)
- [docs/FIX_REPORT_R2.md](../FIX_REPORT_R2.md) (R2 remediation)
- [docs/FIX_REPORT_R3.md](../FIX_REPORT_R3.md) (R3 remediation)

---

## Archived Audit Sets

| Audit Set | Audited Commit / Branch | Date | Verdict | Severity Counts | Description | Files |
|---|---|---|---|---|---|---|
| **Audit 3 (`audit3`)** | `338fd189f39404a8b220993308e7a93be965b5e4` (`remediation-r2`) | 2026-11-25 | `NOT READY` | `0` BLOCKER, `16` MAJOR, `22` MINOR (`200` checks) | Independent 200-check clean-clone audit confirming RTL, stress sims, coverage, and synth/STA while flagging `GP-02`/`SMUT-17`, bounded formal/equiv wording, `README` S0 range, and unverified remote CI. | [AUDIT3_REPORT.md](audit3/AUDIT3_REPORT.md), [audit3_results.csv](audit3/audit3_results.csv), [audit3_results.json](audit3/audit3_results.json) |
| **Audit 3 Closure (`audit3_closure`)** | `4bd08534f3a7ebb5f99c3322843b2703eab7ac96` (`origin/release-prep`) | 2026-11-25 | `READY WITH MINOR ISSUES` | `0` BLOCKER, `0` MAJOR, `15` MINOR (`64` checks) | Independent closure verification on a fresh GitHub clone confirming closure of the 16 MAJORs (`17/17` sanity + `5/5` injected bugs killed, `axil2apb_bridge` `abc pdr` prove, `README` S0 range fixed, CI run `45665895644` matched). | [AUDIT3_CLOSURE_REPORT.md](audit3_closure/AUDIT3_CLOSURE_REPORT.md), [audit3_closure_results.csv](audit3_closure/audit3_closure_results.csv), [audit3_closure_results.json](audit3_closure/audit3_closure_results.json) |

---

## Original Pre-Sanitization File SHA-256 Checksums

Local workspace/build path prefixes in the archived files were sanitized to `<WORK_DIR>` for publication without altering findings, IDs, numbers, or verdicts.

### Audit 3 Originals (`audit3`)
- `AUDIT_REPORT.md`: `cedc8d2196a12dd5ccd4ac0b2ff0edc6a17098d9e23c3c9b3a64d49d7ca01c18`
- `audit_results.csv`: `dd9d691a154d72f820f5e5a13fe52a97211a84da1d38179ba30072bf399786fc`
- `audit_results.json`: `35e2391176202b42418bcc7f5e1fb15fa9b42706637fbe28e512cbf0f3e8bded`

### Audit 3 Closure Originals (`audit3_closure`)
- `AUDIT_REPORT.md`: `47c36c6d3239f65a45d8ba3ff97c4a758a15d826e8dd61295569ec19e2e4964c`
- `audit_results.csv`: `7c5a74faac13dcb971736906ec9ca7626cad98fcb78391c549e78a87ddc32940`
- `audit_results.json`: `085731e98456ebe5c3d81e32212bc281a6ecc8fbae0456fa898b0a89c06ded46`
