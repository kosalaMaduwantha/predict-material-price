
from dash import dcc
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import dash
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.data_processing import filter_data_by_time_range
from src.utils.forecast import generate_forecast

def create_chart():
    """Create the chart component"""
    return dcc.Graph(id='material-chart')

# Register callback
@dash.callback(
    Output('material-chart', 'figure'),
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
def update_chart(selected_rows, show_forecast, show_range, btn1, btn5, btn10, btnmax):    # Import here to avoid circular imports
    from src.app import materials
    
    if not selected_rows:
        # Default to aluminum if nothing selected
        selected_material = "Aluminum"
    else:
        # Get the selected material from the table
        selected_idx = selected_rows[0]
        selected_material = list(materials.keys())[selected_idx]
    
    # Get data for the selected material
    material_data = materials[selected_material].get('data')
    
    # Check for data availability
    if material_data is None:
        return {
            'data': [],
            'layout': {
                'title': f'No data available for {selected_material}',
                'height': 400
            }
        }
    
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
    
    # Filter data based on time range
    filtered_data = filter_data_by_time_range(material_data, time_range)
    
    # Create plot
    fig = go.Figure()
    
    # Add historical data line
    fig.add_trace(go.Scatter(
        x=filtered_data['Date'],
        y=filtered_data['Value'],
        mode='lines',
        name=selected_material,
        line=dict(color='#17becf', width=2),    ))
    
    # Add forecast if enabled
    if show_forecast:
        # Generate forecast dates for any material
        forecast_dates = pd.date_range(
            start=material_data['Date'].max() + pd.DateOffset(months=1), 
            periods=12, 
            freq='MS'
        )
        
        # Generate forecast for the selected material
        forecast_values = generate_forecast(material_data)
        
        fig.add_trace(go.Scatter(
            x=forecast_dates, 
            y=forecast_values,
            mode='lines',
            name='Forecast',
            line=dict(color='#17becf', width=2, dash='dash'),        ))
        
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
            
            fig.add_trace(go.Scatter(
                x=forecast_dates,
                y=lower_bound,
                fill='tonexty',
                mode='lines',
                line_color='rgba(0,0,0,0)',
                fillcolor='rgba(23, 190, 207, 0.2)',
                name='Forecast Range',
            ))
    
    # Update layout
    fig.update_layout(
        title=f'{selected_material} - National',        xaxis_title='Date',
        yaxis_title='Cost',
        height=400,
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )
    
    return fig