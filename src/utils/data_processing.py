   
"""
Data processing functions for the Material Cost Forecaster application.
"""
import pandas as pd

def period_to_date(row):
    """Convert period format to a datetime object"""
    year = int(row['Year'])
    month = int(row['Period'].replace('M', ''))
    return pd.Timestamp(year=year, month=month, day=1)

def prepare_materials_data(material_data_dict):
    """
    Prepare materials data for the application - only include materials with actual data
    
    Args:
        material_data_dict: A dictionary mapping material names to dataframes
        
    Returns:
        A dictionary containing processed materials data
    """
    
    # Calculate percentage changes for materials
    def calculate_changes(df):
        if df is None or len(df) < 12:  # Need at least a year of data
            return None
            
        # Sort by date to ensure calculations are correct
        df_sorted = df.sort_values('Date', ascending=True).copy()
        
        # Get the most recent values
        latest_value = df_sorted['Value'].iloc[-1]
        
        # Calculate changes (in percentages)
        try:
            # Monthly change (1 month)
            month_1_value = df_sorted['Value'].iloc[-2]  # Value from 1 month ago
            monthly_change = ((latest_value - month_1_value) / month_1_value) * 100
            
            # Quarterly change (3 months)
            month_3_value = df_sorted['Value'].iloc[-4]  # Value from 3 months ago
            quarterly_change = ((latest_value - month_3_value) / month_3_value) * 100
            
            # Semi-annual change (6 months)
            month_6_value = df_sorted['Value'].iloc[-7]  # Value from 6 months ago
            semi_annual_change = ((latest_value - month_6_value) / month_6_value) * 100
            
            # Annual change (12 months)
            month_12_value = df_sorted['Value'].iloc[-13]  # Value from 12 months ago
            annual_change = ((latest_value - month_12_value) / month_12_value) * 100
            
            # Determine direction based on annual change
            direction = "up" if annual_change >= 0 else "down"
            
            return {
                "monthly": round(monthly_change, 2),
                "quarterly": round(quarterly_change, 2),
                "semi_annual": round(semi_annual_change, 2),
                "annual": round(annual_change, 2)
            }, direction
        except IndexError:
            # Not enough data points for all calculations
            return {
                "monthly": 0.0,
                "quarterly": 0.0,
                "semi_annual": 0.0,
                "annual": 0.0
            }, "neutral"
    
    # Process each material
    processed_materials = {}
    for material_name, df in material_data_dict.items():
        changes, direction = calculate_changes(df)
        
        processed_materials[material_name] = {
            "data": df,
            "changes": changes,
            "direction": direction
        }
    
    return processed_materials

def filter_data_by_time_range(data, time_range):
    """Filter data based on the selected time range"""
    end_date = data['Date'].max()
    
    if time_range == '1yr':
        start_date = end_date - pd.DateOffset(years=1)
    elif time_range == '5yr':
        start_date = end_date - pd.DateOffset(years=5)
    elif time_range == '10yr':
        start_date = end_date - pd.DateOffset(years=10)
    else:
        start_date = data['Date'].min()
    
    return data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]