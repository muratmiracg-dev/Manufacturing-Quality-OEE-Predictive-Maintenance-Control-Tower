"""SPC control charts, signal rules and process capability calculations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ControlLimits:
    """Statistical control limits. These are not specification limits."""

    center_line: float
    lower_control_limit: float
    upper_control_limit: float
    sigma: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def western_electric_rules(z_scores: pd.Series | np.ndarray) -> pd.DataFrame:
    """Evaluate four documented same-side Western Electric style rules."""

    z = np.asarray(z_scores, dtype=float)
    signals = pd.DataFrame(
        {
            "rule_1_beyond_3sigma": np.abs(z) > 3,
            "rule_2_two_of_three_beyond_2sigma": False,
            "rule_3_four_of_five_beyond_1sigma": False,
            "rule_4_eight_same_side": False,
        }
    )
    for index in range(len(z)):
        if index >= 2:
            window = z[index - 2 : index + 1]
            signals.loc[index, "rule_2_two_of_three_beyond_2sigma"] = bool(
                (window > 2).sum() >= 2 or (window < -2).sum() >= 2
            )
        if index >= 4:
            window = z[index - 4 : index + 1]
            signals.loc[index, "rule_3_four_of_five_beyond_1sigma"] = bool(
                (window > 1).sum() >= 4 or (window < -1).sum() >= 4
            )
        if index >= 7:
            window = z[index - 7 : index + 1]
            signals.loc[index, "rule_4_eight_same_side"] = bool(
                np.all(window > 0) or np.all(window < 0)
            )
    signals["any_signal"] = signals.any(axis=1)
    return signals


def xbar_r_chart(
    measurements: pd.DataFrame,
    baseline_mask: pd.Series,
    subgroup_size: int = 5,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Create an X-bar/R chart for fixed-size rational subgroups."""

    constants = {
        2: (1.880, 0.000, 3.267, 1.128),
        3: (1.023, 0.000, 2.574, 1.693),
        4: (0.729, 0.000, 2.282, 2.059),
        5: (0.577, 0.000, 2.114, 2.326),
        6: (0.483, 0.000, 2.004, 2.534),
    }
    if subgroup_size not in constants:
        raise ValueError("Supported subgroup sizes are 2 through 6")
    group_columns = ["subgroup_id", "timestamp", "machine_id", "product_id"]
    subgroup = (
        measurements.groupby(group_columns, observed=True)["ctq_dimension_mm"]
        .agg(xbar="mean", range=lambda values: values.max() - values.min(), n="count")
        .reset_index()
        .sort_values("timestamp", ignore_index=True)
    )
    if not (subgroup["n"] == subgroup_size).all():
        raise ValueError("X-bar/R requires fixed-size complete rational subgroups")
    baseline_subgroup_ids = set(measurements.loc[baseline_mask, "subgroup_id"])
    baseline = subgroup["subgroup_id"].isin(baseline_subgroup_ids)
    if baseline.sum() < 20:
        raise ValueError("At least 20 baseline subgroups are required")
    a2, d3, d4, d2 = constants[subgroup_size]
    xbarbar = float(subgroup.loc[baseline, "xbar"].mean())
    rbar = float(subgroup.loc[baseline, "range"].mean())
    sigma_within = rbar / d2
    xbar_limits = ControlLimits(
        center_line=xbarbar,
        lower_control_limit=xbarbar - a2 * rbar,
        upper_control_limit=xbarbar + a2 * rbar,
        sigma=max(a2 * rbar / 3.0, 1e-12),
    )
    range_limits = ControlLimits(
        center_line=rbar,
        lower_control_limit=d3 * rbar,
        upper_control_limit=d4 * rbar,
        sigma=max((d4 - 1.0) * rbar / 3.0, 1e-12),
    )
    subgroup["xbar_lcl"] = xbar_limits.lower_control_limit
    subgroup["xbar_cl"] = xbar_limits.center_line
    subgroup["xbar_ucl"] = xbar_limits.upper_control_limit
    subgroup["range_lcl"] = range_limits.lower_control_limit
    subgroup["range_cl"] = range_limits.center_line
    subgroup["range_ucl"] = range_limits.upper_control_limit
    z = (subgroup["xbar"] - xbar_limits.center_line) / xbar_limits.sigma
    subgroup = pd.concat([subgroup, western_electric_rules(z)], axis=1)
    subgroup["range_rule_1"] = (subgroup["range"] < range_limits.lower_control_limit) | (
        subgroup["range"] > range_limits.upper_control_limit
    )
    metadata = {
        "chart": "X-bar/R",
        "baseline_subgroups": int(baseline.sum()),
        "subgroup_size": subgroup_size,
        "xbar_limits": xbar_limits.to_dict(),
        "range_limits": range_limits.to_dict(),
        "sigma_within": sigma_within,
        "control_limits_are_specification_limits": False,
    }
    return subgroup, metadata


