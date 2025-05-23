# data_handler.py
import os
import datetime
import pandas as pd
import logging
from config import DATAFILE_CONSUMPTION_UNIT, DATAFILE_EFFECTIVE_INFLOW_UNIT, DATAFILE_RESERVOIR_FILL_LEVEL_UNIT, DATAFILE_WIND_PRODUCTION_UNIT, AVERAGE_INFLOW

def verify_data_files(base_dir):
    """
    Check if all required input CSV files exist in the given base directory.

    For each zone (NO1 to NO5) the following files are expected:
      - input/<zone>_Wind_Production.csv
      - input/<zone>_Consumption.csv
      - input/<zone>_Effective_Inflow.csv

    Parameters:
      base_dir (str): Base directory path where the 'input' folder is located.

    Returns:
      bool: True if all required files are found; False otherwise.
    """
    required_files = []
    # Add required file names for each zone.
    for zone in ["NO1", "NO2", "NO3", "NO4", "NO5"]:
        required_files.append(f"input/{zone}_Wind_Production.csv")
        required_files.append(f"input/{zone}_Consumption.csv")
        required_files.append(f"input/{zone}_Effective_Inflow.csv")
    
    all_files_found = True
    # Check existence of each required file.
    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if not os.path.exists(full_path):
            logging.warning(f"Missing required file: {file_path}")
            all_files_found = False
    return all_files_found

