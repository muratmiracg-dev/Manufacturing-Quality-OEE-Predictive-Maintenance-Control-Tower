## Summary

Describe the focused change and its user or developer impact.

## Validation

- [ ] `ruff check .`
- [ ] `ruff format --check .`
- [ ] `pytest --cov=manufacturing_ct --cov-fail-under=90`
- [ ] Artifact contract passes
- [ ] Metric-backed artifacts regenerated when analytical behavior changed

## Model and operating boundary

- [ ] Temporal leakage and label horizon reviewed
- [ ] Calibration and threshold effects reported
- [ ] Human approval and recommendation-only boundary preserved
- [ ] No production data, credentials or private identifiers added

## Security

- [ ] New dependencies are necessary and pinned
- [ ] Threat model or risk register updated if the trust boundary changed

