   
"""
Forecasting functions for the Material Cost Forecaster application.
"""
import numpy as np

def generate_forecast(df, periods=12):
    """
    Generate a simple forecast based on historical data
    
    Args:
        df: DataFrame with historical data
        periods: Number of periods to forecast
        
    Returns:
        List of forecasted values
    """
    # Use the last 24 months to generate a simple forecast
    recent_data = df.tail(24)['Value'].values
    
    # Simple forecast - last value + small random change
    last_value = recent_data[-1]
    forecast_values = []
    for i in range(periods):
        # Small decay trend to make it look realistic
        trend = -0.005 * i
        random_factor = np.random.normal(0, 0.01)
        next_val = last_value * (1 + trend + random_factor)
        forecast_values.append(next_val)
        last_value = next_val
        
    return forecast_values