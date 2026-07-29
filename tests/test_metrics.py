from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from manufacturing_ct.metrics import (
    add_oee_components,
    aggregate_oee,
    downtime_pareto,
    executive_kpis,
    reliability_metrics,
)


@pytest.fixture
def production() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "machine_id": ["M1", "M1"],
            "line_id": ["L1", "L1"],
            "planned_production_min": [400.0, 400.0],
            "run_time_min": [360.0, 320.0],
            "ideal_cycle_sec": [30.0, 30.0],
            "total_units": [648, 576],
            "first_pass_good_units": [620, 540],
            "scrap_units": [10, 12],
            "rework_units": [18, 24],
            "copq": [280.0, 360.0],
            "unplanned_downtime_min": [40.0, 80.0],
        }
    )


def test_oee_components_and_ratio_of_sums(production: pd.DataFrame) -> None:
    enriched = add_oee_components(production)
    assert enriched.loc[0, "availability"] == pytest.approx(0.9)
    assert enriched.loc[0, "performance"] == pytest.approx(0.9)
    assert enriched.loc[0, "quality_rate"] == pytest.approx(620 / 648)
    assert enriched.loc[0, "oee"] == pytest.approx(0.9 * 0.9 * 620 / 648)
    aggregate = aggregate_oee(production.assign(plant="P"), ["plant"]).iloc[0]
    assert aggregate["availability"] == pytest.approx(680 / 800)
    assert aggregate["performance"] == pytest.approx((1224 * 30) / (680 * 60))
    assert aggregate["quality_rate"] == pytest.approx(1160 / 1224)


def test_pareto_reliability_and_executive_kpis(production: pd.DataFrame) -> None:
    downtime = pd.DataFrame(
        {
            "event_id": ["D1", "D2", "D3"],
            "machine_id": ["M1", "M1", "M1"],
            "planned": [False, False, False],
            "category": ["Bearing", "Minor Stop", "Bearing"],
            "duration_min": [120.0, 20.0, 60.0],
        }
    )
    machines = pd.DataFrame({"machine_id": ["M1"], "line_id": ["L1"], "criticality": [5]})
    pareto = downtime_pareto(downtime)
    assert pareto.iloc[0]["category"] == "Bearing"
    assert pareto.iloc[-1]["cumulative_share"] == pytest.approx(1.0)
    reliability = reliability_metrics(production, downtime, machines).iloc[0]
    assert reliability["failure_count"] == 2
    assert reliability["mttr_hours"] == pytest.approx(1.5)
    kpis = executive_kpis(production, downtime, machines)
    assert kpis["failure_count"] == 2
    assert kpis["total_units"] == 1224
    assert 0 < kpis["oee"] < 1


def test_empty_pareto_and_zero_failure_reliability(production: pd.DataFrame) -> None:
    empty = pd.DataFrame(columns=["event_id", "machine_id", "planned", "category", "duration_min"])
    pareto = downtime_pareto(empty)
    assert pareto.empty
    machines = pd.DataFrame({"machine_id": ["M1"], "line_id": ["L1"], "criticality": [3]})
    reliability = reliability_metrics(production, empty, machines).iloc[0]
    assert reliability["failure_count"] == 0
    assert np.isnan(reliability["mtbf_hours"])
    assert reliability["mttr_hours"] == 0
