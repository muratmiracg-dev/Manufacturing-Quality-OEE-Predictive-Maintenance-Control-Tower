# ADR 001: Synthetic Data Only

- Status: Accepted
- Date: 2026-07-29

## Decision

All plant, sensor, quality, failure, cost and maintenance records are generated
deterministically from a documented seed.

## Rationale

This prevents disclosure risk, makes the pipeline reproducible and keeps every
reported result auditable.

## Consequence

Model and business performance cannot be generalized to a real facility.

