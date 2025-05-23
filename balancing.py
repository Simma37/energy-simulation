# balancing.py
from models import EnergyZone, Connection
import logging

def import_from_neighbors(zones: dict, connections: list, zone, logger: logging.Logger,
                          transfer_records: list, force_export_required: bool = True,
                          enable_two_hop: bool = True):
    """
    Attempt to import energy from neighboring zones (both direct and, if enabled, two-hop)
    for the given zone (with unmet demand).

    Parameters:
      - zones: Dictionary of all zones.
      - connections: List of all Connection objects.
      - zone: The EnergyZone that needs to import energy.
      - logger: Logger for messages.
      - transfer_records: List to record energy transfers.
      - force_export_required: If True, only consider suppliers above their hydro_force_export threshold.
      - enable_two_hop: If False, only direct (one-hop) candidates will be considered.

    Returns:
      Total energy imported (MWh) for the given zone.
    """
    imported_total = 0
    candidates = []  # List to hold potential supply routes from neighbors

    # --- Direct candidates (one-hop) ---
    # Loop over all connections and check if the destination is the current zone.
    for conn in connections:
        if conn.destination.zone_id == zone.zone_id:
            supplier = conn.source
            # If only suppliers above the force-export level should be used, skip if below threshold.
            if force_export_required and supplier.current_level < supplier.hydro_force_export:
                continue
            # Calculate the surplus energy available from the supplier.
            supplier_surplus = max(0, (supplier.current_level - supplier.hydro_min) * supplier.hydro_efficiency - supplier.local_production)
            # If surplus exists and there is capacity available on the connection, add to candidates.
            if supplier_surplus > 0 and conn.available_capacity > 0:
                candidates.append({
                    "supplier": supplier,
                    "route": [conn],  # One-hop consists of a single connection.
                    "hops": 1,
                    "available_capacity": conn.available_capacity,
                    # Relative supplier availability to evaluate candidate priority.
                    "supplier_relative": (supplier.current_level - supplier.hydro_min) / (supplier.hydro_max - supplier.hydro_min)
                })

    # --- Two-hop candidates (indirect routes) ---
    if enable_two_hop:
        # Consider candidates that might route energy in two hops via a transit zone.
        for conn1 in connections:
            # Check if connection "conn1" targets the importing zone.
            if conn1.destination.zone_id == zone.zone_id:
                intermediate = conn1.source  # This zone acts as a transit.
                # For every connection departing from the transit zone, look for a supplier.
                for conn2 in connections:
                    # Ensure that conn2 starts at the transit zone and leads to a different supplier.
                    if conn2.source.zone_id == intermediate.zone_id and conn2.destination.zone_id != zone.zone_id:
                        supplier = conn2.destination
                        # Again, if forced export is required, verify supplier meets its threshold.
                        if force_export_required and supplier.current_level < supplier.hydro_force_export:
                            continue
                        supplier_surplus = max(0, (supplier.current_level - supplier.hydro_min) * supplier.hydro_efficiency - supplier.local_production)
                        # Validate that surplus exists and both connections have available capacity.
                        if supplier_surplus > 0 and conn1.available_capacity > 0 and conn2.available_capacity > 0:
                            candidates.append({
                                "supplier": supplier,
                                "route": [conn1, conn2],  # Two-hop route uses both connections.
                                "hops": 2,
                                # Use the minimum available capacity along the route.
                                "available_capacity": min(conn1.available_capacity, conn2.available_capacity),
                                "supplier_relative": (supplier.current_level - supplier.hydro_min) / (supplier.hydro_max - supplier.hydro_min),
                                "transit_zone": intermediate.zone_id
                            })

    # Sort candidates by supplier's relative water level (highest first) to prioritize more abundant suppliers.
    candidates.sort(key=lambda c: c["supplier_relative"], reverse=True)

    # Process candidates one-by-one until the zone's remaining demand is satisfied.
    for cand in candidates:
        # If demand is already met, stop processing further candidates.
        if zone.remaining_demand <= 0:
            break
        supplier = cand["supplier"]
        supplier_surplus = max(0, (supplier.current_level - supplier.hydro_min) * supplier.hydro_efficiency - supplier.local_production)
        # Determine the transferable energy: limited by connection capacity, surplus, and the zone's unmet demand.
        transferable = min(cand["available_capacity"], supplier_surplus, zone.remaining_demand)
        if transferable > 0:
            # If single-hop, update the connection capacity; otherwise update both connections in the two-hop route.
            if cand["hops"] == 1:
                conn = cand["route"][0]
                conn.use_capacity(transferable)
                connections_used = [(conn.source.zone_id, conn.destination.zone_id, transferable)]
            else:
                conn1, conn2 = cand["route"]
                conn1.use_capacity(transferable)
                conn2.use_capacity(transferable)
                connections_used = [
                    (conn1.source.zone_id, conn1.destination.zone_id, transferable),
                    (conn2.source.zone_id, conn2.destination.zone_id, transferable)
                ]
            # Update energy balances for both the supplier (export) and the recipient zone (import).
            supplier.exported_energy += transferable
            zone.imported_energy += transferable
            zone.remaining_demand -= transferable
            imported_total += transferable
            # Log the energy transfer details.
            logger.debug(
                f"Imported {transferable} MWh from {supplier.zone_id} to {zone.zone_id} via {cand['hops']} hop(s); "
                f"transit zone: {cand.get('transit_zone', 'N/A')}; supplier relative water level = {cand['supplier_relative']:.2f}; "
                f"Connections used: {connections_used}"
            )
            # Record the transfer details for reporting.
            record = {
                "from": supplier.zone_id,
                "to": zone.zone_id,
                "amount": transferable,
                "hops": cand["hops"],
                "connections_used": connections_used
            }
            if cand["hops"] == 2:
                record["transit_zone"] = cand["transit_zone"]
            transfer_records.append(record)
    return imported_total

