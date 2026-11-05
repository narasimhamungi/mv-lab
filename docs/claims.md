# Claims ledger

Generated 2026-11-05. Tags: Demonstrated / Inferred / Assumed / Unsupported.

| Claim | Tag | Evidence |
|---|---|---|
| Validation toolkit with PRA SS1/23 framing; validator is also the developer and every report says so | Demonstrated (self-validation, not independent) | README "Independence" and "Limits"; `tests/test_pipeline.py` parses every import to check no model package is imported |
| VaR validation on derivatives-risk-lab: full revaluation and delta-gamma HS pass Kupiec but fail independence (exception rate 21.7% / 14.3% after an exception day vs about 1.1% otherwise) | Demonstrated | `data/snapshots/var/` (hashed), `outputs/var_validation.md`, `outputs/var_results.csv` |
| Delta HS and delta-normal not fit for use as configured (Kupiec p 0.003, 0.001) | Demonstrated | `outputs/var_validation.md` |
| Bootstrap rejects the exception-day loss/ES ratio at 5% for all four methods | Demonstrated | `outputs/var_validation.md` |
| PD model validated on real data: 443,579 loans, 2017 out-of-time year, from credit-pricing-lab `--export-scores` | Demonstrated | `outputs/pd_validation.md`, `outputs/pd_summary.json`, `outputs/pd_grades.csv`. Loan-level scores are git-ignored, so the run is reproducible only from credit-pricing-lab; aggregates are committed |
| Both PD models fit for use; no grade under-predicted beyond materiality | Demonstrated | `outputs/pd_findings.csv`, `docs/rubric.md` (10% materiality threshold is this project's rubric) |
| Each planted defect in the demo is found | Demonstrated | `mvlab demo`; `tests/test_pipeline.py` |
| Commentary is grounded: every number in `outputs/commentary.md` traces to the computed results | Demonstrated | `src/mvlab/commentary.py` mechanical check; `tests/test_commentary.py`. Not an LLM call |
| Z2 thresholds are exact critical values | Not claimed | README "Limits": approximate values from Acerbi and Szekely |
| Organisational independence per SS1/23 | Not claimed | README "Limits" |
