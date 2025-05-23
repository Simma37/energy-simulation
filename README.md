# energy-simulation

This Python module simulates daily energy distribution across multiple interconnected energy zones, focusing on the dynamics of wind and hydroelectric power. It enforces physical constraints such as production capacity, hydro storage limits, and transmission capacities, and supports flexible, phase-controlled energy balancing.

## Features

- **Renewable Energy Modeling**: Incorporates both wind and hydroelectric power production based on historical data.
- **Hydropower Constraints**: Includes turbine/generator capacity limits and reservoir minimum levels.
- **Multi-Zone Simulation**: Handles multiple interconnected zones with both direct (one-hop) and indirect (two-hop) energy exchange routes.
- **Import Phases**:
  - **Phase 2**: Imports from zones above a "hydro_force_export" threshold.
  - **Phase 4**: Imports from all zones with extra capacity.
- **Priority Rules**: Zones with higher relative water levels (risk of overspill) are prioritized as exporters.
- **Detailed Logging**: Logs all key actions, decisions, and zone metrics with configurable log levels and output formats.
- **Daily Aggregated Summaries**: Output includes demand, used wind, hydro production, imports by phase, and unmet demand.

## Metrics Captured Per Day

- Wind energy used
- Hydro energy produced
- Energy imported/exported (with hop counts and transit zones)
- Unmet demand
- Water used for hydro

## Visualizations

- **Stacked Area Chart**: Shows demand with components (wind, imports, hydro, unmet demand).
- **Energy Network Diagram**:
  - One-hop transfers shown with directional arrows.
  - Two-hop transfers shown with curved arrows via transit zones.
- **Hydro Storage Trends**: Plots relative hydro storage percentage over time.

## Configuration

- **Phase Toggle**: Enable/disable import phases and two-hop routing.
- **Logging**: Controlled via Python’s `logging` module.

## Requirements

- Python ≥ 3.8
- Libraries: `pandas`, `numpy`, `matplotlib`, `networkx`, `logging`

## Usage

```bash
python run_simulation.py
```
Make sure your input CSV files are correctly formatted and placed in the appropriate folder.

The simulation behavior is controlled by `config.py`, which contains key parameters affecting the results:

### Key Configuration Parameters

- `DEFAULT_START_DATE` and `DEFAULT_SIMULATION_DAYS`: Define the simulation period.
- `CONSUMPTION_FACTOR`: Scales baseline consumption (e.g., `1.16` = +16% increase).
- `WIND_PRODUCTION_FACTOR`, `EFFECTIVE_INFLOW_FACTOR`, `RESERVOIR_FILL_LEVEL_FACTOR`: Scale wind production, inflow, and initial reservoir levels.
- `HYDRO_EFFICIENCY`: Efficiency factor for hydroelectric conversion.
- `ENABLE_WIND`, `ENABLE_LOCAL_HYDRO`: Enable/disable wind and hydro production.
- `ENABLE_IMPORT_PHASE1`, `ENABLE_IMPORT_PHASE2`: Enable import logic for Phase 2 and Phase 4.
- `ENABLE_TWO_HOP`: Allows two-hop routing between zones.
- `SIMULATION_WARM_UP_DAYS`: Number of initial warm-up days (excluded from output).
- `VISUALIZATION_ENABLED`: If set to `True`, generates all PDF plots.
- `LOG_LEVEL`, `LOG_LEVEL_CONSOLE`: Control verbosity of file and console logs.

These parameters allow you to conduct sensitivity analyses, scenario testing, and operational tuning of the simulation.

## Input Files


The system expects the following per-zone CSV files in the `input/` directory:

For each zone (e.g., NO1, NO2, ..., NO5):

- `<ZONE>_Consumption.csv`
- `<ZONE>_Effective_Inflow.csv`
- `<ZONE>_Reservoir_Fill_Level.csv`
- `<ZONE>_Wind_Production.csv`

Example:

- `NO1_Consumption.csv`
- `NO1_Effective_Inflow.csv`
- `NO1_Reservoir_Fill_Level.csv`
- `NO1_Wind_Production.csv`


### Input File Format Specifications

Each input file must follow a standardized format as described below. These formats are essential for the parser to read and align the data properly.

#### 1. Effective Inflow Files

- **Header:** `Iso-uke,1958,1959,...,2025`
- **Columns:** 
  - `Iso-uke`: Week number (1–52)
  - Following columns: Annual inflow values per week (GWh or specified unit)
- **Example:**
  ```
  Iso-uke,1958,1959,1960,...,2023,2024,2025
  1,,49,72,...,60,
  2,38,39,44,...,55,
  ```

#### 2. Reservoir Fill Level Files

- **Header:** `Kapasitet TWh,2022 TWh,...,Uke,Maks TWh,Min TWh,Median TWh,2023 TWh,2024 TWh,2025 TWh`
- **Columns:**
  - First row: Capacity and historical storage levels (TWh)
  - `Uke`: Week number
  - `Maks`, `Min`, `Median`, and future projections
- **Example:**
  ```
  Kapasitet TWh,2022 TWh,...,Uke,Maks TWh,Min TWh,Median TWh,2023 TWh,2024 TWh,2025 TWh
  6.0,3.0,...,1,4.6,2.7,3.7,3.7,3.6,
  ```

#### 3. Wind Production Files

- **Header:** `Produksjon [MWh],Dato_Id`
- **Columns:**
  - `Produksjon [MWh]`: Hourly production values
  - `Dato_Id`: Timestamp (e.g., `2023-01-01 00:00:00`)
- **Example:**
  ```
  Produksjon [MWh],Dato_Id
  4,2018-07-26 00:00:00
  23,2018-07-27 00:00:00
  ```

#### 4. Consumption Files

- **Header:** `Date,Daily_Consumption`
- **Columns:**
  - `Date`: In `YYYY-MM-DD` format
  - `Daily_Consumption`: Daily total in MWh
- **Example:**
  ```
  Date,Daily_Consumption
  2020-12-31,4431.03
  2021-01-01,115295.28
  ```

Ensure that:
- All timestamps are consistent in timezone and format
- Files are UTF-8 encoded
- Missing values are handled as blank cells


## Results Directory (`results/run1/`)

For each zone (e.g., NO1 to NO5):

- `<ZONE>_daily_energy.pdf` – Daily energy balance visualization.
- `<ZONE>_storage_levels.pdf` – Reservoir storage level over time.

General results:

- `config_description.txt` – Configuration metadata for the simulation run.
- `daily_energy.pdf` – Aggregated energy metrics.
- `energy_exchange.pdf` – Network diagram of inter-zonal energy transfers.
- `energy_flows_summary.pdf` – Summary of energy flows by type and phase.
- `storage_levels.pdf` – Absolute storage levels for all zones.
- `storage_levels_relative.pdf` – Relative reservoir fill levels as percentage of capacity.

## License

[Insert license type, e.g., MIT, GPLv3, etc.]
