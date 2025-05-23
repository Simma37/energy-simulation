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

## Input Files

- `Wind_Production_Year_Hour_[MWh].csv`
- `Reservoir_Replenishment_Year_Week_[GWh].csv`
- `Production_Yearly_Hour_[MWh].csv`

These should contain structured hourly/weekly/yearly data as required by the simulation.

## Output

- Per-zone and daily metrics as CSV
- Visualizations as `.png` or `.pdf`
- Log file (configurable)

## License

[Insert license type, e.g., MIT, GPLv3, etc.]
