"""
Main entry point for the Material Cost Forecaster application.

This file acts as the primary entry point that runs the Dash application.
It includes all material data including the newly added materials.
"""
import os
import sys
import dash
from dash import dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

# Add the root directory to Python path to ensure imports work correctly
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

# Define helper functions inline to avoid import issues
def period_to_date(row):
    """Convert period format to a datetime object"""
    year = int(row['Year'])
    month = int(row['Period'].replace('M', ''))
    return pd.Timestamp(year=year, month=month, day=1)

def calculate_changes(df):
    """Calculate percentage changes for a material dataset"""
    if df is None or len(df) < 12:  # Need at least a year of data
        return None, "neutral"
        
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

def generate_forecast(df, periods=12):
    """Generate a simple forecast based on historical data"""
    if df is None or len(df) < 24:
        return None
        
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

def create_chart():
    """Create the chart component"""
    return dcc.Graph(id='material-chart')

def update_chart(materials, material_forecasts, MATERIAL_COLORS, 
                 selected_rows, show_forecast, show_range, btn1, btn5, btn10, btnmax,
                 current_page):
    """
    Update the material chart based on user selections
    
    Args:
        materials: Dictionary of material data
        material_forecasts: Dictionary of forecast data
        MATERIAL_COLORS: Dictionary mapping materials to colors
        selected_rows: List of selected row indices from the table
        show_forecast: Boolean indicating if forecasts should be shown
        show_range: Boolean indicating if forecast ranges should be shown
        btn1, btn5, btn10, btnmax: Click counts for time range buttons
        current_page: Current page index
        
    Returns:
        tuple: (figure, selection_message)
    """
    # Selection info message
    if not selected_rows:
        selection_message = "Please select at least one material (up to 5)"
        # Default to first material if nothing selected
        selected_rows = [0]
        material_names = list(materials.keys())
        offset = current_page * 10
        selected_materials = [material_names[offset]]
    else:
        # Get the selected materials from the table
        material_names = list(materials.keys())
        offset = current_page * 10
        visible_materials = material_names[offset:offset+10]
        selected_materials = [visible_materials[idx] for idx in selected_rows if idx < len(visible_materials)]
        num_selected = len(selected_materials)
        
        # Enforce maximum of 5 materials
        if num_selected > 5:
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
        time_range = '5yr'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'btn-1yr':
            time_range = '1yr'
        elif button_id == 'btn-5yr':
            time_range = '5yr'
        elif button_id == 'btn-10yr':
            time_range = '10yr'
        else:
            time_range = 'max'
    
    # Create plot
    fig = go.Figure()
    
    # Find global date range for all materials
    all_end_dates = []
    for material_name in selected_materials:
        material_data = materials[material_name].get('data')
        if material_data is not None:
            all_end_dates.append(material_data['Date'].max())
      # Use the most recent end date as the reference
    if all_end_dates:
        global_end_date = max(all_end_dates)
        
        # Determine start date based on time range
        if time_range == '1yr':
            # For 1 year filter, show the latest year with months
            # If the global_end_date is in the current year, show all data from beginning of current year
            # Otherwise, show one year back from the latest data point
            current_year = datetime.now().year
            if global_end_date.year == current_year:
                # We are in the current year, so show from Jan 1st
                global_start_date = pd.Timestamp(year=current_year, month=1, day=1)
            else:
                # We do not have current year data, so show last 12 months from latest data point
                global_start_date = global_end_date - pd.DateOffset(years=1)
        elif time_range == '5yr':
            # Show the last 5 years from the latest data point
            global_start_date = global_end_date - pd.DateOffset(years=5)
        elif time_range == '10yr':
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
        material_data = materials[material_name].get('data')
        
        if material_data is None:
            continue
            
        # Filter data based on global time range
        if global_start_date and global_end_date:
            filtered_data = material_data[(material_data['Date'] >= global_start_date) & 
                                         (material_data['Date'] <= global_end_date)]
        else:
            filtered_data = material_data
            
        # Get color for this material
        color = MATERIAL_COLORS.get(material_name, f'#{hash(material_name) % 0xFFFFFF:06x}')
            
        # Add historical data line
        fig.add_trace(go.Scatter(
            x=filtered_data['Date'],
            y=filtered_data['Value'],
            mode='lines',
            name=material_name,
            line=dict(color=color, width=2),
        ))
        
        # Add forecast if enabled
        if show_forecast:
            # Get forecast for this material
            forecast_values = material_forecasts.get(material_name)
                
            if forecast_values:
                # Generate forecast dates
                forecast_dates = pd.date_range(
                    start=material_data['Date'].max() + pd.DateOffset(months=1), 
                    periods=12, 
                    freq='MS'
                )
                
                fig.add_trace(go.Scatter(
                    x=forecast_dates, 
                    y=forecast_values,
                    mode='lines',
                    name=f'{material_name} Forecast',
                    line=dict(color=color, width=2, dash='dash'),
                ))
                
                # Add range bands if enabled
                if show_range:
                    upper_bound = [val * 1.05 for val in forecast_values]
                    lower_bound = [val * 0.95 for val in forecast_values]
                    
                    fig.add_trace(go.Scatter(
                        x=forecast_dates,
                        y=upper_bound,
                        fill=None,
                        mode='lines',
                        line_color='rgba(0,0,0,0)',
                        showlegend=False,
                    ))
                    
                    # Create a proper rgba color for the fill
                    if 'rgba' in color:
                        fill_color = color.replace(')', ', 0.2)')
                    else:
                        r = int(color.lstrip("#")[0:2], 16) if color.startswith("#") else 0
                        g = int(color.lstrip("#")[2:4], 16) if color.startswith("#") else 0
                        b = int(color.lstrip("#")[4:6], 16) if color.startswith("#") else 0
                        fill_color = f'rgba({r}, {g}, {b}, 0.2)'
                    
                    fig.add_trace(go.Scatter(
                        x=forecast_dates,
                        y=lower_bound,
                        fill='tonexty',
                        mode='lines',
                        line_color='rgba(0,0,0,0)',
                        fillcolor=fill_color,
                        name=f'{material_name} Range',                        showlegend=True if i == 0 else False,  # Only show legend for first range
                    ))
    
    # Update layout
    title = 'National Material Costs'
    if selected_materials and len(selected_materials) <= 3:
        title = f'{", ".join(selected_materials)} - Cost Trends'
    
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Cost',
        height=400,
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )
    
    return fig, selection_message

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # for deployment

