import pandas as pd

from modules.recommendations.cost_model import (
    CostModelParams,
    baseline_cost,
    compare_costs,
    cost_with_recommendations,
)

def _df_base():
    # 3 hours, kWh per hour, €/kWh
    return pd.DataFrame(
        {
            "datetime": pd.to_datetime(
                ["2025-01-01T00:00:00Z", "2025-01-01T01:00:00Z", "2025-01-01T02:00:00Z"],
                utc=True,
            ),
            "pv_kwh": [0.0, 2.0, 0.0],
            "load_kwh": [1.0, 1.0, 2.0],
            "price_eur_kwh": [0.10, 0.30, 0.20],
        }
    )

def _reco(actions):
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                ["2025-01-01T00:00:00Z", "2025-01-01T01:00:00Z", "2025-01-01T02:00:00Z"],
                utc=True,
            ),
            "action": actions,
        }
    )

def test_baseline_cost_simple():
    df = _df_base()
    params = CostModelParams(feed_in_factor=0.0)

    # baseline import:
    # hour0: import 1 (pv 0, load 1) -> cost 0.10
    # hour1: export 1 (pv2 - load1) -> no revenue
    # hour2: import 2 -> cost 0.40
    out = baseline_cost(df, params)
    assert round(out["cost_eur"], 5) == 0.50
    assert round(out["import_kwh"], 5) == 3.0
    assert round(out["export_kwh"], 5) == 1.0

def test_recommendations_reduce_cost():
    df = _df_base()
    params = CostModelParams(feed_in_factor=0.0, discharge_offset=1.0, charge_capture=1.0)

    # discharge at hour2 should remove import of 2 kWh at price 0.2 -> save 0.4
    reco = _reco(["idle", "idle", "discharge"])
    out = cost_with_recommendations(df, reco, params)

    assert round(out["cost_eur"], 5) == 0.10  # only hour0 import remains

def test_compare_costs_contains_expected_keys():
    df = _df_base()
    reco = _reco(["idle", "idle", "discharge"])

    out = compare_costs(df, reco)
    assert "baseline_cost_eur" in out
    assert "recommended_cost_eur" in out
    assert "savings_eur" in out

