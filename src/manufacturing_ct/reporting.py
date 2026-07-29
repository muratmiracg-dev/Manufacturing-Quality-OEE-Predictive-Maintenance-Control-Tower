"""Static reporting figures and metric-backed governance documentation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter

COLORS = {
    "charcoal": "#101820",
    "steel": "#334155",
    "orange": "#FF6B00",
    "cyan": "#00A6A6",
    "green": "#2DBE8C",
    "red": "#E63946",
    "cream": "#F5F2EA",
    "gray": "#94A3B8",
}


def _style_axis(axis: plt.Axes, title: str) -> None:
    axis.set_title(title, loc="left", color=COLORS["charcoal"], fontsize=14, fontweight="bold")
    axis.spines[["top", "right"]].set_visible(False)
    axis.spines[["left", "bottom"]].set_color("#CBD5E1")
    axis.grid(axis="y", color="#E2E8F0", linewidth=0.7, alpha=0.8)
    axis.tick_params(colors=COLORS["steel"], labelsize=9)


def _save(figure: plt.Figure, destination: Path) -> None:
    figure.tight_layout()
    figure.savefig(destination, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def create_figures(
    monthly_oee: pd.DataFrame,
    pareto: pd.DataFrame,
    capability: pd.DataFrame,
    spc_xbar: pd.DataFrame,
    calibration: pd.DataFrame,
    oot_metrics: dict[str, Any],
    shap_global: pd.DataFrame,
    maintenance_priority: pd.DataFrame,
    drift: pd.DataFrame,
    output_directory: str | Path,
) -> list[str]:
    """Create a consistent set of figures exclusively from pipeline outputs."""

    destination = Path(output_directory)
    destination.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []

    figure, axis = plt.subplots(figsize=(10, 4.8))
    for index, (line_id, group) in enumerate(monthly_oee.groupby("line_id")):
        axis.plot(
            pd.to_datetime(group["month"]),
            group["oee"],
            marker="o",
            markersize=3,
            linewidth=1.8,
            label=line_id,
            color=[COLORS["orange"], COLORS["cyan"], COLORS["green"], COLORS["steel"]][index % 4],
        )
    _style_axis(axis, "Monthly OEE by production line")
    axis.yaxis.set_major_formatter(PercentFormatter(1.0))
    axis.set_ylim(0.35, 1.0)
    axis.legend(frameon=False, ncol=4, loc="lower left")
    name = "oee_monthly_trend.png"
    _save(figure, destination / name)
    generated.append(name)

    figure, axis = plt.subplots(figsize=(9, 4.8))
    x = np.arange(len(pareto))
    axis.bar(x, pareto["duration_min"] / 60.0, color=COLORS["orange"], alpha=0.88)
    axis.set_xticks(x, pareto["category"], rotation=25, ha="right")
    axis.set_ylabel("Downtime hours")
    _style_axis(axis, "Unplanned downtime Pareto")
    secondary = axis.twinx()
    secondary.plot(
        x,
        pareto["cumulative_share"],
        color=COLORS["charcoal"],
        marker="o",
        linewidth=2,
    )
    secondary.yaxis.set_major_formatter(PercentFormatter(1.0))
    secondary.set_ylim(0, 1.08)
    secondary.spines[["top"]].set_visible(False)
    name = "downtime_pareto.png"
    _save(figure, destination / name)
    generated.append(name)

    figure, axis = plt.subplots(figsize=(9, 4.8))
    sorted_capability = capability.sort_values("cpk")
    positions = np.arange(len(sorted_capability))
    axis.barh(
        positions - 0.18,
        sorted_capability["cpk"],
        height=0.35,
        label="Cpk (within)",
        color=COLORS["cyan"],
    )
    axis.barh(
        positions + 0.18,
        sorted_capability["ppk"],
        height=0.35,
        label="Ppk (overall)",
        color=COLORS["orange"],
    )
    axis.set_yticks(positions, sorted_capability["product_id"])
    axis.axvline(1.0, color=COLORS["red"], linestyle="--", linewidth=1.2)
    axis.set_xlabel("Capability index")
    axis.legend(frameon=False)
    _style_axis(axis, "Process capability by product")
    name = "process_capability.png"
    _save(figure, destination / name)
    generated.append(name)

    tail = spc_xbar.tail(min(220, len(spc_xbar))).reset_index(drop=True)
    figure, axis = plt.subplots(figsize=(10, 4.8))
    axis.plot(tail.index, tail["xbar"], color=COLORS["steel"], linewidth=1.1)
    axis.plot(tail.index, tail["xbar_cl"], color=COLORS["cyan"], linewidth=1.2)
    axis.plot(tail.index, tail["xbar_ucl"], color=COLORS["red"], linestyle="--")
    axis.plot(tail.index, tail["xbar_lcl"], color=COLORS["red"], linestyle="--")
    signals = tail["any_signal"]
    axis.scatter(
        tail.index[signals],
        tail.loc[signals, "xbar"],
        color=COLORS["orange"],
        s=22,
        label="Rule signal",
        zorder=5,
    )
    axis.set_xlabel("Most recent rational subgroups")
    axis.set_ylabel("Subgroup mean (mm)")
    axis.legend(frameon=False)
    _style_axis(axis, "X-bar chart - control limits from development baseline")
    name = "spc_xbar.png"
    _save(figure, destination / name)
    generated.append(name)

    figure, axis = plt.subplots(figsize=(6.5, 5.5))
    axis.plot([0, 1], [0, 1], linestyle="--", color=COLORS["gray"], label="Perfect calibration")
    axis.plot(
        calibration["mean_predicted_probability"],
        calibration["observed_failure_rate"],
        marker="o",
        color=COLORS["orange"],
        linewidth=2,
        label="OOT reliability",
    )
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.set_xlabel("Mean predicted probability")
    axis.set_ylabel("Observed failure rate")
    axis.legend(frameon=False)
    _style_axis(axis, "Champion probability calibration")
    name = "model_calibration.png"
    _save(figure, destination / name)
    generated.append(name)

    matrix = np.array(
        [
            [oot_metrics["true_negative"], oot_metrics["false_positive"]],
            [oot_metrics["false_negative"], oot_metrics["true_positive"]],
        ]
    )
    figure, axis = plt.subplots(figsize=(6.5, 5.2))
    image = axis.imshow(matrix, cmap="YlOrBr")
    for row in range(2):
        for column in range(2):
            axis.text(
                column,
                row,
                f"{matrix[row, column]:,}",
                ha="center",
                va="center",
                fontsize=15,
                fontweight="bold",
                color=COLORS["charcoal"],
            )
    axis.set_xticks([0, 1], ["No alert", "Alert"])
    axis.set_yticks([0, 1], ["No failure", "Failure"])
    axis.set_xlabel("Policy decision")
    axis.set_ylabel("Observed within 24h")
    axis.grid(False)
    axis.set_title("OOT alarm confusion matrix", loc="left", fontweight="bold", fontsize=14)
    figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    name = "oot_confusion_matrix.png"
    _save(figure, destination / name)
    generated.append(name)

    top_shap = shap_global.head(10).sort_values("mean_absolute_shap")
    figure, axis = plt.subplots(figsize=(9, 5.2))
    axis.barh(
        top_shap["reason_code"],
        top_shap["mean_absolute_shap"],
        color=COLORS["cyan"],
    )
    axis.set_xlabel("Mean absolute SHAP value")
    _style_axis(axis, "Global failure-risk drivers")
    name = "shap_global_importance.png"
    _save(figure, destination / name)
    generated.append(name)

    priority = maintenance_priority.sort_values("expected_net_benefit").tail(12)
    colors = priority["priority"].map(
        {
            "P1": COLORS["red"],
            "P2": COLORS["orange"],
            "P3": COLORS["cyan"],
            "MONITOR": COLORS["gray"],
        }
    )
    figure, axis = plt.subplots(figsize=(9, 5.2))
    axis.barh(priority["machine_id"], priority["expected_net_benefit"], color=colors)
    axis.axvline(0, color=COLORS["charcoal"], linewidth=0.8)
    axis.set_xlabel("Expected net benefit (synthetic cost units)")
    _style_axis(axis, "Latest maintenance decision-support ranking")
    name = "maintenance_priority.png"
    _save(figure, destination / name)
    generated.append(name)

    top_drift = drift.head(12).sort_values("psi")
    drift_colors = top_drift["severity"].map(
        {"stable": COLORS["green"], "watch": COLORS["orange"], "action": COLORS["red"]}
    )
    figure, axis = plt.subplots(figsize=(9, 5.2))
    axis.barh(top_drift["feature"], top_drift["psi"], color=drift_colors)
    axis.axvline(0.10, color=COLORS["orange"], linestyle="--", linewidth=1)
    axis.axvline(0.20, color=COLORS["red"], linestyle="--", linewidth=1)
    axis.set_xlabel("Population Stability Index")
    _style_axis(axis, "Feature drift - development vs OOT")
    name = "feature_drift.png"
    _save(figure, destination / name)
    generated.append(name)
    return generated


def write_metric_backed_docs(
    metrics: dict[str, Any],
    capability: pd.DataFrame,
    drift: pd.DataFrame,
    output_directory: str | Path,
) -> None:
    """Write model-card and validation sections from verified metric JSON."""

    destination = Path(output_directory)
    destination.mkdir(parents=True, exist_ok=True)
    model = metrics["model"]
    oot = model["oot_metrics"]
    threshold = model["threshold"]
    model_card = f"""# Model Card

