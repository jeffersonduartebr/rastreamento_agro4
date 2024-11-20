import random
import mysql.connector

# Database connection details
db_config = {
    'host': 'bd',  # Replace with your MariaDB host
    'user': 'root',       # Replace with your MariaDB username
    'password': 'abc.123',  # Replace with your MariaDB password
    'database': 'rastreamento',   # Replace with your database name
    'charset': 'utf8mb4',         # Ensure compatibility with utf8mb4 encoding
    'collation': 'utf8mb4_general_ci'  # Use a MariaDB-supported collation
}

# Connect to MariaDB
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Create the table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS rastreio_detalhado (
    year INT,
    month INT,
    day INT,
    hour INT,
    minute INT,
    seconds INT,
    latitude DOUBLE,
    longitude DOUBLE,
    vehicle_id VARCHAR(50)
)
''')

conn.commit()

# Define coordinate boundaries
latitude_min = -5.66241145639103
latitude_max = -5.597458971140155
longitude_min = -37.83054689188353
longitude_max = -37.79891455406674

# Generate synthetic data
data = []

for _ in range(300):
    year = random.randint(2024, 2024)
    month = random.randint(1, 12)
    day = random.randint(1, 28)  # Simplified for demonstration
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    seconds = random.randint(0, 59)
    latitude = random.uniform(latitude_min, latitude_max)
    longitude = random.uniform(longitude_min, longitude_max)
    vehicle_id = f"V-{random.randint(1, 5)}"
    
    data.append((year, month, day, hour, minute, seconds, latitude, longitude, vehicle_id))

# Insert synthetic data into the table
cursor.executemany('''
INSERT INTO rastreio_detalhado (year, month, day, hour, minute, seconds, latitude, longitude, vehicle_id)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
''', data)

conn.commit()

# Verify data insertion
cursor.execute('SELECT * FROM rastreio_detalhado LIMIT 10')
for row in cursor.fetchall():
    print(row)

# Close the connection
cursor.close()
conn.close()
