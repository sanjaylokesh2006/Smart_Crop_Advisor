from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import requests
import joblib

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load city→pH & best_crop mapping
df = pd.read_csv("city_crop_data.csv")
model = joblib.load("crop_model.pkl")

WEATHER_API_KEY = "a893f9b0ade304d8c21b0d6353a78ce7"
AMBEE_API_KEY = "387063bcc04d0c4a8a9e0b99a72330710d44138cd2dda4e374e3dee5a5d7c895"

class City(BaseModel):
    city: str

# 🔹 Fetch temperature using OpenWeatherMap
def fetch_weather_by_city(city_name: str) -> float:
    geo_url = (
        f"http://api.openweathermap.org/geo/1.0/direct"
        f"?q={city_name},IN&limit=1&appid={WEATHER_API_KEY}"
    )
    geo_resp = requests.get(geo_url)
    if geo_resp.status_code != 200 or not geo_resp.json():
        raise HTTPException(status_code=404, detail="City not found via geocoding")
    loc = geo_resp.json()[0]
    lat, lon = loc["lat"], loc["lon"]

    weather_url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
    )
    weather_resp = requests.get(weather_url)
    if weather_resp.status_code == 401:
        raise HTTPException(status_code=502, detail="Invalid weather API key")
    if weather_resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Weather API error: {weather_resp.status_code}")
    temp = weather_resp.json().get("main", {}).get("temp")
    if temp is None:
        raise HTTPException(status_code=502, detail="Invalid weather data")
    return temp, lat, lon

# 🔹 Fetch soil pH using Ambee
def fetch_soil_ph_ambee(lat: float, lon: float) -> float:
    url = f"https://api.ambeedata.com/soil/latest/by-lat-lng?lat={lat}&lng={lon}"
    headers = {
        "x-api-key": AMBEE_API_KEY,
        "Content-type": "application/json"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print("⚠️ Soil API failed, using fallback pH")
        return None
    ph = resp.json().get("data", {}).get("soil_ph")
    if ph is None:
        print("⚠️ Soil pH missing, using fallback pH")
        return None
    return float(ph)

# 🔹 Fetch air quality using Ambee
def fetch_air_quality(lat: float, lon: float) -> dict:
    url = f"https://api.ambeedata.com/latest/by-lat-lng?lat={lat}&lng={lon}"
    headers = {
        "x-api-key": AMBEE_API_KEY,
        "Content-type": "application/json"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return {"aqi": "Unavailable", "pollutants": {}}
    data = resp.json().get("stations", [{}])[0]
    return {
        "aqi": data.get("AQI", "N/A"),
        "pollutants": {
            "PM2.5": data.get("PM2.5"),
            "PM10": data.get("PM10"),
            "CO": data.get("CO"),
            "NO2": data.get("NO2"),
            "SO2": data.get("SO2")
        }
    }

# 🔹 Fetch disaster alerts using Ambee
def fetch_disaster_alerts(lat: float, lon: float) -> list:
    url = f"https://api.ambeedata.com/natural-disaster/latest/by-lat-lng?lat={lat}&lng={lon}"
    headers = {
        "x-api-key": AMBEE_API_KEY,
        "Content-type": "application/json"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return []
    return resp.json().get("data", [])

# 🔹 Main recommendation endpoint
@app.post("/recommend")
def recommend(req: City):
    name = req.city.strip().lower()
    row = df[df["city"].str.lower() == name]

    if not row.empty:
        # Use CSV data
        ph = float(row.iloc[0]["ph"])
        crop = row.iloc[0]["best_crop"]
        temp, lat, lon = fetch_weather_by_city(req.city)
    else:
        # Use live data
        temp, lat, lon = fetch_weather_by_city(req.city)
        ph = fetch_soil_ph_ambee(lat, lon)
        if ph is None:
            ph = 6.5  # fallback pH for unknown regions
        crop = model.predict([[ph, temp]])[0]

    air_quality = fetch_air_quality(lat, lon)
    disasters = fetch_disaster_alerts(lat, lon)

    return {
        "recommended_crop": crop,
        "ph": ph,
        "temperature": temp,
        "air_quality": air_quality,
        "disaster_alerts": disasters
    }
