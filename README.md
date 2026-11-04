# mv-lab

Model validation applied to two models from this portfolio: the VaR and expected-shortfall engine of
[derivatives-risk-lab](https://github.com/narasimhamungi/derivatives-risk-lab) and the consumer-loan PD model of
[credit-pricing-lab](https://github.com/narasimhamungi/credit-pricing-lab). Each model gets an inventory entry,
tests run on a frozen, hashed copy of its outputs, findings graded by a published rubric, and a conclusion.

## Problem

A model that passes its developer's own headline test can still fail the use it is put to. A VaR model can
have the right number of exceptions overall and still miss every one of them in the same fortnight; a PD
model can rank borrowers well and still price every grade too low the year after it was fitted.

## Why it matters

Second-line validation exists to find those failures before a limit, a price or a capital number depends on
them. The PRA's supervisory statement SS1/23 on model risk management for banks sets the frame: an inventory
with tiering, validation independent of development, and findings with remediation.

## What was built

| Part | What it does |
|---|---|
| Inventory (`inventory/models.yml`) | One entry per model: use, tier, methodology, inputs, outputs, limitations, validation scope |
| Snapshots (`snapshot.py`) | Frozen copies of model outputs with a SHA-256 manifest; validation refuses changed bytes |
| VaR coverage (`coverage.py`) | Kupiec proportion of failures, Christoffersen independence, conditional coverage, Basel traffic light over 250-day windows |
| ES backtests (`es_tests.py`) | Acerbi-Szekely Z2 with its yellow and red thresholds; exceedance residuals with a bootstrap test |
| PD tests (`pd_tests.py`) | AUC with a bootstrap interval, Jeffreys test by grade, Hosmer-Lemeshow, Spiegelhalter, PSI |
| Findings and reports (`findings.py`, `report.py`) | Severity from the rubric in `docs/rubric.md`; one Markdown report per model with its conclusion |
| Demo (`mvlab demo`) | Invented inputs with planted defects (a VaR 25% too low, a VaR that ignores regimes, a PD that drifts out of time); the tests must find each one |
| Commentary (`commentary.py`) | Grounded narrative, not an LLM call: a fact map built from the computed results and findings, templates that only format and concatenate those values, and a mechanical check that every number in the rendered text traces back to the fact map |

## Data and tools

Python, pandas, NumPy, SciPy. Inputs are the models' own output files: `var_backtest_daily.csv` from
derivatives-risk-lab (committed here as the snapshot, 13,728 rows: four methods, two levels, 1,716 days from
2019-12-31 to 2026-10-28) and loan-level scores from `creditlab run --export-scores` (kept out of git; only
aggregates are written).

## Methodology

**Independence.** The validator is also the developer. The code enforces what it can: no module imports a
model repository's package (a test parses every import), and every test reads a hashed snapshot of outputs,
not the model's code or configuration. The grade scale for PD calibration is set in mv-lab's own configuration.
Every report says that this is self-validation.

**Coverage at 99%, ES at 97.5%.** The levels the Basel framework uses for backtesting VaR and for ES.
Exceptions are recomputed from loss and VaR rather than taken from the model's flag.

**Statistical and economic significance.** Every calibration finding needs a gap above 10% of the PD as well
as a p-value, because with hundreds of thousands of loans goodness-of-fit tests reject gaps no lender would act on.

## Key findings

On derivatives-risk-lab's daily backtest (`outputs/var_validation.md`):

- **The two methods the model's own report accepts pass coverage but fail independence.** Full revaluation and
  delta-gamma historical simulation have 23 and 21 exceptions against 17.2 expected (Kupiec p 0.18 and 0.37),
  but after an exception day the exception rate is 21.7% and 14.3% against about 1.1% otherwise
  (Christoffersen p below 0.002). Five of full revaluation's 23 exceptions fall in March 2020, the pattern of a
  historical-simulation window that catches up with a new regime only as it rolls.
- **ES understates the tail without failing Z2.** Z2 stays green for all four methods (-0.38 to -0.65 against
  the -0.70 yellow threshold), but on exception days losses average 1.23 times the ES forecast for full
  revaluation and 1.61 times for delta-normal; the bootstrap test rejects at 5% for all four.
- **Delta-only and delta-normal are not fit for use as configured.** 31 and 32 exceptions against 17.2 expected
  (Kupiec p 0.003 and 0.001), consistent with the developer's own result.
- **Conclusions:** full revaluation and delta-gamma HS fit for use with conditions (volatility scaling or a
  shorter look-back); delta HS and delta-normal not fit for use as configured.

On credit-pricing-lab's loan-level scores for the 2017 out-of-time year, 443,579 loans
(`outputs/pd_validation.md`):

- **Both PD models are fit for use.** The gradient-boosting champion's AUC is 0.672 (95% interval 0.669 to 0.674)
  against 0.655 for the scorecard; its mean PD is 5.96% against an observed default rate of 5.72%.
- **No grade's PD is too low.** On mv-lab's own grade scale, the largest under-prediction is grade A's 6% (1.35%
  observed against 1.27%), below the 10% materiality threshold and not significant (Jeffreys p 0.06). Grade G is
  conservative: 17.6% predicted, 15.4% observed (a Low finding: it overprices that grade).
- **Hosmer-Lemeshow rejects both models (p 9e-18 and 4e-6) on gaps no lender would act on.** With 443,579 loans
  the test rejects a portfolio gap of 0.24 points, which is why the rubric asks for an economic gap as well; both
  rejections are recorded as Low.

On the invented inputs (`mvlab demo`), each planted defect is found: the VaR 25% too low fails Kupiec, Z2
(red) and the traffic light; the VaR that ignores regimes fails independence; the PD that drifts out of time
fails the Jeffreys test in every grade; the well-specified VaR raises no finding.

A grounded narrative version of the findings above -- rendered from a fact map, not an LLM call, with every
number checked against that fact map before the file is written -- is at `outputs/commentary.md`
(`mvlab commentary`).

## Insight demonstrated

- A coverage test answers "how many", not "when". Clustering is the failure that matters for a limit framework,
  and only an independence test sees it.
- Z2 and exception-day residuals measure different things: Z2 averages over all days, so a model can be green on
  Z2 while each tail loss it does catch is a fifth larger than forecast.
- Validation is only as independent as its inputs: frozen, hashed outputs and no shared code are the parts of
  independence a single author can still enforce.

## Employer takeaway

For model validation and model risk roles: the standard VaR, ES and PD test batteries implemented from the
papers, applied to real model outputs, with findings graded by a written rubric and conclusions a model owner
could act on.

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
mvlab demo                                          # invented inputs with planted defects -> outputs/synthetic/
mvlab validate var                                  # the committed VaR snapshot -> outputs/var_validation.md
# PD: export loan-level scores from credit-pricing-lab, snapshot them, validate
mvlab snapshot pd ../credit-pricing-lab/data/exports/pd_scores.parquet --ref "credit-pricing-lab, <date>"
mvlab validate pd                                   # -> outputs/pd_validation.md
mvlab commentary                                    # -> outputs/commentary.md
```

## Repository layout

```
inventory/models.yml   model inventory (SS1/23 Principle 1 fields)
config/mvlab.yml       test levels and rubric thresholds
docs/rubric.md         severity rubric and conclusion rule
src/mvlab/             coverage, es_tests, pd_tests, var_validation, pd_validation, findings, report,
                       commentary, snapshot, inventory, synthetic, cli
data/snapshots/var/    the frozen VaR backtest and its manifest (PD snapshots are git-ignored)
tests/                 18 tests: each statistic against a hand calculation or a simulation with a known
                       answer, the independence import check, snapshot hashing, the demo's planted defects,
                       and commentary's grounding check (every rendered number traces to its fact map)
outputs/               var_validation.md, var_results.csv, var_findings.csv; pd_validation.md, pd_grades.csv,
                       pd_summary.json, pd_findings.csv (aggregates only)
                       commentary.md (grounded narrative over both)
```

## Limits

- Self-validation: the reports say so, and the organisational independence SS1/23 expects is not claimed.
- The VaR tests use the model's own P&L; this validation does not re-price the book.
- The Z2 thresholds are the approximate values from Acerbi and Szekely's simulations, not exact critical values.
- Thresholds outside the Basel traffic light are this project's rubric.

## Licence

MIT.
