from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from manufacturing_ct.api import create_app


class StaticPredictor:
    model_name = "test_champion"
    prediction_horizon_hours = 24
    threshold = 0.30

    def predict_probability(self, snapshot: dict[str, Any]) -> float:
        return 0.72 if snapshot["vibration_rms"] > 4 else 0.08

    def reason_codes(self, snapshot: dict[str, Any]) -> list[str]:
        return ["HIGH_VIBRATION_PATTERN"]


def payload() -> dict[str, Any]:
    return {
        "line_id": "LINE-A",
        "machine_id": "MC-01",
        "machine_type": "CNC",
        "product_id": "PRD-A",
        "shift": "A",
        "criticality": 5,
        "machine_age_years": 9,
        "planned_downtime_min": 18,
        "vibration_rms": 5.2,
        "temperature_c": 78,
        "pressure_bar": 5.6,
        "current_amp": 46,
        "lubrication_index": 42,
        "tool_wear_pct": 73,
        "ambient_temperature_c": 25,
        "ambient_humidity_pct": 52,
        "hours_since_maintenance": 610,
        "cumulative_operating_hours": 50000,
        "changeover_count": 1,
        "failures_last_30d": 1,
        "defect_rate_lag_1": 0.04,
        "downtime_last_7d_min": 120,
        "vibration_rolling_3": 4.8,
        "failure_cost": 30000,
        "maintenance_cost": 2500,
    }


def test_api_health_recommendation_and_metrics() -> None:
    client = TestClient(create_app(StaticPredictor()))
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["model_ready"] is True
    response = client.post("/v1/recommendations", json=payload())
    assert response.status_code == 200
    body = response.json()
    assert body["priority"] == "P1"
    assert body["human_approval_required"] is True
    assert body["execution_mode"] == "recommendation_only"
    assert body["reason_codes"] == ["HIGH_VIBRATION_PATTERN"]
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "manufacturing_recommendation_requests_total" in metrics.text


def test_api_rejects_invalid_contract() -> None:
    client = TestClient(create_app(StaticPredictor()))
    invalid = payload()
    invalid["vibration_rms"] = -1
    invalid["extra_field"] = "not allowed"
    response = client.post("/v1/recommendations", json=invalid)
    assert response.status_code == 422


def test_api_reports_degraded_without_bundle(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_BUNDLE_PATH", "/does/not/exist.joblib")
    from manufacturing_ct.api import default_model_service

    default_model_service.cache_clear()
    client = TestClient(create_app())
    health = client.get("/health")
    assert health.json()["status"] == "degraded"
    response = client.post("/v1/recommendations", json=payload())
    assert response.status_code == 503
    default_model_service.cache_clear()
