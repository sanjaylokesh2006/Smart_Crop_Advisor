import requests

def fetch_soil_ph(lat, lon):
    url = (
      "https://maps.isric.org/mapserv?map=/map/soilgrids.map"
      "&SERVICE=WCS&REQUEST=GetCoverage&COVERAGE=PHIHOX_M_sl1_250m"
      f"&SUBSETTINGCRITERIA={lat},{lon}&FORMAT=application/json"
    )
    r = requests.get(url); return r.json()["properties"]["value"]

def fetch_weather(lat, lon):
    url = (
      f"https://api.open-meteo.com/v1/forecast?"
      f"latitude={lat}&longitude={lon}&hourly=temperature_2m"
    )
    r = requests.get(url); return r.json()["hourly"]["temperature_2m"][0]
