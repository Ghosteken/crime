import streamlit as st
import folium
from streamlit_folium import st_folium
import sqlite3
import requests
import csv
import os
from folium import Popup
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

st.set_page_config(layout="wide")

# Set black background and white text globally
st.markdown(
    """
    <style>
    .main {
        background-color: black;
        color: white;
    }
    .stTextInput>div>div>input {
        color: black;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.title("Login or Signup")
    mode = st.radio("Choose", ["Login", "Signup"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Submit"):
        endpoint = f"http://localhost:5001/{'signup' if mode == 'Signup' else 'login'}"
        try:
            res = requests.post(endpoint, json={"username": username, "password": password})
            if res.ok:
                st.success(res.json()["message"])
                st.session_state.logged_in = True
                st.session_state.username = username
                st.stop()

            else:
                st.error(res.json().get("error", "Something went wrong"))
        except Exception as e:
            st.error(f"Server error: {e}")
    st.stop()

st.title(f"Crime Map Dashboard - Welcome, {st.session_state.username}")

if st.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.stop()

# Initialize geolocator once
geolocator = Nominatim(user_agent="crime-predictor-app")

def get_address(lat, lon):
    try:
        location = geolocator.reverse((lat, lon), timeout=10)
        if location is not None:
            return location.address
        else:
            return "Unknown location"
    except GeocoderTimedOut:
        return "Location timeout"

# Create Folium map centered somewhere neutral
map_center = [7.0, 5.0]
map_zoom = 6
map = folium.Map(location=map_center, zoom_start=map_zoom)

# Load crime records from SQLite and add to map
conn = sqlite3.connect("crime.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS CrimeRecord (
    id INTEGER PRIMARY KEY,
    crime_type TEXT,
    latitude REAL,
    longitude REAL
)""")
records = cursor.execute("SELECT * FROM CrimeRecord").fetchall()
for r in records:
    addr = get_address(r[2], r[3])
    folium.CircleMarker(
        location=[r[2], r[3]],
        radius=10,
        color="red",
        fill=True,
        tooltip=addr,
        popup=f"{r[1]} at {addr}"
    ).add_to(map)

# Load previous predictions and add to map with reverse geocoded address
if os.path.exists("predictions.csv"):
    with open("predictions.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            addr = get_address(lat, lon)
            folium.CircleMarker(
                location=[lat, lon],
                radius=12,
                color="blue",
                fill=True,
                fill_opacity=0.8,
                popup=f"🔵 Predicted by {row.get('user', 'unknown')} at {addr}",
            ).add_to(map)

# Load dataset and add high risk predicted points with reverse geocoded address
DATASET_PATH = "network_logs.csv"
if os.path.exists(DATASET_PATH):
    try:
        with open(DATASET_PATH, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                payload = {
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                    "past_crimes": int(row["past_crimes"]),
                    "deaths": int(row["deaths"]),
                    "crime_type_severity_score": int(row["crime_type_severity_score"]),
                    "time_of_day": row["time_of_day"],
                    "day_of_week": row["day_of_week"]
                }
                res = requests.post("http://localhost:5000/predict", json=payload)
                if res.ok and res.json().get("risk", 0) == 1:
                    lat = payload["latitude"]
                    lon = payload["longitude"]
                    addr = get_address(lat, lon)
                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=12,
                        color="blue",
                        fill=True,
                        fill_opacity=0.8,
                        popup=f"🔵 Predicted High Risk at {addr}",
                    ).add_to(map)
    except Exception as e:
        st.error(f"❌ Failed to load model predictions from dataset: {e}")

st.subheader("Predict Crime Risk at a New Location")
with st.form("predict_form"):
    lat = st.number_input("Latitude", -90.0, 90.0, 7.0)
    lon = st.number_input("Longitude", -180.0, 180.0, 5.0)
    past_crimes = st.slider("Past Crimes", 0, 20, 5)
    deaths = st.slider("Deaths", 0, 20, 1)
    severity = st.slider("Severity Score", 1, 10, 5)
    time_of_day = st.selectbox("Time of Day", ["morning", "afternoon", "night"])
    day_of_week = st.selectbox("Day", ["weekday", "weekend"])
    submit = st.form_submit_button("Predict")

if submit:
    payload = {
        "latitude": lat,
        "longitude": lon,
        "past_crimes": past_crimes,
        "deaths": deaths,
        "crime_type_severity_score": severity,
        "time_of_day": time_of_day,
        "day_of_week": day_of_week,
        "user": st.session_state.username
    }

    try:
        res = requests.post("http://localhost:5000/predict", json=payload)
        if res.ok:
            result = res.json()
            risk = result.get("risk", 0)
            crime_type = result.get("crime_type", "Unknown")
            addr = get_address(lat, lon)
            popup_msg = f"{'High' if risk == 1 else 'Low'} Crime Risk - {crime_type} at {addr}"
            color = "blue" if risk == 1 else "green"

            popup = Popup(popup_msg, max_width=300)
            marker = folium.Marker(location=[lat, lon], popup=popup, icon=folium.Icon(color=color))
            marker.add_to(map)

            # Center map on the predicted location with zoom 12
            map.location = [lat, lon]
            map.zoom_start = 12

            # Save prediction to CSV if high risk
            if risk == 1:
                file_exists = os.path.exists("predictions.csv")
                with open("predictions.csv", "a", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=payload.keys())
                    if not file_exists:
                        writer.writeheader()
                    writer.writerow(payload)
                st.success(f"⚠️ High crime risk at this location! Type: {crime_type}")
            else:
                st.info(f"✅ Low risk of crime at this location. Type: {crime_type}")
        else:
            st.error(res.json().get("error", "❌ Prediction API Error"))
    except Exception as e:
        st.error(f"❌ Connection error: {e}")

st_folium(map, width=1400, height=700)
