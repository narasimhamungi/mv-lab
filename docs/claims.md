# Claims ledger

Generated 2026-11-04, v0.2.0. Tags: Demonstrated / Inferred / Assumed / Unsupported.

| Claim | Tag | Evidence |
|---|---|---|
| Validation toolkit (PRA SS1/23 framing, self-validation stated) | Demonstrated (framing is explicitly self-validation, not independent) | README must keep "self-validation" explicit, never imply independent model validation |
| VaR validation on derivatives-risk-lab: full reval and delta-gamma HS pass Kupiec but fail independence | Demonstrated | 14 tests; exception clustering figures (21.7%/14.3% post-exception rate vs ~1.1% expected) |
| Delta HS and delta-normal not fit for purpose (Kupiec p 0.003, 0.001) | Demonstrated | same run |
| Bootstrap rejects exception-day loss/ES ratio at 5% for all four methods | Demonstrated | same run |
| PD module validated on real data | Unsupported — built and demonstrated on synthetic data only; real PD validation needs credit-pricing-lab's `--export-scores` | README must say "demonstrated on synthetic data; real-data run pending" |
| AI-commentary module | Not built — waits on fpa-lab | — |

## Action
Confirm README doesn't claim real-data PD validation — if it does (since credit-pricing-lab's `--export-scores` exists as of the 2 Nov upgrade but the actual mv-lab re-run using it hasn't happened per the plan doc), correct to "pending" until that run is done.
