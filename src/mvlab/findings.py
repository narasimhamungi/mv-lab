"""Findings and the severity rubric (docs/rubric.md).

High: the model does not do what its use needs (coverage rejected at 1%, an ES backtest in the red zone,
      a material grade's PD too low at 1%, or a PSI above the high threshold).
Medium: evidence of weakness that needs a remediation plan (rejection at 5%, a yellow zone, clustering,
      a material calibration gap at 5%, an out-of-time AUC drop, a PSI above the medium threshold).
Low: an observation to record (a conservative grade, a test that rejects only because the sample is
      very large, a limitation of the data).

Conclusion per model: "Fit for use" with no High or Medium finding; "Fit for use with conditions" with
Medium findings only; "Not fit for use as configured" with any High finding.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

SEVERITIES = ("High", "Medium", "Low")


@dataclass(frozen=True)
class Finding:
    model_id: str
    test: str
    severity: str
    statement: str
    evidence: str
    action: str

    def __post_init__(self):
        if self.severity not in SEVERITIES:
            raise ValueError(f"severity must be one of {SEVERITIES}")

    def row(self) -> dict:
        return asdict(self)


def conclusion(findings: list[Finding]) -> str:
    sev = {f.severity for f in findings}
    if "High" in sev:
        return "Not fit for use as configured"
    if "Medium" in sev:
        return "Fit for use with conditions"
    return "Fit for use"
