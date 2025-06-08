# simulator.py
import datetime
from typing import Dict, Any, List
from models import EnergyZone, Connection
from balancing import balance_energy
import logging

class Simulator:
    def __init__(self, zones, connections, start_date, wind_data, hydro_inflow_data, demand_data, phase_settings,
                 warm_up_days=10, reservoir_fill_data=None):
        self.zones = zones
        self.connections = connections
        self.start_date = start_date
        self.wind_data = wind_data
        self.hydro_inflow_data = hydro_inflow_data
        self.demand_data = demand_data
        self.warm_up_days = warm_up_days
        self.reservoir_fill_data = reservoir_fill_data
        self.logger = logging.getLogger("Simulator")
        self.results = []
        self.transfer_records = []
        self.phase_settings = phase_settings
        if self.reservoir_fill_data:
            # Check if the keys in the reservoir_fill_data are dates rather than zone ids.
            first_key = sorted(self.reservoir_fill_data.keys())[0]
            if isinstance(first_key, (datetime.date, datetime.datetime)):
                # Assume the data for the first date is a DataFrame with zone IDs as its columns.
                fill_df = self.reservoir_fill_data[first_key]
                # For each defined zone, if there's a corresponding column in the DataFrame, set its current level.
                for zone_id, zone in self.zones.items():
                    if zone_id in fill_df:
                        # Get the value from the first row of this column.
                        value = fill_df[zone_id]
                        if value > 0:
                            zone.current_level = value
                            logging.info(f"Setting initial level for {zone_id} to {value} - {zone.initial_level}")

    def update_zone_storage(self, sim_date, inflow_today):
        """
        Update hydro storage levels, calculate spill, and collect daily metrics for each zone.

        Args:
          sim_date: The current simulation date.
          inflow_today: Dictionary of inflow data for the current day.

        Returns:
          Dictionary of metrics for each zone.
        """
        day_metrics = {}
        for zone_id, zone in self.zones.items():
            # Calculate water used for hydro production: include both local production and exported hydro energy
            total_hydro_energy = zone.local_production + zone.exported_energy
            water_used = total_hydro_energy / zone.hydro_efficiency if zone.hydro_efficiency > 0 else 0
            # Update hydro storage: subtract water used and add inflow, clamped between hydro_min and hydro_max
            zone.hydro_spill = max(zone.current_level - water_used + zone.inflow_today - zone.hydro_max, 0)
            zone.current_level = min(max(zone.current_level - water_used + zone.inflow_today, zone.hydro_min), zone.hydro_max)
            day_metrics[zone_id] = {
                "current_level": zone.current_level,
                "wind": zone.wind_today,
                "demand": zone.demand_today,
                "local_production": zone.local_production,
                "imported": zone.imported_energy,
                "exported": zone.exported_energy,
                "unmet_demand": zone.unmet_demand,
                "spill": zone.hydro_spill
            }

        return day_metrics

    def run_simulation(self) -> List[Dict[str, Any]]:
        """
        Run the energy simulation over the specified simulation dates.

        For each simulation day:
          - Retrieve daily input data (wind, inflow, demand).
          - Set the daily data on each EnergyZone.
          - Reset connection capacities to their maximum.
          - Apply the balancing algorithm (considering wind production, import/export, local hydro, etc.).
          - Update hydro storage and spill for each zone.
          - Build a daily summary aggregating key metrics (demand, wind used, imports, local hydro production,
            unmet demand).
          
        Returns:
          List of dictionaries containing daily simulation metrics and summaries.
        """
        # Get the sorted list of simulation dates (keys in wind_data)
        simulation_dates = sorted(self.wind_data.keys())
        total_days = len(simulation_dates)
        self.logger.info(f"Starting simulation for {total_days} days from {self.start_date}")

        for sim_date in simulation_dates:
            self.logger.debug(f"Simulating day {sim_date}")
            # Retrieve daily data; use defaults if a zone's data is missing
            wind_today = self.wind_data.get(sim_date, {})
            inflow_today = self.hydro_inflow_data.get(sim_date, {})
            demand_today = self.demand_data.get(sim_date, {})

            # Set daily data on each zone for wind, demand, and inflow.
            for zone_id, zone in self.zones.items():
                zone.wind_today = wind_today.get(zone_id, 0.0)
                zone.demand_today = demand_today.get(zone_id, 0.0)
                # If inflow data is missing, default to 30000.0.
                zone.inflow_today = inflow_today.get(zone_id, 30000.0)

            # Reset all connections' available capacity for the new day.
            for conn in self.connections:
                conn.available_capacity = conn.capacity

            # Run the balancing algorithm for the current day.
            balance_energy(self.zones, self.connections, self.logger, self.transfer_records, self.phase_settings)

            # Update each zone's hydro storage levels, calculate spill, and collect daily metrics.
            day_metrics = self.update_zone_storage(sim_date, inflow_today)

            # Build daily summary aggregating key metrics across all zones.
            daily_summary = {"demand": 0, "wind": 0, "import": 0, "local_hydro": 0, "unmet": 0}
            for zone in self.zones.values():
                daily_summary["demand"] += zone.demand_today
                # The energy used from wind is the minimum of wind production and demand.
                daily_summary["wind"] += min(zone.wind_today, zone.demand_today)
                daily_summary["import"] += zone.imported_energy
                daily_summary["local_hydro"] += zone.local_production
                daily_summary["unmet"] += zone.unmet_demand
                zone.reset_daily_metrics()

            # Save the day's simulation results.
            self.results.append({
                "date": sim_date,
                "metrics": day_metrics,
                "summary": daily_summary
            })
        self.logger.info("Simulation complete")
        return self.results
