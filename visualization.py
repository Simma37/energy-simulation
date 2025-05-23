# visualization.py
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import FancyArrowPatch
import numpy as np  # used for numeric operations like computing distances and offsets
from config import DISPLAY_MEDIAN_STORAGE_LEVELS
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap
import os  # required for file/directory manipulation
from cycler import cycler
import matplotlib.ticker as ticker  # used for formatting y-axis labels
import matplotlib.dates as mdates


# Enable LaTeX formatting for plots
plt.rc('text', usetex=True)
plt.rc('font', family='serif')
plt.rc('axes', labelsize=12)  # Larger font size for axis labels
plt.rc('xtick', labelsize=10)  # Larger font size for x-axis tick labels
plt.rc('ytick', labelsize=10)  # Larger font size for y-axis tick labels
plt.rc('legend', fontsize=10)  # Larger font size for legends
plt.rc('lines', linewidth=1)  # Thicker lines
plt.rc('lines', markersize=1)  # Larger markers
plt.rc('axes', prop_cycle=cycler(color=plt.cm.tab10.colors))  # Improved color palette


def set_figure_size(textwidth_pt, fraction):
    """Convert LaTeX textwidth in points to inches and return (width, height)."""
    inches_per_pt = 1 / 72.27
    golden_ratio = (5**.5 - 1) / 2  # Aesthetic ratio

    width_in = textwidth_pt * inches_per_pt * fraction
    height_in = textwidth_pt * inches_per_pt * golden_ratio
    print(f"Figure size in inches: {width_in:.2f} x {height_in:.2f}")
    return (width_in, height_in)


textwidth_pt = 358.50473  # LaTeX textwidth in points, adjust as needed
fraction = 1  # Scale for the figure size

figsize = set_figure_size(textwidth_pt, fraction)

