# Monitoring Runbook

## Service indicators

| Signal | Warning | Critical | Owner action |
|---|---:|---:|---|
| 5xx request rate | >2% for 10m | >5% for 5m | Check model bundle, schema errors and pod logs |
| p95 latency | >500 ms for 10m | >1 s for 5m | Check CPU, model load and request volume |
| API unavailable | 2m | 5m | Follow incident response; no automated maintenance fallback |
| OOT-style alert rate | >40% | >55% | Pause recommendations; review threshold and drift |
| PSI | >=0.10 | >=0.20 | Investigate source/process shift before recalibration |
| ECE | >0.05 | >0.10 | Recalibrate only after independent validation |
| Data contract exceptions | any | >1% rows | Quarantine affected batch |

## Daily review

1. Confirm `/health` and Prometheus scrape success.
2. Review request failures and latency.
3. Reconcile alert count, precision proxy and planner review capacity.
4. Check schema exceptions and missing data.
5. Record any human overrides and reason.

## Weekly model review

- Compare score, feature and reason-code distributions with the reference.
- Review PSI and seasonal context.
- Check alarm burden, false-alert review and captured failures.
- Investigate performance by line, machine type, product and shift.
- Do not retrain automatically.

## Retraining gate

Retraining requires approved data quality, temporal split, leakage review,
calibration, champion/challenger comparison, threshold capacity assessment,
updated SHAP analysis, rollback package and human sign-off.

Prometheus guidance favors actionable symptom-based alerts; the project follows
that principle without claiming a production SRE service level:
https://prometheus.io/docs/practices/alerting/

