"""Data-quality, drift and operational alarm-quality monitoring."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def population_stability_index(
    reference: pd.Series,
    current: pd.Series,
    bins: int = 10,
    epsilon: float = 1e-6,
) -> float:
    """Calculate numeric PSI using reference quantile bins."""

    ref = pd.Series(reference, dtype=float).dropna()
    cur = pd.Series(current, dtype=float).dropna()
    if ref.empty or cur.empty:
        raise ValueError("PSI requires non-empty reference and current samples")
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    ref_counts = pd.cut(ref, edges, include_lowest=True).value_counts(sort=False)
    cur_counts = pd.cut(cur, edges, include_lowest=True).value_counts(sort=False)
    ref_share = np.maximum(ref_counts.to_numpy() / len(ref), epsilon)
    cur_share = np.maximum(cur_counts.to_numpy() / len(cur), epsilon)
    return float(np.sum((cur_share - ref_share) * np.log(cur_share / ref_share)))


def categorical_psi(reference: pd.Series, current: pd.Series, epsilon: float = 1e-6) -> float:
    """Calculate PSI across the union of categorical levels."""

    ref = pd.Series(reference).fillna("__MISSING__").astype(str)
    cur = pd.Series(current).fillna("__MISSING__").astype(str)
    categories = sorted(set(ref) | set(cur))
    ref_share = ref.value_counts(normalize=True).reindex(categories, fill_value=0).to_numpy()
    cur_share = cur.value_counts(normalize=True).reindex(categories, fill_value=0).to_numpy()
    ref_share = np.maximum(ref_share, epsilon)
    cur_share = np.maximum(cur_share, epsilon)
    return float(np.sum((cur_share - ref_share) * np.log(cur_share / ref_share)))


def drift_report(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    numeric_features: list[str],
    categorical_features: list[str],
) -> pd.DataFrame:
    """Return feature PSI with traffic-light severity."""

    rows: list[dict[str, Any]] = []
    for feature in numeric_features:
        score = population_stability_index(reference[feature], current[feature])
        rows.append({"feature": feature, "feature_type": "numeric", "psi": score})
    for feature in categorical_features:
        score = categorical_psi(reference[feature], current[feature])
        rows.append({"feature": feature, "feature_type": "categorical", "psi": score})
    result = pd.DataFrame(rows).sort_values("psi", ascending=False, ignore_index=True)
    result["severity"] = pd.cut(
        result["psi"],
        bins=[-np.inf, 0.10, 0.20, np.inf],
        labels=["stable", "watch", "action"],
        right=False,
    ).astype(str)
    return result


def data_quality_report(frame: pd.DataFrame) -> pd.DataFrame:
    """Evaluate operational input contract checks without mutating data."""

    checks = [
        (
            "primary_key_unique",
            bool(frame["shift_id"].is_unique),
            int(frame["shift_id"].duplicated().sum()),
        ),
        (
            "required_fields_complete",
            bool(
                frame[
                    [
                        "timestamp",
                        "machine_id",
                        "product_id",
                        "vibration_rms",
                        "temperature_c",
                    ]
                ]
                .notna()
                .all()
                .all()
            ),
            int(frame.isna().sum().sum()),
        ),
        (
            "non_negative_counts",
            bool(
                (
                    frame[
                        [
                            "total_units",
                            "scrap_units",
                            "rework_units",
                            "unplanned_downtime_min",
                        ]
                    ]
                    >= 0
                )
                .all()
                .all()
            ),
            int(
                (
                    frame[
                        [
                            "total_units",
                            "scrap_units",
                            "rework_units",
                            "unplanned_downtime_min",
                        ]
                    ]
                    < 0
                )
                .sum()
                .sum()
            ),
        ),
        (
            "downtime_within_shift",
            bool((frame["unplanned_downtime_min"] <= frame["planned_production_min"]).all()),
            int((frame["unplanned_downtime_min"] > frame["planned_production_min"]).sum()),
        ),
        (
            "sensor_ranges_plausible",
            bool(
                frame["vibration_rms"].between(0, 15).all()
                and frame["temperature_c"].between(20, 150).all()
                and frame["pressure_bar"].between(0, 12).all()
            ),
            int(
                (~frame["vibration_rms"].between(0, 15)).sum()
                + (~frame["temperature_c"].between(20, 150)).sum()
                + (~frame["pressure_bar"].between(0, 12)).sum()
            ),
        ),
    ]
    return pd.DataFrame(checks, columns=["check", "passed", "exceptions"])


def alarm_quality(predictions: pd.DataFrame) -> dict[str, float | int]:
    """Summarize alert precision, capture, burden and available lead time."""

    alerts = predictions["alert"].astype(bool)
    truth = predictions["failure_within_24h"].astype(bool)
    true_alerts = alerts & truth
    observed_days = max(
        (
            pd.to_datetime(predictions["timestamp"]).max()
            - pd.to_datetime(predictions["timestamp"]).min()
        ).days,
        1,
    )
    lead_time = predictions.loc[true_alerts, "next_failure_hours"].dropna()
    return {
        "alerts": int(alerts.sum()),
        "alerts_per_day": float(alerts.sum() / observed_days),
        "alert_precision": float(true_alerts.sum() / max(alerts.sum(), 1)),
        "failure_capture_rate": float(true_alerts.sum() / max(truth.sum(), 1)),
        "median_lead_time_hours": float(lead_time.median()) if not lead_time.empty else 0.0,
        "false_alerts": int((alerts & ~truth).sum()),
        "missed_failures": int((~alerts & truth).sum()),
    }
