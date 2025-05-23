# reporting.py
import pandas as pd
from config import ENABLE_TWO_HOP
from dash import html, dash_table

def format_energy(value):
    """
    Format energy values consistently with thousand separators and no decimals,
    appending the unit 'MWh'.

    Parameters:
      value (float): Energy value in MWh.

    Returns:
      str: Formatted energy (e.g., "1,234 MWh").
    """
    return f"{value:,.0f} MWh"

def format_percentage(value):
    """
    Format percentage values consistently with 2 decimal places followed by a '%'.

    Parameters:
      value (float): Percentage value to format.

    Returns:
      str: Formatted percentage (e.g., "12.34%").
    """
    return f"{value:.2f}%"

def create_import_export_table(simulator):
    """
    Create and return two pandas DataFrames showing aggregated energy transfers.

    Aggregates:
      - Primary transfers (one-hop): Direct energy transfers among neighbors.
      - Secondary transfers (two-hop): Indirect transfers via a transit zone (if ENABLE_TWO_HOP is True).

    Energy amounts are rounded to whole numbers (MWh).

    Parameters:
      simulator: A simulator object that contains transfer_records.

    Returns:
      Tuple: (primary, secondary)
        primary (DataFrame): Aggregated one-hop energy transfers.
        secondary (DataFrame or None): Aggregated two-hop energy transfers, or None if not applicable.
    """
    records = simulator.transfer_records
    if not records:
        print("No transfer records found.")
        return None, None
    
    # Create a DataFrame from the transfer records.
    df = pd.DataFrame(records)
    # Group by 'from', 'to', and 'hops' to sum the energy transferred among each pair.
    grouped = df.groupby(["from", "to", "hops"], as_index=False).sum()
    
    # Round the energy transfer amounts for consistency.
    grouped["amount"] = grouped["amount"].round(0).astype(int)
    
    # Extract primary (one-hop) transfers.
    primary = grouped[grouped["hops"] == 1][["from", "to", "amount"]].copy()
    
    secondary = None
    # If two-hop transfers are enabled, group additionally by 'transit_zone'
    if ENABLE_TWO_HOP:
        grouped_transit = df.groupby(["from", "to", "hops", "transit_zone"], as_index=False).sum()
        grouped_transit["amount"] = grouped_transit["amount"].round(0).astype(int)
        secondary = grouped_transit[grouped_transit["hops"] == 2][["from", "to", "transit_zone", "amount"]].copy()
    
    # Format the energy values for display.
    primary["Total Energy"] = primary["amount"].apply(format_energy)
    if secondary is not None:
        secondary["Total Energy"] = secondary["amount"].apply(format_energy)
    
    # Rename columns for clarity.
    primary = primary[["from", "to", "Total Energy"]]
    primary.rename(columns={"from": "From", "to": "To"}, inplace=True)
    
    if secondary is not None:
        secondary = secondary[["from", "to", "transit_zone", "Total Energy"]]
        secondary.rename(columns={"from": "From", "to": "To", "transit_zone": "Transit"}, inplace=True)
    
    return primary, secondary

