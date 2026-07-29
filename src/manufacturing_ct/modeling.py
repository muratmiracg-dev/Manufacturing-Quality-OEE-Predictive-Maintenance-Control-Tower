"""Leakage-controlled champion/challenger predictive-maintenance modeling."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from manufacturing_ct.config import PipelineConfig

CATEGORICAL_FEATURES = [
    "line_id",
    "machine_id",
    "machine_type",
    "product_id",
    "shift",
]

NUMERIC_FEATURES = [
    "criticality",
    "machine_age_years",
    "planned_downtime_min",
    "vibration_rms",
    "temperature_c",
    "pressure_bar",
    "current_amp",
    "lubrication_index",
    "tool_wear_pct",
    "ambient_temperature_c",
    "ambient_humidity_pct",
    "hours_since_maintenance",
    "cumulative_operating_hours",
    "changeover_count",
    "failures_last_30d",
    "defect_rate_lag_1",
    "downtime_last_7d_min",
    "vibration_rolling_3",
]

FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET = "failure_within_24h"


@dataclass(frozen=True)
class ThresholdResult:
    threshold: float
    expected_cost_per_observation: float
    precision: float
    recall: float
    f1: float
    alert_rate: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def temporal_partitions(frame: pd.DataFrame, config: PipelineConfig) -> dict[str, pd.DataFrame]:
    """Create development, validation and OOT splits with purged label horizons."""

    timestamps = pd.to_datetime(frame["timestamp"])
    horizon = pd.Timedelta(hours=config.prediction_horizon_hours)
    validation_start = pd.Timestamp(config.validation_start)
    oot_start = pd.Timestamp(config.oot_start)
    end = pd.Timestamp(config.end_date) + pd.Timedelta(days=1)

    development = frame.loc[timestamps < validation_start - horizon].copy()
    validation = frame.loc[
        (timestamps >= validation_start) & (timestamps < oot_start - horizon)
    ].copy()
    oot = frame.loc[(timestamps >= oot_start) & (timestamps < end - horizon)].copy()
    if min(len(development), len(validation), len(oot)) == 0:
        raise ValueError("Temporal partitions must all contain observations")
    if not (
        pd.to_datetime(development["timestamp"]).max()
        < pd.to_datetime(validation["timestamp"]).min()
        < pd.to_datetime(oot["timestamp"]).min()
    ):
        raise ValueError("Temporal ordering or purge gap is invalid")
    return {"development": development, "validation": validation, "oot": oot}


def development_train_calibration_split(
    development: pd.DataFrame, horizon_hours: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reserve the final 60 development days for probability calibration."""

    timestamps = pd.to_datetime(development["timestamp"])
    calibration_start = timestamps.max().normalize() - pd.Timedelta(days=59)
    horizon = pd.Timedelta(hours=horizon_hours)
    train = development.loc[timestamps < calibration_start - horizon].copy()
    calibration = development.loc[timestamps >= calibration_start].copy()
    if min(len(train), len(calibration)) == 0:
        raise ValueError("Development train and calibration partitions must be non-empty")
    if pd.to_datetime(train["timestamp"]).max() >= pd.to_datetime(calibration["timestamp"]).min():
        raise ValueError("Calibration split must be strictly later than model fitting data")
    return train, calibration


def _preprocessor() -> ColumnTransformer:
    numeric = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ],
        verbose_feature_names_out=True,
    )


def build_candidate(name: str, seed: int) -> Pipeline:
    """Build a deterministic candidate with imbalance controls."""

    if name == "random_forest":
        estimator = RandomForestClassifier(
            n_estimators=260,
            max_depth=11,
            min_samples_leaf=7,
            max_features="sqrt",
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=seed,
        )
    elif name == "logistic_regression":
        estimator = LogisticRegression(
            C=0.65,
            class_weight="balanced",
            max_iter=1500,
            random_state=seed,
        )
    else:
        raise ValueError(f"Unknown model candidate: {name}")
    return Pipeline([("preprocessor", _preprocessor()), ("estimator", estimator)])