# Define material colors
MATERIAL_COLORS = {
    "Aluminum": '#1f77b4',
    "Iron and Steel": '#ff7f0e',
    "Paint and Coating Manufacturing": '#2ca02c',
    "Concrete and Brick": '#d62728',
    "Gypsum Building Materials": '#9467bd',
    "Lumber and Plywood": '#8c564b',
    "Copper Wire": '#e377c2',
    "Glass": '#7f7f7f',
    "Construction Machinery and Equipment": '#bcbd22',
    "Electrical Equipment": '#17becf',
    "Plastics Plumbing Fixtures": '#aec7e8',
}

# Read the data
data_dir = os.path.join(root_dir, 'src', 'data')

# Dictionary mapping material names to dataframes
material_data = {}
material_files = {
    "Aluminum": 'aluminum_base_scrap.csv',
    "Iron and Steel": 'iron_and_steel.csv',
    "Paint and Coating Manufacturing": 'paint_and_coating_manufacturing.csv',
    "Concrete and Brick": 'concrete_brick.csv',
    "Gypsum Building Materials": 'gypsum_building_materials.csv',
    "Lumber and Plywood": 'lumber_and_plywood.csv',
    "Copper Wire": 'copper_wire.csv',
    "Glass": 'glass.csv',
    "Construction Machinery and Equipment": 'construction_machinery_and_equipment.csv',
    "Electrical Equipment": 'electrical_equipment.csv',
    "Plastics Plumbing Fixtures": 'plastics_plumbing_fixtures.csv'
}

# Load all material data
for material_name, filename in material_files.items():
    try:
        file_path = os.path.join(data_dir, filename)
        df = pd.read_csv(file_path)
        # Convert period to date
        df['Date'] = df.apply(period_to_date, axis=1)
        material_data[material_name] = df
    except Exception as e:
        print(f"Error loading {material_name}: {e}")
        material_data[material_name] = None

# Process materials data
materials = {}
for material_name, df in material_data.items():
    if df is not None:
        changes, direction = calculate_changes(df)
        materials[material_name] = {
            "data": df,
            "changes": changes,
            "direction": direction
        }

