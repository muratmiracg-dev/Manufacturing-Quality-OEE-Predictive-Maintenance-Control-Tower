from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from manufacturing_ct.config import PipelineConfig
from manufacturing_ct.modeling import (
    FEATURES,
    TARGET,
    bootstrap_interval,
    build_candidate,
    calibration_table,
    classification_metrics,
    development_train_calibration_split,
    expected_calibration_error,
    expected_classification_cost,
    fit_calibrated_candidate,
    select_threshold,
    temporal_partitions,
)


def test_temporal_partitions_are_purged(modeling_frame: pd.DataFrame) -> None:
    config = PipelineConfig(
        start_date="2024-01-01",
        end_date="2024-04-30",
        validation_start="2024-02-15",
        oot_start="2024-03-20",
    )
    partitions = temporal_partitions(modeling_frame, config)
    assert partitions["development"]["timestamp"].max() < pd.Timestamp("2024-02-14")
    assert partitions["validation"]["timestamp"].max() < pd.Timestamp("2024-03-19")
    assert partitions["oot"]["timestamp"].min() >= pd.Timestamp("2024-03-20")
    train, calibration = development_train_calibration_split(modeling_frame, horizon_hours=24)
    assert train["timestamp"].max() < calibration["timestamp"].min()


def test_candidates_and_calibration(modeling_frame: pd.DataFrame) -> None:
    train = modeling_frame.iloc[:220].copy()
    calibration = modeling_frame.iloc[220:300].copy()
    base, calibrated = fit_calibrated_candidate("logistic_regression", train, calibration, seed=9)
    probabilities = calibrated.predict_proba(modeling_frame.iloc[300:][FEATURES])[:, 1]
    assert base.named_steps["estimator"].classes_.tolist() == [0, 1]
    assert np.all((probabilities >= 0) & (probabilities <= 1))
    assert build_candidate("random_forest", 1).steps[-1][0] == "estimator"
    with pytest.raises(ValueError):
        build_candidate("unknown", 1)


def test_threshold_metrics_and_bootstrap() -> None:
    truth = np.array([0, 0, 0, 1, 1, 1, 1, 0, 1, 0])
    probability = np.array([0.02, 0.1, 0.4, 0.6, 0.7, 0.9, 0.55, 0.2, 0.8, 0.3])
    threshold = select_threshold(
        truth,
        probability,
        false_negative_cost=10,
        false_positive_cost=2,
        minimum_recall=0.6,
        maximum_alert_rate=0.6,
    )
    assert threshold.recall >= 0.6
    assert threshold.alert_rate <= 0.6
    metrics = classification_metrics(truth, probability, threshold.threshold, 10, 2)
    assert metrics["roc_auc"] > 0.8
    assert metrics["pr_auc"] > truth.mean()
    assert metrics["observations"] == len(truth)
    assert expected_classification_cost(truth, probability >= 0.5, 10, 2) >= 0
    assert 0 <= expected_calibration_error(truth, probability) <= 1
    table = calibration_table(truth, probability, bins=4)
    assert set(table) == {"mean_predicted_probability", "observed_failure_rate"}
    interval = bootstrap_interval(truth, probability, "pr_auc", seed=3, samples=30)
    assert interval["lower_95"] <= interval["median"] <= interval["upper_95"]
    with pytest.raises(ValueError):
        bootstrap_interval(truth, probability, "unsupported", seed=3, samples=2)


def test_modeling_rejects_bad_partitions(modeling_frame: pd.DataFrame) -> None:
    config = PipelineConfig(
        start_date="2024-01-01",
        end_date="2024-01-05",
        validation_start="2024-01-02",
        oot_start="2024-01-04",
    )
    with pytest.raises(ValueError):
        temporal_partitions(modeling_frame.iloc[:5], config)
    one_class = modeling_frame.iloc[:100].copy()
    one_class[TARGET] = 0
    with pytest.raises(ValueError):
        fit_calibrated_candidate(
            "logistic_regression", one_class.iloc[:60], one_class.iloc[60:], seed=1
        )
