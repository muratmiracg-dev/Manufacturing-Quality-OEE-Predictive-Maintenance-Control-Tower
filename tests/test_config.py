from __future__ import annotations

from pathlib import Path

import pytest

from manufacturing_ct.config import PipelineConfig, machine_master, product_master


def test_configuration_validation_and_master_data(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        "seed: 7\nstart_date: '2024-01-01'\nend_date: '2024-12-31'\n"
        "validation_start: '2024-08-01'\noot_start: '2024-11-01'\n",
        encoding="utf-8",
    )
    config = PipelineConfig.from_yaml(path)
    config.validate_dates()
    assert config.seed == 7
    assert config.to_dict()["maximum_alert_rate"] == pytest.approx(0.40)
    machines = machine_master()
    products = product_master()
    assert machines["machine_id"].nunique() == 12
    assert machines["line_id"].nunique() == 4
    assert products["product_id"].nunique() == 4
    assert (products["ctq_lsl_mm"] < products["ctq_usl_mm"]).all()


@pytest.mark.parametrize(
    "overrides",
    [
        {"validation_start": "2023-01-01"},
        {"prediction_horizon_hours": 0},
        {"subgroup_size": 1},
        {"minimum_recall": 0},
        {"maximum_alert_rate": 1.1},
    ],
)
def test_configuration_rejects_invalid_values(overrides: dict[str, object]) -> None:
    config = PipelineConfig(**overrides)
    with pytest.raises(ValueError):
        config.validate_dates()


def test_configuration_rejects_unknown_fields(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("unknown: true\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown"):
        PipelineConfig.from_yaml(path)
