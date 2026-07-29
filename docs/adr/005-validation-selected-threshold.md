# ADR 005: Validation-Selected Capacity-Constrained Threshold

- Status: Accepted
- Date: 2026-07-29

## Decision

Select the alert threshold on validation data using asymmetric error costs,
minimum recall of 72% and maximum review load of 40%.

## Consequence

OOT load may still exceed the validation cap under drift; this becomes a
monitoring event and does not trigger automatic threshold changes.

