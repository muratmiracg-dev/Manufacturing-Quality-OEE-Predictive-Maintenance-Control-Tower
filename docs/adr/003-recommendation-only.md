# ADR 003: Recommendation-Only Service

- Status: Accepted
- Date: 2026-07-29

## Decision

The service returns probability, priority, reasons and synthetic economics. It
will not connect to PLC, SCADA or CMMS write interfaces.

## Consequence

Every recommendation includes `human_approval_required=true`; downstream
automation is outside the supported design.

