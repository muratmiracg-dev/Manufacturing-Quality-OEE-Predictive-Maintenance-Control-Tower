"""End-to-end deterministic analytics, modeling and reporting pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from manufacturing_ct.config import PipelineConfig
from manufacturing_ct.explain import create_shap_outputs
from manufacturing_ct.metrics import (
    add_oee_components,
    aggregate_oee,
    downtime_pareto,
    executive_kpis,
    reliability_metrics,
)
from manufacturing_ct.modeling import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    train_champion_challenger,
)
from manufacturing_ct.monitoring import (
    alarm_quality,
    data_quality_report,
    drift_report,
)
from manufacturing_ct.policy import PolicyConfig, prioritize_predictions
from manufacturing_ct.reporting import create_figures, write_metric_backed_docs
from manufacturing_ct.spc import (
    individuals_mr_chart,
    p_chart,
    process_capability,
    u_chart,
    xbar_r_chart,
)
from manufacturing_ct.synthetic import generate_plant_data


def _json_default(value: Any) -> Any:
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, default=_json_default, sort_keys=True),
        encoding="utf-8",
    )


def _spc_analysis(
    production: pd.DataFrame,
    quality: pd.DataFrame,
    products: pd.DataFrame,
    config: PipelineConfig,
    result_directory: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    baseline_end = pd.Timestamp(config.validation_start)
    xbar_outputs: list[pd.DataFrame] = []
    capabilities: list[dict[str, Any]] = []
    metadata: dict[str, Any] = {}
    for product in products.to_dict("records"):
        subset = quality.loc[quality["product_id"] == product["product_id"]].copy()
        baseline_mask = pd.to_datetime(subset["timestamp"]) < baseline_end
        chart, chart_metadata = xbar_r_chart(
            subset, baseline_mask, subgroup_size=config.subgroup_size
        )
        chart["product_id"] = product["product_id"]
        xbar_outputs.append(chart)
        capability = process_capability(
            subset["ctq_dimension_mm"],
            product["ctq_lsl_mm"],
            product["ctq_usl_mm"],
            chart_metadata["sigma_within"],
        )
        capabilities.append({"product_id": product["product_id"], **capability})
        metadata[f"xbar_r_{product['product_id']}"] = chart_metadata

    xbar = pd.concat(xbar_outputs, ignore_index=True)
    capability_frame = pd.DataFrame(capabilities)

    selected_product = products.iloc[0]["product_id"]
    production_subset = production.loc[production["product_id"] == selected_product].copy()
    baseline = pd.to_datetime(production_subset["timestamp"]) < baseline_end
    individuals, individuals_metadata = individuals_mr_chart(
        production_subset["surface_roughness_um"], baseline
    )
    individuals.insert(0, "timestamp", production_subset["timestamp"].to_numpy())
    individuals.insert(1, "product_id", selected_product)
    defectives = production_subset["scrap_units"] + production_subset["rework_units"]
    p_result, p_metadata = p_chart(defectives, production_subset["total_units"], baseline)
    p_result.insert(0, "timestamp", production_subset["timestamp"].to_numpy())
    p_result.insert(1, "product_id", selected_product)
    u_result, u_metadata = u_chart(
        production_subset["defect_count"], production_subset["total_units"], baseline
    )
    u_result.insert(0, "timestamp", production_subset["timestamp"].to_numpy())
    u_result.insert(1, "product_id", selected_product)

    xbar.to_csv(result_directory / "spc_xbar_r.csv", index=False)
    (
        xbar.sort_values("timestamp")
        .groupby("product_id", observed=True)
        .tail(80)
        .to_csv(result_directory / "spc_xbar_latest.csv", index=False)
    )
    individuals.to_csv(result_directory / "spc_individuals_mr.csv", index=False)
    p_result.to_csv(result_directory / "spc_p_chart.csv", index=False)
    u_result.to_csv(result_directory / "spc_u_chart.csv", index=False)
    capability_frame.to_csv(result_directory / "process_capability.csv", index=False)
    metadata.update(
        {
            "individuals_mr": individuals_metadata,
            "p_chart": p_metadata,
            "u_chart": u_metadata,
            "selection_note": (
                "X-bar/R is used for fixed n=5 CTQ subgroups; I-MR for one roughness "
                "observation per shift; p for defective proportion with variable lot "
                "sizes; u for defects per unit with variable unit counts. np and c are "
                "not selected because their constant-size assumptions do not hold."
            ),
            "alarm_rules": [
                "Rule 1: one point beyond 3 sigma",
                "Rule 2: two of three consecutive points beyond 2 sigma on one side",
                "Rule 3: four of five consecutive points beyond 1 sigma on one side",
                "Rule 4: eight consecutive points on one side of the center line",
            ],
            "control_vs_specification": (
                "Control limits estimate baseline process behavior. LSL/USL are "
                "independent product requirements and are used only for capability."
            ),
        }
    )
    return xbar, capability_frame, metadata


def run_pipeline(config: PipelineConfig) -> dict[str, Any]:
    """Run the complete, deterministic pipeline and persist auditable outputs."""

    config.validate_dates()
    data_directory = Path(config.data_dir)
    artifact_directory = Path(config.artifact_dir)
    result_directory = artifact_directory / "results"
    model_directory = artifact_directory / "model"
    figure_directory = artifact_directory / "figures"
    sample_directory = Path("data/sample")
    for directory in [
        data_directory,
        result_directory,
        model_directory,
        figure_directory,
        sample_directory,
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    plant = generate_plant_data(config)
    plant.production = add_oee_components(plant.production)
    plant.write_csv(data_directory)
    plant.production.head(360).to_csv(
        sample_directory / "production_shifts_sample.csv", index=False
    )
    plant.quality_measurements.head(500).to_csv(
        sample_directory / "quality_measurements_sample.csv", index=False
    )
    plant.machines.to_csv(sample_directory / "machines.csv", index=False)
    plant.products.to_csv(sample_directory / "products.csv", index=False)

    production = plant.production.copy()
    production["month"] = (
        pd.to_datetime(production["timestamp"]).dt.to_period("M").dt.to_timestamp()
    )
    monthly_oee = aggregate_oee(production, ["month", "line_id"])
    machine_oee = aggregate_oee(production, ["machine_id", "line_id"])
    pareto = downtime_pareto(plant.downtime_events)
    reliability = reliability_metrics(production, plant.downtime_events, plant.machines)
    kpis = executive_kpis(production, plant.downtime_events, plant.machines)
    monthly_oee.to_csv(result_directory / "oee_monthly_line.csv", index=False)
    machine_oee.to_csv(result_directory / "oee_machine.csv", index=False)
    pareto.to_csv(result_directory / "downtime_pareto.csv", index=False)
    reliability.to_csv(result_directory / "reliability_metrics.csv", index=False)

    xbar, capability, spc_metadata = _spc_analysis(
        production,
        plant.quality_measurements,
        plant.products,
        config,
        result_directory,
    )
    model_result = train_champion_challenger(production, config, model_directory)
    predictions = model_result["predictions"]
    predictions.to_csv(result_directory / "oot_predictions.csv", index=False)
    model_result["calibration"].to_csv(result_directory / "calibration_curve.csv", index=False)

    explanation = create_shap_outputs(
        model_result["bundle"],
        model_result["oot_frame"],
        predictions,
        result_directory,
    )
    policy_config = PolicyConfig(intervention_effectiveness=config.intervention_effectiveness)
    priority = prioritize_predictions(
        predictions,
        model_result["threshold"]["threshold"],
        explanation["reason_codes_by_shift"],
        policy_config,
    )
    priority.to_csv(result_directory / "maintenance_priority.csv", index=False)
    _write_json(artifact_directory / "results" / "policy_config.json", policy_config.to_dict())

    drift = drift_report(
        model_result["development_frame"],
        model_result["oot_frame"],
        NUMERIC_FEATURES,
        CATEGORICAL_FEATURES,
    )
    quality_checks = data_quality_report(production)
    alarms = alarm_quality(predictions)
    drift.to_csv(result_directory / "data_drift.csv", index=False)
    quality_checks.to_csv(result_directory / "data_quality_checks.csv", index=False)

    figures = create_figures(
        monthly_oee,
        pareto,
        capability,
        xbar.loc[xbar["product_id"] == plant.products.iloc[0]["product_id"]],
        model_result["calibration"],
        model_result["oot_metrics"],
        explanation["global_importance"],
        priority,
        drift,
        figure_directory,
    )

    metrics = {
        "project": "Manufacturing Quality, OEE & Predictive Maintenance Control Tower",
        "dataset_mode": "deterministic_fully_synthetic",
        "seed": config.seed,
        "period": {"start": config.start_date, "end": config.end_date},
        "prediction_horizon_hours": config.prediction_horizon_hours,
        "dataset": {
            "production_shift_rows": len(production),
            "quality_measurement_rows": len(plant.quality_measurements),
            "downtime_event_rows": len(plant.downtime_events),
            "maintenance_event_rows": len(plant.maintenance_events),
            "lines": int(production["line_id"].nunique()),
            "machines": int(production["machine_id"].nunique()),
            "products": int(production["product_id"].nunique()),
            "shifts": int(production["shift"].nunique()),
            "target_positive_rate": float(production["failure_within_24h"].mean()),
        },
        "executive_kpis": kpis,
        "spc": {
            "metadata": spc_metadata,
            "capability": capability.to_dict("records"),
            "xbar_signal_count": int(xbar["any_signal"].sum()),
        },
        "model": {
            "champion_name": model_result["champion_name"],
            "challenger_name": model_result["challenger_name"],
            "threshold": model_result["threshold"],
            "validation_metrics": model_result["validation_metrics"],
            "oot_metrics": model_result["oot_metrics"],
            "oot_confidence_intervals": model_result["oot_confidence_intervals"],
            "candidate_summary": model_result["candidate_summary"],
            "partitions": model_result["partitions"],
            "cost_assumptions": {
                "false_negative_cost": config.false_negative_cost,
                "false_positive_cost": config.false_positive_cost,
                "minimum_recall": config.minimum_recall,
                "maximum_alert_rate": config.maximum_alert_rate,
                "intervention_effectiveness": config.intervention_effectiveness,
            },
        },
        "explainability": {
            "model_name": explanation["model_name"],
            "explained_rows": explanation["explained_rows"],
            "transformed_feature_count": explanation["transformed_feature_count"],
            "top_global_drivers": explanation["top_global_drivers"],
            "scope_note": explanation["scope_note"],
        },
        "decision_support": {
            "recommendation_counts": {
                str(key): int(value)
                for key, value in priority["priority"].value_counts().to_dict().items()
            },
            "human_approval_required": True,
            "execution_mode": "recommendation_only",
        },
        "monitoring": {
            "alarm_quality": alarms,
            "max_psi": float(drift["psi"].max()),
            "features_at_action_level": int((drift["severity"] == "action").sum()),
            "data_quality_checks_passed": int(quality_checks["passed"].sum()),
            "data_quality_checks_total": len(quality_checks),
        },
        "figures": figures,
    }
    _write_json(result_directory / "pipeline_metrics.json", metrics)
    _write_json(result_directory / "spc_metadata.json", spc_metadata)
    _write_json(result_directory / "pipeline_config.json", config.to_dict())
    write_metric_backed_docs(metrics, capability, drift, "docs/governance")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/base.yaml")
    arguments = parser.parse_args()
    metrics = run_pipeline(PipelineConfig.from_yaml(arguments.config))
    print(
        json.dumps(
            {
                "oee": metrics["executive_kpis"]["oee"],
                "champion": metrics["model"]["champion_name"],
                "oot_pr_auc": metrics["model"]["oot_metrics"]["pr_auc"],
                "oot_recall": metrics["model"]["oot_metrics"]["recall"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
