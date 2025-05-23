# run_simulation.py
import os
import datetime
import argparse
from data_handler import verify_data_files, load_zone_data
from simulator import Simulator
from norway_setup import setup_norway_network
from utils import setup_logging
from config import DEFAULT_SIMULATION_DAYS, SIMULATION_WARM_UP_DAYS, DEFAULT_START_DATE, VISUALIZATION_ENABLED, LOG_LEVEL
from config import LOG_LEVEL_CONSOLE, ENABLE_WIND, ENABLE_IMPORT_PHASE1, ENABLE_LOCAL_HYDRO, ENABLE_IMPORT_PHASE2, ENABLE_TWO_HOP
from config import WIND_PRODUCTION_FACTOR, CONSUMPTION_FACTOR, EFFECTIVE_INFLOW_FACTOR, RESERVOIR_FILL_LEVEL_FACTOR
from datetime import datetime as dt
import logging


def main():
    # Setup logging according to the configured log level.
    setup_logging(log_level=LOG_LEVEL, log_level_console=LOG_LEVEL_CONSOLE)
    logger = logging.getLogger(__name__)
        
    # Determine current directory and parent directory for locating data files.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # Parse the simulation start date from configuration.
    start_date = dt.strptime(DEFAULT_START_DATE, "%Y-%m-%d").date()
    
    # Calculate total simulation days (simulation days plus warm-up period) and compute simulation end date.
    simulation_days = DEFAULT_SIMULATION_DAYS + SIMULATION_WARM_UP_DAYS
    sim_end_date = start_date + datetime.timedelta(days=simulation_days - 1)
    
    # Log simulation period.
    logger.info(f"Simulating from {start_date} to {sim_end_date}")
    
    # Verify that the necessary data files exist in the parent directory.
    verify_data_files(parent_dir)
    
    # Setup the Norway network consisting of zones and connections.
    zones, connections = setup_norway_network()
    
    # Initialize dictionaries to hold time series data for wind, hydro inflow, reservoir fill, and demand.
    wind_data = {}
    hydro_inflow_data = {}
    hydro_resfill_data = {}
    demand_data = {}
    
    # Loop over each zone and load its respective data.
    for zone_id in zones:
        logger.info(f"Loading data for {zone_id}...")
        # Load the zone's daily data given the parent directory and simulation period.
        zone_data = load_zone_data(zone_id, parent_dir, start_date, sim_end_date)
        
        # Store the daily wind data, keyed by date and zone.
        for dt_item, val in zone_data['wind'].items():
            wind_data.setdefault(dt_item, {})[zone_id] = val * WIND_PRODUCTION_FACTOR
        
        # Store the daily hydro inflow data.
        for dt_item, val in zone_data['inflow'].items():
            hydro_inflow_data.setdefault(dt_item, {})[zone_id] = val * EFFECTIVE_INFLOW_FACTOR
        
        # Store the reservoir fill (hydro reserve fill) data.
        for dt_item, val in zone_data['resfill'].items():
            hydro_resfill_data.setdefault(dt_item, {})[zone_id] = val * RESERVOIR_FILL_LEVEL_FACTOR
        
        # Store the daily demand data.
        for dt_item, val in zone_data['demand'].items():
            demand_data.setdefault(dt_item, {})[zone_id] = val * CONSUMPTION_FACTOR

    # Build settings for the balancing algorithm from configuration flags.
    phase_settings = {
        "enable_wind": ENABLE_WIND,
        "enable_import_phase1": ENABLE_IMPORT_PHASE1,
        "enable_local_hydro": ENABLE_LOCAL_HYDRO,
        "enable_import_phase2": ENABLE_IMPORT_PHASE2,
        "enable_two_hop": ENABLE_TWO_HOP
    }


    # Create a Simulator object using the loaded data and configuration parameters.
    sim = Simulator(
        zones, connections, start_date, wind_data, hydro_inflow_data, demand_data,
        phase_settings, warm_up_days=SIMULATION_WARM_UP_DAYS,
        reservoir_fill_data=hydro_resfill_data
    )
    # Run the simulation and store the results.
    results = sim.run_simulation()
    logger.info("Simulation complete.")
    
    # If visualization is enabled, generate the plots.
    if VISUALIZATION_ENABLED:
        # Import visualization functions.
        from visualization import (plot_storage_levels, plot_storage_levels_per_zone, plot_abs_storage_levels,
                                   plot_abs_storage_levels_per_zone, plot_energy_flows_summary,
                                   plot_energy_exchange_split_import_export, plot_daily_energy_components,
                                   plot_daily_energy_components_per_zone)
        
        from config import REPORT_OUTPUT_DIR
        from utils import write_config_description
        
        # Create an output directory
        output_dir = REPORT_OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)

        write_config_description(output_dir+"/config_description.txt")
        
        # Generate relative storage level plots.
        relative_storage_plot = os.path.join(output_dir, "storage_levels_relative.pdf")
        plot_storage_levels(sim, output_file=relative_storage_plot)
        #plot_storage_levels_per_zone(sim, output_file=relative_storage_plot)
        
        # Generate absolute storage level plots.
        storage_plot = os.path.join(output_dir, "storage_levels.pdf")
        plot_abs_storage_levels(sim, output_file=storage_plot)
        plot_abs_storage_levels_per_zone(sim, output_file=storage_plot)
        
        # Generate the energy exchange plot (showing energy transfers).
        exchange_plot = os.path.join(output_dir, "energy_exchange.pdf")
        #plot_energy_exchange_split_import_export(sim, output_file=exchange_plot)
        
        # Generate energy flows summary plot using the first simulation day.
        first_day = sorted(sim.results, key=lambda x: x["date"])[0]["date"]
        flow_plot = os.path.join(output_dir, "energy_flows_summary.pdf")
        plot_energy_flows_summary(sim, output_file=flow_plot)
    
        # Generate daily energy components plots.
        daily_energy_plot = os.path.join(output_dir, "daily_energy.pdf")
        plot_daily_energy_components(sim, output_file=daily_energy_plot)
        plot_daily_energy_components_per_zone(sim, output_file=daily_energy_plot)
        
        # Generate and print a simulation summary.
        from reporting import print_simulation_summary
        print_simulation_summary(sim)
        logger.info("Visualizing and reporting complete.")

if __name__ == "__main__":
    # Only call main if this script is executed directly.
    main()
