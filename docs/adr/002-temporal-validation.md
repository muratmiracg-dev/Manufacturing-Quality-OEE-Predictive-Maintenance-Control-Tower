# ADR 002: Temporal Validation with Purge Gaps

- Status: Accepted
- Date: 2026-07-29

## Decision

Use chronological model-fit, calibration, validation and OOT windows. Purge 24
hours before validation and OOT boundaries to match the label horizon.

## Consequence

Fewer rows are available for fitting, but future outcomes cannot silently cross
the evaluation boundary.

