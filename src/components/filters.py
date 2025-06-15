
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import dash

def create_filter_buttons():
    """Create filter buttons for grouping and time range"""
    return html.Div([
        # Group Buttons
        html.Div([
            dbc.ButtonGroup([
                dbc.Button("Group by Material", id="btn-group-material", color="primary", outline=True, active=True),
                dbc.Button("Group by Region", id="btn-group-region", color="primary", outline=True),
                dbc.Button("Group by Type", id="btn-group-type", color="primary", outline=True),
            ], className="me-2"),
            
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
    ])

# Register callbacks for active button states
@dash.callback(
    [
        Output("btn-group-material", "active"),
        Output("btn-group-region", "active"),
        Output("btn-group-type", "active"),
    ],
    [
        Input("btn-group-material", "n_clicks"),
        Input("btn-group-region", "n_clicks"),
        Input("btn-group-type", "n_clicks"),
    ],
)
def toggle_group_buttons(n1, n2, n3):
    ctx = dash.callback_context
    
    # Default to "Group by Material" if no button has been clicked
    if not ctx.triggered:
        return True, False, False
    
    # Get the ID of the button that triggered the callback
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Set only the clicked button to active
    return (
        button_id == "btn-group-material",
        button_id == "btn-group-region",
        button_id == "btn-group-type",
    )

@dash.callback(
    [
        Output("btn-1yr", "active"),
        Output("btn-5yr", "active"),
        Output("btn-10yr", "active"),
        Output("btn-max", "active"),
    ],
    [
        Input("btn-1yr", "n_clicks"),
        Input("btn-5yr", "n_clicks"),
        Input("btn-10yr", "n_clicks"),
        Input("btn-max", "n_clicks"),
    ],
)
def toggle_time_buttons(n1, n2, n3, n4):
    ctx = dash.callback_context
    
    # Default to 5yr if no button has been clicked
    if not ctx.triggered:
        return False, True, False, False
    
    # Get the ID of the button that triggered the callback
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Set only the clicked button to active
    return (
        button_id == "btn-1yr",
        button_id == "btn-5yr",
        button_id == "btn-10yr",
        button_id == "btn-max",
    )