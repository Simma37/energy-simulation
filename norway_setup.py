# norway_setup.py
from models import EnergyZone, Connection
from config import HYDRO_EFFICIENCY
def setup_norway_network():
    """
    Set up the energy network for Norway by initializing energy zones and the connections between them.
    
    Each EnergyZone is created with its unique hydro storage characteristics, operational parameters,
    and geographical details. Connections are then established between zones with predefined
    capacities to represent possible energy transfers.

    Returns:
      Tuple:
        - zones (dict): A dictionary mapping zone identifiers (e.g., "NO1") to EnergyZone objects.
        - connections (list): A list of Connection objects representing available transfer routes.
    """
    # Create a dictionary of EnergyZone objects
    zones = {
        "NO1": EnergyZone(
            zone_id="NO1",
            name="Eastern Norway",
            hydro_min=6e6 * 0.070,
            hydro_max=6e6,
            hydro_force_export=6e6 * 0.85,
            hydro_target=6e6 * 0.65,
            hydro_efficiency= HYDRO_EFFICIENCY,
            hydro_max_daily_production=2608.0 * 24, #+ (((23*1e6)/8760)*1/5)) * 24, # for expanded capacity
            hydro_spill=0.0,
            initial_level=6e6 * 0.617,
            coordinates=(3, 2),
            zone_color="blue"
        ),
        "NO2": EnergyZone(
            zone_id="NO2",
            name="Southern Norway",
            hydro_min=33.99e6 * 0.152,
            hydro_max=33.99e6,
            hydro_force_export=33.99e6 * 0.85,
            hydro_target=33.99e6 * 0.65,
            hydro_efficiency=HYDRO_EFFICIENCY,
            hydro_max_daily_production=9847.0 * 24,
            hydro_spill=0.0,
            initial_level=33.99e6 * 0.717,
            coordinates=(2, 1),
            zone_color="green"
        ),
        "NO3": EnergyZone(
            zone_id="NO3",
            name="Central Norway",
            hydro_min=9.12e6 * 0.113,
            hydro_max=9.12e6,
            hydro_force_export=9.12e6 * 0.85,
            hydro_target=9.12e6 * 0.65,
            hydro_efficiency=HYDRO_EFFICIENCY,
            hydro_max_daily_production=2928.0 * 24,
            hydro_spill=0.0,
            initial_level=9.12e6 * 0.611,
            coordinates=(2, 3),
            zone_color="red"
        ),
        "NO4": EnergyZone(
            zone_id="NO4",
            name="Northern Norway",
            hydro_min=20.87e6 * 0.260,
            hydro_max=20.87e6,
            hydro_force_export=20.87e6 * 0.85,
            hydro_target=20.87e6 * 0.65,
            hydro_efficiency=HYDRO_EFFICIENCY,
            hydro_max_daily_production=4509.0 * 24,
            hydro_spill=0.0,
            initial_level=20.87e6 * 0.645,
            coordinates=(2, 4),
            zone_color="orange"
        ),
        "NO5": EnergyZone(
            zone_id="NO5",
            name="Western Norway",
            hydro_min=17.3e6 * 0.095,
            hydro_max=17.3e6,
            hydro_force_export=17.3e6 * 0.85,
            hydro_target=17.3e6 * 0.65,
            hydro_efficiency=HYDRO_EFFICIENCY,
            hydro_max_daily_production=7163.0 * 24,
            hydro_spill=0.0,
            initial_level=17.3e6 * 0.665,
            coordinates=(1, 2),
            zone_color="purple"
        )
    }
    
    # For consistency, assign each zone's 'id' attribute to its zone_id property.
    for zone_id, zone in zones.items():
        zone.id = zone.zone_id

    # Create connections (energy transfer routes) between zones with specified capacities.
    connections = [
        Connection(zones["NO1"], zones["NO2"], capacity=2200.0 * 24),
        Connection(zones["NO2"], zones["NO1"], capacity=3500.0 * 24),
        Connection(zones["NO1"], zones["NO3"], capacity=500.0 * 24),
        Connection(zones["NO3"], zones["NO1"], capacity=500.0 * 24),
        Connection(zones["NO1"], zones["NO5"], capacity=600.0 * 24),
        Connection(zones["NO5"], zones["NO1"], capacity=3900.0 * 24),
        Connection(zones["NO2"], zones["NO5"], capacity=500.0 * 24),
        Connection(zones["NO5"], zones["NO2"], capacity=600.0 * 24),
        Connection(zones["NO3"], zones["NO4"], capacity=400.0 * 24),
        Connection(zones["NO4"], zones["NO3"], capacity=1200.0 * 24),
        Connection(zones["NO3"], zones["NO5"], capacity=800.0 * 24),
        Connection(zones["NO5"], zones["NO3"], capacity=500.0 * 24)
    ]
    # Return the complete network data: zones and their interconnections.
    return zones, connections
