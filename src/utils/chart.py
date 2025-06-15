"""
Chart utilities for the Material Cost Forecaster.
"""
import plotly.graph_objects as go
import dash
import pandas as pd
from dash import dcc

def create_chart():
    """Create the chart component"""
    return dcc.Graph(id="material-chart")

def update_chart(materials, material_forecasts, MATERIAL_COLORS, 
                 selected_rows, show_forecast, show_range, btn1, btn5, btn10, btnmax):
    """
    Update the material chart based on user selections
    
    Args:
        materials: Dictionary of material data
        material_forecasts: Dictionary mapping materials to forecast data
        MATERIAL_COLORS: Dictionary mapping materials to colors
        selected_rows: List of selected row indices from the table
        show_forecast: Boolean indicating if forecasts should be shown
        show_range: Boolean indicating if forecast ranges should be shown
        btn1, btn5, btn10, btnmax: Click counts for time range buttons
            - btn1: Show only the latest year (2025) with monthly data
            - btn5: Show the last 5 years (2021-2025)
            - btn10: Show the last 10 years (2016-2025)
            - btnmax: Show from 2000 to current year (2000-2025)
        
    Returns:
        tuple: (figure, selection_message)
    """
    # Selection info message
    if not selected_rows:
        selection_message = "Please select at least one material (up to 5)"
        # Default to aluminum if nothing selected
        selected_rows = [0]
        selected_materials = ["Aluminum"]
    else:
        # Get the selected materials from the table
        selected_materials = [list(materials.keys())[idx] for idx in selected_rows]
        num_selected = len(selected_materials)
        
        # Enforce maximum of 5 materials
        if num_selected > 5:
            selected_rows = selected_rows[:5]
            selected_materials = selected_materials[:5]
            selection_message = "Maximum of 5 materials reached - showing first 5 selected"
        elif num_selected == 5:
            selection_message = "Maximum of 5 materials selected"
        else:
            selection_message = f"{num_selected} material(s) selected (select up to 5)"
    
    # Determine time range
    ctx = dash.callback_context
    if not ctx.triggered:
        # Default to 5 years
        time_range = "5yr"
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if button_id == "btn-1yr":
            time_range = "1yr"
        elif button_id == "btn-5yr":
            time_range = "5yr"
        elif button_id == "btn-10yr":
            time_range = "10yr"
        else:
            time_range = "max"
    
    # Create plot
    fig = go.Figure()
    
    # Find global date range for all materials
    all_end_dates = []
    current_year = 2025  # Current year for our app
    
    for material_name in selected_materials:
        material_data = materials[material_name].get("data")
        if material_data is not None:
            all_end_dates.append(material_data["Date"].max())
    
    # Use the most recent end date as the reference
    if all_end_dates:
        global_end_date = max(all_end_dates)
        
        # Determine start date based on time range
        if time_range == "1yr":
            # For 1 year filter, show the latest year with months
            # If the global_end_date is in the current year, show all data from beginning of current year
            # Otherwise, show one year back from the latest data point
            if global_end_date.year == current_year:
                # We are in the current year, so show from Jan 1st
                global_start_date = pd.Timestamp(year=current_year, month=1, day=1)
            else:
                # We do not have current year data, so show last 12 months from latest data point
                global_start_date = global_end_date - pd.DateOffset(years=1)
        elif time_range == "5yr":
            # Show the last 5 years from the latest data point
            global_start_date = global_end_date - pd.DateOffset(years=5)
        elif time_range == "10yr":
            # Show the last 10 years from the latest data point
            global_start_date = global_end_date - pd.DateOffset(years=10)
        else:  # Max range
            # Show from 2000 to current year (2000-2025)
            global_start_date = pd.Timestamp(year=2000, month=1, day=1)
    else:
        # Fallback if no materials are selected
        global_start_date = None
        global_end_date = None
    
    # Plot each selected material
    for i, material_name in enumerate(selected_materials):
        material_data = materials[material_name].get("data")
        
        if material_data is None:
            continue
            
        # Filter data based on global time range
        if global_start_date and global_end_date:
            filtered_data = material_data[(material_data["Date"] >= global_start_date) & 
                                         (material_data["Date"] <= global_end_date)]
        else:
            filtered_data = material_data
            
        # Get color for this material
        color = MATERIAL_COLORS.get(material_name, f"#{hash(material_name) % 0xFFFFFF:06x}")
            
        # Add historical data line
        fig.add_trace(go.Scatter(
            x=filtered_data["Date"],
            y=filtered_data["Value"],
            mode="lines",
            name=material_name,
            line=dict(color=color, width=2),
        ))
        
        # Add forecast if enabled
        if show_forecast:
            # Get the forecast for this material
            forecast_values = material_forecasts.get(material_name)
                
            if forecast_values:
                # Generate forecast dates for any material
                forecast_dates = pd.date_range(
                    start=material_data["Date"].max() + pd.DateOffset(months=1), 
                    periods=12, 
                    freq="MS"
                )
                
                # Only show forecasts if they fall within the selected time range
                if global_start_date and global_end_date:
                    # Filter forecast dates that fall within the selected time range
                    # We will also include forecasts that are within the next 12 months
                    forecast_end_date = global_end_date + pd.DateOffset(months=12)
                    forecast_dates_filtered = [date for date in forecast_dates 
                                              if date >= global_start_date and date <= forecast_end_date]
                    
                    # Only plot if there are forecast dates within range
                    if forecast_dates_filtered:
                        # Get corresponding forecast values
                        indices = [i for i, date in enumerate(forecast_dates) if date in forecast_dates_filtered]
                        forecast_values_filtered = [forecast_values[i] for i in indices]
                        
                        fig.add_trace(go.Scatter(
                            x=forecast_dates_filtered, 
                            y=forecast_values_filtered,
                            mode="lines",
                            name=f"{material_name} Forecast",
                            line=dict(color=color, width=2, dash="dash"),
                        ))
                else:
                    # If no time range filter, show all forecasts
                    fig.add_trace(go.Scatter(
                        x=forecast_dates, 
                        y=forecast_values,
                        mode="lines",
                        name=f"{material_name} Forecast",
                        line=dict(color=color, width=2, dash="dash"),
                    ))
                  
                # Add range bands if enabled
                if show_range:
                    # Prepare range bands according to time range filter
                    if global_start_date and global_end_date:
                        # Filter forecast dates that fall within the selected time range + 12 months
                        forecast_end_date = global_end_date + pd.DateOffset(months=12)
                        forecast_dates_filtered = [date for date in forecast_dates 
                                              if date >= global_start_date and date <= forecast_end_date]
                        
                        # Only show range bands if there are forecast dates within range
                        if forecast_dates_filtered:
                            # Get corresponding forecast values
                            indices = [i for i, date in enumerate(forecast_dates) if date in forecast_dates_filtered]
                            upper_bound = [forecast_values[i] * 1.05 for i in indices]
                            lower_bound = [forecast_values[i] * 0.95 for i in indices]
                            
                            fig.add_trace(go.Scatter(
                                x=forecast_dates_filtered,
                                y=upper_bound,
                                fill=None,
                                mode="lines",
                                line_color="rgba(0,0,0,0)",
                                showlegend=False,
                            ))
                            
                            # Create proper fill color
                            if "rgba" in color:
                                fill_color = color.replace(")", ", 0.2)")
                            else:
                                try:
                                    r = int(color.lstrip("#")[0:2], 16)
                                    g = int(color.lstrip("#")[2:4], 16)
                                    b = int(color.lstrip("#")[4:6], 16)
                                    fill_color = f"rgba({r}, {g}, {b}, 0.2)"
                                except:
                                    fill_color = "rgba(150, 150, 150, 0.2)"  # Fallback color
                            
                            fig.add_trace(go.Scatter(
                                x=forecast_dates_filtered,
                                y=lower_bound,
                                fill="tonexty",
                                mode="lines",
                                line_color="rgba(0,0,0,0)",
                                fillcolor=fill_color,
                                name=f"{material_name} Range",
                                showlegend=True if i == 0 else False,  # Only show legend for first range
                            ))
                    else:
                        # If no time range filter, show all range bands
                        upper_bound = [val * 1.05 for val in forecast_values]
                        lower_bound = [val * 0.95 for val in forecast_values]
                        
                        fig.add_trace(go.Scatter(
                            x=forecast_dates,
                            y=upper_bound,
                            fill=None,
                            mode="lines",
                            line_color="rgba(0,0,0,0)",
                            showlegend=False,
                        ))
                        
                        # Create proper fill color
                        if "rgba" in color:
                            fill_color = color.replace(")", ", 0.2)")
                        else:
                            try:
                                r = int(color.lstrip("#")[0:2], 16)
                                g = int(color.lstrip("#")[2:4], 16)
                                b = int(color.lstrip("#")[4:6], 16)
                                fill_color = f"rgba({r}, {g}, {b}, 0.2)"
                            except:
                                fill_color = "rgba(150, 150, 150, 0.2)"  # Fallback color
                        
                        fig.add_trace(go.Scatter(
                            x=forecast_dates,
                            y=lower_bound,
                            fill="tonexty",
                            mode="lines",
                            line_color="rgba(0,0,0,0)",
                            fillcolor=fill_color,
                            name=f"{material_name} Range",
                            showlegend=True if i == 0 else False,  # Only show legend for first range
                        ))
    
    # Update layout
    title = "National Material Costs"
    if selected_materials and len(selected_materials) <= 3:
        title = f"{', '.join(selected_materials)} - Cost Trends"
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Cost",
        height=400,
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )
    
    return fig, selection_message
