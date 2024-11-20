import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import mysql.connector
import pandas as pd

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

# Calculate distances and aggregate by vehicle and month
def calculate_distances(df):
    df['datetime'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute', 'seconds']])
    df = df.sort_values(['vehicle_id', 'datetime'])
    
    distances = []
    for vehicle_id, group in df.groupby('vehicle_id'):
        group = group.reset_index(drop=True)
        group['distance'] = group.apply(
            lambda row: geodesic(
                (row['latitude'], row['longitude']),
                (group.loc[row.name - 1, 'latitude'], group.loc[row.name - 1, 'longitude'])
            ).meters if row.name > 0 else 0,
            axis=1
        )
        distances.append(group)
    
    distance_df = pd.concat(distances)
    distance_summary = (
        distance_df.groupby(['vehicle_id', 'year', 'month'])['distance']
        .sum()
        .reset_index()
        .rename(columns={'distance': 'total_distance_meters'})
    )
    return distance_summary

# Create Dash app
app = dash.Dash(__name__)

# Layout
app.layout = html.Div([
    html.H1("Rastreamento - Map Visualization and Distance Table"),
    dcc.Graph(id="map"),
    dcc.Dropdown(
        id="vehicle-dropdown",
        placeholder="Select a Vehicle ID",
        options=[],  # Will be populated dynamically
        multi=True
    ),
    html.H2("Distance Traveled per Month"),
    dcc.Graph(id="distance-table")
])

# Callbacks
@app.callback(
    [Output("map", "figure"), Output("vehicle-dropdown", "options"), Output("distance-table", "figure")],
    [Input("vehicle-dropdown", "value")]
)
def update_map_and_table(selected_vehicle_ids):
    # Fetch data
    df = fetch_data()
    
    # Filter data by selected vehicle IDs
    if selected_vehicle_ids:
        df = df[df["vehicle_id"].isin(selected_vehicle_ids)]
    
    # Create map
    fig_map = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        color="vehicle_id",
        hover_data={"latitude": True, "longitude": True, "vehicle_id": True,
                    "year": True, "month": True, "day": True,
                    "hour": True, "minute": True, "seconds": True},
        title="Vehicle Tracking Map",
        zoom=10
    )
    fig_map.update_layout(mapbox_style="open-street-map", height=600)

    # Update dropdown options
    options = [{"label": vehicle, "value": vehicle} for vehicle in df["vehicle_id"].unique()]

    # Calculate distances
    distance_summary = calculate_distances(df)
    
    # Create distance table
    fig_table = px.bar(
        distance_summary,
        x="month",
        y="total_distance_meters",
        color="vehicle_id",
        barmode="group",
        text="total_distance_meters",
        title="Total Distance Traveled per Month for Each Vehicle"
    )
    fig_table.update_layout(xaxis_title="Month", yaxis_title="Distance (meters)", height=500)

    return fig_map, options, fig_table


# Run the app
if __name__ == '__main__':
   app.run_server(debug=True, port=8080, host='0.0.0.0')