# Hydro Storage Level
def plot_abs_storage_levels(simulator, output_file="storage_levels.pdf"):
    """
    Plot absolute hydro storage levels over time for all zones in a single chart.

    For each zone:
      - A line is plotted representing its absolute storage levels.
      - If DISPLAY_MEDIAN_STORAGE_LEVELS is True, target levels (if available) are plotted as dashed lines.
    
    The resulting plot is saved to the given output_file.
    """
    # Extract the simulation dates and zone identifiers from the simulation results.
    dates = [res["date"] for res in simulator.results]
    zone_ids = list(next(iter(simulator.results))["metrics"].keys())
    plt.figure(figsize=figsize)
    
    # Plot storage levels for each zone.
    for zone_id in zone_ids:
        # Build a mapping for zone color based on zone configuration.
        zoneColor = {zone_id: zone.zone_color for zone_id, zone in simulator.zones.items()}
        # Extract current storage level for this zone from each day's metrics.
        levels = [day["metrics"][zone_id]["current_level"] for day in simulator.results]
        plt.plot(dates, levels, color=zoneColor[zone_id], label=zone_id)

        if DISPLAY_MEDIAN_STORAGE_LEVELS:
            # Plot target (median) storage levels if available.
            try:
                target_levels = []
                # Loop through each simulation date and check for corresponding target level data.
                for date in dates:
                    if date in simulator.reservoir_fill_data and zone_id in simulator.reservoir_fill_data[date]:
                        target_levels.append(simulator.reservoir_fill_data[date][zone_id])
                    else:
                        # Append None to skip dates with missing data.
                        target_levels.append(None)
                
                # Filter out dates with no valid target level.
                valid_dates = []
                valid_levels = []
                for i, level in enumerate(target_levels):
                    if level is not None and level > 0:
                        valid_dates.append(dates[i])
                        valid_levels.append(level)
                
                # Only plot if there are valid target levels.
                if valid_dates:
                    plt.plot(valid_dates, valid_levels, linestyle='--', color=zoneColor[zone_id],
                             label=f"{zone_id} (Target)", alpha=0.7)
            except Exception as e:
                print(f"Could not plot target levels for {zone_id}: {e}")

    plt.xlabel("Month")
    plt.ylabel("Hydro Storage Level (MWh)/day")
    #plt.title("Daily Hydro Storage Levels")
    # if you have an Axes object:
    plt.legend()
    plt.grid()
    ax = plt.gca()
    # one tick every 3 months → 4 ticks per year
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    # show abbreviated month and full year
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()
# Hydro Storage Levels per zone
def plot_abs_storage_levels_per_zone(simulator, output_file="storage_levels.pdf"):
    """
    For each zone, plot its absolute hydro storage levels over time and save the plot 
    under a folder named after the zone. The output filename in each zone folder is prefixed by the zone name.
    
    If DISPLAY_MEDIAN_STORAGE_LEVELS is True, target levels are also plotted.
    """

    # Determine base directory and filename for saving plots.
    base_dir = os.path.dirname(output_file) if os.path.dirname(output_file) else "."
    base_filename = os.path.basename(output_file)

    if not simulator.results:
        print("No simulation results available.")
        return

    # Extract zone IDs and simulation dates.
    zones = list(next(iter(simulator.results))["metrics"].keys())
    dates = [res["date"] for res in simulator.results]

    for zone in zones:
        # Get current storage levels for the zone.
        levels = [day["metrics"].get(zone, {}).get("current_level", None) for day in simulator.results]
        zone_color = (simulator.zones[zone].zone_color 
                      if zone in simulator.zones and hasattr(simulator.zones[zone], "zone_color")
                      else "black")

        plt.figure(figsize=figsize)
        plt.plot(dates, levels, color=zone_color, label=zone)

        if DISPLAY_MEDIAN_STORAGE_LEVELS:
            target_levels = []
            # Iterate over dates to collect target levels for the zone.
            for date in dates:
                if date in simulator.reservoir_fill_data and zone in simulator.reservoir_fill_data[date]:
                    target_levels.append(simulator.reservoir_fill_data[date][zone])
                else:
                    target_levels.append(None)
            valid_dates = []
            valid_levels = []
            for i, lvl in enumerate(target_levels):
                if lvl is not None and lvl > 0:
                    valid_dates.append(dates[i])
                    valid_levels.append(lvl)
            if valid_dates:
                plt.plot(valid_dates, valid_levels, linestyle='--', color=zone_color,
                         label=f"{zone} (Target)", alpha=0.7)

        plt.xlabel("Month")
        ax = plt.gca()
        # one tick every 3 months → 4 ticks per year
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        # show abbreviated month and full year
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        plt.ylabel("Hydro Storage Level (MWh)/day")
        #plt.title(f"Absolute Hydro Storage Levels - Zone {zone}")
        plt.legend()

        # Save the plot in a dedicated subfolder for the zone.
        zone_dir = os.path.join(base_dir, zone)
        os.makedirs(zone_dir, exist_ok=True)
        zone_output_file = os.path.join(zone_dir, f"{zone}_{base_filename}")
        plt.grid()
        plt.savefig(zone_output_file, bbox_inches='tight')
        plt.close()
