# ADR 005: Validation-Selected Capacity-Constrained Threshold

- Status: Accepted
- Date: 2026-07-29

## Decision

Select the alert threshold on validation data using asymmetric error costs,
minimum recall of 72% and maximum review load of 40%.

If no threshold satisfies both limits, the review load stays a hard ceiling: the
threshold with the highest recall within capacity is chosen and
`model.threshold.constraints_met` is `false` in `pipeline_metrics.json`, so the
breached recall floor is visible to reviewers. The current validation threshold
meets both limits (`constraints_met: true`).

## Consequence

OOT load may still exceed the validation cap under drift; this becomes a
monitoring event and does not trigger automatic threshold changes.