def fit_calibrated_candidate(
    name: str,
    train: pd.DataFrame,
    calibration: pd.DataFrame,
    seed: int,
) -> tuple[Pipeline, CalibratedClassifierCV]:
    """Fit base model on earlier data and sigmoid calibration on later data."""

    if train[TARGET].nunique() < 2 or calibration[TARGET].nunique() < 2:
        raise ValueError("Training and calibration data must each contain both target classes")
    base = build_candidate(name, seed)
    base.fit(train[FEATURES], train[TARGET])
    calibrated = CalibratedClassifierCV(FrozenEstimator(base), method="sigmoid")
    calibrated.fit(calibration[FEATURES], calibration[TARGET])
    return base, calibrated


def expected_classification_cost(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    false_negative_cost: float,
    false_positive_cost: float,
) -> float:
    """Return mean asymmetric classification cost."""

    false_negative = np.sum((y_true == 1) & (y_pred == 0))
    false_positive = np.sum((y_true == 0) & (y_pred == 1))
    return float(
        (false_negative * false_negative_cost + false_positive * false_positive_cost)
        / max(len(y_true), 1)
    )


def select_threshold(
    y_true: pd.Series | np.ndarray,
    probabilities: pd.Series | np.ndarray,
    false_negative_cost: float,
    false_positive_cost: float,
    minimum_recall: float,
    maximum_alert_rate: float = 1.0,
) -> ThresholdResult:
    """Select a validation-only cost threshold subject to recall and capacity limits."""

    truth = np.asarray(y_true, dtype=int)
    scores = np.asarray(probabilities, dtype=float)
    candidates = np.unique(np.concatenate([np.linspace(0.02, 0.90, 177), scores]))
    rows: list[ThresholdResult] = []
    for threshold in candidates:
        predicted = (scores >= threshold).astype(int)
        recall = recall_score(truth, predicted, zero_division=0)
        rows.append(
            ThresholdResult(
                threshold=float(threshold),
                expected_cost_per_observation=expected_classification_cost(
                    truth, predicted, false_negative_cost, false_positive_cost
                ),
                precision=float(precision_score(truth, predicted, zero_division=0)),
                recall=float(recall),
                f1=float(f1_score(truth, predicted, zero_division=0)),
                alert_rate=float(predicted.mean()),
            )
        )
    feasible = [
        row for row in rows if row.recall >= minimum_recall and row.alert_rate <= maximum_alert_rate
    ]
    pool = feasible or rows
    return min(pool, key=lambda row: (row.expected_cost_per_observation, -row.f1))


