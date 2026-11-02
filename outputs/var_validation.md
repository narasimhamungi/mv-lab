# Validation report: VAR-OPT-01, Options book VaR and ES (historical simulation and delta-normal)

Model repository: https://github.com/narasimhamungi/derivatives-risk-lab. Use: Daily 99% VaR and 97.5% ES for an illustrative equity options book; limit monitoring. Tier 2.

Validated on a frozen snapshot: `var_backtest_daily.csv`, SHA-256 `1ab293e30547170c...`, taken 2026-11-02T00:44:45+00:00 (model reference: derivatives-risk-lab, untagged; outputs of the 2026-11-01 run).

**Independence.** The validator is also the model's developer. SS1/23 expects validation to be independent of development; this report applies the tests and the rubric a second-line function would, on frozen outputs, without importing the model's code, but it is self-validation and says so.

## Conclusion

- **delta_gamma_hs:** Fit for use with conditions.
- **delta_hs:** Not fit for use as configured.
- **delta_normal:** Not fit for use as configured.
- **full_revaluation_hs:** Fit for use with conditions.

## Coverage at 99%

| Method | Forecasts | Exceptions | Expected | Kupiec p | Independence p | Cond. coverage p | Traffic light: green / yellow / red | Latest window |
|---|---|---|---|---|---|---|---|---|
| delta_gamma_hs | 1,716 | 21 | 17.2 | 0.3681 | 0.0015 | 0.0045 | 97% / 3% / 0% | 3 |
| delta_hs | 1,716 | 31 | 17.2 | 0.0026 | 0.0001 | 0.0000 | 51% / 49% / 0% | 4 |
| delta_normal | 1,716 | 32 | 17.2 | 0.0013 | 0.0002 | 0.0000 | 54% / 46% / 0% | 3 |
| full_revaluation_hs | 1,716 | 23 | 17.2 | 0.1780 | 0.0000 | 0.0000 | 87% / 13% / 0% | 3 |

Traffic light: share of trailing 250-day windows in each Basel zone (green 0-4, yellow 5-9, red 10 or more exceptions at 99%).

## Expected shortfall at 97.5%

| Method | Exceptions | Z2 | Zone | Mean exceedance residual | Residual p | Loss / ES |
|---|---|---|---|---|---|---|
| delta_gamma_hs | 48 | -0.383 | green | 0.236 | 0.023 | 1.24 |
| delta_hs | 54 | -0.627 | green | 0.293 | 0.009 | 1.29 |
| delta_normal | 44 | -0.646 | green | 0.605 | 0.000 | 1.61 |
| full_revaluation_hs | 48 | -0.377 | green | 0.230 | 0.025 | 1.23 |

Z2 (Acerbi and Szekely, 2014): 0 when the ES is right, negative when tail losses run larger; the paper's approximate thresholds -0.70 (5%) and -1.80 (0.01%) set the yellow and red zones. Exceedance residual: (loss - ES) / ES on exception days; the p-value is a one-sided bootstrap test that the mean is above zero.

## Findings

| Severity | Test | Finding | Evidence | Action |
|---|---|---|---|---|
| High | Kupiec POF (delta_hs, 99%) | delta_hs: the exception rate is inconsistent with 99% coverage. | 31 exceptions in 1716 forecasts, 17.2 expected; p = 0.0026 | Do not use this method for limits or capital until coverage is restored. |
| High | Kupiec POF (delta_normal, 99%) | delta_normal: the exception rate is inconsistent with 99% coverage. | 32 exceptions in 1716 forecasts, 17.2 expected; p = 0.0013 | Do not use this method for limits or capital until coverage is restored. |
| Medium | Christoffersen independence (delta_gamma_hs) | delta_gamma_hs: exceptions cluster in time. | 3 exceptions followed an exception; exception rate after an exception day 14.3% against 1.1% otherwise; p = 0.0015 | Add volatility scaling or a shorter look-back so the VaR reacts to regimes. |
| Medium | Exceedance residuals (delta_gamma_hs, 97.5%) | delta_gamma_hs: on exception days the loss runs above the ES forecast. | mean residual +0.24 over 48 exceptions; p = 0.023 | Review the tail model. |
| Medium | Christoffersen independence (delta_hs) | delta_hs: exceptions cluster in time. | 5 exceptions followed an exception; exception rate after an exception day 16.1% against 1.5% otherwise; p = 0.0001 | Add volatility scaling or a shorter look-back so the VaR reacts to regimes. |
| Medium | Exceedance residuals (delta_hs, 97.5%) | delta_hs: on exception days the loss runs above the ES forecast. | mean residual +0.29 over 54 exceptions; p = 0.009 | Review the tail model. |
| Medium | Christoffersen independence (delta_normal) | delta_normal: exceptions cluster in time. | 5 exceptions followed an exception; exception rate after an exception day 15.6% against 1.6% otherwise; p = 0.0002 | Add volatility scaling or a shorter look-back so the VaR reacts to regimes. |
| Medium | Exceedance residuals (delta_normal, 97.5%) | delta_normal: on exception days the loss runs above the ES forecast. | mean residual +0.61 over 44 exceptions; p = 0.000 | Review the tail model. |
| Medium | Christoffersen independence (full_revaluation_hs) | full_revaluation_hs: exceptions cluster in time. | 5 exceptions followed an exception; exception rate after an exception day 21.7% against 1.1% otherwise; p = 0.0000 | Add volatility scaling or a shorter look-back so the VaR reacts to regimes. |
| Medium | Exceedance residuals (full_revaluation_hs, 97.5%) | full_revaluation_hs: on exception days the loss runs above the ES forecast. | mean residual +0.23 over 48 exceptions; p = 0.025 | Review the tail model. |

## Limits of this validation

- Implied volatility, rates and dividends are held fixed (no option quotes), so the backtest measures non-linearity in spot only.
- The coverage and ES tests use the model's own forecasts and P&L; they do not re-derive the P&L.
- Thresholds outside the Basel traffic light are this project's rubric (docs/rubric.md).
