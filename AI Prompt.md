# Energy Distribution System – Complete Implementation Specification and Code Review Prompt

## 1. System Overview
Develop a Python module that simulates daily energy distribution across multiple interconnected energy zones using historical data. The simulation must capture the dynamics of wind and hydroelectric power, enforce physical constraints (production capacities, hydro storage limits, and transmission capacities), and support flexible energy balancing. The system must:

### Energy Sources:

- Wind: Produced based on historical data. Wind energy is used immediately (it cannot be stored); any surplus is exported.

- Hydro: Produced based on water available above a minimum level and subject to turbine/generator capacity.

### Energy Flow:

- A zone first uses its own wind production, then imports energy (if needed) from neighbors, then produces local hydro.

- Imports can occur over direct (one-hop) routes or via indirect (two-hop) routes through a transit zone.

**Two import phases are defined:**

Phase 2: Imports only from suppliers above their hydro_force_export threshold.

Phase 4: Imports from all suppliers with extra capacity.

In both phases, candidates are prioritized solely by the supplier’s relative water level, ensuring that zones at risk of overspill (i.e. above the force export threshold) are used preferentially.

### Phase Control:
The balancing algorithm must allow you to enable/disable each phase (e.g., wind production, import phases, local hydro production) and to toggle two-hop routing independently.

### Metrics & Logging:

Detailed per-zone metrics (e.g., wind used, local hydro production, imported energy, exported energy, unmet demand, and water used for hydro production) must be captured daily.

#### Energy transfers (imports/exports) must be recorded with details, including:

Number of hops (1 for direct, 2 for two-hop)

For two-hop transfers, the transit zone is recorded

The connections used and the capacity consumed on each connection.

The system should log all important events, decisions, and metrics using Python’s logging module. Logging must be configurable (`log level`, `file output`).

**Aggregated Daily Summary:**
For each simulation day, an aggregated summary is produced that includes:

Total demand

Total wind used (local consumption)

Imported energy from Phase 2 (direct, one-hop) and Phase 4 (two-hop) separately

Local hydro production

Unmet demand
This summary is used for visualizations.

**Visualization:**
Visualizations must include:

1. Stacked Area Chart: A chart plotting the total daily demand as a line, with the components (wind, Phase 1 imports, local hydro production, Phase 2 imports, and unmet demand) shown as stacked areas behind the demand line.
2. Energy Exchange Network Diagram: A network diagram (using zone coordinates from the configuration) that shows energy transfers between zones. For direct (one-hop) transfers, display two separate arrows (one representing export, one representing import) with a slight offset to avoid overlap. For two-hop transfers, instead of drawing both segments separately, display two curved arrows that touch the transit zone (or, if preferred, a single summarized curved arrow) with labels showing the energy amount (in GWh, with zero decimals).
3. Relative hydro storage trends (as a percentage) over time.
Additional Visualizations:



## 2. File Structure and Modules
Organize the code into these files and directories:

python
Kopier

```
energy_distribution/
├── models.py          # Data structures: EnergyZone, Connection
├── simulator.py       # Simulator engine: advances simulation day-by-day, updates water storage, aggregates per-zone metrics, and computes daily summary.
├── balancing.py       # Balancing algorithm supporting multiple phases:
│                         1. Local Wind Production  
│                         2. First Import Phase (only from suppliers above hydro_force_export)  
│                         3. Local Hydro Production  
│                         4. Second Import Phase (from all suppliers with extra capacity)  
│                         - Two-hop routing can be toggled.
├── data_handler.py    # Functions for verifying and loading input files (wind, consumption, hydro inflow, optional reservoir fill levels).
├── visualization.py   # Visualization functions:
│                         - plot_energy_flows_summary: Stacked area chart for daily summary.
│                         - plot_energy_exchange_split_import_export (or plot_energy_exchange_curved): Network diagram for energy exchanges, showing separate lines for import and export; curved arrows for two-hop transfers.
├── config.py          # Configuration defaults (DEFAULT_SIMULATION_DAYS, SIMULATION_WARM_UP_DAYS, DEFAULT_START_DATE, LOG_LEVEL, etc.)
├── utils.py           # Utility functions including logging setup (with file handler).
├── norway_setup.py    # Setup functions for the Norwegian network:
│                         - Defines zones (NO1–NO5) with hydro parameters, coordinates, etc.
│                         - Defines bidirectional connections with capacities and loss factors.
├── run_simulation.py  # Driver script: uses config.py values (with ability to override via command-line), loads data, runs simulation, and calls visualization functions.
├── tests/             # Unit and integration tests for core modules (models, simulator, balancing).
└── examples/          # Example configuration files (e.g., example_config.json)
```
## 3. Data Loading and Configuration
Input Files:

