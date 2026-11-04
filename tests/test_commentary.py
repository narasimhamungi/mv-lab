from mvlab.commentary import build_pd_fact_map, build_var_fact_map, check_grounding, render_commentary
from mvlab.findings import Finding
import pandas as pd


def _var_results():
    return pd.DataFrame([
        {"method": "full_reval", "kupiec_p": 0.18, "independence_p": 0.002, "exceptions": 23, "expected": 17.2,
         "z2": -0.38, "z2_zone": "green"},
        {"method": "delta_normal", "kupiec_p": 0.001, "independence_p": 0.0002, "exceptions": 32, "expected": 17.2,
         "z2": -0.90, "z2_zone": "yellow"},
    ])


def _var_findings():
    return [
        Finding("VAR-OPT-01", "Kupiec POF (delta_normal, 99%)", "High", "delta_normal: coverage fails.",
                "32 exceptions vs 17.2 expected; p = 0.001", "Do not use."),
        Finding("VAR-OPT-01", "Christoffersen independence (full_reval)", "Medium", "full_reval: clusters.",
                "p = 0.002", "Add volatility scaling."),
    ]


def _pd_summaries():
    return {
        "gbm": {"loans": 443579, "default_rate": 0.0572, "mean_pd": 0.0596, "auc_test": 0.672,
                "auc_test_low": 0.669, "auc_test_high": 0.674},
        "scorecard": {"loans": 443579, "default_rate": 0.0572, "mean_pd": 0.0587, "auc_test": 0.655,
                      "auc_test_low": 0.652, "auc_test_high": 0.658},
    }


def _pd_findings():
    return {
        "gbm": [Finding("PD-CONS-01", "Hosmer-Lemeshow (gbm)", "Low", "Rejected on large-sample gaps.",
                        "p = 8.9e-18", "Review the grade table.")],
        "scorecard": [],
    }


def test_build_var_fact_map_finds_the_real_worst_method():
    facts = build_var_fact_map(_var_results(), _var_findings())
    assert facts["worst_kupiec_method"] == "delta_normal"
    assert facts["worst_independence_method"] == "delta_normal"
    assert facts["worst_z2_method"] == "delta_normal"
    assert facts["n_high"] == 1
    assert facts["n_medium"] == 1


def test_build_pd_fact_map_separates_champion_and_challenger():
    facts = build_pd_fact_map(_pd_summaries(), _pd_findings(), champion="gbm")
    assert facts["champion"] == "gbm"
    assert facts["challenger"] == "scorecard"
    assert facts["champion_n_medium"] == 0  # the one finding is Low, not Medium/High
    assert facts["challenger_conclusion"] == "Fit for use"


def test_render_commentary_passes_grounding():
    vf = build_var_fact_map(_var_results(), _var_findings())
    pf = build_pd_fact_map(_pd_summaries(), _pd_findings(), champion="gbm")
    text = render_commentary(vf, pf)
    assert check_grounding(text, vf, pf) == []


def test_check_grounding_catches_an_invented_number():
    vf = build_var_fact_map(_var_results(), _var_findings())
    pf = build_pd_fact_map(_pd_summaries(), _pd_findings(), champion="gbm")
    text = render_commentary(vf, pf) + "\n\nA made-up figure: 777777.\n"
    assert "777777" in check_grounding(text, vf, pf)
