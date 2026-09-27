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


def _validate_policy_inputs(
    failure_probability: float,
    model_threshold: float,
    criticality: int,
    failure_cost: float,
    maintenance_cost: float,
    policy: PolicyConfig,
) -> tuple[float, float, int, float, float]:
    """Return normalized policy inputs after fail-closed domain validation."""

    try:
        values = np.asarray(
            [
                failure_probability,
                model_threshold,
                criticality,
                failure_cost,
                maintenance_cost,
                policy.intervention_effectiveness,
                policy.urgent_multiplier,
                policy.watch_multiplier,
            ],
            dtype=float,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("Maintenance policy inputs must be numeric") from exc
    if not np.isfinite(values).all():
        raise ValueError("Maintenance policy inputs must be finite")

    probability, threshold, criticality_value, failure, maintenance = values[:5]
    if not 0.0 <= probability <= 1.0:
        raise ValueError("Failure probability must be between zero and one")
    if not 0.0 < threshold < 1.0:
        raise ValueError("Model threshold must be strictly between zero and one")
    if isinstance(criticality, bool | np.bool_) or not criticality_value.is_integer():
        raise ValueError("Criticality must be an integer between one and five")
    criticality_integer = int(criticality_value)
    if not 1 <= criticality_integer <= 5:
        raise ValueError("Criticality must be an integer between one and five")
    if failure <= 0.0 or maintenance <= 0.0:
        raise ValueError("Failure and maintenance costs must be positive")
    if not 0.0 < policy.intervention_effectiveness <= 1.0:
        raise ValueError("Intervention effectiveness must be in (0, 1]")
    if policy.urgent_multiplier < 1.0:
        raise ValueError("Urgent multiplier must be at least one")
    if not 0.0 < policy.watch_multiplier < 1.0:
        raise ValueError("Watch multiplier must be in (0, 1)")
    return probability, threshold, criticality_integer, failure, maintenance


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
    probability, threshold, criticality, failure_cost, maintenance_cost = _validate_policy_inputs(
        failure_probability,
        model_threshold,
        criticality,
        failure_cost,
        maintenance_cost,
        policy,
    )
    criticality_factor = 0.75 + 0.10 * criticality
    expected_failure_cost = probability * failure_cost * criticality_factor
    expected_avoided_loss = expected_failure_cost * policy.intervention_effectiveness
    net_benefit = expected_avoided_loss - maintenance_cost
    risk_cost_ratio = expected_avoided_loss / max(maintenance_cost, 1.0)

    if (
        probability >= min(threshold * policy.urgent_multiplier, 0.95)
        and criticality >= 4
        and net_benefit > 0
    ):
        priority = "P1"
        action = "Inspect within 8 hours; maintenance planner approval required"
    elif probability >= threshold and net_benefit > 0:
        priority = "P2"
        action = "Schedule diagnostic inspection within 24 hours"
    elif probability >= threshold * policy.watch_multiplier or risk_cost_ratio >= 0.75:
        priority = "P3"
        action = "Increase monitoring and review at next planning meeting"
    else:
        priority = "MONITOR"
        action = "Continue standard monitoring"

    return {
        "priority": priority,
        "recommended_action": action,
        "failure_probability": probability,
        "model_threshold": threshold,
        "criticality": criticality,
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