def load_zone_data(zone_id, base_dir, start_date, end_date):
    """
    Load time series data for a given zone from CSV files.

    Four categories of data are loaded:
      - wind: Wind production in MWh.
      - inflow: Effective hydro inflow.
      - demand: Consumption data converted to Wh.
      - resfill: Reservoir fill level data (if available).

    The time series is generated for each day between start_date and end_date.

    Parameters:
      zone_id (str): Identifier of the zone (e.g., "NO1").
      base_dir (str): Base directory where the 'input' folder is located.
      start_date (date): Start date of the simulation.
      end_date (date): End date of the simulation.

    Returns:
      dict: A dictionary with keys 'wind', 'inflow', 'demand', and 'resfill'. 
            Each value is a pandas Series indexed by date.
    """
    data = {'wind': None, 'inflow': None, 'demand': None, 'resfill': None}
    days = (end_date - start_date).days + 1
    # Generate a list of dates covering the entire simulation period.
    date_range = [start_date + datetime.timedelta(days=i) for i in range(days)]
    
    # -------------------
    # Load Wind Production
    # -------------------
    try:
        wind_file = os.path.join(base_dir, f"input/{zone_id}_Wind_Production.csv")
        if os.path.exists(wind_file):
            # Read CSV file and convert date column ('Dato_Id') to datetime.
            wind_df = pd.read_csv(wind_file)
            wind_df['Dato_Id'] = pd.to_datetime(wind_df['Dato_Id'])
            # Filter rows within the simulation period.
            wind_df = wind_df[(wind_df['Dato_Id'] >= pd.Timestamp(start_date)) &
                              (wind_df['Dato_Id'] <= pd.Timestamp(end_date))]
            # Build a dictionary of date -> production value.
            wind_dict = {row['Dato_Id'].date(): row['Produksjon [MWh]']  * DATAFILE_WIND_PRODUCTION_UNIT for _, row in wind_df.iterrows()}
            # Prepare a list of wind values for each day in the date_range.
            wind_values = [wind_dict.get(dt, 0.0) for dt in date_range]
            data['wind'] = pd.Series(wind_values, index=date_range)
        else:
            # If file missing, create a series with zero wind production.
            data['wind'] = pd.Series([0.0]*days, index=date_range)
    except Exception as e:
        logging.error(f"Error loading wind data for {zone_id}: {str(e)}")
        data['wind'] = pd.Series([0.0]*days, index=date_range)

    # -------------------
    # Load Consumption Data
    # -------------------
    try:
        cons_file = os.path.join(base_dir, f"input/{zone_id}_Consumption.csv")
        if os.path.exists(cons_file):
            cons_df = pd.read_csv(cons_file)
            if 'Date' in cons_df.columns:
                # Convert 'Date' column to timestamps.
                cons_df['Date'] = pd.to_datetime(cons_df['Date'])
                cons_df = cons_df[(cons_df['Date'] >= pd.Timestamp(start_date)) &
                                  (cons_df['Date'] <= pd.Timestamp(end_date))]
                # Convert consumption to Wh (assuming the provided numbers are in MWh).
                cons_dict = {row['Date'].date(): row["Daily_Consumption"]*DATAFILE_CONSUMPTION_UNIT for _, row in cons_df.iterrows()}
                cons_values = []
                last_value = 200000.0  # Default initial consumption value.
                # If a date is missing, use the last known value.
                for dt in date_range:
                    if dt in cons_dict:
                        last_value = cons_dict[dt]
                        cons_values.append(last_value)
                    else:
                        cons_values.append(last_value)
                data['demand'] = pd.Series(cons_values, index=date_range)
            else:
                # Fall back: use the Daily_Consumption column directly and replicate values if needed.
                cons_values = cons_df["Daily_Consumption"].values * DATAFILE_CONSUMPTION_UNIT
                if len(cons_values) < days:
                    cons_values = list(cons_values) * ((days // len(cons_values)) + 1)
                data['demand'] = pd.Series(cons_values[:days], index=date_range)
        else:
            # Default consumption if file does not exist.
            data['demand'] = pd.Series([200000.0]*days, index=date_range)
    except Exception as e:
        logging.error(f"Error loading consumption data for {zone_id}: {str(e)}")
        data['demand'] = pd.Series([200000.0]*days, index=date_range)

    # -------------------
    # Load Hydro Inflow Data
    # -------------------
    try:
        inflow_file = os.path.join(base_dir, f"input/{zone_id}_Effective_Inflow.csv")
        if os.path.exists(inflow_file):
            inflow_df = pd.read_csv(inflow_file)
            
            # Initialize an empty list to store all years' inflow data
            all_inflow_weekly = []
            
            if AVERAGE_INFLOW:
                for year in range(start_date.year, end_date.year + 1):
                    if str(year) in inflow_df.columns:
                        year_data = inflow_df['T_Gj.snitt'].dropna().values
                        all_inflow_weekly.extend(year_data)
            else:
                for year in range(start_date.year, end_date.year + 1):
                    if str(year) in inflow_df.columns:
                        # Append this year's data to our collection
                        year_data = inflow_df[str(year)].dropna().values
                        all_inflow_weekly.extend(year_data)
                    else:
                        year_data = inflow_df['T_Gj.snitt'].dropna().values
                        all_inflow_weekly.extend(year_data)

            
            # Use the combined weekly average inflow values
            weekly = pd.array(all_inflow_weekly)
            # weekly = inflow_df["T_Gj.snitt"].dropna().values

            inflow_daily = []
            # Convert weekly averages to a daily value by dividing by 7.
            for week_val in weekly:
                inflow_daily.extend([week_val *  DATAFILE_EFFECTIVE_INFLOW_UNIT/7]*7)
            # If the daily list is shorter than required, repeat the pattern.
            if len(inflow_daily) < days:
                while len(inflow_daily) < days:
                    inflow_daily.extend(inflow_daily[:days])
            data['inflow'] = pd.Series(inflow_daily[:days], index=date_range)
        else:
            # Use a default inflow value.
            data['inflow'] = pd.Series([30000.0]*days, index=date_range)
    except Exception as e:
        logging.error(f"Error loading inflow data for {zone_id}: {str(e)}")
        data['inflow'] = pd.Series([30000.0]*days, index=date_range)
    
    # -------------------
    # Load Reservoir Fill Level Data
    # -------------------
    try:
        resfill_file = os.path.join(base_dir, f"input/{zone_id}_Reservoir_Fill_Level.csv")
        if os.path.exists(resfill_file):
            resfill_df = pd.read_csv(resfill_file)
            weekly = resfill_df["Median TWh"].dropna().values
            
            # Initialize with None values for all dates.
            resfill_daily = [None] * days
            
            # Set reservoir fill values on Mondays (0 = Monday in datetime.weekday()).
            weekly_idx = 0
            for i, date in enumerate(date_range):
                if date.weekday() == 0 and weekly_idx < len(weekly):
                    resfill_daily[i] = weekly[weekly_idx] * DATAFILE_RESERVOIR_FILL_LEVEL_UNIT
                    weekly_idx += 1
            
            # If weekly data remains, assign values to remaining Mondays.
            if weekly_idx < len(weekly):
                remaining_mondays = [i for i, d in enumerate(date_range) if d.weekday() == 0][weekly_idx:]
                for i, monday_idx in enumerate(remaining_mondays):
                    if weekly_idx + i < len(weekly):
                        resfill_daily[monday_idx] = weekly[weekly_idx + i] * DATAFILE_RESERVOIR_FILL_LEVEL_UNIT
            
            data['resfill'] = pd.Series(resfill_daily, index=date_range)
        else:
            # Default: set reservoir fill values only on Mondays.
            resfill_daily = [30000.0 if d.weekday() == 0 else None for d in date_range]
            data['resfill'] = pd.Series(resfill_daily, index=date_range)
    except Exception as e:
        logging.error(f"Error loading reservoir fill data for {zone_id}: {str(e)}")
        resfill_daily = [30000.0 if d.weekday() == 0 else None for d in date_range]
        data['resfill'] = pd.Series(resfill_daily, index=date_range)

    return data