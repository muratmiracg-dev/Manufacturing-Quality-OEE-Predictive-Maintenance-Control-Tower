# Contributing

1. Create a focused branch from `main`.
2. Keep generated data deterministic and synthetic.
3. Do not add production identifiers, secrets or operational credentials.
4. Run `ruff check .`, `ruff format --check .` and
   `pytest --cov=manufacturing_ct --cov-fail-under=90`.
5. If model logic or any pinned dependency changes (including Dependabot bumps),
   rerun `python -m manufacturing_ct.pipeline --config configs/base.yaml`, commit the
   regenerated `artifacts/` and `docs/governance/` files in the same change and update
   metric-backed deliverables. CI fails when a rerun drifts from the committed evidence.
6. Explain any effect on temporal leakage, calibration, thresholds,
   decision-policy cost assumptions and human approval.

Pull requests should be small enough to review, link to relevant ADRs and avoid
mixing unrelated refactoring with behavior changes.