def balance_energy(zones: dict, connections: list, logger: logging.Logger, transfer_records: list = None, phase_settings: dict = None):
    """
    Perform daily balancing in five phases, with phase settings allowing individual phases to be turned on/off.

    Phase Settings (default):
      - "enable_wind": True          (Local wind production)
      - "enable_import_phase1": True (First import phase: only suppliers above hydro_force_export)
      - "enable_local_hydro": True   (Local hydro production)
      - "enable_import_phase2": True (Second import phase: all suppliers with extra capacity)
      - "enable_two_hop": True       (Allow two-hop routing)
    
    Phases:
      1. Local Wind Production.
      2. First Import Phase.
      3. Local Hydro Production.
      4. Second Import Phase.
      5. Record any residual unmet demand.
    """
    # Initialize transfer_records if not provided.
    if transfer_records is None:
        transfer_records = []
    # If no phase settings are provided, use defaults.
    if phase_settings is None:
        phase_settings = {
            "enable_wind": True,
            "enable_import_phase1": True,
            "enable_local_hydro": True,
            "enable_import_phase2": True,
            "enable_two_hop": True
        }
    
    # --- Phase 1: Local Wind Production ---
    if phase_settings.get("enable_wind", True):
        for zone_id, zone in zones.items():
            # Use as much wind as possible to cover the zone's demand.
            wind_used = min(zone.wind_today, zone.demand_today)
            logger.debug(f"{zone.zone_id}: Wind production {wind_used} MWh used.")
            zone.local_consumption = wind_used
            surplus_wind = zone.wind_today - wind_used  # Excess wind production.
            if surplus_wind > 0:
                # The surplus wind is considered exported.
                zone.exported_energy += surplus_wind
                transfer_records.append({
                    "from": zone.zone_id,
                    "to": None,
                    "amount": surplus_wind,
                    "hops": 1,
                    "type": "wind_export"
                })
                logger.debug(f"{zone_id}: Surplus wind {surplus_wind} MWh exported.")
            # Set remaining demand after wind usage.
            zone.remaining_demand = zone.demand_today - wind_used
    else:
        # If wind phase is disabled, the remaining demand is simply the total demand.
        for zone in zones.values():
            zone.remaining_demand = zone.demand_today
            # Added to ensure local consumption is set to zero when wind is disabled. Mulig feil
            zone.local_consumption = 0
            zone.wind_today = 0
            ######################

    # --- Phase 2: First Import Phase (Force export required) ---
    if phase_settings.get("enable_import_phase1", True):
        for zone in zones.values():
            if zone.remaining_demand > 0:
                # Only consider suppliers above their force-export threshold.
                import_from_neighbors(zones, connections, zone, logger, transfer_records,
                                      force_export_required=True,
                                      enable_two_hop=phase_settings.get("enable_two_hop", True))

    # --- Phase 3: Local Hydro Production ---
    if phase_settings.get("enable_local_hydro", True):
        for zone in zones.values():
            if zone.remaining_demand > 0:
                # Calculate the potential hydro energy from available water above hydro_min.
                potential_hydro = (zone.current_level - zone.hydro_min) * zone.hydro_efficiency
                # Limit production by maximum daily production capacity and remaining demand.
                local_hydro = min(zone.hydro_max_daily_production, potential_hydro, zone.remaining_demand) # legger inn ekstra begrensning for å unngå at det blir for mye
                zone.local_production += local_hydro
                zone.remaining_demand -= local_hydro
                logger.debug(f"{zone.zone_id}: Local hydro production {local_hydro} MWh used.")
                logger.debug(f"{zone.zone_id}: Hydro storage level after production {zone.current_level - local_hydro / zone.hydro_efficiency:.2f}.")
                if zone.current_level - local_hydro /zone.hydro_efficiency == zone.hydro_min:
                    logger.debug(f"{zone.zone_id}: Hydro storage level is at the minimum threshold (hydro_min).")

    # --- Phase 4: Second Import Phase (Include all suppliers with extra capacity) ---
    if phase_settings.get("enable_import_phase2", True):
        for zone in zones.values():
            if zone.remaining_demand > 0:
                # This phase does not enforce the force-export threshold.
                import_from_neighbors(zones, connections, zone, logger, transfer_records,
                                      force_export_required=False,
                                      enable_two_hop=phase_settings.get("enable_two_hop", True))

    # --- Phase 5: Record Unmet Demand ---
    for zone in zones.values():
        if zone.remaining_demand > 0:
            zone.unmet_demand += zone.remaining_demand
            logger.warning(f"{zone.zone_id}: Unmet demand {zone.remaining_demand} MWh.")
            zone.remaining_demand = 0

    
    return transfer_records