# Generate forecasts for all materials
material_forecasts = {}
for material_name, df in material_data.items():
    if df is not None:
        material_forecasts[material_name] = generate_forecast(df)

# Count total materials for pagination
total_materials = len(materials)
materials_per_page = 10
total_pages = (total_materials + materials_per_page - 1) // materials_per_page  # Ceiling division

# Keep track of current page (0-indexed)
current_page = 0

# Define the application layout
app.layout = html.Div([
    html.H1("Material Cost Forecaster", className="text-center mt-3 mb-4"),
    
    # Time Range Buttons
    html.Div([
        dbc.ButtonGroup([
            dbc.Button("1 Year", id="btn-1yr", color="primary", outline=True),
            dbc.Button("5 Years", id="btn-5yr", color="primary", outline=True, active=True),
            dbc.Button("10 Years", id="btn-10yr", color="primary", outline=True),
            dbc.Button("Max", id="btn-max", color="primary", outline=True),
        ], id="time-buttons"),
    ], className="d-flex justify-content-between mb-3"),
    
    # Forecast Toggle and Range Toggle
    html.Div([
        html.Div([
            html.Span("Forecast", className="me-2"),
            dbc.Checkbox(id="forecast-toggle", value=True),
        ], className="d-flex align-items-center"),
        
        html.Div([
            html.Span("Include Range", className="me-2"),
            dbc.Checkbox(id="range-toggle", value=False),
        ], className="d-flex align-items-center"),
    ], className="d-flex justify-content-between mb-3"),
    
    # Data Table and Chart
    dbc.Row([        # Data Table Column
        dbc.Col([
            # Store current page in a dcc.Store
            dcc.Store(id='current-page', data=0),
            
            # Table Header
            html.H4("Material Price Change Summary", className="mb-3"),
            
            # Data Table
            dash_table.DataTable(
                id='materials-table',
                columns=[
                    {"name": "Material", "id": "Material"},
                    {"name": "Monthly Change", "id": "Monthly Change"},
                    {"name": "Quarterly Change", "id": "Quarterly Change"},
                    {"name": "Semi-Annual Change", "id": "Semi-Annual Change"},
                    {"name": "Annual Change", "id": "Annual Change"},
                ],
                # We'll populate this data dynamically based on the current page
                data=[],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '8px'},
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{Monthly Change} contains "+"'},
                        'color': 'green'
                    },
                    {
                        'if': {'filter_query': '{Monthly Change} contains "-"'},
                        'color': 'red'
                    },
                    {
                        'if': {'filter_query': '{Quarterly Change} contains "+"'},
                        'color': 'green'
                    },
                    {
                        'if': {'filter_query': '{Quarterly Change} contains "-"'},
                        'color': 'red'
                    },
                    {
                        'if': {'filter_query': '{Semi-Annual Change} contains "+"'},
                        'color': 'green'
                    },
                    {
                        'if': {'filter_query': '{Semi-Annual Change} contains "-"'},
                        'color': 'red'
                    },
                    {
                        'if': {'filter_query': '{Annual Change} contains "+"'},
                        'color': 'green'
                    },
                    {
                        'if': {'filter_query': '{Annual Change} contains "-"'},
                        'color': 'red'
                    },
                ],
                row_selectable="multi",
                selected_rows=[0]  # Select first item by default
            ),
            
            # Pagination Controls
            html.Div([
                dbc.Button("Previous", id="prev-page-btn", color="secondary", outline=True, 
                          className="me-2", disabled=True),
                html.Span(id="page-indicator", children="Page 1 of 2"),
                dbc.Button("Next", id="next-page-btn", color="secondary", outline=True, 
                          className="ms-2", disabled=False),
            ], className="d-flex justify-content-center align-items-center mt-3"),
            
            # Selection Info
            html.Div(id='selection-info', className="mt-2 text-muted", 
                    children="Select up to 5 materials to display on the graph"),
        ], width=6),
          # Chart Column
        dbc.Col([
            html.H4("Material Cost Trends & Forecasts", className="mb-3"),
            create_chart(),
        ], width=6),
    ]),
])

