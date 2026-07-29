# Data Contract

## Contract principles

- Fully synthetic and deterministic for a fixed configuration and seed.
- UTC-naive ISO timestamps representing a single hypothetical plant time zone.
- One `production_shifts` row per machine and eight-hour shift.
- Five CTQ observations per `quality_measurements` subgroup.
- Stable string identifiers; no personal or production identifiers.
- Features used for prediction are available at the pre-shift decision point.
- Current-shift outcome fields are never model features.

## Primary tables

| Table | Grain | Primary key | Key consumers |
|---|---|---|---|
| `production_shifts` | machine x shift | `shift_id` | KPI, model, p/u, policy |
| `quality_measurements` | CTQ sample | subgroup + sample number | X-bar/R, capability |
| `downtime_events` | downtime event | `event_id` | Pareto, MTTR |
| `maintenance_events` | maintenance event | `event_id` | intervention audit |
| `machines` | machine | `machine_id` | criticality and costs |
| `products` | product | `product_id` | cycles and specifications |

## Critical production fields

| Field | Type | Unit / domain | Rule |
|---|---|---|---|
| `timestamp` | datetime | 8-hour cadence | non-null |
| `planned_production_min` | float | minutes | 0 < value <= 480 |
| `run_time_min` | float | minutes | <= planned production |
| `total_units` | integer | count | > 0 |
| `first_pass_good_units` | integer | count | <= total units |
| `scrap_units`, `rework_units` | integer | count | non-negative |
| `vibration_rms` | float | synthetic RMS | 0 to 15 API bound |
| `temperature_c` | float | Celsius | 0 to 180 API bound |
| `pressure_bar` | float | bar | 0 to 20 API bound |
| `lubrication_index` | float | 0-100 index | bounded |
| `failure_event` | integer | 0/1 | current-shift outcome |
| `failure_within_24h` | integer | 0/1 | future three shifts |
| `next_failure_hours` | float/null | 8, 16, 24 | audit only |

## OEE definitions

```text
Availability = Run Time / Planned Production Time
Performance  = Ideal Cycle Time x Total Count / Run Time
Quality      = First-Pass Good Count / Total Count
OEE          = Availability x Performance x Quality
```

Components are aggregated from numerator and denominator sums. Percentages are
not averaged across rows.

## Change control

Breaking changes require:

1. a new ADR;
2. contract tests and migration notes;
3. regenerated metric artifacts;
4. revalidated model and thresholds;
5. a major or minor semantic version increment.

