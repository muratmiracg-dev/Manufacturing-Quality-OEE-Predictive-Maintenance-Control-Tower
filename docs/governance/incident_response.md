# Incident Response

## Severity

- SEV-1: recommendations may create immediate unsafe or materially misleading
  guidance, model artifact compromise, or unauthorized write integration.
- SEV-2: sustained outage, severe drift, widespread contract failure or
  calibration breakdown.
- SEV-3: localized quality degradation, dashboard mismatch or non-critical
  dependency issue.

## Response

1. Detect and declare severity.
2. Disable recommendation delivery or route to `MONITOR`; never automate a
   maintenance action as fallback.
3. Preserve logs, model hash, configuration, data batch and request samples.
4. Determine whether the source is data, code, model, policy or infrastructure.
5. Apply the smallest reviewed correction.
6. Rerun unit, integration, coverage, security and metric reconciliation checks.
7. Compare the candidate fix with the prior bundle on validation and OOT-like
   holdout data.
8. Obtain human approval before restoring recommendations.
9. Document root cause, impact, missed controls and preventive action.

## Rollback

Restore the previous signed model/configuration package. If a trustworthy
package is unavailable, keep the service unavailable or return monitoring-only
guidance. No operational work order should be generated from cached scores.

