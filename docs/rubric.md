# Severity rubric

Each test that fails produces one finding with a severity. A model's conclusion follows from its findings.

| Severity | Raised when | Expected response |
|---|---|---|
| High | Kupiec coverage rejected at 1%; the latest 250-day traffic-light window red; ES Z2 in the red zone (at or below -1.80); a grade holding at least 5% of loans has a PD too low at the 1% level (Jeffreys) with a gap above 10% of the PD; score PSI above 0.25 | Do not use the model for its stated purpose until remediated |
| Medium | Kupiec rejected at 5%; exceptions cluster (Christoffersen, 5%); a red traffic-light window in the history; Z2 yellow (at or below -0.70); exception-day losses above ES (bootstrap, 5%); a grade's PD too low at 5% with a gap above 10%; Hosmer-Lemeshow rejected with a portfolio gap above 10%; out-of-time AUC more than 0.03 below validation; score PSI above 0.10 | Use with conditions and a dated remediation plan |
| Low | A grade's PD conservative at 5% with a gap above 10%; Hosmer-Lemeshow rejected with an immaterial portfolio gap | Record |

| Conclusion | Rule |
|---|---|
| Fit for use | No High or Medium finding |
| Fit for use with conditions | Medium findings only |
| Not fit for use as configured | Any High finding |

Why an economic threshold sits beside every p-value: with hundreds of thousands of loans, a goodness-of-fit test rejects gaps no lender would act on. A finding needs both the statistical evidence and a gap above 10% of the PD.

Sources for the tests: Kupiec (1995); Christoffersen (1998); the Basel Committee's backtesting traffic light (zones at 99% over 250 days); Acerbi and Szekely (2014) for Z2 and its approximate thresholds; McNeil and Frey (2000) for exceedance residuals; the ECB guide to internal models for the Jeffreys test. The PRA's SS1/23 sets the frame: model inventory and tiering (Principle 1), independent validation (Principle 4), and findings with remediation (Principle 5). The thresholds in this table, other than the traffic-light zones, are this project's choices.
