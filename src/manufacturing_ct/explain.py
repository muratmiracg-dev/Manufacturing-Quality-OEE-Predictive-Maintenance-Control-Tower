"""SHAP explanations and operationally meaningful reason-code mapping."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import shap

from manufacturing_ct.modeling import FEATURES

REASON_CODE_MAP = {
    "vibration_rms": "HIGH_VIBRATION_PATTERN",
    "vibration_rolling_3": "SUSTAINED_VIBRATION",
    "temperature_c": "THERMAL_STRESS",
    "lubrication_index": "LOW_LUBRICATION_INDEX",
    "pressure_bar": "PRESSURE_DEVIATION",
    "current_amp": "ELECTRICAL_LOAD_STRESS",
    "tool_wear_pct": "TOOL_WEAR_ELEVATED",
    "hours_since_maintenance": "MAINTENANCE_INTERVAL_EXCEEDED",
    "failures_last_30d": "RECENT_FAILURE_HISTORY",
    "downtime_last_7d_min": "RECENT_DOWNTIME_BURDEN",
    "criticality": "ASSET_CRITICALITY",
    "machine_id": "MACHINE_BASELINE_EFFECT",
    "machine_type": "MACHINE_TYPE_EFFECT",
    "shift": "SHIFT_PATTERN",
    "product_id": "PRODUCT_MIX_EFFECT",
}


def _normalize_shap_values(values: Any) -> np.ndarray:
    if isinstance(values, list):
        return np.asarray(values[-1])
    array = np.asarray(values)
    if array.ndim == 3:
        return array[:, :, -1]
    if array.ndim != 2:
        raise ValueError(f"Unexpected SHAP output shape: {array.shape}")
    return array


def _base_feature(transformed_name: str) -> str:
    clean = transformed_name.split("__", 1)[-1]
    for feature in FEATURES:
        if clean == feature or clean.startswith(f"{feature}_"):
            return feature
    return clean


def reason_code_for_feature(transformed_name: str) -> str:
    """Map an encoded model feature to a stable maintenance reason code."""

    base = _base_feature(transformed_name)
    return REASON_CODE_MAP.get(base, f"MODEL_DRIVER_{base.upper()}")


def create_shap_outputs(
    bundle: dict[str, Any],
    oot_frame: pd.DataFrame,
    predictions: pd.DataFrame,
    output_directory: str | Path,
    max_explanations: int = 700,
) -> dict[str, Any]:
    """Generate global and local SHAP results from the actual champion base model."""

    destination = Path(output_directory)
    destination.mkdir(parents=True, exist_ok=True)
    base_pipeline = bundle["base_pipeline"]
    preprocessor = base_pipeline.named_steps["preprocessor"]
    estimator = base_pipeline.named_steps["estimator"]

    sample_count = min(max_explanations, len(oot_frame))
    probability_order = np.argsort(predictions["failure_probability"].to_numpy())[::-1]
    high_risk_count = min(sample_count // 2, len(probability_order))
    high_risk_indices = probability_order[:high_risk_count]
    rng = np.random.default_rng(20260729)
    remaining = np.setdiff1d(np.arange(len(oot_frame)), high_risk_indices)
    random_count = sample_count - high_risk_count
    random_indices = rng.choice(remaining, size=random_count, replace=False)
    selected = np.unique(np.concatenate([high_risk_indices, random_indices]))

    raw = oot_frame.iloc[selected][FEATURES]
    transformed = np.asarray(preprocessor.transform(raw), dtype=float)
    feature_names = list(preprocessor.get_feature_names_out())
    model_name = bundle["model_name"]
    if model_name == "random_forest":
        explainer = shap.TreeExplainer(estimator)
        shap_values = _normalize_shap_values(explainer.shap_values(transformed))
    elif model_name == "logistic_regression":
        background = transformed[: min(250, len(transformed))]
        explainer = shap.LinearExplainer(estimator, background)
        shap_values = _normalize_shap_values(explainer(transformed).values)
    else:
        raise ValueError(f"No SHAP implementation registered for {model_name}")

    global_rows = []
    for feature_name, importance in zip(
        feature_names, np.abs(shap_values).mean(axis=0), strict=True
    ):
        global_rows.append(
            {
                "transformed_feature": feature_name,
                "base_feature": _base_feature(feature_name),
                "reason_code": reason_code_for_feature(feature_name),
                "mean_absolute_shap": float(importance),
            }
        )
    global_importance = (
        pd.DataFrame(global_rows)
        .groupby(["base_feature", "reason_code"], as_index=False)["mean_absolute_shap"]
        .sum()
        .sort_values("mean_absolute_shap", ascending=False, ignore_index=True)
    )
    global_importance.to_csv(destination / "shap_global_importance.csv", index=False)

    local_rows: list[dict[str, Any]] = []
    explanation_lookup: dict[str, list[str]] = {}
    local_probability = predictions.iloc[selected]["failure_probability"].to_numpy()
    local_ids = predictions.iloc[selected]["shift_id"].to_numpy()
    for row_position, shift_id in enumerate(local_ids):
        positive_order = np.argsort(shap_values[row_position])[::-1]
        selected_features = [
            index for index in positive_order if shap_values[row_position, index] > 0
        ][:4]
        if not selected_features:
            selected_features = list(np.argsort(np.abs(shap_values[row_position]))[::-1][:4])
        codes: list[str] = []
        for rank, feature_index in enumerate(selected_features, start=1):
            code = reason_code_for_feature(feature_names[feature_index])
            if code not in codes:
                codes.append(code)
            local_rows.append(
                {
                    "shift_id": shift_id,
                    "failure_probability": float(local_probability[row_position]),
                    "rank": rank,
                    "transformed_feature": feature_names[feature_index],
                    "reason_code": code,
                    "shap_value": float(shap_values[row_position, feature_index]),
                    "transformed_value": float(transformed[row_position, feature_index]),
                }
            )
        explanation_lookup[str(shift_id)] = codes[:3]
    local_explanations = pd.DataFrame(local_rows).sort_values(
        ["failure_probability", "shift_id", "rank"],
        ascending=[False, True, True],
        ignore_index=True,
    )
    local_explanations.to_csv(destination / "shap_local_explanations.csv", index=False)
    return {
        "model_name": model_name,
        "explained_rows": len(selected),
        "transformed_feature_count": len(feature_names),
        "top_global_drivers": global_importance.head(10).to_dict("records"),
        "global_importance": global_importance,
        "local_explanations": local_explanations,
        "reason_codes_by_shift": explanation_lookup,
        "scope_note": (
            "SHAP explains the fitted base estimator. The sigmoid calibration layer "
            "changes reported probabilities but is not included in the attribution."
        ),
    }