def print_simulation_summary(simulator):
    """
    Print a comprehensive summary of the simulation metrics.

    This summary includes:
      - Zone totals aggregated across the simulation period.
      - Percentages for key metrics relative to demand.
      - System-wide totals.
      - Detailed energy transfer statistics.
      - Changes in hydro storage levels from the initial to the final simulation day.

    Parameters:
      simulator: A simulator object containing simulation results and zone information.
    """
    # Collect all unique metric keys across simulation results.
    all_metrics = set()
    for day_result in simulator.results:
        for zone_id, metrics in day_result["metrics"].items():
            all_metrics.update(metrics.keys())
    
    # Aggregate metrics by zone.
    zone_metrics = {}
    for day_result in simulator.results:
        for zone_id, metrics in day_result["metrics"].items():
            if zone_id not in zone_metrics:
                zone_metrics[zone_id] = {metric: 0 for metric in all_metrics}
                zone_metrics[zone_id]["days"] = 0
            # Sum each day's metric values.
            for metric, value in metrics.items():
                zone_metrics[zone_id][metric] += value
            zone_metrics[zone_id]["days"] += 1
    
    # Calculate system-wide totals by summing over zones.
    system_totals = {metric: 0 for metric in all_metrics}
    system_totals["days"] = 0 if not zone_metrics else list(zone_metrics.values())[0]["days"]
    
    for zone_data in zone_metrics.values():
        for metric, value in zone_data.items():
            if metric != "days":
                system_totals[metric] += value
    
    # Print the simulation summary header.
    print("\n===== SIMULATION SUMMARY =====")
    print(f"Total simulation period: {system_totals['days']} days")
    
    # --- Zone Metrics Totals ---
    print("\n----- ZONE METRICS (TOTALS) -----")
    df_data = []
    for zone_id, metrics in zone_metrics.items():
        row = {"Zone": zone_id}
        for metric in sorted(all_metrics):
            # Skip non-cumulative metrics like 'current_level'.
            if metric != "current_level":
                value = metrics.get(metric, 0)
                # Format only selected metrics.
                if ("demand" in metric.lower() or "production" in metric.lower() or "wind" in metric.lower() or 
                    "imported" in metric.lower() or "exported" in metric.lower() or "spill" in metric.lower()):
                    row[metric] = format_energy(value)
        df_data.append(row)
    
    metrics_df = pd.DataFrame(df_data)
    print(metrics_df.to_string(index=False))
    
    # --- Zone Metrics Percentages ---
    print("\n----- ZONE METRICS (PERCENTAGES) -----")
    pct_data = []
    for zone_id, metrics in zone_metrics.items():
        row = {"Zone": zone_id}
        if "demand" in metrics and metrics["demand"] > 0:
            if "unmet_demand" in metrics:
                row["Unmet Demand %"] = format_percentage((metrics['unmet_demand'] / metrics['demand']) * 100)
            if "local_production" in metrics:
                row["Local Production %"] = format_percentage((metrics['local_production'] / metrics['demand']) * 100)
            if "wind" in metrics:
                row["Wind %"] = format_percentage((metrics['wind'] / metrics['demand']) * 100)
            if "imported" in metrics:
                row["Imported Energy %"] = format_percentage((metrics['imported'] / metrics['demand']) * 100)
            if "exported" in metrics and "local_production" in metrics and metrics['local_production'] > 0:
                row["Exported/Produced %"] = format_percentage((metrics['exported'] / metrics['local_production']) * 100)
            if "spill" in metrics:
                row["Spill %"] = format_percentage((metrics['spill'] / metrics['demand']) * 100)
        pct_data.append(row)
    
    pct_df = pd.DataFrame(pct_data)
    print(pct_df.to_string(index=False))
    
    # --- System Totals ---
    print("\n----- SYSTEM TOTALS -----")
    for metric in sorted(all_metrics):
        if metric != "current_level" and (
            "demand" in metric.lower() or "production" in metric.lower() or "wind" in metric.lower() or
            "imported" in metric.lower() or "exported" in metric.lower() or "spill" in metric.lower()):
            value = system_totals.get(metric, 0)
            print(f"{metric}: {format_energy(value)}")
    
    # --- Energy Transfers ---
    print("\n----- ENERGY TRANSFERS -----")
    primary, secondary = create_import_export_table(simulator)
    if primary is not None:
        print("Primary (One-Hop) Energy Transfers:")
        print(primary.to_string(index=False))
    if secondary is not None:
        print("\nSecondary (Two-Hop) Energy Transfers:")
        print(secondary.to_string(index=False))
    
    # --- Storage Level Changes ---
    print("\n----- STORAGE LEVEL CHANGES -----")
    if simulator.results:
        initial_day = simulator.results[0]
        final_day = simulator.results[-1]
        storage_changes = []
        # Calculate change in storage for each zone.
        for zone_id in simulator.zones.keys():
            initial_level = initial_day["metrics"].get(zone_id, {}).get("current_level")
            final_level = final_day["metrics"].get(zone_id, {}).get("current_level")
            if initial_level is not None and final_level is not None:
                change = final_level - initial_level
                change_str = "increased" if change > 0 else "decreased" if change < 0 else "unchanged"
                storage_changes.append({
                    "Zone": zone_id,
                    "Initial Storage": format_energy(initial_level),
                    "Final Storage": format_energy(final_level),
                    "Change": f"{format_energy(change)} ({change_str})"
                })
        
        # Add totals row if there are any records
        if storage_changes:
            # Calculate totals using raw values
            total_initial = sum(initial_day["metrics"].get(zone_id, {}).get("current_level", 0) or 0 
                               for zone_id in simulator.zones.keys())
            total_final = sum(final_day["metrics"].get(zone_id, {}).get("current_level", 0) or 0 
                             for zone_id in simulator.zones.keys())
            total_change = total_final - total_initial
            change_str = "increased" if total_change > 0 else "decreased" if total_change < 0 else "unchanged"
            
            storage_changes.append({
                "Zone": "TOTAL",
                "Initial Storage": format_energy(total_initial),
                "Final Storage": format_energy(total_final),
                "Change": f"{format_energy(total_change)} ({change_str})"
            })
        
        if storage_changes:
            df_storage = pd.DataFrame(storage_changes)
            print(df_storage.to_string(index=False))
        else:
            print("No storage level data available.")
    else:
        print("No simulation results available.")

