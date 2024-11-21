import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import mysql.connector
import pandas as pd
from geopy.distance import geodesic  # To calculate distances

# Database connection details
db_config = {
    'host': 'bd',  # Replace with your MariaDB host
    'user': 'root',       # Replace with your MariaDB username
    'password': 'abc.123',  # Replace with your MariaDB password
    'database': 'rastreamento',    # Replace with your database name
    'charset': 'utf8mb4',         # Ensure compatibility with utf8mb4 encoding
    'collation': 'utf8mb4_general_ci'  # Use a MariaDB-supported collation
}

# Fetch data from database
def fetch_data():
    conn = mysql.connector.connect(**db_config)
    query = "SELECT latitude, longitude, vehicle_id, year, month, day, hour, minute, seconds FROM rastreio_detalhado ORDER BY vehicle_id, year, month, day, hour, minute, seconds"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Calculate distances and speeds
def process_data(df):
    df['datetime'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute', 'seconds']])
    df = df.sort_values(['vehicle_id', 'datetime'])
    
    distances = []
    speeds = []
    stops = []
    for vehicle_id, group in df.groupby('vehicle_id'):
        group = group.reset_index(drop=True)
        group['distance'] = group.apply(
            lambda row: geodesic(
                (row['latitude'], row['longitude']),
                (group.loc[row.name - 1, 'latitude'], group.loc[row.name - 1, 'longitude'])
            ).meters if row.name > 0 else 0,
            axis=1
        )
        group['speed'] = group['distance'] / group['datetime'].diff().dt.total_seconds().fillna(1)
        group['speed'] = group['speed'].fillna(0).replace([float('inf'), float('-inf')], 0) * 3.6  # Convert m/s to km/h
        distances.append(group)
    return pd.concat(distances)

# Create Dash app
app = dash.Dash(__name__)

# Layout
app.layout = html.Div([
    html.H1("Rastreamento Veicular - Dashboard"),
    dcc.Tabs(id="tabs", value="trajectory", children=[
        dcc.Tab(label="Trajetórias", value="trajectory"),
        dcc.Tab(label="Paradas e Tempo de Parada", value="stops"),
        dcc.Tab(label="Comparação de Uso de Veículos", value="comparison"),
        dcc.Tab(label="Velocidade ao Longo do Tempo", value="speed"),
    ]),
    html.Div(id="content"),
    dcc.Interval(
        id="interval-component",
        interval=300000,  # 300,000 ms = 5 minutes
        n_intervals=0
    )
])

@app.callback(
    Output("content", "children"),
    [Input("tabs", "value"), Input("interval-component", "n_intervals")]
)
def render_tab_content(tab):
    df = fetch_data()
    processed_df = process_data(df)
    
    if tab == "trajectory":
        # Trajectory Visualization
        fig = px.line_mapbox(
            processed_df,
            lat="latitude",
            lon="longitude",
            color="vehicle_id",
            line_group="vehicle_id",
            hover_data={"datetime": True},
            title="Trajetórias dos Veículos"
        )
        fig.update_layout(mapbox_style="open-street-map", height=600)
        return dcc.Graph(figure=fig)
    
    elif tab == "stops":
        # Stops and Idle Time Visualization
        stop_data = processed_df[processed_df['speed'] < 5]  # Filter low-speed data as stops
        stop_data['idle_time'] = stop_data['datetime'].diff().dt.total_seconds() / 60  # Idle time in minutes
        stop_data['idle_time'] = stop_data['idle_time'].abs().fillna(1)  # Remove negative values
        #stop_data['idle_time'] = stop_data['idle_time'].fillna(1)
        fig = px.scatter_mapbox(
            stop_data,
            lat="latitude",
            lon="longitude",
            size="idle_time",
            color="vehicle_id",
            hover_data={"idle_time": "Idle Time (minutes)"},
            title="Paradas e Tempos de Parada dos Veículos"
        )
        fig.update_layout(mapbox_style="open-street-map", height=600)
        return dcc.Graph(figure=fig)
    
    elif tab == "comparison":
        # Comparison of Vehicle Usage
        usage_summary = processed_df.groupby("vehicle_id")['distance'].sum().reset_index()
        usage_summary['distance'] = usage_summary['distance'] / 1000  # Convert to km
        usage_summary['distance'] = usage_summary['distance'].round(2)
        fig = px.bar(
            usage_summary,
            x="vehicle_id",
            y="distance",
            text="distance",
            title="Comparação de Distância Percorrida pelos Veículos (em km)"
        )
        fig.update_layout(xaxis_title="Vehicle ID", yaxis_title="Distância (km)", height=600)
        return dcc.Graph(figure=fig)
    
    elif tab == "speed":
        # Speed Over Time
        fig = px.line(
            processed_df,
            x="datetime",
            y="speed",
            color="vehicle_id",
            title="Velocidade dos Veículos ao Longo do Tempo"
        )
        fig.update_layout(xaxis_title="Date/Time", yaxis_title="Velocidade (km/h)", height=600)
        return dcc.Graph(figure=fig)

# Run the app

if __name__ == '__main__':
    app.run_server(debug=True, port=8080, host='0.0.0.0', threaded=True)