## Intended use

The model estimates the probability of a synthetic machine failure in the next
{metrics["prediction_horizon_hours"]} hours. Its output is decision support for a
maintenance planner. It does not create work orders, stop equipment, or approve
maintenance.

## Data and split

- Data: deterministic, fully synthetic plant telemetry and events.
- Champion: `{model["champion_name"]}`.
- Challenger: `{model["challenger_name"]}`.
- Development fit rows: {model["partitions"]["model_fit"]["rows"]:,}.
- Calibration rows: {model["partitions"]["calibration"]["rows"]:,}.
- Validation rows: {model["partitions"]["validation"]["rows"]:,}.
- Out-of-time rows: {model["partitions"]["oot"]["rows"]:,}.
- A 24-hour purge gap is enforced at temporal boundaries.

## Out-of-time performance

| Metric | Result |
|---|---:|
| PR-AUC | {oot["pr_auc"]:.4f} |
| ROC-AUC | {oot["roc_auc"]:.4f} |
| Brier score | {oot["brier_score"]:.4f} |
| ECE (10 bins) | {oot["ece_10_bin"]:.4f} |
| Precision | {oot["precision"]:.4f} |
| Recall | {oot["recall"]:.4f} |
| F1 | {oot["f1"]:.4f} |
| Selected threshold | {threshold["threshold"]:.4f} |

