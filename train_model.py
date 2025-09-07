import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import joblib
import os

# 1. Load your CSV
df = pd.read_csv("crop_data.csv")

# 2. Train
X = df[["ph", "temperature"]]
y = df["best_crop"]
model = DecisionTreeClassifier().fit(X, y)

# 3. Save
output_path = "crop_model.pkl"
joblib.dump(model, output_path)

# 4. Confirm
print(f"✅ Model saved at {os.path.abspath(output_path)}")
