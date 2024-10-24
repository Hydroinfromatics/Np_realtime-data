# Corrected and improved version of the code based on the provided content

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


def create_header():
    return html.Div([
        html.Div([
            html.Div([
                html.H1("Water Monitoring Unit", style={'text-align': 'center', 'color': '#010738', 'margin': '0'}),
                html.H3("Nanoorpar", style={'text-align': 'center', 'color': '#010738', 'margin': '8px 0 0 0'}),
            ]),
        ], style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'})
    ])


# Callback function to fetch and display data from API
@app.callback(
    [Output('output-data', 'children'),
     Output('pH-value', 'children'),
     Output('TDS-value', 'children'),
     Output('Depth-value', 'children'),
     Output('FlowInd-value', 'children'),
     Output('graph-output', 'figure')],
    [Input('duration-dropdown', 'value'),
     Input('column-dropdown', 'value')],
)
def update_data(selected_duration, selected_column):
    try:
        # Fetch data from API
        response = requests.get(f"{API_URL}/data")
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
        else:
            return ["No data available. Please check the API connection."] + ["N/A"] * 4 + [go.Figure()]

        # Filter based on the selected duration
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        end_time = df['Timestamp'].max()
        start_time = end_time - TIME_DURATIONS[selected_duration]
        df_filtered = df[(df['Timestamp'] >= start_time) & (df['Timestamp'] <= end_time)]

        # Create the graph
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

        # Get the latest values
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