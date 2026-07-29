# Contributing

1. Create a focused branch from `main`.
2. Keep generated data deterministic and synthetic.
3. Do not add production identifiers, secrets or operational credentials.
4. Run `ruff check .`, `ruff format --check .` and
   `pytest --cov=manufacturing_ct --cov-fail-under=90`.
5. If model logic changes, rerun the pipeline and update metric-backed
   deliverables from the new outputs.
6. Explain any effect on temporal leakage, calibration, thresholds,
   decision-policy cost assumptions and human approval.

Pull requests should be small enough to review, link to relevant ADRs and avoid
mixing unrelated refactoring with behavior changes.