Wind Production: input/{zone_id}_Wind_Production.csv with columns "Dato_Id" (date) and `"Produksjon [MWh]"`.

Consumption: input/{zone_id}_Consumption.csv with either a "Date" column and "Daily_Consumption" or sequential "Daily_Consumption" values.

Hydro Inflow: input/{zone_id}_Effective_Inflow.csv with column "T_Gj.snitt" (weekly average inflow; converted to daily values).

Optional Reservoir Fill Levels: input/{zone_id}_Reservoir_Fill_Level.csv with a week column (e.g., "Uke") and year-specific fill data to interpolate daily fill percentages.

Date Range:

Simulation start date is taken either from command-line arguments or from DEFAULT_START_DATE in config.py.

The simulation runs for a number of days set by DEFAULT_SIMULATION_DAYS (or overridden via arguments).

Error Handling:

Missing files or data for a day are logged and replaced with default values.

4. Balancing Algorithm Details
Phases:

Local Wind Production:

Immediately satisfy demand using wind; record surplus as export.

First Import Phase:

For zones with unmet demand, attempt to import energy from neighboring zones (direct or two-hop) from suppliers that are above their hydro_force_export threshold.

Local Hydro Production:

Produce hydro energy locally to meet remaining demand.

Second Import Phase:

For any residual unmet demand, attempt imports from all suppliers with extra capacity (ignoring the force export threshold).

Record Unmet Demand:

Any remaining deficit is logged as unmet demand.

Two-Hop Routing:

A helper function import_from_neighbors is used to collect candidates from both one-hop and (if enabled) two-hop routes.

The parameter enable_two_hop allows turning off two-hop routing if desired.

Transfer records are generated with a "hops" key (1 or 2), and for two-hop transfers, the "transit_zone" is recorded along with details of connections used.

Water Balance:

Hydro water used is computed from total hydro production (local plus exported) divided by the efficiency.

The reservoir storage is updated daily by subtracting water used and adding daily inflow, then clamped between hydro_min and hydro_max.

## 5. Aggregated Daily Summary and Metrics
For each simulation day, the Simulator must:

Record detailed per-zone metrics (wind, demand, local production, imported energy, exported energy, unmet demand, water used).

Compute an aggregated daily summary that separates imports into Phase 1 and Phase 2 (by summing transfer records with hops == 1 and hops == 2, respectively) and aggregates total wind used, local hydro production, total demand, and unmet demand.

## 6. Visualization
The visualization module must include functions to:

**Stacked Area Chart:**
Plot a chart where the total daily demand is a line, and behind it, the components (wind used, Phase 1 imports, local hydro production, Phase 2 imports, unmet demand) are plotted as stacked areas.

**Energy Exchange Network Diagram:**
A function (e.g., `plot_energy_exchange_split_import_export` or `plot_energy_exchange_curved`) that:

Uses zone coordinates from norway_setup.py.

For direct transfers (hops == 1), draws separate (slightly offset) arrows for export and import between zones.

For two-hop transfers (hops == 2), draws curved arrows summarizing the transfer between supplier and importer. Optionally, it can show two curved arrows (one for export, one for import) that touch the transit node; however, if labels overlap, it may summarize the flow directly between the supplier and importer.

Labels show energy amounts (converted to GWh with zero decimals).

## 7. Configuration and Logging
Configuration:
Use config.py for default parameters (e.g., `DEFAULT_SIMULATION_DAYS`, `SIMULATION_WARM_UP_DAYS`, `DEFAULT_START_DATE`, `LOG_LEVEL`).

Logging:
Use a logging setup in utils.py that writes logs both to console and to a file (e.g., `simulation.log`). Log levels must include `ERROR`, `INFO`, and `DEBUG/TRACE`. Logging should cover data loading, balancing phases, transfers (with hop and transit information), and water storage updates.

## 8. Testing
Develop unit and integration tests in the tests/ folder that verify:

Correct instantiation of core models (EnergyZone, Connection).

Functionality of the balancing algorithm (ensuring proper phase execution, transfer recording, two-hop routing, and unmet demand handling).

Proper aggregation of daily summaries.

Visualization functions produce output without overlapping labels.

## 9. Execution
Driver Script:
The run_simulation.py script should:

Import configuration values from config.py.

Use command-line arguments to optionally override simulation days, start date, and visualization options.

Load data via data_handler.py.

Set up the network using norway_setup.py.

Run the simulation using Simulator.

Output results and generate visualizations (unless disabled).

Write logs to both console and a log file.

## Final Note
This prompt is designed to capture all the details necessary to build a robust Energy Distribution System with flexible balancing, detailed logging, and advanced visualizations. It covers data loading, multi-phase energy balancing with toggling of phases (including two-hop routing), aggregation of daily metrics, and clear visual summaries. Use this prompt to guide code generation, testing, and refinement.
