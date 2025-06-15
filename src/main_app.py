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
from src.utils.data_processing import period_to_date, prepare_materials_data
from src.utils.forecast import generate_forecast
from src.utils.config import MATERIAL_COLORS
from src.utils.chart import update_chart, create_chart

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # for deployment

# Read the data
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
aluminum_df = pd.read_csv(os.path.join(data_dir, 'aluminum_base_scrap.csv'))
iron_steel_df = pd.read_csv(os.path.join(data_dir, 'iron_and_steel.csv'))
paint_df = pd.read_csv(os.path.join(data_dir, 'paint_and_coating_manufacturing.csv'))

# Preprocess data: Convert period to date 
for df in [aluminum_df, iron_steel_df, paint_df]:
    df['Date'] = df.apply(period_to_date, axis=1)

# Prepare materials data
materials = prepare_materials_data(aluminum_df, iron_steel_df, paint_df)

# Generate forecasts
forecast_dates = pd.date_range(
    start=aluminum_df['Date'].max() + pd.DateOffset(months=1), 
    periods=12, 
    freq='MS'
)

# Generate forecasts for all available materials
aluminum_forecast = generate_forecast(aluminum_df)
iron_steel_forecast = generate_forecast(iron_steel_df)
paint_forecast = generate_forecast(paint_df)

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
                } for material, mat_info in materials.items()],
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
                selected_rows=[0]  # Select aluminum by default
            ),
            html.Div(id='selection-info', className="mt-2 text-muted", children="Select up to 5 materials to display on the graph"),
        ], width=6),
        
        # Chart
        dbc.Col([
            create_chart(),
        ], width=6),
    ]),
])

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
    ]
)
def update_chart_callback(selected_rows, show_forecast, show_range, btn1, btn5, btn10, btnmax):
    """
    Update the material chart based on user selections
    
    Args:
        selected_rows: List of selected row indices from the table
        show_forecast: Boolean indicating if forecasts should be shown
        show_range: Boolean indicating if forecast ranges should be shown
        btn1, btn5, btn10, btnmax: Click counts for time range buttons
        
    Returns:
        tuple: (figure, selection_message)
    """
    return update_chart(
        materials=materials,
        aluminum_forecast=aluminum_forecast,
        iron_steel_forecast=iron_steel_forecast,
        paint_forecast=paint_forecast,
        MATERIAL_COLORS=MATERIAL_COLORS,
        selected_rows=selected_rows,
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
