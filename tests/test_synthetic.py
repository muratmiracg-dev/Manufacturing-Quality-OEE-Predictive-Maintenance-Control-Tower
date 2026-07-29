from __future__ import annotations

from pathlib import Path

import pandas as pd

from manufacturing_ct.config import PipelineConfig
from manufacturing_ct.synthetic import generate_plant_data


def small_config() -> PipelineConfig:
    return PipelineConfig(
        seed=123,
        start_date="2024-01-01",
        end_date="2024-03-31",
        validation_start="2024-02-01",
        oot_start="2024-03-01",
        sample_machine_limit=2,
    )


def test_generation_is_deterministic_and_contract_valid() -> None:
    first = generate_plant_data(small_config())
    second = generate_plant_data(small_config())
    pd.testing.assert_frame_equal(first.production, second.production)
    pd.testing.assert_frame_equal(first.quality_measurements, second.quality_measurements)
    assert first.production["machine_id"].nunique() == 2
    assert first.production["shift"].nunique() == 3
    assert first.quality_measurements.groupby("subgroup_id").size().eq(5).all()
    assert first.production["shift_id"].is_unique
    assert first.production["failure_within_24h"].isin([0, 1]).all()
    assert first.production["failure_within_24h"].mean() > 0
    assert (first.production["first_pass_good_units"] <= first.production["total_units"]).all()
    assert (
        first.production["unplanned_downtime_min"] <= first.production["planned_production_min"]
    ).all()
    assert first.production["downtime_last_7d_min"].notna().all()


def test_future_target_excludes_current_failure() -> None:
    data = generate_plant_data(small_config()).production
    machine = data.loc[data["machine_id"] == data["machine_id"].iloc[0]].reset_index(drop=True)
    failure_positions = machine.index[machine["failure_event"] == 1]
    assert len(failure_positions) > 0
    position = int(failure_positions[0])
    if position > 0:
        assert machine.loc[position - 1, "failure_within_24h"] == 1


def test_write_csv_round_trip(tmp_path: Path) -> None:
    data = generate_plant_data(small_config())
    data.write_csv(tmp_path)
    expected = {
        "production_shifts.csv",
        "quality_measurements.csv",
        "downtime_events.csv",
        "maintenance_events.csv",
        "machines.csv",
        "products.csv",
    }
    assert expected == {path.name for path in tmp_path.iterdir()}
    reloaded = pd.read_csv(tmp_path / "production_shifts.csv")
    assert len(reloaded) == len(data.production)
