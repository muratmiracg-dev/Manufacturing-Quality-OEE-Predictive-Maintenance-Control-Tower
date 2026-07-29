from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from manufacturing_ct.modeling import CATEGORICAL_FEATURES, NUMERIC_FEATURES, TARGET


@pytest.fixture
def modeling_frame() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rows = 360
    timestamps = pd.date_range("2024-01-01", periods=rows, freq="8h")
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "shift_id": [f"S-{index:04d}" for index in range(rows)],
            "line_id": np.where(np.arange(rows) % 2, "LINE-A", "LINE-B"),
            "machine_id": [f"MC-{index % 6:02d}" for index in range(rows)],
            "machine_type": np.where(np.arange(rows) % 2, "CNC", "Press"),
            "product_id": [f"PRD-{chr(65 + index % 3)}" for index in range(rows)],
            "shift": [chr(65 + index % 3) for index in range(rows)],
        }
    )
    for index, feature in enumerate(NUMERIC_FEATURES):
        frame[feature] = rng.normal(1 + index * 0.1, 0.35, rows)
    frame["criticality"] = rng.integers(1, 6, rows)
    frame["changeover_count"] = rng.integers(0, 3, rows)
    frame["failures_last_30d"] = rng.integers(0, 5, rows)
    risk = (
        1.2 * frame["vibration_rms"]
        + 0.9 * frame["temperature_c"]
        - 0.8 * frame["lubrication_index"]
        + rng.normal(0, 0.8, rows)
    )
    frame[TARGET] = (risk > np.quantile(risk, 0.75)).astype(int)
    frame["next_failure_hours"] = np.where(frame[TARGET] == 1, 16.0, np.nan)
    frame["failure_cost"] = 20000.0
    frame["maintenance_cost"] = 2500.0
    assert set(CATEGORICAL_FEATURES + NUMERIC_FEATURES).issubset(frame.columns)
    return frame
