# models.py
from dataclasses import dataclass, field
from typing import Tuple

@dataclass
class EnergyZone:
    """
    Represents an energy zone with hydro storage and production characteristics.

    Attributes:
      zone_id (str): Unique identifier for the zone.
      name (str): Human-readable name of the zone.
      hydro_min (float): Minimum hydro storage level (MWh).
      hydro_max (float): Maximum hydro storage level (MWh).
      hydro_force_export (float): Threshold level for forced export of hydro energy.
      hydro_target (float): Target storage level for hydro operation.
      hydro_efficiency (float): Efficiency factor for converting water to energy.
      hydro_max_daily_production (float): Maximum energy (MWh) producible in one day via hydro.
      hydro_spill (float): Amount of water spilled (unused energy generation).
      initial_level (float): Initial hydro storage level at simulation start.
      coordinates (Tuple[float, float]): (x, y) coordinates for plotting or spatial analysis.
      zone_color (str): A string representing a preferred color for plotting.
    """
    zone_id: str
    name: str
    hydro_min: float
    hydro_max: float
    hydro_force_export: float
    hydro_target: float
    hydro_efficiency: float
    hydro_max_daily_production: float
    hydro_spill: float
    initial_level: float
    coordinates: Tuple[float, float] = (0, 0)
    zone_color: str = ""
    
    # Attributes that are initialized during simulation
    current_level: float = field(init=False)  # Updated after each simulation step
    imported_energy: float = field(default=0.0)
    exported_energy: float = field(default=0.0)
    local_production: float = field(default=0.0)
    local_consumption: float = field(default=0.0)
    unmet_demand: float = field(default=0.0)
    
    # Daily data placeholders; these values are set during each simulation day.
    wind_today: float = field(default=0.0)
    demand_today: float = field(default=0.0)
    inflow_today: float = field(default=0.0)
    remaining_demand: float = field(default=0.0)
    
    def __post_init__(self):
        """Post-initialization: Set the current storage level to the initial level."""
        self.current_level = self.initial_level

    def reset_daily_metrics(self):
        """
        Reset all daily metrics to their default values.
        
        This method is typically called at the start of each simulation day
        so that fresh values can be computed for daily wind, demand, inflow,
        energy transfers and spills.
        """
        self.wind_today = 0.0
        self.demand_today = 0.0
        self.inflow_today = 30000.0  # Default inflow value can be adjusted as needed.
        self.imported_energy = 0.0
        self.exported_energy = 0.0
        self.local_production = 0.0
        self.unmet_demand = 0.0
        self.hydro_spill = 0.0

@dataclass
class Connection:
    """
    Represents an energy transfer connection between two zones.

    Attributes:
      source (EnergyZone): The originating zone of the energy transfer.
      destination (EnergyZone): The receiving zone of the energy transfer.
      capacity (float): Maximum energy (MWh) that can be transferred over this connection.
      loss_factor (float): Fraction of energy lost during transfer (default is 0).
      available_capacity (float): Remaining transferable capacity, updated as transfers occur.
    """
    source: EnergyZone
    destination: EnergyZone
    capacity: float
    loss_factor: float = 0.0
    available_capacity: float = field(init=False)

    def __post_init__(self):
        """Post-initialization: Set the available capacity to the defined connection capacity."""
        self.available_capacity = self.capacity

    def use_capacity(self, amount: float):
        """
        Deduct a specified amount from the connection's available capacity.

        Parameters:
          amount (float): The energy amount (MWh) to deduct from capacity.
        """
        # Ensure available_capacity does not go below 0.
        self.available_capacity = max(self.available_capacity - amount, 0)