# Energy Exchange graph
def plot_energy_exchange_split_import_export(simulator, output_file="energy_exchange_split.pdf"):
    """
    Visualize aggregated energy transfers between zones using two subplots:
      - Left subplot: Direct (one-hop) transfers (drawn as straight blue arrows).
      - Right subplot: Two-hop transfers (drawn as curved red arrows).
    
    Energy transfer values are labeled (in GWh). Node positions are derived from zone coordinates.
    """
    # Separate transfer records into direct (one-hop) and two-hop categories.
    direct_edges = {}
    two_hop_edges = {}
    for record in simulator.transfer_records:
        if record.get("to") is None:  # skip wind export records that don't target a specific zone
            continue
        key = (record["from"], record["to"])
        hops = record.get("hops", 1)
        if hops == 1:
            direct_edges[key] = direct_edges.get(key, 0) + record["amount"]
        elif hops == 2:
            two_hop_edges[key] = two_hop_edges.get(key, 0) + record["amount"]

    # Retrieve node positions from zones' coordinates.
    pos = {zone_id: zone.coordinates for zone_id, zone in simulator.zones.items()}
    
    # Create the figure with two subplots (side-by-side).
    fig, (ax_direct, ax_twohop) = plt.subplots(1, 2, figsize=figsize)
    
    # Create a directed graph to draw nodes and labels on both subplots.
    G = nx.DiGraph()
    for zone_id in simulator.zones.keys():
        G.add_node(zone_id)
    
    # Draw nodes and labels on both subplots.
    for ax in (ax_direct, ax_twohop):
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color='lightblue', node_size=1500)
        nx.draw_networkx_labels(G, pos, ax=ax)
        ax.axis('off')
    
    offset_distance = 10  # base offset (in points) for arrow labels
    multiplier = 1.5      # multiplier for offset adjustment

    # --- Left Subplot: Direct transfers ---
    for (src, dest), amount in direct_edges.items():
        # Draw a straight arrow for the direct transfer.
        arrow = FancyArrowPatch(pos[src], pos[dest],
                                arrowstyle='-|>', mutation_scale=20,
                                color='blue', linewidth=2,
                                connectionstyle="arc3,rad=0.0")
        ax_direct.add_patch(arrow)
        # Calculate midpoint and determine an offset for the label.
        mid = ((pos[src][0] + pos[dest][0]) / 2, (pos[src][1] + pos[dest][1]) / 2)
        dx = pos[dest][0] - pos[src][0]
        dy = pos[dest][1] - pos[src][1]
        norm = np.hypot(dx, dy)
        if norm == 0:
            offset = (5, 5)
        else:
            offset = (-dy/norm * offset_distance, dx/norm * offset_distance)
        effective_offset = (offset[0]*multiplier, offset[1]*multiplier) if not (src == "NO5" and dest == "NO1") else offset
        label = f"{(amount/1e3):.0f} GWh"
        angle = np.degrees(np.arctan2(dy, dx))
        if angle > 90 or angle < -90:
            angle += 180
        ax_direct.annotate(label, xy=mid, xytext=effective_offset, textcoords='offset points',
                           color='blue', fontsize=10, ha="center", va="center",
                           rotation=angle, rotation_mode='anchor', zorder=5)
    ax_direct.set_title("Direct (One-Hop) Energy Transfers")
    
    # --- Right Subplot: Two-Hop transfers ---
    for (src, dest), amount in two_hop_edges.items():
        arrow = FancyArrowPatch(pos[src], pos[dest],
                                arrowstyle='-|>', mutation_scale=20,
                                color='red', linewidth=2,
                                connectionstyle="arc3,rad=0.0")
        ax_twohop.add_patch(arrow)
        mid = ((pos[src][0] + pos[dest][0]) / 2, (pos[src][1] + pos[dest][1]) / 2)
        dx = pos[dest][0] - pos[src][0]
        dy = pos[dest][1] - pos[src][1]
        norm = np.hypot(dx, dy)
        if norm == 0:
            offset = (5, 5)
        else:
            offset = (-dy/norm * offset_distance, dx/norm * offset_distance)
        effective_offset = (offset[0]*multiplier, offset[1]*multiplier) if not (src == "NO5" and dest == "NO1") else offset
        label = f"{(amount/1e3):.0f} GWh"
        angle = np.degrees(np.arctan2(dy, dx))
        if angle > 90 or angle < -90:
            angle += 180
        ax_twohop.annotate(label, xy=mid, xytext=effective_offset, textcoords='offset points',
                           color='red', fontsize=10, ha="center", va="center",
                           rotation=angle, rotation_mode='anchor', zorder=5)
    ax_twohop.set_title("Two-Hop Energy Transfers")
    
    plt.tight_layout()
    plt.grid()
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()
# Energy Exchange Graph (Brukes ikke?)
def plot_energy_exchange(simulator, output_file="energy_exchange.pdf"):
    """
    Create a directed network visualization showing aggregated energy transfers between zones.
    
    - Direct (one-hop) transfers are drawn as solid blue lines.
    - Two-hop transfers are drawn as dashed red lines.
    
    Node positions are determined by the zones' coordinates.
    Energy transfer labels (in GWh) are added on the edges.
    
    Assumes simulator.transfer_records is a list of dictionaries with:
        "from", "to", "amount", and "hops" keys.
    """
    # Separate records into direct and two-hop transfers.
    direct_edges = {}
    two_hop_edges = {}
    for record in simulator.transfer_records:
        key = (record["from"], record["to"])
        hops = record.get("hops", 1)
        if hops == 1:
            direct_edges[key] = direct_edges.get(key, 0) + record["amount"]
        elif hops == 2:
            two_hop_edges[key] = two_hop_edges.get(key, 0) + record["amount"]
    
    # Build a directed graph with node positions.
    G = nx.DiGraph()
    for zone_id, zone in simulator.zones.items():
        G.add_node(zone_id)
    pos = {zone_id: zone.coordinates for zone_id, zone in simulator.zones.items()}
    
    plt.figure(figsize=figsize)
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=1500)
    nx.draw_networkx_labels(G, pos)
    
    # Draw direct transfers as solid blue edges.
    for (src, dest), amount in direct_edges.items():
        nx.draw_networkx_edges(
            G, pos,
            edgelist=[(src, dest)],
            width=2,
            edge_color='blue',
            style='solid',
            arrows=True,
            arrowsize=20
        )
    # Draw two-hop transfers as dashed red edges.
    for (src, dest), amount in two_hop_edges.items():
        nx.draw_networkx_edges(
            G, pos,
            edgelist=[(src, dest)],
            width=2,
            edge_color='red',
            style='dashed',
            arrows=True,
            arrowsize=20
        )
    
    # Combine edge labels from both sets and convert amounts to GWh.
    edge_labels = {(src, dest): f"{(amount/1e3):.0f} GWh" 
                   for (src, dest), amount in {**direct_edges, **two_hop_edges}.items()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    
    plt.grid()
    #plt.title("Aggregated Energy Exchange Between Zones")
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()
# Hydro Storage Level Relative
def plot_storage_levels(simulator, output_file="storage_levels.pdf"):
    """
    Plot the daily relative hydro storage levels for all zones on a single chart.
    
    The relative storage is computed as:
        ((current_level - hydro_min) / (hydro_max - hydro_min)) * 100.
    
    If DISPLAY_MEDIAN_STORAGE_LEVELS is enabled, target levels are shown as dashed lines.
    """
    dates = [res["date"] for res in simulator.results]
    zone_ids = list(next(iter(simulator.results))["metrics"].keys())
    zoneColor = {zone_id: zone.zone_color for zone_id, zone in simulator.zones.items()}
    plt.figure(figsize=figsize)
    
    for zone_id in zone_ids:
        relative_levels = []
        # Compute the relative storage level for each day.
        for day in simulator.results:
            current = day["metrics"][zone_id]["current_level"]
            zone = simulator.zones[zone_id]
            relative = ((current - zone.hydro_min) / (zone.hydro_max - zone.hydro_min)) * 100
            relative_levels.append(relative)
        plt.plot(dates, relative_levels, color=zoneColor[zone_id], label=zone_id)

        if DISPLAY_MEDIAN_STORAGE_LEVELS:
            try:
                target_levels = []
                for date in dates:
                    if date in simulator.reservoir_fill_data and zone_id in simulator.reservoir_fill_data[date]:
                        # Compute relative target level.
                        target_levels.append(((simulator.reservoir_fill_data[date][zone_id] - zone.hydro_min) 
                                              / (zone.hydro_max - zone.hydro_min)) * 100)
                    else:
                        target_levels.append(None)
                
                valid_dates = []
                valid_levels = []
                for i, level in enumerate(target_levels):
                    if level is not None and level > 0:
                        valid_dates.append(dates[i])
                        valid_levels.append(level)
                
                if valid_dates:
                    plt.plot(valid_dates, valid_levels, linestyle='--', color=zoneColor[zone_id],
                             label=f"{zone_id} (Target)", alpha=0.7)
            except Exception as e:
                print(f"Could not plot target levels for {zone_id}: {e}")

    plt.xlabel("Month")
    ax = plt.gca()
    # one tick every 3 months → 4 ticks per year
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    # show abbreviated month and full year
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.ylabel("Relative Hydro Storage (\%)/day")
    #plt.title("Daily Relative Hydro Storage Levels")
    plt.grid()
    plt.legend()
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()
# Hydro Storage Level Relative per zone (Brukes ikke)
def plot_storage_levels_per_zone(simulator, output_file="storage_levels_relative.pdf"):
    """
    For each zone, plot the daily relative hydro storage levels as a line chart.
    
    The relative storage is calculated as:
         ((current_level - hydro_min) / (hydro_max - hydro_min)) * 100.
    
    Each zone's plot is saved in a folder named after the zone, with the zone name prefixed to the output filename.
    """
    import os
    import matplotlib.pyplot as plt

    base_dir = os.path.dirname(output_file) if os.path.dirname(output_file) else "."
    base_filename = os.path.basename(output_file)

    if not simulator.results:
        print("No simulation results available.")
        return

    zones = list(next(iter(simulator.results))["metrics"].keys())
    dates = [res["date"] for res in simulator.results]

    for zone in zones:
        levels = [day["metrics"].get(zone, {}).get("current_level", None) for day in simulator.results]
        if zone not in simulator.zones:
            print(f"Zone {zone} not found in simulator.zones.")
            continue
        zone_obj = simulator.zones[zone]
        zone_color = zone_obj.zone_color if hasattr(zone_obj, "zone_color") else "black"

        relative_levels = []
        for lvl in levels:
            if lvl is None:
                relative_levels.append(None)
            else:
                relative = ((lvl - zone_obj.hydro_min) / (zone_obj.hydro_max - zone_obj.hydro_min)) * 100
                relative_levels.append(relative)

        plt.figure(figsize=figsize)
        plt.plot(dates, relative_levels, color=zone_color, label=zone)

        if DISPLAY_MEDIAN_STORAGE_LEVELS:
            target_levels = []
            for date in dates:
                if date in simulator.reservoir_fill_data and zone in simulator.reservoir_fill_data[date]:
                    target = simulator.reservoir_fill_data[date][zone]
                    target_relative = ((target - zone_obj.hydro_min) / (zone_obj.hydro_max - zone_obj.hydro_min)) * 100
                    target_levels.append(target_relative)
                else:
                    target_levels.append(None)
            valid_dates = []
            valid_targets = []
            for i, t in enumerate(target_levels):
                if t is not None and t > 0:
                    valid_dates.append(dates[i])
                    valid_targets.append(t)
            if valid_dates:
                plt.plot(valid_dates, valid_targets, linestyle='--', color=zone_color,
                         label=f"{zone} (Target)", alpha=0.7)

        plt.xlabel("Date")
        plt.ylabel("Relative Hydro Storage (%)")
        #plt.title(f"Relative Hydro Storage Levels - Zone {zone}")
        plt.legend()

        zone_dir = os.path.join(base_dir, zone)
        os.makedirs(zone_dir, exist_ok=True)
        zone_output_file = os.path.join(zone_dir, f"{zone}_{base_filename}")
        plt.grid()
        plt.savefig(zone_output_file, bbox_inches='tight')
        plt.close()

# Energy Flows Summary Bar Chart
def plot_energy_flows_summary(simulator, output_file="energy_flows_summary.pdf"):
    """
    Aggregate daily energy flow metrics (local hydro production, imported energy, exported energy) 
    for each zone and display them as a stacked bar chart.
    
    The x-axis represents zones, while the y-axis shows energy (in MWh). 
    """
    # Get zone identifiers.
    zone_ids = list(simulator.zones.keys())
    
    # Initialize aggregation per zone.
    aggregated = {z: {"wind":0, "local": 0, "imported": 0, "exported": 0} for z in zone_ids}
    
    # Sum energy flows for each simulation day.
    for day_result in simulator.results:
        metrics = day_result.get("metrics", {})
        for zone_id in zone_ids:
            aggregated[zone_id]["wind"] += metrics[zone_id].get("wind", 0)
            aggregated[zone_id]["local"] += metrics[zone_id].get("local_production", 0)
            aggregated[zone_id]["imported"] += metrics[zone_id].get("imported", 0)
            aggregated[zone_id]["exported"] += metrics[zone_id].get("exported", 0)
    
    # Prepare data for plotting.
    wind_vals = [aggregated[z]["wind"] for z in zone_ids]
    local_vals = [aggregated[z]["local"] for z in zone_ids]
    imported_vals = [aggregated[z]["imported"] for z in zone_ids]
    exported_vals = [aggregated[z]["exported"] for z in zone_ids]
    
    x = range(len(zone_ids))
    plt.figure(figsize=figsize)

    # Stack bars properly using bottom parameter with consistent colors
    plt.bar(x, wind_vals, label="Local Wind Production", color="skyblue")
    plt.bar(x, local_vals, bottom=wind_vals, label="Local Hydro Production", color="darkblue")
    plt.bar(x, imported_vals, bottom=[w+l for w,l in zip(wind_vals, local_vals)], 
            label="Imported Energy", color="green")
    plt.bar(x, exported_vals, 
            bottom=[w+l+i for w,l,i in zip(wind_vals, local_vals, imported_vals)], 
            label="Exported Energy", color="darkgray")
    
    plt.xticks(x, zone_ids)
    plt.ylabel("Total Energy (MWh)/year")
    #plt.title("Aggregated Energy Flows per Zone")
    plt.legend()
    plt.savefig(output_file)
    plt.close()
# Daily Energy Components Area Chart
def plot_daily_energy_components(simulator, output_file="daily_components.pdf"):
    """
    Plot daily energy components as a stacked area chart with the total demand shown as a line.
    
    Components include wind, local hydro, imports, and unmet demand.
    """
    # Ensure results are sorted by date.
    results = sorted(simulator.results, key=lambda r: r["date"])
    dates = [r["date"] for r in results]
    summary = [r["summary"] for r in results]
    
    total_demand = [s["demand"] for s in summary]
    wind_used = [s["wind"] for s in summary]
    imports = [s["import"] for s in summary]
    local_hydro = [s["local_hydro"] for s in summary]
    unmet = [s["unmet"] for s in summary]

    plt.figure(figsize=figsize)
    plt.stackplot(dates, 
                  wind_used, local_hydro, imports, unmet,
                  labels=["Wind", "Local Hydro", "Import", "Unmet"],
                  colors=["skyblue", "darkblue", "green", "red"])
    # Overlay the total demand as a black line.
    plt.plot(dates, total_demand, color="black", label="Total Demand", linewidth=2)
    plt.xlabel("Month")
    ax = plt.gca()
    # one tick every 3 months → 4 ticks per year
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    # show abbreviated month and full year
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.ylabel("Energy (MWh)/day")

# Format the y-axis to use scientific notation
    ax = plt.gca()
    ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))    

    #plt.title("Daily Energy Components vs Total Demand")
    plt.legend(loc="upper right")
    plt.grid()
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()
# Daily Energy Components Area Chart per zone
def plot_daily_energy_components_per_zone(simulator, output_file="daily_components.pdf"):
    """
    For each zone, generate a stacked area chart of daily energy components and save it in a zone-specific folder.
    
    The chart shows wind, local production, imported energy, and unmet demand, with total demand as a line.
    The output filename is prefixed with the zone name.
    """
    import os
    import matplotlib.pyplot as plt

    base_dir = os.path.dirname(output_file) if os.path.dirname(output_file) else "."
    base_filename = os.path.basename(output_file)
    
    if not simulator.results:
        print("No simulation results available.")
        return
    zones = list(next(iter(simulator.results))["metrics"].keys())
    results = sorted(simulator.results, key=lambda r: r["date"])
    
    for zone in zones:
        dates = [r["date"] for r in results]
        demand = [r["metrics"].get(zone, {}).get("demand", 0) for r in results]
        wind = [r["metrics"].get(zone, {}).get("wind", 0) for r in results]
        local_prod = [r["metrics"].get(zone, {}).get("local_production", 0) for r in results]
        imported = [r["metrics"].get(zone, {}).get("imported", 0) for r in results]
        unmet = [r["metrics"].get(zone, {}).get("unmet", 0) for r in results]
        
        
        plt.figure(figsize=figsize)
        plt.stackplot(dates, 
                      wind, local_prod, imported, unmet,
                      labels=["Wind", "Local Production", "Imported", "Unmet"],
                      colors=["skyblue", "darkblue", "green", "red"])
        plt.plot(dates, demand, color="black", label="Total Demand", linewidth=2)
        plt.xlabel("Month")
        ax = plt.gca()
        # one tick every 3 months → 4 ticks per year
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        # show abbreviated month and full year
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        plt.ylabel("Energy (MWh)/day")
        # Format the y-axis to use scientific notation
        ax = plt.gca()
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
        ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        #plt.title(f"Daily Energy Components vs Total Demand - Zone {zone}")
        plt.legend(loc="upper left")
        plt.grid()
        
        zone_dir = os.path.join(base_dir, zone)
        os.makedirs(zone_dir, exist_ok=True)
        zone_output_file = os.path.join(zone_dir, f"{zone}_{base_filename}")
        plt.savefig(zone_output_file, bbox_inches='tight')
        plt.close()