def individuals_mr_chart(
    values: pd.Series, baseline_mask: pd.Series
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Create an I-MR chart for one observation per time period."""

    series = pd.Series(values, dtype=float).reset_index(drop=True)
    baseline = pd.Series(baseline_mask).reset_index(drop=True).astype(bool)
    if baseline.sum() < 20:
        raise ValueError("At least 20 baseline observations are required")
    moving_range = series.diff().abs()
    center = float(series.loc[baseline].mean())
    baseline_mr = moving_range.loc[baseline & moving_range.notna()]
    mrbar = float(baseline_mr.mean())
    sigma = max(mrbar / 1.128, 1e-12)
    individual_limits = ControlLimits(center, center - 3 * sigma, center + 3 * sigma, sigma)
    mr_limits = ControlLimits(mrbar, 0.0, 3.267 * mrbar, max(0.756 * mrbar, 1e-12))
    result = pd.DataFrame(
        {
            "value": series,
            "moving_range": moving_range,
            "i_lcl": individual_limits.lower_control_limit,
            "i_cl": individual_limits.center_line,
            "i_ucl": individual_limits.upper_control_limit,
            "mr_lcl": mr_limits.lower_control_limit,
            "mr_cl": mr_limits.center_line,
            "mr_ucl": mr_limits.upper_control_limit,
        }
    )
    z = (series - center) / sigma
    result = pd.concat([result, western_electric_rules(z)], axis=1)
    result["mr_rule_1"] = moving_range > mr_limits.upper_control_limit
    metadata = {
        "chart": "I-MR",
        "baseline_observations": int(baseline.sum()),
        "individual_limits": individual_limits.to_dict(),
        "moving_range_limits": mr_limits.to_dict(),
        "control_limits_are_specification_limits": False,
    }
    return result, metadata


def p_chart(
    defectives: pd.Series, sample_size: pd.Series, baseline_mask: pd.Series
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Create a p chart with limits that vary by inspected lot size."""

    defects = pd.Series(defectives, dtype=float).reset_index(drop=True)
    n = pd.Series(sample_size, dtype=float).reset_index(drop=True)
    baseline = pd.Series(baseline_mask).reset_index(drop=True).astype(bool)
    if (n <= 0).any():
        raise ValueError("p chart sample sizes must be positive")
    pbar = float(defects.loc[baseline].sum() / n.loc[baseline].sum())
    standard_error = np.sqrt(pbar * (1 - pbar) / n)
    lcl = np.maximum(0.0, pbar - 3 * standard_error)
    ucl = np.minimum(1.0, pbar + 3 * standard_error)
    proportion = defects / n
    z = (proportion - pbar) / standard_error.replace(0, np.nan)
    result = pd.DataFrame(
        {
            "defectives": defects,
            "sample_size": n,
            "proportion": proportion,
            "lcl": lcl,
            "center_line": pbar,
            "ucl": ucl,
        }
    )
    result = pd.concat([result, western_electric_rules(z.fillna(0))], axis=1)
    return result, {
        "chart": "p",
        "baseline_observations": int(baseline.sum()),
        "center_line": pbar,
        "variable_sample_size": bool(n.nunique() > 1),
        "control_limits_are_specification_limits": False,
    }


def u_chart(
    defects: pd.Series, units: pd.Series, baseline_mask: pd.Series
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Create a u chart for defect counts with variable units of opportunity."""

    counts = pd.Series(defects, dtype=float).reset_index(drop=True)
    n = pd.Series(units, dtype=float).reset_index(drop=True)
    baseline = pd.Series(baseline_mask).reset_index(drop=True).astype(bool)
    if (n <= 0).any():
        raise ValueError("u chart unit counts must be positive")
    ubar = float(counts.loc[baseline].sum() / n.loc[baseline].sum())
    standard_error = np.sqrt(ubar / n)
    lcl = np.maximum(0.0, ubar - 3 * standard_error)
    ucl = ubar + 3 * standard_error
    rate = counts / n
    z = (rate - ubar) / standard_error.replace(0, np.nan)
    result = pd.DataFrame(
        {
            "defects": counts,
            "units": n,
            "defects_per_unit": rate,
            "lcl": lcl,
            "center_line": ubar,
            "ucl": ucl,
        }
    )
    result = pd.concat([result, western_electric_rules(z.fillna(0))], axis=1)
    return result, {
        "chart": "u",
        "baseline_observations": int(baseline.sum()),
        "center_line": ubar,
        "variable_units": bool(n.nunique() > 1),
        "control_limits_are_specification_limits": False,
    }


def process_capability(
    measurements: pd.Series,
    lsl: float,
    usl: float,
    sigma_within: float,
) -> dict[str, float]:
    """Calculate Cp/Cpk (within) and Pp/Ppk (overall) against specifications."""

    values = pd.Series(measurements, dtype=float).dropna()
    if len(values) < 2 or sigma_within <= 0 or usl <= lsl:
        raise ValueError("Capability requires valid specifications and variation estimates")
    mean = float(values.mean())
    sigma_overall = float(values.std(ddof=1))
    cp = (usl - lsl) / (6 * sigma_within)
    cpk = min((usl - mean) / (3 * sigma_within), (mean - lsl) / (3 * sigma_within))
    pp = (usl - lsl) / (6 * sigma_overall)
    ppk = min((usl - mean) / (3 * sigma_overall), (mean - lsl) / (3 * sigma_overall))
    return {
        "mean": mean,
        "lsl": float(lsl),
        "usl": float(usl),
        "sigma_within": float(sigma_within),
        "sigma_overall": sigma_overall,
        "cp": float(cp),
        "cpk": float(cpk),
        "pp": float(pp),
        "ppk": float(ppk),
    }
