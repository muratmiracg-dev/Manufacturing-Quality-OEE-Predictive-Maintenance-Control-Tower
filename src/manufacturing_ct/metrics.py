"""Manufacturing KPI, loss, quality and reliability calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_oee_components(frame: pd.DataFrame) -> pd.DataFrame:
    """Add availability, performance, quality and OEE using explicit denominators."""

    output = frame.copy()
    output["availability"] = (
        output["run_time_min"] / output["planned_production_min"].replace(0, np.nan)
    ).clip(0, 1)
    output["performance"] = (
        output["ideal_cycle_sec"]
        * output["total_units"]
        / (output["run_time_min"].replace(0, np.nan) * 60.0)
    ).clip(0, 1)
    output["quality_rate"] = (
        output["first_pass_good_units"] / output["total_units"].replace(0, np.nan)
    ).clip(0, 1)
    output["oee"] = output["availability"] * output["performance"] * output["quality_rate"]
    output["fpy"] = output["quality_rate"]
    output["scrap_rate"] = output["scrap_units"] / output["total_units"].replace(0, np.nan)
    output["rework_rate"] = output["rework_units"] / output["total_units"].replace(0, np.nan)
    return output


def aggregate_oee(frame: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Aggregate OEE using ratio-of-sums rather than averaging row percentages."""

    source = add_oee_components(frame)
    grouped = (
        source.groupby(by, observed=True)
        .agg(
            planned_production_min=("planned_production_min", "sum"),
            run_time_min=("run_time_min", "sum"),
            ideal_runtime_sec=("ideal_cycle_sec", lambda series: 0.0),
            total_units=("total_units", "sum"),
            first_pass_good_units=("first_pass_good_units", "sum"),
            scrap_units=("scrap_units", "sum"),
            rework_units=("rework_units", "sum"),
            copq=("copq", "sum"),
            unplanned_downtime_min=("unplanned_downtime_min", "sum"),
        )
        .reset_index()
    )
    ideal_runtime = (
        source.assign(ideal_runtime_sec=source["ideal_cycle_sec"] * source["total_units"])
        .groupby(by, observed=True)["ideal_runtime_sec"]
        .sum()
        .reset_index(drop=True)
    )
    grouped["availability"] = (
        grouped["run_time_min"] / grouped["planned_production_min"].replace(0, np.nan)
    ).clip(0, 1)
    grouped["performance"] = (
        ideal_runtime / (grouped["run_time_min"].replace(0, np.nan) * 60.0)
    ).clip(0, 1)
    grouped["quality_rate"] = (
        grouped["first_pass_good_units"] / grouped["total_units"].replace(0, np.nan)
    ).clip(0, 1)
    grouped["oee"] = grouped["availability"] * grouped["performance"] * grouped["quality_rate"]
    grouped["fpy"] = grouped["quality_rate"]
    grouped["scrap_rate"] = grouped["scrap_units"] / grouped["total_units"].replace(0, np.nan)
    grouped["rework_rate"] = grouped["rework_units"] / grouped["total_units"].replace(0, np.nan)
    return grouped.drop(columns="ideal_runtime_sec")


def downtime_pareto(downtime: pd.DataFrame) -> pd.DataFrame:
    """Return unplanned downtime categories with cumulative Pareto share."""

    if downtime.empty:
        return pd.DataFrame(
            columns=["category", "duration_min", "event_count", "share", "cumulative_share"]
        )
    result = (
        downtime.loc[~downtime["planned"]]
        .groupby("category", observed=True)
        .agg(duration_min=("duration_min", "sum"), event_count=("event_id", "count"))
        .sort_values("duration_min", ascending=False)
        .reset_index()
    )
    total = result["duration_min"].sum()
    result["share"] = result["duration_min"] / total if total else 0.0
    result["cumulative_share"] = result["share"].cumsum()
    return result


def reliability_metrics(
    production: pd.DataFrame, downtime: pd.DataFrame, machines: pd.DataFrame
) -> pd.DataFrame:
    """Calculate MTBF and MTTR from observed operating time and failure repairs."""

    failures = downtime.loc[(~downtime["planned"]) & (downtime["category"] != "Minor Stop")]
    failure_summary = (
        failures.groupby("machine_id", observed=True)
        .agg(
            failure_count=("event_id", "count"),
            total_repair_hours=("duration_min", lambda values: values.sum() / 60.0),
        )
        .reset_index()
    )
    operating = (
        production.groupby("machine_id", observed=True)["run_time_min"]
        .sum()
        .div(60.0)
        .rename("operating_hours")
        .reset_index()
    )
    result = machines[["machine_id", "line_id", "criticality"]].merge(
        operating, on="machine_id", how="left"
    )
    result = result.merge(failure_summary, on="machine_id", how="left")
    result["failure_count"] = result["failure_count"].astype(float).fillna(0).astype(int)
    result["total_repair_hours"] = result["total_repair_hours"].astype(float).fillna(0.0)
    result["mtbf_hours"] = np.where(
        result["failure_count"] > 0,
        result["operating_hours"] / result["failure_count"],
        np.nan,
    )
    result["mttr_hours"] = np.where(
        result["failure_count"] > 0,
        result["total_repair_hours"] / result["failure_count"],
        0.0,
    )
    result["intrinsic_reliability"] = result["mtbf_hours"] / (
        result["mtbf_hours"] + result["mttr_hours"]
    )
    return result


def executive_kpis(
    production: pd.DataFrame, downtime: pd.DataFrame, machines: pd.DataFrame
) -> dict[str, float | int]:
    """Return reconciled portfolio-level KPI values."""

    enriched = add_oee_components(production)
    plant = aggregate_oee(enriched.assign(plant="Plant"), ["plant"]).iloc[0]
    reliability = reliability_metrics(enriched, downtime, machines)
    return {
        "availability": float(plant["availability"]),
        "performance": float(plant["performance"]),
        "quality_rate": float(plant["quality_rate"]),
        "oee": float(plant["oee"]),
        "fpy": float(plant["fpy"]),
        "scrap_rate": float(plant["scrap_rate"]),
        "rework_rate": float(plant["rework_rate"]),
        "copq": float(plant["copq"]),
        "unplanned_downtime_hours": float(plant["unplanned_downtime_min"] / 60.0),
        "failure_count": int(reliability["failure_count"].sum()),
        "mtbf_hours": float(
            reliability["operating_hours"].sum() / max(reliability["failure_count"].sum(), 1)
        ),
        "mttr_hours": float(
            reliability["total_repair_hours"].sum() / max(reliability["failure_count"].sum(), 1)
        ),
        "total_units": int(plant["total_units"]),
    }
