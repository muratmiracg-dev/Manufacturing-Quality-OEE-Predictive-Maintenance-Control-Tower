"""Deterministic, synthetic manufacturing event and measurement generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from manufacturing_ct.config import PipelineConfig, machine_master, product_master


@dataclass
class PlantData:
    """Container for generated plant datasets."""

    production: pd.DataFrame
    quality_measurements: pd.DataFrame
    downtime_events: pd.DataFrame
    maintenance_events: pd.DataFrame
    machines: pd.DataFrame
    products: pd.DataFrame

    def write_csv(self, directory: str | Path) -> None:
        """Write generated tables using stable ordering and ISO timestamps."""

        destination = Path(directory)
        destination.mkdir(parents=True, exist_ok=True)
        tables = {
            "production_shifts.csv": self.production,
            "quality_measurements.csv": self.quality_measurements,
            "downtime_events.csv": self.downtime_events,
            "maintenance_events.csv": self.maintenance_events,
            "machines.csv": self.machines,
            "products.csv": self.products,
        }
        for filename, frame in tables.items():
            frame.to_csv(destination / filename, index=False, date_format="%Y-%m-%dT%H:%M:%S")


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + np.exp(-value))


def _failure_type(
    rng: np.random.Generator,
    vibration: float,
    temperature: float,
    pressure: float,
    current: float,
) -> str:
    scores = np.array(
        [
            max(vibration - 3.6, 0.1),
            max(temperature - 70.0, 0.1) / 7.0,
            max(5.4 - pressure, 0.1),
            max(current - 42.0, 0.1) / 5.0,
            0.35,
        ]
    )
    probabilities = scores / scores.sum()
    return str(
        rng.choice(
            ["Bearing", "Overheating", "Hydraulic", "Electrical", "Sensor"],
            p=probabilities,
        )
    )


class SyntheticPlantGenerator:
    """Sequential state simulation for a synthetic discrete-manufacturing plant."""

    def __init__(self, config: PipelineConfig):
        config.validate_dates()
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        self.machines = machine_master()
        if config.sample_machine_limit is not None:
            self.machines = self.machines.head(config.sample_machine_limit).copy()
        self.products = product_master()

    def generate(self) -> PlantData:
        """Generate shift snapshots, downtime, maintenance and CTQ subgroups."""

        production_rows: list[dict[str, Any]] = []
        quality_rows: list[dict[str, Any]] = []
        downtime_rows: list[dict[str, Any]] = []
        maintenance_rows: list[dict[str, Any]] = []

        timestamps = pd.date_range(
            self.config.start_date,
            pd.Timestamp(self.config.end_date) + pd.Timedelta(hours=16),
            freq="8h",
        )
        product_records = self.products.to_dict("records")

        for machine_number, machine in enumerate(self.machines.to_dict("records")):
            wear = 0.08 + 0.012 * (machine_number % 4)
            hours_since_maintenance = float(40 + machine_number * 11)
            cumulative_operating_hours = float(
                (2024 - machine["install_year"]) * 365 * 18 + machine_number * 140
            )
            machine_bias = (machine_number % 5 - 2) * 0.012
            prior_failure_timestamps: list[pd.Timestamp] = []

            for shift_index, timestamp in enumerate(timestamps):
                product = product_records[
                    (shift_index // 6 + machine_number) % len(product_records)
                ]
                shift = ["A", "B", "C"][timestamp.hour // 8]
                month_angle = 2 * np.pi * (timestamp.dayofyear / 365.25)
                ambient_temperature = 21.5 + 7.5 * np.sin(month_angle - 1.2)
                ambient_humidity = 48.0 + 13.0 * np.cos(month_angle) + self.rng.normal(0, 3)
                changeover = int(shift_index % 6 == 0)
                planned_downtime = 18.0 + 17.0 * changeover
                planned_maintenance = bool(
                    hours_since_maintenance >= 690
                    or (timestamp.day == 1 and shift == "A" and machine_number % 3 == 0)
                )
                if planned_maintenance:
                    planned_downtime += 70.0
                    maintenance_rows.append(
                        {
                            "event_id": f"PM-{machine['machine_id']}-{timestamp:%Y%m%d%H}",
                            "machine_id": machine["machine_id"],
                            "timestamp": timestamp,
                            "maintenance_type": "Preventive",
                            "duration_min": 70.0,
                            "cost": machine["maintenance_cost"],
                            "human_approved": True,
                        }
                    )
                    wear *= 0.54
                    hours_since_maintenance = 0.0

                load_factor = 0.94 + 0.05 * np.sin(shift_index / 17) + self.rng.normal(0, 0.025)
                shift_heat = 2.0 if shift == "C" else 0.0
                vibration = 1.75 + 4.6 * wear + machine_bias * 8 + self.rng.normal(0, 0.22)
                temperature = (
                    55.0
                    + 27.0 * wear
                    + 0.24 * (ambient_temperature - 20)
                    + shift_heat
                    + self.rng.normal(0, 1.2)
                )
                pressure = 6.15 - 1.15 * wear + self.rng.normal(0, 0.10)
                current = 33.0 + 12.5 * load_factor + 8.5 * wear + self.rng.normal(0, 1.1)
                lubrication = np.clip(96.0 - 68.0 * wear + self.rng.normal(0, 3.2), 8.0, 100.0)
                tool_wear_pct = np.clip(wear * 100 + self.rng.normal(0, 2.0), 0.0, 100.0)

                nonlinear_stress = (
                    0.8 * (vibration > 4.6)
                    + 0.7 * (temperature > 78.0)
                    + 0.75 * (lubrication < 48.0)
                    + 0.45 * (pressure < 5.35)
                )
                hazard_logit = (
                    -6.2
                    + 5.6 * wear
                    + 0.18 * machine["criticality"]
                    + 0.0031 * hours_since_maintenance
                    + nonlinear_stress
                )
                true_hazard = float(np.clip(_sigmoid(hazard_logit), 0.001, 0.62))
                failure_event = bool(self.rng.random() < true_hazard)
                failure_type = ""
                failure_downtime = 0.0
                if failure_event:
                    failure_type = _failure_type(
                        self.rng, vibration, temperature, pressure, current
                    )
                    base_duration = {
                        "Bearing": 130,
                        "Overheating": 85,
                        "Hydraulic": 115,
                        "Electrical": 105,
                        "Sensor": 45,
                    }[failure_type]
                    failure_downtime = float(
                        np.clip(self.rng.lognormal(np.log(base_duration), 0.25), 25, 270)
                    )
                    prior_failure_timestamps.append(timestamp)
                    downtime_rows.append(
                        {
                            "event_id": f"DT-{machine['machine_id']}-{timestamp:%Y%m%d%H}",
                            "machine_id": machine["machine_id"],
                            "line_id": machine["line_id"],
                            "timestamp": timestamp,
                            "planned": False,
                            "category": failure_type,
                            "duration_min": failure_downtime,
                            "production_loss_cost": failure_downtime
                            * machine["failure_cost"]
                            / 480.0,
                        }
                    )
                    maintenance_rows.append(
                        {
                            "event_id": f"CM-{machine['machine_id']}-{timestamp:%Y%m%d%H}",
                            "machine_id": machine["machine_id"],
                            "timestamp": timestamp,
                            "maintenance_type": "Corrective",
                            "duration_min": failure_downtime,
                            "cost": machine["maintenance_cost"] * 1.35,
                            "human_approved": True,
                        }
                    )

                microstop_probability = 0.14 + 0.16 * wear
                microstop = (
                    float(np.clip(self.rng.gamma(2.0, 5.5), 2.0, 40.0))
                    if self.rng.random() < microstop_probability
                    else 0.0
                )
                if microstop > 0:
                    downtime_rows.append(
                        {
                            "event_id": (f"DT-MICRO-{machine['machine_id']}-{timestamp:%Y%m%d%H}"),
                            "machine_id": machine["machine_id"],
                            "line_id": machine["line_id"],
                            "timestamp": timestamp,
                            "planned": False,
                            "category": "Minor Stop",
                            "duration_min": microstop,
                            "production_loss_cost": microstop * machine["failure_cost"] / 960.0,
                        }
                    )

                planned_production_time = max(480.0 - planned_downtime, 1.0)
                unplanned_downtime = min(
                    failure_downtime + microstop, planned_production_time * 0.92
                )
                run_time = max(planned_production_time - unplanned_downtime, 1.0)
                speed_factor = float(
                    np.clip(
                        0.985 - 0.20 * wear - 0.025 * (shift == "C") + self.rng.normal(0, 0.018),
                        0.58,
                        1.0,
                    )
                )
                theoretical_units = run_time * 60.0 / product["ideal_cycle_sec"]
                total_units = max(int(theoretical_units * speed_factor), 1)
                process_drift = 0.55 * (shift_index % 211 in range(188, 211))
                defect_logit = (
                    -4.35
                    + 2.8 * wear
                    + 0.55 * (speed_factor > 0.96)
                    + 0.35 * (shift == "C")
                    + process_drift
                    + 0.14 * (machine_number % 3)
                )
                defect_rate = float(np.clip(_sigmoid(defect_logit), 0.002, 0.22))
                defective_units = int(self.rng.binomial(total_units, defect_rate))
                rework_units = int(self.rng.binomial(defective_units, 0.58))
                scrap_units = defective_units - rework_units
                first_pass_good_units = total_units - defective_units
                copq = scrap_units * product["unit_cost"] + rework_units * product["rework_cost"]
                defect_count = int(
                    defective_units + self.rng.poisson(max(total_units * defect_rate * 0.22, 0.1))
                )
                mean_shift = (
                    machine_bias
                    + 0.09 * wear
                    + (0.035 if shift_index % 211 in range(188, 211) else 0.0)
                )
                process_sigma = 0.025 + 0.035 * wear
                ctq_values = self.rng.normal(
                    product["ctq_nominal_mm"] + mean_shift,
                    process_sigma,
                    self.config.subgroup_size,
                )
                roughness = float(
                    np.clip(
                        0.85 + 1.25 * wear + 0.12 * (shift == "C") + self.rng.normal(0, 0.10),
                        0.25,
                        4.5,
                    )
                )
                for sample_number, ctq_value in enumerate(ctq_values, start=1):
                    quality_rows.append(
                        {
                            "subgroup_id": (f"SG-{machine['machine_id']}-{timestamp:%Y%m%d%H}"),
                            "timestamp": timestamp,
                            "line_id": machine["line_id"],
                            "machine_id": machine["machine_id"],
                            "product_id": product["product_id"],
                            "shift": shift,
                            "sample_number": sample_number,
                            "ctq_dimension_mm": float(ctq_value),
                            "lsl_mm": product["ctq_lsl_mm"],
                            "usl_mm": product["ctq_usl_mm"],
                        }
                    )

                recent_cutoff = timestamp - pd.Timedelta(days=30)
                prior_failure_timestamps = [
                    item for item in prior_failure_timestamps if item >= recent_cutoff
                ]
                energy_kwh = float(
                    run_time
                    * (0.72 + 0.18 * load_factor + 0.12 * wear)
                    * (1.0 + machine_number % 3 * 0.08)
                )
                production_rows.append(
                    {
                        "shift_id": f"SH-{machine['machine_id']}-{timestamp:%Y%m%d%H}",
                        "timestamp": timestamp,
                        "date": timestamp.normalize(),
                        "line_id": machine["line_id"],
                        "machine_id": machine["machine_id"],
                        "machine_type": machine["machine_type"],
                        "product_id": product["product_id"],
                        "shift": shift,
                        "criticality": machine["criticality"],
                        "machine_age_years": 2024 - machine["install_year"],
                        "failure_cost": machine["failure_cost"],
                        "maintenance_cost": machine["maintenance_cost"],
                        "planned_minutes": 480.0,
                        "planned_downtime_min": planned_downtime,
                        "planned_production_min": planned_production_time,
                        "unplanned_downtime_min": unplanned_downtime,
                        "run_time_min": run_time,
                        "ideal_cycle_sec": product["ideal_cycle_sec"],
                        "speed_factor": speed_factor,
                        "total_units": total_units,
                        "first_pass_good_units": first_pass_good_units,
                        "rework_units": rework_units,
                        "scrap_units": scrap_units,
                        "defect_count": defect_count,
                        "copq": copq,
                        "vibration_rms": vibration,
                        "temperature_c": temperature,
                        "pressure_bar": pressure,
                        "current_amp": current,
                        "lubrication_index": lubrication,
                        "tool_wear_pct": tool_wear_pct,
                        "surface_roughness_um": roughness,
                        "ambient_temperature_c": ambient_temperature,
                        "ambient_humidity_pct": ambient_humidity,
                        "hours_since_maintenance": hours_since_maintenance,
                        "cumulative_operating_hours": cumulative_operating_hours,
                        "changeover_count": changeover,
                        "failures_last_30d": len(prior_failure_timestamps) - int(failure_event),
                        "energy_kwh": energy_kwh,
                        "failure_event": int(failure_event),
                        "failure_type": failure_type,
                        "true_hazard_probability": true_hazard,
                        "_latent_wear_state": wear,
                    }
                )

                operating_hours = run_time / 60.0
                cumulative_operating_hours += operating_hours
                hours_since_maintenance += operating_hours
                wear_increment = (
                    0.0020 * operating_hours
                    + 0.0045 * changeover
                    + 0.0030 * (shift == "C")
                    + max(temperature - 78.0, 0.0) * 0.0008
                )
                wear = float(np.clip(wear + wear_increment, 0.02, 1.25))
                if failure_event:
                    wear *= 0.34
                    hours_since_maintenance = 0.0

        production = pd.DataFrame(production_rows).sort_values(
            ["machine_id", "timestamp"], ignore_index=True
        )
        production = self._add_safe_lag_features_and_target(production)
        quality = pd.DataFrame(quality_rows).sort_values(
            ["machine_id", "timestamp", "sample_number"], ignore_index=True
        )
        downtime = pd.DataFrame(downtime_rows).sort_values(
            ["timestamp", "machine_id"], ignore_index=True
        )
        maintenance = pd.DataFrame(maintenance_rows).sort_values(
            ["timestamp", "machine_id"], ignore_index=True
        )
        return PlantData(
            production=production,
            quality_measurements=quality,
            downtime_events=downtime,
            maintenance_events=maintenance,
            machines=self.machines.copy(),
            products=self.products.copy(),
        )

    def _add_safe_lag_features_and_target(self, frame: pd.DataFrame) -> pd.DataFrame:
        output = frame.copy()
        grouped = output.groupby("machine_id", sort=False, group_keys=False)
        output["defect_rate_lag_1"] = grouped.apply(
            lambda group: (
                (group["scrap_units"] + group["rework_units"]) / group["total_units"]
            ).shift(1),
            include_groups=False,
        ).reset_index(level=0, drop=True)
        output["downtime_last_7d_min"] = grouped["unplanned_downtime_min"].transform(
            lambda series: series.shift(1).rolling(21, min_periods=1).sum()
        )
        output["vibration_rolling_3"] = grouped["vibration_rms"].transform(
            lambda series: series.rolling(3, min_periods=1).mean()
        )
        output["defect_rate_lag_1"] = output["defect_rate_lag_1"].fillna(0.0)
        output["downtime_last_7d_min"] = output["downtime_last_7d_min"].fillna(0.0)

        future_failure = pd.Series(0, index=output.index, dtype=int)
        future_hours = pd.Series(np.nan, index=output.index, dtype=float)
        for _, indices in output.groupby("machine_id", sort=False).groups.items():
            machine_rows = output.loc[indices]
            events = machine_rows["failure_event"].to_numpy()
            for position, row_index in enumerate(indices):
                future_slice = events[position + 1 : position + 4]
                if future_slice.any():
                    first_offset = int(np.flatnonzero(future_slice)[0]) + 1
                    future_failure.loc[row_index] = 1
                    future_hours.loc[row_index] = float(first_offset * 8)
        output["failure_within_24h"] = future_failure
        output["next_failure_hours"] = future_hours
        return output


def generate_plant_data(config: PipelineConfig) -> PlantData:
    """Convenience entry point used by the pipeline and tests."""

    return SyntheticPlantGenerator(config).generate()
