import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import mysql.connector
import pandas as pd

# Database connection details
db_config = {
    'host': '172.17.0.3',  # Replace with your MariaDB host
    'user': 'root',       # Replace with your MariaDB username
    'password': 'abc@123',  # Replace with your MariaDB password
    'database': 'rastreamento',    # Replace with your database name
    'charset': 'utf8mb4',         # Ensure compatibility with utf8mb4 encoding
    'collation': 'utf8mb4_general_ci'  # Use a MariaDB-supported collation
}

# Connect to MariaDB and fetch data
def fetch_data():
    conn = mysql.connector.connect(**db_config)
    query = "SELECT latitude, longitude, vehicle_id, year, month, day, hour, minute, seconds FROM rastreio_detalhado"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Create Dash app
app = dash.Dash(__name__)

# Layout
app.layout = html.Div([
    html.H1("Rastreamento - Map Visualization"),
    dcc.Graph(id="map"),
    dcc.Dropdown(
        id="vehicle-dropdown",
        placeholder="Select a Vehicle ID",
        options=[],  # Will be populated dynamically
        multi=True
    )
])

# Callbacks
@app.callback(
    Output("map", "figure"),
    Output("vehicle-dropdown", "options"),
    Input("vehicle-dropdown", "value")
)
def update_map(selected_vehicle_ids):
    # Fetch data from database
    df = fetch_data()
    
    # Filter data by selected vehicle IDs
    if selected_vehicle_ids:
        df = df[df["vehicle_id"].isin(selected_vehicle_ids)]
    
    # Create map
    fig = px.scatter_mapbox(
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
    fig.update_layout(mapbox_style="open-street-map", height=600)

    # Update dropdown options
    options = [{"label": vehicle, "value": vehicle} for vehicle in df["vehicle_id"].unique()]
    return fig, options

# Run the app
if __name__ == '__main__':
   app.run_server(debug=True, port=8080)
