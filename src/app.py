"""
Main application file for the Material Cost Forecaster.

This module contains the core Dash application and UI components for the 
Material Cost Forecaster. It imports utility functions from the utils package
and provides the main entry point for the application.
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

# Import utilities from the utils package
import sys
from pathlib import Path

# Add the parent directory to the sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.data_processing import period_to_date, prepare_materials_data
from src.utils.forecast import generate_forecast
from src.utils.config import MATERIAL_COLORS
from src.utils.chart import update_chart, create_chart

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # for deployment

# Read the data
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'data')
aluminum_df = pd.read_csv(os.path.join(data_dir, 'aluminum_base_scrap.csv'))
iron_steel_df = pd.read_csv(os.path.join(data_dir, 'iron_and_steel.csv'))
paint_df = pd.read_csv(os.path.join(data_dir, 'paint_and_coating_manufacturing.csv'))
concrete_brick_df = pd.read_csv(os.path.join(data_dir, 'concrete_brick.csv'))
gypsum_df = pd.read_csv(os.path.join(data_dir, 'gypsum_building_materials.csv'))
lumber_plywood_df = pd.read_csv(os.path.join(data_dir, 'lumber_and_plywood.csv'))
copper_wire_df = pd.read_csv(os.path.join(data_dir, 'copper_wire.csv'))
glass_df = pd.read_csv(os.path.join(data_dir, 'glass.csv'))
construction_machinery_df = pd.read_csv(os.path.join(data_dir, 'construction_machinery_and_equipment.csv'))
electrical_equipment_df = pd.read_csv(os.path.join(data_dir, 'electrical_equipment.csv'))
plastics_plumbing_df = pd.read_csv(os.path.join(data_dir, 'plastics_plumbing_fixtures.csv'))

# Preprocess data: Convert period to date 
for df in [aluminum_df, iron_steel_df, paint_df, concrete_brick_df, gypsum_df, 
           lumber_plywood_df, copper_wire_df, glass_df, construction_machinery_df,
           electrical_equipment_df, plastics_plumbing_df]:
    df['Date'] = df.apply(period_to_date, axis=1)

# Dictionary mapping CSV files to display names
material_data_mapping = {
    "Aluminum": aluminum_df,
    "Iron and Steel": iron_steel_df,
    "Paint and Coating Manufacturing": paint_df,
    "Concrete and Brick": concrete_brick_df,
    "Gypsum Building Materials": gypsum_df,
    "Lumber and Plywood": lumber_plywood_df,
    "Copper Wire": copper_wire_df,
    "Glass": glass_df,
    "Construction Machinery and Equipment": construction_machinery_df,
    "Electrical Equipment": electrical_equipment_df,
    "Plastics Plumbing Fixtures": plastics_plumbing_df,
}

# Prepare materials data
materials = {}
for name, df in material_data_mapping.items():
    # We'll update the prepare_materials_data function to handle one material at a time
    material_info = prepare_materials_data({name: df})[name] if df is not None else None
    if material_info:
        materials[name] = material_info

# Generate forecasts
forecast_dates = pd.date_range(
    start=aluminum_df['Date'].max() + pd.DateOffset(months=1), 
    periods=12, 
    freq='MS'
)

# Generate forecasts for all available materials
material_forecasts = {}
for material_name, df in material_data_mapping.items():
    if df is not None and not df.empty:
        material_forecasts[material_name] = generate_forecast(df)

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
        ]),
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
    dbc.Row([
        # Data Table
        dbc.Col([
            # Hidden div to store current page state
            html.Div(id='current-page', style={'display': 'none'}, children='1'),
              dash_table.DataTable(
                id='materials-table',
                columns=[
                    {"name": "Material", "id": "Material"},
                    {"name": "Monthly Change", "id": "Monthly Change"},
                    {"name": "Quarterly Change", "id": "Quarterly Change"},
                    {"name": "Semi-Annual Change", "id": "Semi-Annual Change"},
                    {"name": "Annual Change", "id": "Annual Change"},
                ],
                data=[{
                    "Material": material,
                    "Monthly Change": f"{mat_info['changes']['monthly']}% {'+' if mat_info['direction'] == 'up' else '-'}",
                    "Quarterly Change": f"{mat_info['changes']['quarterly']}% {'+' if mat_info['direction'] == 'up' else '-'}",
                    "Semi-Annual Change": f"{mat_info['changes']['semi_annual']}% {'+' if mat_info['direction'] == 'up' else '-'}",
                    "Annual Change": f"{mat_info['changes']['annual']}% {'+' if mat_info['direction'] == 'up' else '-'}",
                } for material, mat_info in list(materials.items())[:10]],  # Show first 10 materials initially
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
                selected_rows=[0],  # Select first material by default
                page_current=0,
                page_size=10,
                page_action='custom',
            ),
            
            # Pagination controls
            html.Div([
                dbc.ButtonGroup([
                    dbc.Button("Previous", id="btn-prev-page", color="secondary", outline=True, className="mr-1"),
                    dbc.Button("Next", id="btn-next-page", color="secondary", outline=True),
                ], className="mt-2"),
                html.Span(id="page-indicator", className="ml-2 mt-2"),
            ], className="d-flex justify-content-between align-items-center mt-2"),
            
            html.Div(id='selection-info', className="mt-2 text-muted", children="Select up to 5 materials to display on the graph"),
        ], width=6),
        
        # Chart
        dbc.Col([
            create_chart(),
        ], width=6),
    ]),
])

# Prepare table data
def prepare_table_data():
    """
    Prepare data for the materials table
    
    Returns:
        List of dictionaries containing the table data
    """
    return [{
        "Material": material,
        "Monthly Change": f"{mat_info['changes']['monthly']}% {'+' if mat_info['direction'] == 'up' else '-'}",
        "Quarterly Change": f"{mat_info['changes']['quarterly']}% {'+' if mat_info['direction'] == 'up' else '-'}",
        "Semi-Annual Change": f"{mat_info['changes']['semi_annual']}% {'+' if mat_info['direction'] == 'up' else '-'}",
        "Annual Change": f"{mat_info['changes']['annual']}% {'+' if mat_info['direction'] == 'up' else '-'}",
    } for material, mat_info in materials.items()]

# Callback to update the table data with pagination
@app.callback(
    Output('materials-table', 'data'),
    Output('page-indicator', 'children'),
    Input('materials-table', 'page_current'),
    Input('materials-table', 'page_size'),
    Input('btn-prev-page', 'n_clicks'),
    Input('btn-next-page', 'n_clicks'),
    State('current-page', 'children')
)
def update_table(page_current, page_size, btn_prev, btn_next, current_page):
    """
    Update the materials table with pagination
    
    Args:
        page_current: Current page
        page_size: Number of rows per page
        btn_prev: Previous button clicks
        btn_next: Next button clicks
        current_page: Current page state
        
    Returns:
        tuple: (table_data, page_indicator)
    """
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    table_data = prepare_table_data()
    total_pages = (len(table_data) - 1) // page_size + 1
    
    # Update current page based on button clicks
    page = int(current_page)
    if trigger_id == 'btn-prev-page' and page > 1:
        page -= 1
    elif trigger_id == 'btn-next-page' and page < total_pages:
        page += 1
    
    # Calculate start and end indices for slicing the data
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    # Slice the data for the current page
    page_data = table_data[start_idx:end_idx]
    
    # Update the page indicator
    page_indicator = f"Page {page} of {total_pages}"
    
    return page_data, page_indicator

# Callback to update current page state
@app.callback(
    Output('current-page', 'children'),
    Input('btn-prev-page', 'n_clicks'),
    Input('btn-next-page', 'n_clicks'),
    State('current-page', 'children')
)
def update_page_state(btn_prev, btn_next, current_page):
    """
    Update the current page state based on button clicks
    
    Args:
        btn_prev: Previous button clicks
        btn_next: Next button clicks
        current_page: Current page state
        
    Returns:
        str: Updated page number
    """
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    table_data = prepare_table_data()
    page_size = 10
    total_pages = (len(table_data) - 1) // page_size + 1
    
    page = int(current_page)
    if trigger_id == 'btn-prev-page' and page > 1:
        page -= 1
    elif trigger_id == 'btn-next-page' and page < total_pages:
        page += 1
    
    return str(page)

# Callback to update the chart based on the selected materials
@app.callback(
    [Output('material-chart', 'figure'),
     Output('selection-info', 'children')],
    [
        Input('materials-table', 'selected_rows'),
        Input('materials-table', 'data'),
        Input('forecast-toggle', 'value'),
        Input('range-toggle', 'value'),
        Input('btn-1yr', 'n_clicks'),
        Input('btn-5yr', 'n_clicks'),
        Input('btn-10yr', 'n_clicks'),
        Input('btn-max', 'n_clicks'),
    ]
)
def update_chart_callback(selected_rows, table_data, show_forecast, show_range, btn1, btn5, btn10, btnmax):
    """
    Update the material chart based on user selections
    
    Args:
        selected_rows: List of selected row indices from the table
        table_data: Current table data
        show_forecast: Boolean indicating if forecasts should be shown
        show_range: Boolean indicating if forecast ranges should be shown
        btn1, btn5, btn10, btnmax: Click counts for time range buttons
        
    Returns:
        tuple: (figure, selection_message)
    """
    # Get selected material names from the current page's data
    selected_materials = [table_data[idx]['Material'] for idx in selected_rows] if selected_rows else []
    
    # Create a mapping of row indices to material names
    material_list = list(materials.keys())
    selected_material_indices = [material_list.index(name) for name in selected_materials if name in material_list]
    
    return update_chart(
        materials=materials,
        material_forecasts=material_forecasts,
        MATERIAL_COLORS=MATERIAL_COLORS,
        selected_rows=selected_material_indices,
        show_forecast=show_forecast,
        show_range=show_range,
        btn1=btn1, 
        btn5=btn5, 
        btn10=btn10, 
        btnmax=btnmax
    )

if __name__ == '__main__':
    print("Starting Material Cost Forecaster...")
    print("Application will be available at http://127.0.0.1:8050/")
    app.run_server(debug=True)
