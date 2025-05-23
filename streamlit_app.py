import streamlit as st
import folium
from streamlit_folium import st_folium
import sqlite3
import requests
import csv
import os

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
                st.rerun()
            else:
                st.error(res.json().get("error", "Something went wrong"))
        except Exception as e:
            st.error(f"Server error: {e}")
    st.stop()


st.set_page_config(layout="wide")
st.title(f"Crime Map Dashboard - Welcome, {st.session_state.username}")

if st.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()


map = folium.Map(location=[7.0, 5.0], zoom_start=6)


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
    folium.CircleMarker(location=[r[2], r[3]], radius=10, color="red", fill=True, tooltip=r[1]).add_to(map)

if os.path.exists("predictions.csv"):
    with open("predictions.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            folium.CircleMarker(
                location=[float(row["latitude"]), float(row["longitude"])],
                radius=12,
                color="blue",
                fill=True,
                fill_opacity=0.8,
                tooltip=f"🔵 Predicted by {row.get('user', 'unknown')}"
            ).add_to(map)

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
                    folium.CircleMarker(
                        location=[payload["latitude"], payload["longitude"]],
                        radius=12,
                        color="blue",
                        fill=True,
                        fill_opacity=0.8,
                        tooltip="🔵 Predicted High Risk"
                    ).add_to(map)
    except Exception as e:
        st.error(f"❌ Failed to load model predictions from dataset: {e}")


st.subheader("Predict Crime Risk at a New Location")
with st.form("predict_form"):
    lat = st.number_input("Latitude", 5.0, 9.0)
    lon = st.number_input("Longitude", 3.0, 7.0)
    past_crimes = st.slider("Past Crimes", 0, 20, 5)
    deaths = st.slider("Deaths", 0, 10, 1)
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
                risk = res.json().get("risk", 0)
                popup_msg = "High Crime Risk!" if risk == 1 else "Low Crime Risk"
                color = "blue" if risk == 1 else "green"

                folium.Marker(
                    location=[lat, lon],
                    popup=popup_msg,
                    icon=folium.Icon(color=color)
                ).add_to(map)

                if risk == 1:
                    file_exists = os.path.exists("predictions.csv")
                    with open("predictions.csv", "a", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=payload.keys())
                        if not file_exists:
                            writer.writeheader()
                        writer.writerow(payload)
                    st.success("⚠️ High crime risk at this location!")
                else:
                    st.info("✅ Low risk of crime at this location.")
            else:
                st.error("❌ Prediction API Error")
        except Exception as e:
            st.error(f"❌ Connection error: {e}")


st_folium(map, width=1400, height=700)
