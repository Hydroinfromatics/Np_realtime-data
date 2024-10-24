

# The rest of your code remains the same, starting from:
# Import statements...
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import defaultdict
import requests
from flask import Flask, request, render_template, redirect, url_for
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from branca.colormap import LinearColormap
from functools import lru_cache
from data_process import process_data
from get_data import fetch_data_from_api
# Configuration
API_URL = "https://mongodb-api-hmeu.onrender.com"
COLUMNS = ['TDS', 'pH', 'Depth', 'FlowInd', 'Timestamp']
Y_RANGES = {
    "pH": [7, 10],
    "TDS": [0, 500],
    "Depth": [0, 100],  # Adjust range as needed
    "FlowInd": [0, 15]
}
TIME_DURATIONS = {
    '1 Hour': timedelta(hours=1),
    '3 Hours': timedelta(hours=3),
    '6 Hours': timedelta(hours=6),
    '12 Hours': timedelta(hours=12),
    '24 Hours': timedelta(hours=24),
    '3 Days': timedelta(days=3),
    '1 Week': timedelta(weeks=1)
}
UNITS = {
    "pH": "",
    "TDS": "ppm",
    "Depth": "m",
    "FlowInd": "kL per 10 min"
}

# Initialize Flask and Dash apps
server = Flask(__name__)
server.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
app = dash.Dash(__name__, server=server, url_base_pathname='/dashboard/')


# Add these functions before the app.layout definition:

def create_header():
    return html.Div([
        html.Div([
            html.Div([
                html.H1("Water Monitoring Unit", style={'text-align': 'center', 'color': '#010738', 'margin': '0'}),
                html.H3("Nanoorpar", style={'text-align': 'center', 'color': '#010738', 'margin': '8px 0 0 0'}),
            ]),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'maxWidth': '1200px', 'margin': '0 auto', 'padding': '0 20px'})
    ], style={'width': '100%', 'backgroundColor': '#f5f5f5', 'padding': '10px 0', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'})

def create_footer():
    return html.Footer([
        html.Div([
            html.P('Dashboard - Powered by ICCW', style={'fontSize': '12px', 'margin': '5px 0'}),
            html.P('Technology Implementation Partner - EyeNet Aqua', style={'fontSize': '12px', 'margin': '5px 0'}),
        ], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '0 20px', 'textAlign': 'center'})
    ], style={'width': '100%', 'backgroundColor': '#f9f9f9', 'padding': '20px 0', 'marginTop': '20px', 'boxShadow': '0 -2px 5px rgba(0,0,0,0.1)'})
# Dash layout
app.layout = html.Div([
    create_header(),
    html.Div([
        html.H3("Water Quality", style={'textAlign': 'center','color': '#7ec1fd'}),
        html.Div(id='error-message', style={'color': '#e74c3c', 'textAlign': 'center', 'margin': '10px 0'}),
        html.Div([html.Div(id=f'{param.lower()}', className='value-box') for param in ['pH', 'TDS', 'Depth', 'FlowInd']],
                 style={
                     'display': 'flex',
                     'flexWrap': 'wrap',
                     'justifyContent': 'space-around',
                     'alignItems': 'center',
                     'margin': '20px 0',
                     'padding': '20px',
                     'backgroundColor': '#ffffff',
                     'fontWeight': 'bold',
                     'fontSize': '30px',
                     'color': 'black',
                     'textAlign': 'center',
                     'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)',
                     'border': '1px solid #7ec1fd',
                     'borderRadius': '10px'
                 }),
        html.Div([
            html.Div([
                html.Div([
                    html.P("Select Parameter:", style={'marginBottom': '5px'}),
                    dcc.Dropdown(
                        id="dist_column",
                        options=[{'label': col, 'value': col} for col in ['TDS', 'pH', 'Depth', 'FlowInd']],
                        value="pH",
                        clearable=False,
                        style={'width': '200px'}
                    )
                ], style={'flex': 1, 'marginRight': '10px'}),
                html.Div([
                    html.P("Select Time Duration:", style={'marginBottom': '5px'}),
                    dcc.Dropdown(
                        id="time_duration",
                        options=[{'label': k, 'value': k} for k in TIME_DURATIONS.keys()],
                        value='3 Hours',
                        clearable=False,
                        style={'width': '200px'}
                    )
                ], style={'flex': 1})
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '20px'}),
            dcc.Graph(id="graph", style={'height': '600px'})
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'})
    ], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '0 20px'}),
    create_footer(),
    dcc.Interval(id='interval-component', interval=60000, n_intervals=0)
], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f9f9f9'})

@app.callback(
    [Output('error-message', 'children')] +
    [Output(f'{param.lower()}', 'children') for param in ['pH', 'TDS', 'Depth', 'FlowInd']] +
    [Output('graph', 'figure')],
    [Input('interval-component', 'n_intervals'),
     Input('dist_column', 'value'),
     Input('time_duration', 'value')]
)
def update_dashboard(n, selected_column, selected_duration):
    try:
        data = fetch_data_from_api(API_URL)
        df = process_data(data)
        
        if df.empty:
            return ["No data available. Please check the API connection."] + ["N/A"] * 4 + [go.Figure()]

        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        end_time = df['Timestamp'].max()
        start_time = end_time - TIME_DURATIONS[selected_duration]
        df_filtered = df[(df['Timestamp'] >= start_time) & (df['Timestamp'] <= end_time)]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_filtered['Timestamp'],
            y=df_filtered[selected_column],
            mode='lines+markers',
            line=dict(color='green')
        ))
        
        y_min, y_max = Y_RANGES.get(selected_column, [None, None])
        
        fig.update_layout(
            title=f'{selected_column} Vs {selected_duration}',
            xaxis_title='Time (hrs)', 
            yaxis_title=f'{selected_column} ({UNITS[selected_column]})', 
            yaxis=dict(range=[y_min, y_max]),
            height=600, 
            margin=dict(l=50, r=50, t=50, b=50),
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            font=dict(size=14)
        )

        latest = df.iloc[-1] if not df.empty else pd.Series()
        value_boxes = []
        for param in ['pH', 'TDS', 'Depth', 'FlowInd']:
            value = latest.get(param, 'N/A')
            if value != 'N/A':
                value = f"{value:.2f}"
            value_boxes.append(html.Div([
                html.Div(param, style={'fontSize': '18px', 'marginBottom': '5px'}),
                html.Div(f"{value} {UNITS[param]}", style={'fontSize': '18px'})
            ]))

        return [None] + value_boxes + [fig]
    
    except Exception as e:
        return [f"An error occurred: {str(e)}"] + ["Error"] * 4 + [go.Figure()]

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5080))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    server.run(host='0.0.0.0', port=port, debug=debug)