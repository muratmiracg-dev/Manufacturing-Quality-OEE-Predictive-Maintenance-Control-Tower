"""Load generated synthetic CSV files into the PostgreSQL demonstration schema."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


def load(data_directory: Path, database_url: str, replace: bool = False) -> None:
    engine = create_engine(database_url)
    machines = pd.read_csv(data_directory / "machines.csv")
    products = pd.read_csv(data_directory / "products.csv")
    production = pd.read_csv(data_directory / "production_shifts.csv")
    quality = pd.read_csv(data_directory / "quality_measurements.csv")
    downtime = pd.read_csv(data_directory / "downtime_events.csv")
    maintenance = pd.read_csv(data_directory / "maintenance_events.csv")

    production = production.rename(columns={"timestamp": "observed_at", "shift": "shift_code"})
    quality = quality.rename(columns={"timestamp": "observed_at"})
    downtime = downtime.rename(columns={"timestamp": "observed_at"})
    maintenance = maintenance.rename(columns={"timestamp": "observed_at"})
    production_columns = [
        "shift_id",
        "observed_at",
        "line_id",
        "machine_id",
        "product_id",
        "shift_code",
        "planned_production_min",
        "run_time_min",
        "unplanned_downtime_min",
        "ideal_cycle_sec",
        "total_units",
        "first_pass_good_units",
        "scrap_units",
        "rework_units",
        "defect_count",
        "copq",
        "vibration_rms",
        "temperature_c",
        "pressure_bar",
        "current_amp",
        "lubrication_index",
        "failure_event",
        "failure_within_24h",
    ]
    quality_columns = [
        "subgroup_id",
        "sample_number",
        "observed_at",
        "machine_id",
        "product_id",
        "ctq_dimension_mm",
        "lsl_mm",
        "usl_mm",
    ]
    with engine.begin() as connection:
        if replace:
            connection.execute(
                text(
                    "TRUNCATE manufacturing.fact_maintenance_recommendation, "
                    "manufacturing.fact_model_prediction, "
                    "manufacturing.fact_maintenance_event, "
                    "manufacturing.fact_quality_measurement, "
                    "manufacturing.fact_downtime_event, "
                    "manufacturing.fact_production_shift, "
                    "manufacturing.dim_product, manufacturing.dim_machine "
                    "RESTART IDENTITY CASCADE"
                )
            )
        machines.to_sql(
            "dim_machine", connection, schema="manufacturing", if_exists="append", index=False
        )
        products.to_sql(
            "dim_product", connection, schema="manufacturing", if_exists="append", index=False
        )
        production[production_columns].to_sql(
            "fact_production_shift",
            connection,
            schema="manufacturing",
            if_exists="append",
            index=False,
            chunksize=1000,
            method="multi",
        )
        quality[quality_columns].to_sql(
            "fact_quality_measurement",
            connection,
            schema="manufacturing",
            if_exists="append",
            index=False,
            chunksize=1000,
            method="multi",
        )
        downtime.to_sql(
            "fact_downtime_event",
            connection,
            schema="manufacturing",
            if_exists="append",
            index=False,
            chunksize=1000,
            method="multi",
        )
        maintenance.to_sql(
            "fact_maintenance_event",
            connection,
            schema="manufacturing",
            if_exists="append",
            index=False,
            chunksize=1000,
            method="multi",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data/generated")
    parser.add_argument("--replace", action="store_true")
    arguments = parser.parse_args()
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://manufacturing:synthetic-demo-only@localhost:5432/manufacturing",
    )
    load(Path(arguments.data_dir), url, replace=arguments.replace)


if __name__ == "__main__":
    main()
