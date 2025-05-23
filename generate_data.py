import pandas as pd
import numpy as np

np.random.seed(42)
data = pd.DataFrame({
    "latitude": np.random.uniform(5.0, 9.0, 500),
    "longitude": np.random.uniform(3.0, 7.0, 500),
    "past_crimes": np.random.poisson(5, 500),
    "deaths": np.random.binomial(3, 0.2, 500),
    "crime_type_severity_score": np.random.randint(1, 10, 500),
    "time_of_day": np.random.choice(["morning", "afternoon", "night"], 500),
    "day_of_week": np.random.choice(["weekday", "weekend"], 500)
})
data["risk_level"] = ((data["past_crimes"] + data["crime_type_severity_score"] + data["deaths"]) > 10).astype(int)
data.to_csv("crime_dataset.csv", index=False)
print("✅ Data generated.")
