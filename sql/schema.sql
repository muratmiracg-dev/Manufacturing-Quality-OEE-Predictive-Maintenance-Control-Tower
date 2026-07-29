CREATE SCHEMA IF NOT EXISTS manufacturing;

CREATE TABLE IF NOT EXISTS manufacturing.dim_machine (
    machine_id text PRIMARY KEY,
    line_id text NOT NULL,
    machine_type text NOT NULL,
    criticality smallint NOT NULL CHECK (criticality BETWEEN 1 AND 5),
    install_year integer NOT NULL,
    failure_cost numeric(14, 2) NOT NULL CHECK (failure_cost > 0),
    maintenance_cost numeric(14, 2) NOT NULL CHECK (maintenance_cost > 0)
);

CREATE TABLE IF NOT EXISTS manufacturing.dim_product (
    product_id text PRIMARY KEY,
    product_name text NOT NULL,
    ideal_cycle_sec numeric(10, 3) NOT NULL CHECK (ideal_cycle_sec > 0),
    ctq_nominal_mm numeric(12, 5) NOT NULL,
    ctq_lsl_mm numeric(12, 5) NOT NULL,
    ctq_usl_mm numeric(12, 5) NOT NULL,
    roughness_usl_um numeric(12, 5) NOT NULL,
    unit_cost numeric(14, 2) NOT NULL,
    rework_cost numeric(14, 2) NOT NULL,
    CHECK (ctq_lsl_mm < ctq_usl_mm)
);

CREATE TABLE IF NOT EXISTS manufacturing.fact_production_shift (
    shift_id text PRIMARY KEY,
    observed_at timestamp NOT NULL,
    line_id text NOT NULL,
    machine_id text NOT NULL REFERENCES manufacturing.dim_machine(machine_id),
    product_id text NOT NULL REFERENCES manufacturing.dim_product(product_id),
    shift_code char(1) NOT NULL CHECK (shift_code IN ('A', 'B', 'C')),
    planned_production_min numeric(10, 3) NOT NULL CHECK (planned_production_min > 0),
    run_time_min numeric(10, 3) NOT NULL CHECK (run_time_min >= 0),
    unplanned_downtime_min numeric(10, 3) NOT NULL CHECK (unplanned_downtime_min >= 0),
    ideal_cycle_sec numeric(10, 3) NOT NULL CHECK (ideal_cycle_sec > 0),
    total_units integer NOT NULL CHECK (total_units > 0),
    first_pass_good_units integer NOT NULL CHECK (first_pass_good_units >= 0),
    scrap_units integer NOT NULL CHECK (scrap_units >= 0),
    rework_units integer NOT NULL CHECK (rework_units >= 0),
    defect_count integer NOT NULL CHECK (defect_count >= 0),
    copq numeric(16, 2) NOT NULL CHECK (copq >= 0),
    vibration_rms numeric(12, 5) NOT NULL,
    temperature_c numeric(12, 5) NOT NULL,
    pressure_bar numeric(12, 5) NOT NULL,
    current_amp numeric(12, 5) NOT NULL,
    lubrication_index numeric(12, 5) NOT NULL,
    failure_event boolean NOT NULL,
    failure_within_24h boolean NOT NULL,
    CHECK (run_time_min <= planned_production_min),
    CHECK (first_pass_good_units <= total_units),
    CHECK (scrap_units + rework_units <= total_units)
);

CREATE INDEX IF NOT EXISTS idx_shift_machine_time
    ON manufacturing.fact_production_shift(machine_id, observed_at);
CREATE INDEX IF NOT EXISTS idx_shift_line_time
    ON manufacturing.fact_production_shift(line_id, observed_at);

CREATE TABLE IF NOT EXISTS manufacturing.fact_quality_measurement (
    subgroup_id text NOT NULL,
    sample_number smallint NOT NULL,
    observed_at timestamp NOT NULL,
    machine_id text NOT NULL REFERENCES manufacturing.dim_machine(machine_id),
    product_id text NOT NULL REFERENCES manufacturing.dim_product(product_id),
    ctq_dimension_mm numeric(12, 5) NOT NULL,
    lsl_mm numeric(12, 5) NOT NULL,
    usl_mm numeric(12, 5) NOT NULL,
    PRIMARY KEY (subgroup_id, sample_number),
    CHECK (sample_number > 0),
    CHECK (lsl_mm < usl_mm)
);

CREATE TABLE IF NOT EXISTS manufacturing.fact_downtime_event (
    event_id text PRIMARY KEY,
    machine_id text NOT NULL REFERENCES manufacturing.dim_machine(machine_id),
    line_id text NOT NULL,
    observed_at timestamp NOT NULL,
    planned boolean NOT NULL,
    category text NOT NULL,
    duration_min numeric(10, 3) NOT NULL CHECK (duration_min >= 0),
    production_loss_cost numeric(16, 2) NOT NULL CHECK (production_loss_cost >= 0)
);

CREATE TABLE IF NOT EXISTS manufacturing.fact_maintenance_event (
    event_id text PRIMARY KEY,
    machine_id text NOT NULL REFERENCES manufacturing.dim_machine(machine_id),
    observed_at timestamp NOT NULL,
    maintenance_type text NOT NULL CHECK (
        maintenance_type IN ('Preventive', 'Corrective')
    ),
    duration_min numeric(10, 3) NOT NULL CHECK (duration_min >= 0),
    cost numeric(16, 2) NOT NULL CHECK (cost >= 0),
    human_approved boolean NOT NULL CHECK (human_approved = true)
);

CREATE TABLE IF NOT EXISTS manufacturing.fact_model_prediction (
    shift_id text PRIMARY KEY REFERENCES manufacturing.fact_production_shift(shift_id),
    scored_at timestamp NOT NULL DEFAULT current_timestamp,
    model_name text NOT NULL,
    failure_probability numeric(8, 7) NOT NULL CHECK (
        failure_probability BETWEEN 0 AND 1
    ),
    threshold numeric(8, 7) NOT NULL CHECK (threshold BETWEEN 0 AND 1),
    alert boolean NOT NULL,
    prediction_horizon_hours integer NOT NULL CHECK (prediction_horizon_hours > 0)
);

CREATE TABLE IF NOT EXISTS manufacturing.fact_maintenance_recommendation (
    recommendation_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shift_id text NOT NULL REFERENCES manufacturing.fact_production_shift(shift_id),
    created_at timestamp NOT NULL DEFAULT current_timestamp,
    priority text NOT NULL CHECK (priority IN ('P1', 'P2', 'P3', 'MONITOR')),
    recommended_action text NOT NULL,
    expected_net_benefit numeric(16, 2) NOT NULL,
    reason_codes jsonb NOT NULL,
    human_approval_required boolean NOT NULL DEFAULT true,
    approved_by text,
    approved_at timestamp,
    CHECK (human_approval_required = true)
);

COMMENT ON SCHEMA manufacturing IS
    'Synthetic demonstration only; not a production control or CMMS schema.';
COMMENT ON TABLE manufacturing.fact_maintenance_recommendation IS
    'Recommendation audit record. It does not represent an executed work order.';
