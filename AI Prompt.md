# Simulation Configuration Overview

Simulation parameters that define the system setup are configured in a centralised file, `config.py`. Scenarios 1 to 3 represent predefined combinations of these parameters.

# Parameter Categories

The parameters in `config.py` can be divided into three main categories:

## 1. Simulation Time Settings
These define the duration and start date of the simulation:
- `DEFAULT_START_DATE`
- `DEFAULT_SIMULATION_DAYS`

## 2. System Scaling Parameters
These control the magnitude and efficiency of key system inputs:
- `HYDRO_EFFICIENCY`: Efficiency of hydroelectric production
- `CONSUMPTION_FACTOR`: Scale factor for electricity consumption
- `WIND_PRODUCTION_FACTOR`: Scale factor for wind production
- `EFFECTIVE_INFLOW_FACTOR`: Scale factor for hydro inflow
- `RESERVOIR_FILL_LEVEL_FACTOR`: Scale factor for initial hydro levels

## 3. Simulation Logic Toggles
Boolean flags that define the simulation’s logic and import behaviour:
- `ENABLE_WIND`
- `ENABLE_LOCAL_HYDRO`
- `ENABLE_IMPORT_PHASE1`
- `ENABLE_IMPORT_PHASE2`
- `ENABLE_TWO_HOP`

These settings allow users to explore how the system behaves under varying structural and operational assumptions.

# Reference
The full list of parameters and default values is presented in Table \cref{{tab:simulation_config_baseline}} of the thesis.
