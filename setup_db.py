import sqlite3
import pandas as pd

conn = sqlite3.connect("crime.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS CrimeRecord (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT,
    latitude REAL,
    longitude REAL
)
""")

df = pd.read_csv("crime_dataset.csv")
for _, row in df.iterrows():
    if row["risk_level"] == 1:
        cursor.execute("INSERT INTO CrimeRecord (location, latitude, longitude) VALUES (?, ?, ?)", (
            "High Risk Area", row["latitude"], row["longitude"]
        ))

conn.commit()
conn.close()
print("✅ Database setup complete.")
