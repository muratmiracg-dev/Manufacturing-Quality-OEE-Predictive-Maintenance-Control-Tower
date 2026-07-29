# Risk Register

| ID | Risk | Likelihood | Impact | Control | Residual |
|---|---|---|---|---|---|
| R-01 | Synthetic-to-real transfer gap | High | High | Explicit limitation, shadow validation, no production claim | High |
| R-02 | Temporal leakage | Medium | High | Pre-shift features, chronological splits, 24h purge gaps | Low |
| R-03 | Poor probability calibration | Medium | High | Later calibration window, Brier/ECE monitoring | Medium |
| R-04 | Alert overload | High | Medium | 40% validation capacity cap, alarm-quality runbook | Medium |
| R-05 | Seasonal or source drift | High | Medium | PSI by feature, segmented review, no auto-retrain | Medium |
| R-06 | Misread control vs specification limits | Medium | High | Separate fields, figures and SPC documentation | Low |
| R-07 | SHAP over-interpretation | Medium | Medium | Base-model scope note, correlation caveat, reason-code review | Medium |
| R-08 | Cost assumption sensitivity | High | Medium | Visible assumptions and formula-driven scenario workbook | Medium |
| R-09 | Unauthorized operational integration | Low | Critical | Recommendation-only API, no PLC/CMMS write path | Low |
| R-10 | Vulnerable dependency or image | Medium | High | pip-audit, Trivy, Dependabot, CodeQL | Medium |
| R-11 | Model bundle tampering | Low | High | Read-only mount, CI provenance, checksum/runbook | Medium |
| R-12 | Missing or malformed sensor data | Medium | Medium | Schema validation, imputation, contract checks and quarantine | Medium |

Risks are illustrative for this portfolio and require plant-specific owners,
tolerances and evidence before any real deployment.

