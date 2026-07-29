# Model Card

## Intended use

The model estimates the probability of a synthetic machine failure in the next
24 hours. Its output is decision support for a
maintenance planner. It does not create work orders, stop equipment, or approve
maintenance.

## Data and split

- Data: deterministic, fully synthetic plant telemetry and events.
- Champion: `random_forest`.
- Challenger: `logistic_regression`.
- Development fit rows: 9,828.
- Calibration rows: 2,160.
- Validation rows: 3,204.
- Out-of-time rows: 4,356.
- A 24-hour purge gap is enforced at temporal boundaries.

## Out-of-time performance

| Metric | Result |
|---|---:|
| PR-AUC | 0.3887 |
| ROC-AUC | 0.7489 |
| Brier score | 0.1137 |
| ECE (10 bins) | 0.0164 |
| Precision | 0.2630 |
| Recall | 0.7351 |
| F1 | 0.3875 |
| Selected threshold | 0.1478 |

## Explainability

Global and local SHAP outputs explain the uncalibrated base estimator. The
sigmoid calibration layer changes reported probabilities and is deliberately
reported as outside the SHAP attribution scope.

## Limitations

Synthetic performance does not establish real-world effectiveness. Plant
transfer requires new validation, calibration, process-engineering review,
data-contract checks, and a monitored shadow deployment.
