from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from manufacturing_ct.spc import (
    individuals_mr_chart,
    p_chart,
    process_capability,
    u_chart,
    western_electric_rules,
    xbar_r_chart,
)


def measurement_frame() -> pd.DataFrame:
    rng = np.random.default_rng(4)
    rows = []
    for subgroup in range(36):
        mean = 10.0 + (0.20 if subgroup >= 31 else 0.0)
        for sample in range(5):
            rows.append(
                {
                    "subgroup_id": f"G{subgroup:02d}",
                    "timestamp": pd.Timestamp("2024-01-01") + pd.Timedelta(hours=8 * subgroup),
                    "machine_id": "M1",
                    "product_id": "P1",
                    "ctq_dimension_mm": rng.normal(mean, 0.03),
                    "sample_number": sample + 1,
                }
            )
    return pd.DataFrame(rows)


def test_western_electric_rules_detect_patterns() -> None:
    z = pd.Series([0.1, 0.2, 3.2, 2.2, 2.4, 1.2, 1.3, 1.4, 1.5, 0.2] + [0.5] * 8)
    result = western_electric_rules(z)
    assert result.loc[2, "rule_1_beyond_3sigma"]
    assert result["rule_2_two_of_three_beyond_2sigma"].any()
    assert result["rule_3_four_of_five_beyond_1sigma"].any()
    assert result.iloc[-1]["rule_4_eight_same_side"]
    assert result["any_signal"].any()


def test_xbar_r_and_capability_keep_limits_separate() -> None:
    measurements = measurement_frame()
    baseline = measurements["timestamp"] < pd.Timestamp("2024-01-10")
    chart, metadata = xbar_r_chart(measurements, baseline, subgroup_size=5)
    assert len(chart) == 36
    assert metadata["control_limits_are_specification_limits"] is False
    assert metadata["xbar_limits"]["upper_control_limit"] > metadata["xbar_limits"]["center_line"]
    capability = process_capability(
        measurements["ctq_dimension_mm"], 9.8, 10.2, metadata["sigma_within"]
    )
    assert capability["cp"] > 0
    assert capability["pp"] > 0
    assert capability["lsl"] == 9.8
    assert capability["usl"] == 10.2


def test_i_mr_p_and_u_charts() -> None:
    values = pd.Series(np.linspace(1.0, 1.2, 40))
    baseline = pd.Series([True] * 30 + [False] * 10)
    individuals, i_metadata = individuals_mr_chart(values, baseline)
    assert len(individuals) == 40
    assert i_metadata["chart"] == "I-MR"
    defects = pd.Series([2 + index % 3 for index in range(40)])
    sample_size = pd.Series([90 + index % 7 for index in range(40)])
    p_result, p_metadata = p_chart(defects, sample_size, baseline)
    u_result, u_metadata = u_chart(defects * 2, sample_size, baseline)
    assert p_result["proportion"].between(0, 1).all()
    assert p_metadata["variable_sample_size"] is True
    assert (u_result["defects_per_unit"] >= 0).all()
    assert u_metadata["variable_units"] is True


@pytest.mark.parametrize("subgroup_size", [1, 7])
def test_xbar_rejects_unsupported_subgroup_size(subgroup_size: int) -> None:
    measurements = measurement_frame()
    baseline = pd.Series(True, index=measurements.index)
    with pytest.raises(ValueError):
        xbar_r_chart(measurements, baseline, subgroup_size=subgroup_size)


def test_spc_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        individuals_mr_chart(pd.Series([1.0, 2.0]), pd.Series([True, True]))
    with pytest.raises(ValueError):
        p_chart(pd.Series([1]), pd.Series([0]), pd.Series([True]))
    with pytest.raises(ValueError):
        u_chart(pd.Series([1]), pd.Series([0]), pd.Series([True]))
    with pytest.raises(ValueError):
        process_capability(pd.Series([1.0]), 0.0, 2.0, 0.1)


def test_attribute_charts_reject_invalid_count_inputs() -> None:
    baseline = pd.Series([True, True])
    with pytest.raises(ValueError, match="non-negative"):
        p_chart(pd.Series([-1, 1]), pd.Series([100, 100]), baseline)
    with pytest.raises(ValueError, match="cannot exceed"):
        p_chart(pd.Series([101, 1]), pd.Series([100, 100]), baseline)
    with pytest.raises(ValueError, match="non-negative"):
        u_chart(pd.Series([-1, 1]), pd.Series([100, 100]), baseline)
    with pytest.raises(ValueError, match="equal lengths"):
        p_chart(pd.Series([1]), pd.Series([100, 100]), baseline)
    with pytest.raises(ValueError, match="finite"):
        p_chart(pd.Series([np.nan, 1]), pd.Series([100, 100]), baseline)
    with pytest.raises(ValueError, match="finite"):
        p_chart(pd.Series([1, 1]), pd.Series([np.nan, 100]), baseline)
    with pytest.raises(ValueError, match="baseline labels"):
        u_chart(pd.Series([1, 1]), pd.Series([100, 100]), pd.Series([True, None]))
    with pytest.raises(ValueError, match="baseline observation"):
        u_chart(pd.Series([1, 1]), pd.Series([100, 100]), pd.Series([False, False]))
