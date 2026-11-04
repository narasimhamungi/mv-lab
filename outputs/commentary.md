# Validation commentary

Rendered from a fact map built on var_results.csv, var_findings.csv, pd_summary.json and pd_findings.csv; every number below is checked to trace back to that fact map before this file is written (mvlab.commentary.check_grounding). No LLM call is involved.

## VaR and ES validation

Across 4 methods, findings graded 2 High, 8 Medium and 0 Low: 0 fit for use, 2 fit for use with conditions, 2 not fit for use as configured.

delta_normal has the weakest coverage test: Kupiec p 0.0013 on 32 exceptions against 17.2 expected.

full_revaluation_hs has the weakest independence test, p 0.0000 — evidence that exceptions cluster rather than spreading evenly.

delta_normal has the weakest expected-shortfall backtest: Z2 -0.65 (green zone).

## PD validation

The champion model (gbm) is fit for use; the challenger (scorecard) is fit for use.

On 443,579 out-of-time loans, the champion's AUC is 0.672 (95% interval 0.669 to 0.674) against 0.655 for the challenger; mean PD 5.96% against an observed default rate of 5.72%.

Findings: champion 0 High / 0 Medium; challenger 0 High / 0 Medium.
