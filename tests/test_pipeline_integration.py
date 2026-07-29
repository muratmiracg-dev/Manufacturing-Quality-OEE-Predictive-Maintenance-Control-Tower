from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from manufacturing_ct.api import ModelService
from manufacturing_ct.config import PipelineConfig
from manufacturing_ct.modeling import FEATURES
from manufacturing_ct.pipeline import run_pipeline


def test_small_end_to_end_pipeline(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = PipelineConfig(
        seed=2026,
        start_date="2024-01-01",
        end_date="2024-12-31",
        validation_start="2024-08-01",
        oot_start="2024-11-01",
        sample_machine_limit=3,
        data_dir=str(tmp_path / "data/generated"),
        artifact_dir=str(tmp_path / "artifacts"),
        minimum_recall=0.60,
        maximum_alert_rate=0.55,
    )
    metrics = run_pipeline(config)
    assert metrics["dataset"]["production_shift_rows"] > 3000
    assert metrics["dataset"]["quality_measurement_rows"] == (
        metrics["dataset"]["production_shift_rows"] * config.subgroup_size
    )
    assert 0 < metrics["executive_kpis"]["oee"] < 1
    assert metrics["model"]["champion_name"] in {
        "random_forest",
        "logistic_regression",
    }
    assert metrics["model"]["oot_metrics"]["pr_auc"] > 0
    assert metrics["monitoring"]["data_quality_checks_passed"] == 5
    assert metrics["decision_support"]["human_approval_required"] is True

    artifact_dir = tmp_path / "artifacts"
    assert (artifact_dir / "model/champion_bundle.joblib").exists()
    assert len(list((artifact_dir / "figures").glob("*.png"))) == 9
    assert (tmp_path / "docs/governance/model_card.md").exists()
    persisted = json.loads(
        (artifact_dir / "results/pipeline_metrics.json").read_text(encoding="utf-8")
    )
    assert persisted["executive_kpis"]["oee"] == metrics["executive_kpis"]["oee"]

    service = ModelService(artifact_dir / "model/champion_bundle.joblib")
    production = pd.read_csv(tmp_path / "data/generated/production_shifts.csv")
    snapshot = production.iloc[-1].to_dict()
    probability = service.predict_probability({feature: snapshot[feature] for feature in FEATURES})
    assert 0 <= probability <= 1
    assert len(service.reason_codes(snapshot)) == 3
