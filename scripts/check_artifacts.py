"""Validate committed metric, PBIP and executive deliverable contracts."""

from __future__ import annotations

import json
import math
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def main() -> None:
    metrics = load_json(ROOT / "artifacts/results/pipeline_metrics.json")
    require(metrics["dataset_mode"] == "deterministic_fully_synthetic", "data mode")
    require(metrics["seed"] == 20260729, "seed changed without artifact regeneration")
    require(metrics["dataset"]["production_shift_rows"] == 19692, "shift row count")
    require(metrics["dataset"]["quality_measurement_rows"] == 98460, "CTQ row count")
    require(math.isclose(metrics["executive_kpis"]["oee"], 0.8526647989, abs_tol=1e-9), "OEE")
    require(0 <= metrics["model"]["oot_metrics"]["brier_score"] <= 1, "Brier range")
    require(
        metrics["model"]["oot_metrics"]["pr_auc"] > metrics["dataset"]["target_positive_rate"],
        "PR lift",
    )
    require(metrics["decision_support"]["human_approval_required"] is True, "human gate")
    require(metrics["decision_support"]["execution_mode"] == "recommendation_only", "mode")
    require(metrics["monitoring"]["data_quality_checks_passed"] == 5, "data quality")

    for path in (ROOT / "powerbi").rglob("*.json"):
        load_json(path)
    load_json(ROOT / "powerbi/ManufacturingControlTower.pbip")
    load_json(ROOT / "powerbi/ManufacturingControlTower.SemanticModel/definition.pbism")

    workbook = ROOT / "deliverables/excel/Manufacturing_Control_Tower.xlsx"
    deck = ROOT / "deliverables/presentation/Manufacturing_Control_Tower_Executive_Deck.pptx"
    report = ROOT / "deliverables/report/Manufacturing_Control_Tower_Governance_Report.pdf"
    for path in [workbook, deck, report]:
        require(path.exists() and path.stat().st_size > 10_000, f"missing artifact: {path}")
    require(zipfile.is_zipfile(workbook), "invalid XLSX container")
    require(zipfile.is_zipfile(deck), "invalid PPTX container")
    require(report.read_bytes().startswith(b"%PDF"), "invalid PDF signature")

    required_docs = [
        "README.md",
        "README_TR.md",
        "docs/architecture.md",
        "docs/data_contract.md",
        "docs/spc_methodology.md",
        "docs/governance/model_card.md",
        "docs/governance/validation_report.md",
        "docs/governance/risk_register.md",
        "docs/governance/threat_model.md",
        "docs/monitoring_runbook.md",
        "docs/branch_protection_guide.md",
    ]
    for relative in required_docs:
        require((ROOT / relative).exists(), f"missing documentation: {relative}")
    print("Artifact contract checks passed.")


if __name__ == "__main__":
    main()