# Callback to update the table data and pagination based on page
@app.callback(
    [Output('materials-table', 'data'),
     Output('prev-page-btn', 'disabled'),
     Output('next-page-btn', 'disabled'),
     Output('page-indicator', 'children'),
     Output('current-page', 'data')],
    [Input('prev-page-btn', 'n_clicks'),
     Input('next-page-btn', 'n_clicks')],
    [State('current-page', 'data')]
)
def update_table_pagination(prev_clicks, next_clicks, current_page):
    """Update table data and pagination controls based on current page"""
    ctx = dash.callback_context
    
    # Default values
    if not ctx.triggered:
        # Initial load, start at page 0
        page = 0
    else:
        # Determine which button was clicked
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        page = current_page
        
        if button_id == 'prev-page-btn' and page > 0:
            page -= 1
        elif button_id == 'next-page-btn' and page < total_pages - 1:
            page += 1
    
    # Get material names for the current page
    material_names = list(materials.keys())
    start_idx = page * materials_per_page
    end_idx = min(start_idx + materials_per_page, total_materials)
    current_materials = material_names[start_idx:end_idx]
    
    # Create table data for current page
    table_data = []
    for material in current_materials:
        mat_info = materials[material]
        table_data.append({
            "Material": material,
            "Monthly Change": f"{mat_info['changes']['monthly']}% {'+' if mat_info['direction'] == 'up' else '-'}",
            "Quarterly Change": f"{mat_info['changes']['quarterly']}% {'+' if mat_info['direction'] == 'up' else '-'}",
            "Semi-Annual Change": f"{mat_info['changes']['semi_annual']}% {'+' if mat_info['direction'] == 'up' else '-'}",
            "Annual Change": f"{mat_info['changes']['annual']}% {'+' if mat_info['direction'] == 'up' else '-'}",
        })
    
    # Update pagination controls
    prev_disabled = page == 0
    next_disabled = page == total_pages - 1
    page_indicator = f"Page {page + 1} of {total_pages}"
    
    return table_data, prev_disabled, next_disabled, page_indicator, page

# Callback to update the chart based on the selected materials
@app.callback(
    [Output('material-chart', 'figure'),
     Output('selection-info', 'children')],
    [
        Input('materials-table', 'selected_rows'),
        Input('forecast-toggle', 'value'),
        Input('range-toggle', 'value'),
        Input('btn-1yr', 'n_clicks'),
        Input('btn-5yr', 'n_clicks'),
        Input('btn-10yr', 'n_clicks'),
        Input('btn-max', 'n_clicks'),
        Input('current-page', 'data')
    ]
)
def update_chart_callback(selected_rows, show_forecast, show_range, btn1, btn5, btn10, btnmax, current_page):
    """
    Update the material chart based on user selections
    
    Args:
        selected_rows: List of selected row indices from the table
        show_forecast: Boolean indicating if forecasts should be shown
        show_range: Boolean indicating if forecast ranges should be shown
        btn1, btn5, btn10, btnmax: Click counts for time range buttons
        current_page: Current page index
        
    Returns:
        tuple: (figure, selection_message)
    """
    return update_chart(
        materials=materials,
        material_forecasts=material_forecasts,
        MATERIAL_COLORS=MATERIAL_COLORS,
        selected_rows=selected_rows,
        show_forecast=show_forecast,
        show_range=show_range,
        btn1=btn1, 
        btn5=btn5, 
        btn10=btn10, 
        btnmax=btnmax,
        current_page=current_page
    )

# Callback to update button active states based on which one was clicked
@app.callback(
    [Output("btn-1yr", "active"),
     Output("btn-5yr", "active"),
     Output("btn-10yr", "active"),
     Output("btn-max", "active")],
    [Input("btn-1yr", "n_clicks"),
     Input("btn-5yr", "n_clicks"),
     Input("btn-10yr", "n_clicks"),
     Input("btn-max", "n_clicks")]
)
def update_button_active_state(btn1, btn5, btn10, btnmax):
    """Update which button is active based on user clicks"""
    ctx = dash.callback_context
    
    # Default to 5yr active on initial load
    if not ctx.triggered:
        return False, True, False, False
    
    # Determine which button was clicked
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Set appropriate button to active
    return (button_id == "btn-1yr",
            button_id == "btn-5yr",
            button_id == "btn-10yr",
            button_id == "btn-max")

if __name__ == '__main__':
    print("Starting Material Cost Forecaster...")
    print("Application will be available at http://127.0.0.1:8050/")
    app.run_server(debug=True)
