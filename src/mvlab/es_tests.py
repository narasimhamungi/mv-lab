"""Expected-shortfall backtests that need only the forecast VaR, ES and the realised loss.

* Acerbi and Szekely (2014) Z2: Z2 = 1 - sum(L_t * I_t / ES_t) / (T * (1 - alpha)), losses positive.
  Under a correct ES its expectation is 0; it is negative when realised tail losses are larger or more
  frequent than forecast. The paper reports that its significance thresholds are stable across
  distributions: about -0.70 at the 5% level and -1.8 at 0.01%, which this module uses as yellow and red.
  These thresholds are approximations from the paper's simulations, not exact critical values.
* Exceedance residuals (McNeil and Frey, 2000): on exception days, r_t = (L_t - ES_t) / ES_t should have
  mean zero. A one-sided bootstrap test asks whether tail losses run larger than the ES said.
"""
from __future__ import annotations

import numpy as np

Z2_YELLOW, Z2_RED = -0.70, -1.80


def acerbi_szekely_z2(loss, var, es, alpha: float) -> dict:
    loss, var, es = (np.asarray(v, dtype=float) for v in (loss, var, es))
    exc = loss > var
    t = len(loss)
    z2 = 1 - float(np.sum(loss[exc] / es[exc])) / (t * (1 - alpha)) if t else None
    zone = None if z2 is None else ("red" if z2 <= Z2_RED else "yellow" if z2 <= Z2_YELLOW else "green")
    return {"z2": z2, "zone": zone, "exceptions": int(exc.sum()), "forecasts": t}


def exceedance_residuals(loss, var, es, draws: int = 5000, seed: int = 7) -> dict:
    loss, var, es = (np.asarray(v, dtype=float) for v in (loss, var, es))
    exc = loss > var
    r = (loss[exc] - es[exc]) / es[exc]
    if len(r) < 2:
        return {"n": int(len(r)), "mean": None, "p_value": None}
    rng = np.random.default_rng(seed)
    centred = r - r.mean()
    boot = rng.choice(centred, size=(draws, len(r)), replace=True).mean(axis=1)
    p = float((boot >= r.mean()).mean())          # H0: mean residual <= 0; small p = tail losses exceed ES
    return {"n": int(len(r)), "mean": float(r.mean()), "median": float(np.median(r)), "p_value": p,
            "loss_over_es": float((loss[exc] / es[exc]).mean())}
