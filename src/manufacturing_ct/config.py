"""Configuration and deterministic plant master-data definitions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


@dataclass(frozen=True)
class PipelineConfig:
    """Configuration for deterministic synthetic generation and validation."""

    seed: int = 20260729
    start_date: str = "2024-01-01"
    end_date: str = "2025-06-30"
    validation_start: str = "2024-12-01"
    oot_start: str = "2025-03-01"
    prediction_horizon_hours: int = 24
    subgroup_size: int = 5
    sample_machine_limit: int | None = None
    data_dir: str = "data/generated"
    artifact_dir: str = "artifacts"
    minimum_recall: float = 0.72
    maximum_alert_rate: float = 0.40
    false_negative_cost: float = 8000.0
    false_positive_cost: float = 450.0
    intervention_effectiveness: float = 0.65

    @classmethod
    def from_yaml(cls, path: str | Path) -> PipelineConfig:
        """Load validated fields from a YAML configuration file."""

        with Path(path).open(encoding="utf-8") as stream:
            payload = yaml.safe_load(stream) or {}
        unknown = set(payload) - set(cls.__dataclass_fields__)
        if unknown:
            raise ValueError(f"Unknown configuration fields: {sorted(unknown)}")
        return cls(**payload)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable configuration dictionary."""

        return asdict(self)

    def validate_dates(self) -> None:
        """Fail fast when temporal partitions are not strictly ordered."""

        start = pd.Timestamp(self.start_date)
        validation = pd.Timestamp(self.validation_start)
        oot = pd.Timestamp(self.oot_start)
        end = pd.Timestamp(self.end_date)
        if not start < validation < oot <= end:
            raise ValueError("Expected start_date < validation_start < oot_start <= end_date")
        if self.prediction_horizon_hours <= 0:
            raise ValueError("prediction_horizon_hours must be positive")
        if self.subgroup_size < 2:
            raise ValueError("subgroup_size must be at least 2")
        if not 0 < self.minimum_recall <= 1:
            raise ValueError("minimum_recall must be in (0, 1]")
        if not 0 < self.maximum_alert_rate <= 1:
            raise ValueError("maximum_alert_rate must be in (0, 1]")


def machine_master() -> pd.DataFrame:
    """Return deterministic multi-line machine master data."""

    machine_types = ["CNC", "Press", "Filler"]
    rows: list[dict[str, Any]] = []
    for line_index, line_id in enumerate(["LINE-A", "LINE-B", "LINE-C", "LINE-D"]):
        for machine_index in range(3):
            serial = line_index * 3 + machine_index + 1
            criticality = 3 + ((line_index + machine_index) % 3)
            rows.append(
                {
                    "line_id": line_id,
                    "machine_id": f"MC-{serial:02d}",
                    "machine_type": machine_types[machine_index],
                    "criticality": criticality,
                    "install_year": 2014 + ((serial * 3) % 9),
                    "failure_cost": float(9000 + criticality * 5500 + line_index * 1200),
                    "maintenance_cost": float(1600 + criticality * 420 + machine_index * 180),
                }
            )
    return pd.DataFrame(rows)


def product_master() -> pd.DataFrame:
    """Return product routing, cost and CTQ specification master data."""

    rows = [
        {
            "product_id": "PRD-A",
            "product_name": "Precision Shaft",
            "ideal_cycle_sec": 20.0,
            "ctq_nominal_mm": 25.00,
            "ctq_lsl_mm": 24.85,
            "ctq_usl_mm": 25.15,
            "roughness_usl_um": 2.20,
            "unit_cost": 18.0,
            "rework_cost": 6.0,
        },
        {
            "product_id": "PRD-B",
            "product_name": "Pump Housing",
            "ideal_cycle_sec": 32.0,
            "ctq_nominal_mm": 80.00,
            "ctq_lsl_mm": 79.72,
            "ctq_usl_mm": 80.28,
            "roughness_usl_um": 2.50,
            "unit_cost": 28.0,
            "rework_cost": 9.0,
        },
        {
            "product_id": "PRD-C",
            "product_name": "Valve Body",
            "ideal_cycle_sec": 26.0,
            "ctq_nominal_mm": 42.00,
            "ctq_lsl_mm": 41.80,
            "ctq_usl_mm": 42.20,
            "roughness_usl_um": 2.35,
            "unit_cost": 23.0,
            "rework_cost": 7.5,
        },
        {
            "product_id": "PRD-D",
            "product_name": "Gear Blank",
            "ideal_cycle_sec": 24.0,
            "ctq_nominal_mm": 60.00,
            "ctq_lsl_mm": 59.78,
            "ctq_usl_mm": 60.22,
            "roughness_usl_um": 2.10,
            "unit_cost": 25.0,
            "rework_cost": 8.0,
        },
    ]
    return pd.DataFrame(rows)
