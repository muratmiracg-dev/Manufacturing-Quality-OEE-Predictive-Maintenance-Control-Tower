from __future__ import annotations

import pytest

from manufacturing_ct.explain import reason_code_for_feature


@pytest.mark.parametrize(
    ("feature", "reason"),
    [
        ("numeric__vibration_rms", "HIGH_VIBRATION_PATTERN"),
        ("numeric__temperature_c", "THERMAL_STRESS"),
        ("categorical__machine_id_MC-01", "MACHINE_BASELINE_EFFECT"),
        ("numeric__unknown_signal", "MODEL_DRIVER_UNKNOWN_SIGNAL"),
    ],
)
def test_reason_code_mapping(feature: str, reason: str) -> None:
    assert reason_code_for_feature(feature) == reason