def expected_calibration_error(
    y_true: pd.Series | np.ndarray,
    probabilities: pd.Series | np.ndarray,
    bins: int = 10,
) -> float:
    """Calculate weighted absolute calibration error."""

    truth = np.asarray(y_true, dtype=int)
    scores = np.asarray(probabilities, dtype=float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    error = 0.0
    for lower, upper in pairwise(edges):
        inclusive = upper == 1.0
        mask = (scores >= lower) & (scores <= upper if inclusive else scores < upper)
        if mask.any():
            error += mask.mean() * abs(scores[mask].mean() - truth[mask].mean())
    return float(error)


def classification_metrics(
    y_true: pd.Series | np.ndarray,
    probabilities: pd.Series | np.ndarray,
    threshold: float,
    false_negative_cost: float,
    false_positive_cost: float,
) -> dict[str, float | int]:
    """Calculate discrimination, calibration, threshold and cost metrics."""

    truth = np.asarray(y_true, dtype=int)
    scores = np.asarray(probabilities, dtype=float)
    predicted = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(truth, predicted, labels=[0, 1]).ravel()
    return {
        "observations": len(truth),
        "positive_rate": float(truth.mean()),
        "pr_auc": float(average_precision_score(truth, scores)),
        "roc_auc": float(roc_auc_score(truth, scores)),
        "brier_score": float(brier_score_loss(truth, scores)),
        "log_loss": float(log_loss(truth, scores, labels=[0, 1])),
        "ece_10_bin": expected_calibration_error(truth, scores),
        "threshold": float(threshold),
        "precision": float(precision_score(truth, predicted, zero_division=0)),
        "recall": float(recall_score(truth, predicted, zero_division=0)),
        "f1": float(f1_score(truth, predicted, zero_division=0)),
        "specificity": float(tn / max(tn + fp, 1)),
        "alert_rate": float(predicted.mean()),
        "expected_cost_per_observation": expected_classification_cost(
            truth, predicted, false_negative_cost, false_positive_cost
        ),
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }


def bootstrap_interval(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    metric: str,
    seed: int,
    samples: int = 250,
) -> dict[str, float]:
    """Return deterministic percentile confidence intervals for OOT metrics."""

    rng = np.random.default_rng(seed)
    values: list[float] = []
    for _ in range(samples):
        index = rng.integers(0, len(y_true), len(y_true))
        truth = y_true[index]
        scores = probabilities[index]
        if truth.min() == truth.max():
            continue
        if metric == "pr_auc":
            values.append(float(average_precision_score(truth, scores)))
        elif metric == "roc_auc":
            values.append(float(roc_auc_score(truth, scores)))
        elif metric == "brier_score":
            values.append(float(brier_score_loss(truth, scores)))
        else:
            raise ValueError(f"Unsupported bootstrap metric: {metric}")
    if not values:
        raise ValueError("Bootstrap samples did not contain both classes")
    return {
        "lower_95": float(np.quantile(values, 0.025)),
        "median": float(np.quantile(values, 0.5)),
        "upper_95": float(np.quantile(values, 0.975)),
        "resamples": len(values),
    }


def calibration_table(
    y_true: pd.Series | np.ndarray,
    probabilities: pd.Series | np.ndarray,
    bins: int = 10,
) -> pd.DataFrame:
    """Return an auditable reliability-curve table."""

    observed, predicted = calibration_curve(
        np.asarray(y_true), np.asarray(probabilities), n_bins=bins, strategy="quantile"
    )
    return pd.DataFrame(
        {"mean_predicted_probability": predicted, "observed_failure_rate": observed}
    )


def train_champion_challenger(
    frame: pd.DataFrame,
    config: PipelineConfig,
    model_directory: str | Path,
) -> dict[str, Any]:
    """Train candidates, select on validation and evaluate once on OOT."""

    partitions = temporal_partitions(frame, config)
    train, calibration = development_train_calibration_split(
        partitions["development"], config.prediction_horizon_hours
    )
    validation = partitions["validation"]
    oot = partitions["oot"]
    candidates: dict[str, dict[str, Any]] = {}

    for offset, name in enumerate(["random_forest", "logistic_regression"]):
        base, calibrated = fit_calibrated_candidate(name, train, calibration, config.seed + offset)
        validation_probability = calibrated.predict_proba(validation[FEATURES])[:, 1]
        selection_metrics = classification_metrics(
            validation[TARGET],
            validation_probability,
            threshold=0.5,
            false_negative_cost=config.false_negative_cost,
            false_positive_cost=config.false_positive_cost,
        )
        selection_score = (
            0.70 * selection_metrics["pr_auc"]
            + 0.20 * selection_metrics["roc_auc"]
            - 0.10 * selection_metrics["brier_score"]
        )
        candidates[name] = {
            "base_pipeline": base,
            "calibrated_model": calibrated,
            "validation_probability": validation_probability,
            "selection_metrics": selection_metrics,
            "selection_score": float(selection_score),
        }

    champion_name = max(candidates, key=lambda item: candidates[item]["selection_score"])
    challenger_name = next(name for name in candidates if name != champion_name)
    champion = candidates[champion_name]
    threshold = select_threshold(
        validation[TARGET],
        champion["validation_probability"],
        config.false_negative_cost,
        config.false_positive_cost,
        config.minimum_recall,
        config.maximum_alert_rate,
    )
    oot_probability = champion["calibrated_model"].predict_proba(oot[FEATURES])[:, 1]
    validation_metrics = classification_metrics(
        validation[TARGET],
        champion["validation_probability"],
        threshold.threshold,
        config.false_negative_cost,
        config.false_positive_cost,
    )
    oot_metrics = classification_metrics(
        oot[TARGET],
        oot_probability,
        threshold.threshold,
        config.false_negative_cost,
        config.false_positive_cost,
    )
    intervals = {
        metric: bootstrap_interval(
            oot[TARGET].to_numpy(),
            oot_probability,
            metric,
            seed=config.seed + index + 50,
        )
        for index, metric in enumerate(["pr_auc", "roc_auc", "brier_score"])
    }
    model_path = Path(model_directory)
    model_path.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model_name": champion_name,
        "calibrated_model": champion["calibrated_model"],
        "base_pipeline": champion["base_pipeline"],
        "features": FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "threshold": threshold.threshold,
        "prediction_horizon_hours": config.prediction_horizon_hours,
        "maximum_alert_rate": config.maximum_alert_rate,
        "fitted_through": str(pd.to_datetime(calibration["timestamp"]).max()),
        "validation_start": config.validation_start,
        "oot_start": config.oot_start,
    }
    joblib.dump(bundle, model_path / "champion_bundle.joblib", compress=3)

    predictions = oot[
        [
            "shift_id",
            "timestamp",
            "line_id",
            "machine_id",
            "product_id",
            "criticality",
            "failure_cost",
            "maintenance_cost",
            TARGET,
            "next_failure_hours",
        ]
    ].copy()
    predictions["failure_probability"] = oot_probability
    predictions["alert"] = (oot_probability >= threshold.threshold).astype(int)
    predictions["model_name"] = champion_name

    candidate_summary = {
        name: {
            "selection_score": payload["selection_score"],
            "validation_at_0_5": payload["selection_metrics"],
        }
        for name, payload in candidates.items()
    }
    return {
        "champion_name": champion_name,
        "challenger_name": challenger_name,
        "threshold": threshold.to_dict(),
        "validation_metrics": validation_metrics,
        "oot_metrics": oot_metrics,
        "oot_confidence_intervals": intervals,
        "candidate_summary": candidate_summary,
        "predictions": predictions,
        "calibration": calibration_table(oot[TARGET], oot_probability),
        "bundle": bundle,
        "partitions": {
            "model_fit": {
                "rows": len(train),
                "start": str(pd.to_datetime(train["timestamp"]).min()),
                "end": str(pd.to_datetime(train["timestamp"]).max()),
                "positive_rate": float(train[TARGET].mean()),
            },
            "calibration": {
                "rows": len(calibration),
                "start": str(pd.to_datetime(calibration["timestamp"]).min()),
                "end": str(pd.to_datetime(calibration["timestamp"]).max()),
                "positive_rate": float(calibration[TARGET].mean()),
            },
            "validation": {
                "rows": len(validation),
                "start": str(pd.to_datetime(validation["timestamp"]).min()),
                "end": str(pd.to_datetime(validation["timestamp"]).max()),
                "positive_rate": float(validation[TARGET].mean()),
            },
            "oot": {
                "rows": len(oot),
                "start": str(pd.to_datetime(oot["timestamp"]).min()),
                "end": str(pd.to_datetime(oot["timestamp"]).max()),
                "positive_rate": float(oot[TARGET].mean()),
            },
        },
        "development_frame": partitions["development"],
        "oot_frame": oot,
    }
