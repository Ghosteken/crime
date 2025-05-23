from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle

app = Flask(__name__)
CORS(app)

with open("crime_model.pkl", "rb") as f:
    model = pickle.load(f)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    features = [[
        data["latitude"],
        data["longitude"],
        data["past_crimes"],
        data["deaths"],
        data["crime_type_severity_score"],
        2 if data["time_of_day"] == "night" else 1,
        1 if data["day_of_week"] == "weekend" else 0
    ]]
    risk = model.predict(features)[0]
    return jsonify({"risk": int(risk)})

if __name__ == "__main__":
    app.run(debug=True)
