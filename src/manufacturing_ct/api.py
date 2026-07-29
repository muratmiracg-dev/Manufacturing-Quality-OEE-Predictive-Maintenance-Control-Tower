"""FastAPI recommendation-only inference service with Prometheus metrics."""

from __future__ import annotations

import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, ConfigDict, Field

from manufacturing_ct.modeling import FEATURES
from manufacturing_ct.policy import maintenance_recommendation

REQUESTS = Counter(
    "manufacturing_recommendation_requests_total",
    "Recommendation requests by outcome.",
    ["outcome"],
)
LATENCY = Histogram(
    "manufacturing_recommendation_latency_seconds",
    "Recommendation endpoint latency.",
)
RISK_SCORE = Histogram(
    "manufacturing_failure_probability",
    "Distribution of reported failure probabilities.",
    buckets=(0.02, 0.05, 0.1, 0.2, 0.35, 0.5, 0.7, 0.9, 1.0),
)


class MachineSnapshot(BaseModel):
    """Validated pre-shift feature snapshot and cost context."""

    model_config = ConfigDict(extra="forbid")

    line_id: str = Field(min_length=1, max_length=40)
    machine_id: str = Field(min_length=1, max_length=40)
    machine_type: str = Field(min_length=1, max_length=40)
    product_id: str = Field(min_length=1, max_length=40)
    shift: str = Field(pattern="^[ABC]$")
    criticality: int = Field(ge=1, le=5)
    machine_age_years: float = Field(ge=0, le=80)
    planned_downtime_min: float = Field(ge=0, le=480)
    vibration_rms: float = Field(ge=0, le=15)
    temperature_c: float = Field(ge=0, le=180)
    pressure_bar: float = Field(ge=0, le=20)
    current_amp: float = Field(ge=0, le=250)
    lubrication_index: float = Field(ge=0, le=100)
    tool_wear_pct: float = Field(ge=0, le=100)
    ambient_temperature_c: float = Field(ge=-40, le=80)
    ambient_humidity_pct: float = Field(ge=0, le=100)
    hours_since_maintenance: float = Field(ge=0, le=10000)
    cumulative_operating_hours: float = Field(ge=0)
    changeover_count: int = Field(ge=0, le=20)
    failures_last_30d: int = Field(ge=0, le=100)
    defect_rate_lag_1: float = Field(ge=0, le=1)
    downtime_last_7d_min: float = Field(ge=0, le=10080)
    vibration_rolling_3: float = Field(ge=0, le=15)
    failure_cost: float = Field(gt=0)
    maintenance_cost: float = Field(gt=0)


class RecommendationResponse(BaseModel):
    """Auditable human-in-the-loop response contract."""

    model_name: str
    prediction_horizon_hours: int
    priority: str
    recommended_action: str
    failure_probability: float
    model_threshold: float
    criticality: int
    estimated_failure_cost: float
    estimated_maintenance_cost: float
    expected_failure_cost: float
    expected_avoided_loss: float
    expected_net_benefit: float
    risk_cost_ratio: float
    reason_codes: list[str]
    human_approval_required: bool
    execution_mode: str
    disclaimer: str


class Predictor(Protocol):
    model_name: str
    prediction_horizon_hours: int
    threshold: float

    def predict_probability(self, snapshot: dict[str, Any]) -> float: ...

    def reason_codes(self, snapshot: dict[str, Any]) -> list[str]: ...


class ModelService:
    """Load and serve a validated champion bundle."""

    def __init__(self, bundle_path: str | Path):
        bundle = joblib.load(bundle_path)
        self.model = bundle["calibrated_model"]
        self.base_pipeline = bundle["base_pipeline"]
        self.model_name = str(bundle["model_name"])
        self.prediction_horizon_hours = int(bundle["prediction_horizon_hours"])
        self.threshold = float(bundle["threshold"])

    def predict_probability(self, snapshot: dict[str, Any]) -> float:
        frame = pd.DataFrame([{feature: snapshot[feature] for feature in FEATURES}])
        return float(self.model.predict_proba(frame)[:, 1][0])

    def reason_codes(self, snapshot: dict[str, Any]) -> list[str]:
        candidates: list[tuple[str, float]] = [
            ("HIGH_VIBRATION_PATTERN", snapshot["vibration_rms"] / 4.5),
            ("THERMAL_STRESS", snapshot["temperature_c"] / 78.0),
            ("LOW_LUBRICATION_INDEX", (100 - snapshot["lubrication_index"]) / 52.0),
            (
                "MAINTENANCE_INTERVAL_EXCEEDED",
                snapshot["hours_since_maintenance"] / 650.0,
            ),
            ("RECENT_FAILURE_HISTORY", snapshot["failures_last_30d"] / 2.0),
        ]
        return [name for name, _ in sorted(candidates, key=lambda item: item[1], reverse=True)[:3]]


@lru_cache(maxsize=1)
def default_model_service() -> ModelService:
    path = os.getenv("MODEL_BUNDLE_PATH", "artifacts/model/champion_bundle.joblib")
    if not Path(path).exists():
        raise FileNotFoundError(f"Champion model bundle not found: {path}")
    return ModelService(path)


def create_app(predictor: Predictor | None = None) -> FastAPI:
    """Create the API with optional dependency injection for tests."""

    application = FastAPI(
        title="Manufacturing Predictive Maintenance Decision Support API",
        version="1.0.0",
        description=(
            "Recommendation-only synthetic demonstration. Every action requires "
            "qualified human review and approval."
        ),
    )

    def resolve_predictor() -> Predictor:
        return predictor or default_model_service()

    @application.get("/health")
    def health() -> dict[str, Any]:
        try:
            service = resolve_predictor()
        except (FileNotFoundError, KeyError, ValueError) as exc:
            return {"status": "degraded", "model_ready": False, "detail": str(exc)}
        return {
            "status": "ok",
            "model_ready": True,
            "model_name": service.model_name,
            "execution_mode": "recommendation_only",
        }

    @application.post("/v1/recommendations", response_model=RecommendationResponse)
    def recommend(snapshot: MachineSnapshot) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            service = resolve_predictor()
            payload = snapshot.model_dump()
            probability = service.predict_probability(payload)
            decision = maintenance_recommendation(
                failure_probability=probability,
                model_threshold=service.threshold,
                criticality=snapshot.criticality,
                failure_cost=snapshot.failure_cost,
                maintenance_cost=snapshot.maintenance_cost,
                reason_codes=service.reason_codes(payload),
            )
            REQUESTS.labels(outcome="success").inc()
            RISK_SCORE.observe(probability)
            return {
                "model_name": service.model_name,
                "prediction_horizon_hours": service.prediction_horizon_hours,
                **decision,
                "disclaimer": (
                    "Decision support only. A qualified maintenance planner must "
                    "review evidence, safety context, and operating constraints."
                ),
            }
        except (FileNotFoundError, KeyError, ValueError) as exc:
            REQUESTS.labels(outcome="error").inc()
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        finally:
            LATENCY.observe(time.perf_counter() - started)

    @application.get("/metrics")
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return application


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run(
        "manufacturing_ct.api:app",
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", "8000")),
    )


if __name__ == "__main__":
    run()
