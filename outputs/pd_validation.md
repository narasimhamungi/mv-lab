# Validation report: PD-CONS-01, Consumer loan 12-month PD (gradient boosting champion, WoE scorecard challenger)

Model repository: https://github.com/narasimhamungi/credit-pricing-lab. Use: Risk-based pricing and approval of unsecured consumer loans (illustrative lender). Tier 1.

Validated on a frozen snapshot: `pd_scores.parquet`, SHA-256 `8cb35e2f343b13a0...`, taken 2026-11-02T00:59:59+00:00 (model reference: credit-pricing-lab, 2026-11-02 run).

**Independence.** The validator is also the model's developer. SS1/23 expects validation to be independent of development; this report applies the tests and the rubric a second-line function would, on frozen outputs, without importing the model's code, but it is self-validation and says so.

## Conclusion

- **gbm (champion):** Fit for use.
- **scorecard (challenger):** Fit for use.

## Discrimination and calibration, out-of-time window

| Model | Loans | Default rate | Mean PD | AUC train | AUC valid | AUC test (95% interval) | Gini test | HL p | Spiegelhalter p | Score PSI |
|---|---|---|---|---|---|---|---|---|---|---|
| gbm | 443,579 | 5.72% | 5.96% | 0.703 | 0.676 | 0.672 (0.669 to 0.674) | 0.343 | 8.9e-18 | 1.7e-09 | 0.009 |
| scorecard | 443,579 | 5.72% | 5.87% | 0.667 | 0.657 | 0.655 (0.651 to 0.658) | 0.309 | 3.7e-06 | 0.00022 | 0.030 |

## Calibration by grade: gbm

| Grade | Loans | Share | Defaults | Default rate | Mean PD | Gap (DR / PD - 1) | Jeffreys p (PD too low) |
|---|---|---|---|---|---|---|---|
| A | 49,108 | 11.1% | 663 | 1.35% | 1.27% | +6.2% | 0.0604 |
| B | 90,300 | 20.4% | 2,513 | 2.78% | 2.84% | -2.0% | 0.85 |
| C | 49,545 | 11.2% | 2,109 | 4.26% | 4.29% | -0.8% | 0.639 |
| D | 97,605 | 22.0% | 5,317 | 5.45% | 5.62% | -3.0% | 0.99 |
| E | 105,276 | 23.7% | 8,472 | 8.05% | 8.21% | -1.9% | 0.97 |
| F | 36,772 | 8.3% | 4,007 | 10.90% | 11.92% | -8.6% | 1 |
| G | 14,973 | 3.4% | 2,304 | 15.39% | 17.58% | -12.5% | 1 |

## Calibration by grade: scorecard

| Grade | Loans | Share | Defaults | Default rate | Mean PD | Gap (DR / PD - 1) | Jeffreys p (PD too low) |
|---|---|---|---|---|---|---|---|
| A | 38,950 | 8.8% | 556 | 1.43% | 1.35% | +5.7% | 0.0956 |
| B | 71,967 | 16.2% | 1,991 | 2.77% | 2.75% | +0.5% | 0.41 |
| C | 96,179 | 21.7% | 4,184 | 4.35% | 4.35% | -0.1% | 0.522 |
| D | 83,072 | 18.7% | 4,735 | 5.70% | 5.85% | -2.5% | 0.965 |
| E | 103,612 | 23.4% | 8,165 | 7.88% | 8.05% | -2.1% | 0.98 |
| F | 41,684 | 9.4% | 4,540 | 10.89% | 11.48% | -5.2% | 1 |
| G | 8,115 | 1.8% | 1,214 | 14.96% | 16.57% | -9.7% | 1 |

## Stability by quarter of origination: gbm

| Quarter | Loans | Default rate | Mean PD | AUC |
|---|---|---|---|---|
| 2017Q1 | 96,779 | 5.43% | 5.81% | 0.671 |
| 2017Q2 | 105,451 | 5.74% | 5.87% | 0.672 |
| 2017Q3 | 122,701 | 5.94% | 6.09% | 0.671 |
| 2017Q4 | 118,648 | 5.72% | 6.04% | 0.673 |

## Findings

### gbm

| Severity | Test | Finding | Evidence | Action |
|---|---|---|---|---|
| Low | Jeffreys test (gbm, grade G) | Grade G's PD is conservative out of time. | grade G: 2,304 defaults in 14,973 loans, default rate 15.39% against mean PD 17.58%; p = 0.0000 | Record; conservative PDs overprice this grade. |
| Low | Hosmer-Lemeshow (gbm) | Calibration across deciles is rejected; with this many loans small gaps are significant, and the portfolio-level gap is not material. | HL = 98.4 on 8 df, p = 8.9e-18; default rate 5.72% against mean PD 5.96% | Review the grade table for where the gap sits. |

### scorecard

| Severity | Test | Finding | Evidence | Action |
|---|---|---|---|---|
| Low | Hosmer-Lemeshow (scorecard) | Calibration across deciles is rejected; with this many loans small gaps are significant, and the portfolio-level gap is not material. | HL = 39.7 on 8 df, p = 3.7e-06; default rate 5.72% against mean PD 5.87% | Review the grade table for where the gap sits. |

## Limits of this validation

- Booked loans only (no rejects), so the PD is conditional on Lending Club's approval; 12-month default approximated from the last payment date because the file has no charge-off date.
- Jeffreys test as described in the ECB guide to internal models; the grade scale is mv-lab's own.
- With hundreds of thousands of loans, goodness-of-fit tests reject small gaps; the rubric asks for an economically material gap as well (docs/rubric.md).
