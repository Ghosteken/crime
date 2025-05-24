from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

app = Flask(__name__)
CORS(app)

with open("crime_model.pkl", "rb") as f:
    model = pickle.load(f)

CRIME_TYPE_MAP = {
    0: "Theft",
    1: "Robbery",
    2: "Assault",
    3: "Burglary",
    4: "Vandalism",
}

def is_valid_location(lat, lon):
    try:
        geolocator = Nominatim(user_agent="crime-predictor")
        location = geolocator.reverse((lat, lon), timeout=10)
        if location is None or "country" not in location.raw.get("address", {}):
            return False, None
        return True, location.raw["address"].get("country", "Unknown")
    except GeocoderTimedOut:
        return False, None

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json

    is_valid, country = is_valid_location(data["latitude"], data["longitude"])
    if not is_valid:
        return jsonify({"error": "Invalid location - possibly sea or unrecognized area."}), 400

    df = pd.DataFrame([{
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "past_crimes": data["past_crimes"],
        "deaths": data["deaths"],
        "crime_type_severity_score": data["crime_type_severity_score"],
        "time_of_day": 2 if data["time_of_day"] == "night" else 1,
        "day_of_week": 1 if data["day_of_week"] == "weekend" else 0
    }])

    risk = model.predict(df)[0]
    crime_type_idx = model.predict_proba(df).argmax()
    crime_type_name = CRIME_TYPE_MAP.get(crime_type_idx, "Unknown")

    return jsonify({
        "risk": int(risk),
        "crime_type": crime_type_name,
        "country": country
    })

if __name__ == "__main__":
    app.run(debug=True)
