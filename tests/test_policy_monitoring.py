from __future__ import annotations

import pandas as pd
import pytest

from manufacturing_ct.monitoring import (
    alarm_quality,
    categorical_psi,
    data_quality_report,
    drift_report,
    population_stability_index,
)
from manufacturing_ct.policy import (
    PolicyConfig,
    maintenance_recommendation,
    prioritize_predictions,
)


def test_policy_priorities_and_human_boundary() -> None:
    urgent = maintenance_recommendation(0.8, 0.3, 5, 30000, 2000, ["HIGH_VIBRATION"])
    assert urgent["priority"] == "P1"
    assert urgent["human_approval_required"] is True
    assert urgent["execution_mode"] == "recommendation_only"
    schedule = maintenance_recommendation(0.35, 0.3, 3, 30000, 2000)
    assert schedule["priority"] == "P2"
    watch = maintenance_recommendation(0.22, 0.3, 2, 10000, 5000)
    assert watch["priority"] == "P3"
    monitor = maintenance_recommendation(0.01, 0.3, 1, 10000, 5000)
    assert monitor["priority"] == "MONITOR"
    assert PolicyConfig().to_dict()["intervention_effectiveness"] == pytest.approx(0.65)


def test_priority_table_keeps_latest_per_machine() -> None:
    predictions = pd.DataFrame(
        {
            "shift_id": ["S1", "S2", "S3"],
            "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-01"]),
            "machine_id": ["M1", "M1", "M2"],
            "failure_probability": [0.1, 0.7, 0.2],
            "criticality": [5, 5, 3],
            "failure_cost": [30000, 30000, 15000],
            "maintenance_cost": [2000, 2000, 3000],
        }
    )
    result = prioritize_predictions(predictions, 0.3, {"S2": ["THERMAL_STRESS"]})
    assert len(result) == 2
    assert "S1" not in result["shift_id"].tolist()
    assert result.iloc[0]["priority"] == "P1"


def test_drift_data_quality_and_alarm_metrics() -> None:
    reference = pd.DataFrame({"numeric": list(range(100)), "category": ["A"] * 50 + ["B"] * 50})
    current = pd.DataFrame({"numeric": list(range(40, 140)), "category": ["A"] * 20 + ["B"] * 80})
    assert population_stability_index(reference["numeric"], reference["numeric"]) == pytest.approx(
        0
    )
    assert population_stability_index(reference["numeric"], current["numeric"]) > 0
    assert categorical_psi(reference["category"], current["category"]) > 0
    report = drift_report(reference, current, ["numeric"], ["category"])
    assert set(report["severity"]).issubset({"stable", "watch", "action"})

    production = pd.DataFrame(
        {
            "shift_id": ["S1", "S2"],
            "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "machine_id": ["M1", "M1"],
            "product_id": ["P1", "P1"],
            "vibration_rms": [2.0, 3.0],
            "temperature_c": [60.0, 70.0],
            "pressure_bar": [6.0, 5.8],
            "total_units": [100, 90],
            "scrap_units": [2, 3],
            "rework_units": [1, 2],
            "unplanned_downtime_min": [10, 20],
            "planned_production_min": [400, 400],
        }
    )
    checks = data_quality_report(production)
    assert checks["passed"].all()
    predictions = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "alert": [1, 1, 0],
            "failure_within_24h": [1, 0, 1],
            "next_failure_hours": [8.0, float("nan"), 16.0],
        }
    )
    alarms = alarm_quality(predictions)
    assert alarms["alerts"] == 2
    assert alarms["false_alerts"] == 1
    assert alarms["missed_failures"] == 1


def test_psi_rejects_empty_samples() -> None:
    with pytest.raises(ValueError):
        population_stability_index(pd.Series(dtype=float), pd.Series([1.0]))
