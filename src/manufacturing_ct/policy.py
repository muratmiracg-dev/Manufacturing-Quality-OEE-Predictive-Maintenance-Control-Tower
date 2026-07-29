"""Human-in-the-loop maintenance recommendation and prioritization policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PolicyConfig:
    intervention_effectiveness: float = 0.65
    urgent_multiplier: float = 1.25
    watch_multiplier: float = 0.65

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def maintenance_recommendation(
    failure_probability: float,
    model_threshold: float,
    criticality: int,
    failure_cost: float,
    maintenance_cost: float,
    reason_codes: list[str] | None = None,
    config: PolicyConfig | None = None,
) -> dict[str, Any]:
    """Return a recommendation only; never create or execute maintenance work."""

    policy = config or PolicyConfig()
    probability = float(np.clip(failure_probability, 0.0, 1.0))
    criticality_factor = 0.75 + 0.10 * int(np.clip(criticality, 1, 5))
    expected_failure_cost = probability * failure_cost * criticality_factor
    expected_avoided_loss = expected_failure_cost * policy.intervention_effectiveness
    net_benefit = expected_avoided_loss - maintenance_cost
    risk_cost_ratio = expected_avoided_loss / max(maintenance_cost, 1.0)

    if (
        probability >= min(model_threshold * policy.urgent_multiplier, 0.95)
        and criticality >= 4
        and net_benefit > 0
    ):
        priority = "P1"
        action = "Inspect within 8 hours; maintenance planner approval required"
    elif probability >= model_threshold and net_benefit > 0:
        priority = "P2"
        action = "Schedule diagnostic inspection within 24 hours"
    elif probability >= model_threshold * policy.watch_multiplier or risk_cost_ratio >= 0.75:
        priority = "P3"
        action = "Increase monitoring and review at next planning meeting"
    else:
        priority = "MONITOR"
        action = "Continue standard monitoring"

    return {
        "priority": priority,
        "recommended_action": action,
        "failure_probability": probability,
        "model_threshold": float(model_threshold),
        "criticality": int(criticality),
        "estimated_failure_cost": float(failure_cost),
        "estimated_maintenance_cost": float(maintenance_cost),
        "expected_failure_cost": float(expected_failure_cost),
        "expected_avoided_loss": float(expected_avoided_loss),
        "expected_net_benefit": float(net_benefit),
        "risk_cost_ratio": float(risk_cost_ratio),
        "reason_codes": (reason_codes or ["MODEL_RISK_SCORE"])[:3],
        "human_approval_required": True,
        "execution_mode": "recommendation_only",
    }


def prioritize_predictions(
    predictions: pd.DataFrame,
    model_threshold: float,
    reason_codes_by_shift: dict[str, list[str]] | None = None,
    config: PolicyConfig | None = None,
) -> pd.DataFrame:
    """Apply the policy to predictions and retain the latest record per machine."""

    latest = (
        predictions.sort_values("timestamp").groupby("machine_id", observed=True).tail(1).copy()
    )
    rows = []
    lookup = reason_codes_by_shift or {}
    for record in latest.to_dict("records"):
        decision = maintenance_recommendation(
            failure_probability=record["failure_probability"],
            model_threshold=model_threshold,
            criticality=int(record["criticality"]),
            failure_cost=float(record["failure_cost"]),
            maintenance_cost=float(record["maintenance_cost"]),
            reason_codes=lookup.get(str(record["shift_id"])),
            config=config,
        )
        rows.append({**record, **decision})
    priority_order = {"P1": 0, "P2": 1, "P3": 2, "MONITOR": 3}
    result = pd.DataFrame(rows)
    result["_priority_order"] = result["priority"].map(priority_order)
    return result.sort_values(
        ["_priority_order", "expected_net_benefit", "failure_probability"],
        ascending=[True, False, False],
        ignore_index=True,
    ).drop(columns="_priority_order")
