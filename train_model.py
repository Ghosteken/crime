import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

data = pd.read_csv("crime_dataset.csv")
le_time = LabelEncoder()
le_day = LabelEncoder()
data["time_of_day"] = le_time.fit_transform(data["time_of_day"])
data["day_of_week"] = le_day.fit_transform(data["day_of_week"])

X = data.drop(columns=["risk_level"])
y = data["risk_level"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model = RandomForestClassifier()
model.fit(X_train, y_train)

with open("crime_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("✅ Model trained and saved.")