def generate_simulation_summary_html(simulator):
    """
    Generate HTML components presenting a comprehensive simulation summary.

    Returns a list of Dash HTML components (tables and text).
    This function is broken into several sections:
      1. Aggregation of daily metrics into zone totals and system totals.
      2. Construction of DataFrames for Zone Metrics Totals and Percentages.
      3. Construction of a DataFrame showing Storage Level Changes.
      4. Inclusion of Energy Transfers tables (optional).

    If an error occurs in one section, it is caught to allow the rest of the summary to render.
    """
    summary_components = []
    summary_components.append(html.H3("SIMULATION SUMMARY"))
    
    try:
        # ----- Aggregate Metrics Across Simulator Results -----
        all_metrics = set()
        for day_result in simulator.results:
            for zone_id, metrics in day_result["metrics"].items():
                all_metrics.update(metrics.keys())
                
        zone_metrics = {}
        for day_result in simulator.results:
            for zone_id, metrics in day_result["metrics"].items():
                if zone_id not in zone_metrics:
                    zone_metrics[zone_id] = {metric: 0 for metric in all_metrics}
                    zone_metrics[zone_id]["days"] = 0
                for metric, value in metrics.items():
                    zone_metrics[zone_id][metric] += value
                zone_metrics[zone_id]["days"] += 1

        system_totals = {metric: 0 for metric in all_metrics}
        system_totals["days"] = 0 if not zone_metrics else list(zone_metrics.values())[0]["days"]
        for zone_data in zone_metrics.values():
            for metric, value in zone_data.items():
                if metric != "days":
                    system_totals[metric] += value
                    
        summary_components.append(html.P(f"Total simulation period: {system_totals.get('days', 0)} days"))
    except Exception as e:
        summary_components.append(html.P(f"Error aggregating metrics: {e}"))

    # ----- Zone Metrics Totals -----
    try:
        zone_rows = []
        for zone_id, metrics in zone_metrics.items():
            row = {"Zone": zone_id}
            for metric in sorted(all_metrics):
                if metric != "current_level":
                    # Format only selected metrics.
                    if any(k in metric.lower() for k in ["demand", "production", "wind", "imported", "exported", "spill"]):
                        row[metric] = f"{metrics.get(metric, 0):,.0f} MWh"
            zone_rows.append(row)
        metrics_df = pd.DataFrame(zone_rows)
        summary_components.append(html.H4("Zone Metrics (Totals)"))
        summary_components.append(
            dash_table.DataTable(
                data=metrics_df.to_dict("records"),
                columns=[{"name": col, "id": col} for col in metrics_df.columns],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'center'}
            )
        )
    except Exception as e:
        summary_components.append(html.P(f"Error creating Zone Metrics Totals: {e}"))

    # ----- Zone Metrics Percentages -----
    try:
        pct_rows = []
        for zone_id, metrics in zone_metrics.items():
            row = {"Zone": zone_id}
            if "demand" in metrics and metrics["demand"] > 0:
                if "unmet_demand" in metrics:
                    row["Unmet Demand %"] = f"{(metrics['unmet_demand']/metrics['demand']*100):.2f}%"
                if "local_production" in metrics:
                    row["Local Production %"] = f"{(metrics['local_production']/metrics['demand']*100):.2f}%"
                if "wind" in metrics:
                    row["Wind %"] = f"{(metrics['wind']/metrics['demand']*100):.2f}%"
                if "imported" in metrics:
                    row["Imported Energy %"] = f"{(metrics['imported']/metrics['demand']*100):.2f}%"
                if "exported" in metrics and metrics.get("local_production", 0) > 0:
                    row["Exported/Produced %"] = f"{(metrics['exported']/metrics['local_production']*100):.2f}%"
                if "spill" in metrics:
                    row["Spill %"] = f"{(metrics['spill']/metrics['demand']*100):.2f}%"
            pct_rows.append(row)
        pct_df = pd.DataFrame(pct_rows)
        summary_components.append(html.H4("Zone Metrics (Percentages)"))
        summary_components.append(
            dash_table.DataTable(
                data=pct_df.to_dict("records"),
                columns=[{"name": col, "id": col} for col in pct_df.columns],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'center'}
            )
        )
    except Exception as e:
        summary_components.append(html.P(f"Error creating Zone Metrics Percentages: {e}"))

    # ----- Storage Level Changes -----
    try:
        if simulator.results:
            initial_day = simulator.results[0]
            final_day = simulator.results[-1]
            storage_rows = []
            for zone_id in simulator.zones.keys():
                initial_level = initial_day["metrics"].get(zone_id, {}).get("current_level")
                final_level = final_day["metrics"].get(zone_id, {}).get("current_level")
                if initial_level is not None and final_level is not None:
                    change = final_level - initial_level
                    change_str = "increased" if change > 0 else "decreased" if change < 0 else "unchanged"
                    storage_rows.append({
                        "Zone": zone_id,
                        "Initial Storage": f"{initial_level:,.0f} MWh",
                        "Final Storage": f"{final_level:,.0f} MWh",
                        "Change": f"{change:,.0f} MWh ({change_str})"
                    })
            storage_df = pd.DataFrame(storage_rows)
        else:
            storage_df = pd.DataFrame()
        summary_components.append(html.H4("Storage Level Changes"))
        if not storage_df.empty:
            summary_components.append(
                dash_table.DataTable(
                    data=storage_df.to_dict("records"),
                    columns=[{"name": col, "id": col} for col in storage_df.columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'center'}
                )
            )
        else:
            summary_components.append(html.P("No storage level data available."))
    except Exception as e:
        summary_components.append(html.P(f"Error processing Storage Level Changes: {e}"))

    # ----- Energy Transfers -----
    try:
        primary, secondary = create_import_export_table(simulator)
        summary_components.append(html.H4("Energy Transfers"))
        if primary is not None:
            summary_components.append(html.P("Primary (One-Hop) Transfers:"))
            primary_str = primary.to_string(index=False)
            summary_components.append(html.Pre(primary_str, style={'whiteSpace': 'pre-wrap'}))
        else:
            summary_components.append(html.P("No Primary transfer records available."))
        if secondary is not None:
            summary_components.append(html.P("Secondary (Two-Hop) Transfers:"))
            secondary_str = secondary.to_string(index=False)
            summary_components.append(html.Pre(secondary_str, style={'whiteSpace': 'pre-wrap'}))
        else:
            summary_components.append(html.P("No Secondary transfer records available."))
    except Exception as e:
        summary_components.append(html.P(f"Error processing Energy Transfers: {e}"))

    return summary_components