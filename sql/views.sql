CREATE OR REPLACE VIEW manufacturing.vw_oee_daily AS
SELECT
    date_trunc('day', observed_at)::date AS production_date,
    line_id,
    sum(run_time_min) / nullif(sum(planned_production_min), 0) AS availability,
    sum(ideal_cycle_sec * total_units)
        / nullif(sum(run_time_min) * 60.0, 0) AS performance,
    sum(first_pass_good_units)::numeric
        / nullif(sum(total_units), 0) AS quality,
    (
        sum(run_time_min) / nullif(sum(planned_production_min), 0)
    ) * (
        sum(ideal_cycle_sec * total_units)
        / nullif(sum(run_time_min) * 60.0, 0)
    ) * (
        sum(first_pass_good_units)::numeric / nullif(sum(total_units), 0)
    ) AS oee,
    sum(total_units) AS total_units,
    sum(copq) AS copq
FROM manufacturing.fact_production_shift
GROUP BY 1, 2;

CREATE OR REPLACE VIEW manufacturing.vw_downtime_pareto AS
WITH category_loss AS (
    SELECT
        category,
        sum(duration_min) AS duration_min,
        count(*) AS event_count,
        sum(production_loss_cost) AS production_loss_cost
    FROM manufacturing.fact_downtime_event
    WHERE NOT planned
    GROUP BY category
)
SELECT
    category,
    duration_min,
    event_count,
    production_loss_cost,
    duration_min / nullif(sum(duration_min) OVER (), 0) AS downtime_share,
    sum(duration_min) OVER (
        ORDER BY duration_min DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) / nullif(sum(duration_min) OVER (), 0) AS cumulative_share
FROM category_loss;

CREATE OR REPLACE VIEW manufacturing.vw_quality_copq AS
SELECT
    date_trunc('month', observed_at)::date AS month,
    line_id,
    product_id,
    sum(first_pass_good_units)::numeric / nullif(sum(total_units), 0) AS fpy,
    sum(scrap_units)::numeric / nullif(sum(total_units), 0) AS scrap_rate,
    sum(rework_units)::numeric / nullif(sum(total_units), 0) AS rework_rate,
    sum(copq) AS copq
FROM manufacturing.fact_production_shift
GROUP BY 1, 2, 3;

CREATE OR REPLACE VIEW manufacturing.vw_machine_reliability AS
WITH operating AS (
    SELECT
        machine_id,
        sum(run_time_min) / 60.0 AS operating_hours
    FROM manufacturing.fact_production_shift
    GROUP BY machine_id
),
failures AS (
    SELECT
        machine_id,
        count(*) AS failure_count,
        sum(duration_min) / 60.0 AS repair_hours
    FROM manufacturing.fact_downtime_event
    WHERE NOT planned
      AND category <> 'Minor Stop'
    GROUP BY machine_id
)
SELECT
    m.machine_id,
    m.line_id,
    m.criticality,
    coalesce(o.operating_hours, 0) AS operating_hours,
    coalesce(f.failure_count, 0) AS failure_count,
    coalesce(f.repair_hours, 0) AS repair_hours,
    CASE
        WHEN coalesce(f.failure_count, 0) > 0
            THEN o.operating_hours / f.failure_count
    END AS mtbf_hours,
    CASE
        WHEN coalesce(f.failure_count, 0) > 0
            THEN f.repair_hours / f.failure_count
        ELSE 0
    END AS mttr_hours,
    CASE
        WHEN coalesce(f.failure_count, 0) > 0
            THEN o.operating_hours / nullif(o.operating_hours + f.repair_hours, 0)
    END AS intrinsic_reliability
FROM manufacturing.dim_machine AS m
LEFT JOIN operating AS o USING (machine_id)
LEFT JOIN failures AS f USING (machine_id);

CREATE OR REPLACE VIEW manufacturing.vw_maintenance_priority AS
SELECT DISTINCT ON (s.machine_id)
    s.machine_id,
    s.line_id,
    p.model_name,
    p.failure_probability,
    p.threshold,
    r.priority,
    r.recommended_action,
    r.expected_net_benefit,
    r.reason_codes,
    r.human_approval_required,
    s.observed_at
FROM manufacturing.fact_production_shift AS s
JOIN manufacturing.fact_model_prediction AS p USING (shift_id)
JOIN manufacturing.fact_maintenance_recommendation AS r USING (shift_id)
ORDER BY s.machine_id, s.observed_at DESC;
