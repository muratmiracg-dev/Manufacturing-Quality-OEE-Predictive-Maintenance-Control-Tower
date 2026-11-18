# Changelog

## Unreleased

### Fixed

- `select_threshold` silently ignored the recall floor and the 40% review-capacity cap
  when no threshold met both: it fell back to the unconstrained minimum-cost threshold,
  which could alert on 80% of cases with nothing in the outputs to say so. It now keeps
  the capacity cap, takes the highest recall within it, and records
  `constraints_met: false` on the threshold (`model.threshold` in `pipeline_metrics.json`
  and the governance snapshot). The current threshold is feasible; other evidence is
  unchanged.
- Regenerated the committed evidence with the pinned dependency set. The August 2026
  refresh (#10: scikit-learn 1.8.0 -> 1.9.0, pandas 2.2 -> 3.0, shap 0.49 -> 0.51) did not
  rerun the pipeline, so the API loaded a model bundle pickled with scikit-learn 1.8.0
  (`InconsistentVersionWarning`) and the published metrics no longer matched a rerun.
  OOT PR-AUC 0.3887 -> 0.3866, ROC-AUC 0.7489 -> 0.7487, threshold 0.1478 -> 0.1454,
  alarm rate 43.11% -> 43.71%; one machine's recommendation moves from P1 to P2.
  OEE, quality, reliability and SPC results are unchanged.
- CI now reruns the pipeline and compares the regenerated CSV/JSON evidence with the
  committed files (`scripts/compare_artifacts.py`), and a test fails if the committed
  model bundle was pickled with another scikit-learn version.
- CI lint uses the pinned Ruff 0.16.4 instead of 0.12.8.
- Known follow-up: the static Excel/PowerPoint/PDF deliverables still quote the
  pre-refresh model metrics and are refreshed with their next rebuild.

## 1.0.0 - 2026-07-29

- Added deterministic multi-line synthetic manufacturing data.
- Added OEE, downtime Pareto, reliability, quality and SPC analytics.
- Added Cp/Cpk/Pp/Ppk capability analysis with separated control/spec limits.
- Added calibrated champion/challenger predictive maintenance models.
- Added SHAP explanations and cost-risk maintenance recommendations.
- Added FastAPI, PostgreSQL, PBIP, Excel, PowerPoint and PDF deliverables.
- Added Docker, Kubernetes, Prometheus, Grafana and security automation.
- Added 35 tests with 95.30% measured coverage.

