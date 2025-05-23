from flask import Flask, request, jsonify
import pickle
import numpy as np

app = Flask(__name__)

with open("crime_model.pkl", "rb") as f:
    model = pickle.load(f)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()

    features = [
        data["latitude"],
        data["longitude"],
        data["past_crimes"],
        data["deaths"],
        data["crime_type_severity_score"],
        1 if data["time_of_day"] == "night" else 0,
        1 if data["day_of_week"] == "weekend" else 0
    ]

    prediction = model.predict([features])[0]

    return jsonify({"risk": int(prediction)})

if __name__ == "__main__":
    app.run(debug=True)