## Explainability

Global and local SHAP outputs explain the uncalibrated base estimator. The
sigmoid calibration layer changes reported probabilities and is deliberately
reported as outside the SHAP attribution scope.

## Limitations

Synthetic performance does not establish real-world effectiveness. Plant
transfer requires new validation, calibration, process-engineering review,
data-contract checks, and a monitored shadow deployment.
"""
    (destination / "model_card.md").write_text(model_card, encoding="utf-8")

    capability_rows = "\n".join(
        f"| {row.product_id} | {row.cp:.3f} | {row.cpk:.3f} | {row.pp:.3f} | {row.ppk:.3f} |"
        for row in capability.itertuples()
    )
    drift_rows = "\n".join(
        f"| {row.feature} | {row.feature_type} | {row.psi:.4f} | {row.severity} |"
        for row in drift.head(12).itertuples()
    )
    validation = f"""# Validation Report

## Independent temporal assessment

Model selection used validation data only. Threshold selection used the
validation period with an explicit false-negative cost of
{metrics["model"]["cost_assumptions"]["false_negative_cost"]:,.0f} and
false-positive cost of
{metrics["model"]["cost_assumptions"]["false_positive_cost"]:,.0f}. The OOT
period was evaluated once after candidate and threshold decisions.

## Champion/challenger outcome

The selected champion is `{model["champion_name"]}` and the retained challenger
is `{model["challenger_name"]}`. OOT PR-AUC is {oot["pr_auc"]:.4f}, ROC-AUC is
{oot["roc_auc"]:.4f}, Brier score is {oot["brier_score"]:.4f}, precision is
{oot["precision"]:.4f}, and recall is {oot["recall"]:.4f}.

## Process capability snapshot

Control limits are computed from baseline process behavior. The specification
limits below are independent engineering requirements.

| Product | Cp | Cpk | Pp | Ppk |
|---|---:|---:|---:|---:|
{capability_rows}

## Drift snapshot

| Feature | Type | PSI | Severity |
|---|---|---:|---|
{drift_rows}

## Decision

This synthetic demonstration is fit for portfolio and technical evaluation.
It is not approved for production deployment or autonomous maintenance action.
"""
    (destination / "validation_report.md").write_text(validation, encoding="utf-8")

    (destination / "metrics_snapshot.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
