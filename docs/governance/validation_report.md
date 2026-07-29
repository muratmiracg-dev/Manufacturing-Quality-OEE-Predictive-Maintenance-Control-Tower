# Validation Report

## Independent temporal assessment

Model selection used validation data only. Threshold selection used the
validation period with an explicit false-negative cost of
8,000 and
false-positive cost of
450. The OOT
period was evaluated once after candidate and threshold decisions.

## Champion/challenger outcome

The selected champion is `random_forest` and the retained challenger
is `logistic_regression`. OOT PR-AUC is 0.3887, ROC-AUC is
0.7489, Brier score is 0.1137, precision is
0.2630, and recall is 0.7351.

## Process capability snapshot

Control limits are computed from baseline process behavior. The specification
limits below are independent engineering requirements.

| Product | Cp | Cpk | Pp | Ppk |
|---|---:|---:|---:|---:|
| PRD-A | 1.376 | 1.096 | 1.148 | 0.915 |
| PRD-B | 2.575 | 2.295 | 2.161 | 1.927 |
| PRD-C | 1.822 | 1.546 | 1.537 | 1.304 |
| PRD-D | 2.015 | 1.733 | 1.677 | 1.442 |

## Drift snapshot

| Feature | Type | PSI | Severity |
|---|---|---:|---|
| cumulative_operating_hours | numeric | 8.8993 | action |
| ambient_temperature_c | numeric | 3.8839 | action |
| ambient_humidity_pct | numeric | 0.5604 | action |
| temperature_c | numeric | 0.0773 | stable |
| failures_last_30d | numeric | 0.0543 | stable |
| downtime_last_7d_min | numeric | 0.0148 | stable |
| lubrication_index | numeric | 0.0056 | stable |
| hours_since_maintenance | numeric | 0.0048 | stable |
| pressure_bar | numeric | 0.0047 | stable |
| current_amp | numeric | 0.0040 | stable |
| tool_wear_pct | numeric | 0.0039 | stable |
| defect_rate_lag_1 | numeric | 0.0031 | stable |

## Decision

This synthetic demonstration is fit for portfolio and technical evaluation.
It is not approved for production deployment or autonomous maintenance action.
