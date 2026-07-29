# ADR 004: Frozen SPC Baseline and Separate Specifications

- Status: Accepted
- Date: 2026-07-29

## Decision

Fit control limits on the development baseline and apply them forward. Store
LSL/USL independently and use them only in capability analysis.

## Consequence

Future shifts cannot normalize their own out-of-control behavior, and users can
distinguish statistical stability from engineering acceptability.

