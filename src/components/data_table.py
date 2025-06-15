   
from dash import dash_table
from dash.dependencies import Input, Output
import dash

def create_data_table(materials):
    """Create the data table component"""
    
    # Prepare data for the table
    table_data = [{
        "Material": material,
        "Monthly Change": f"{mat_info['changes']['monthly']}% {'↑' if mat_info['direction'] == 'up' else '↓'}",
        "Quarterly Change": f"{mat_info['changes']['quarterly']}% {'↑' if mat_info['direction'] == 'up' else '↓'}",
        "Semi-Annual Change": f"{mat_info['changes']['semi_annual']}% {'↑' if mat_info['direction'] == 'up' else '↓'}",
        "Annual Change": f"{mat_info['changes']['annual']}% {'↑' if mat_info['direction'] == 'up' else '↓'}",
    } for material, mat_info in materials.items()]
    
    # Create the data table
    data_table = dash_table.DataTable(
        id='materials-table',
        columns=[
            {"name": "Material", "id": "Material"},
            {"name": "Monthly Change", "id": "Monthly Change"},
            {"name": "Quarterly Change", "id": "Quarterly Change"},
            {"name": "Semi-Annual Change", "id": "Semi-Annual Change"},
            {"name": "Annual Change", "id": "Annual Change"},
        ],
        data=table_data,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '8px'},
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        style_cell_conditional=[
            {
                'if': {'column_id': 'Material'},
                'width': '40%'
            }
        ],
        style_data_conditional=[
            {
                'if': {'filter_query': '{Monthly Change} contains "↑"'},
                'color': 'green'
            },
            {
                'if': {'filter_query': '{Monthly Change} contains "↓"'},
                'color': 'red'
            },
            {
                'if': {'filter_query': '{Quarterly Change} contains "↑"'},
                'color': 'green'
            },
            {
                'if': {'filter_query': '{Quarterly Change} contains "↓"'},
                'color': 'red'
            },
            {
                'if': {'filter_query': '{Semi-Annual Change} contains "↑"'},
                'color': 'green'
            },
            {
                'if': {'filter_query': '{Semi-Annual Change} contains "↓"'},
                'color': 'red'
            },
            {
                'if': {'filter_query': '{Annual Change} contains "↑"'},
                'color': 'green'
            },
            {
                'if': {'filter_query': '{Annual Change} contains "↓"'},
                'color': 'red'
            },
        ],
        row_selectable="single",
        selected_rows=[0],  # Select aluminum by default
    )
    
    return data_table