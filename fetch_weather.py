import requests
import json
from pathlib import Path

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

VILLES_COORDS = {
    "paris": (48.8566, 2.3522),
}

WEATHER_CODES = {
    0: {"fr": "Ciel dégagé", "icone": "☀️"},
    1: {"fr": "Plutôt dégagé", "icone": "🌤️"},
    2: {"fr": "Partiellement nuageux", "icone": "⛅"},
    3: {"fr": "Couvert", "icone": "☁️"},
    45: {"fr": "Brouillard", "icone": "🌫️"},
    48: {"fr": "Brouillard givrant", "icone": "🌫️"},
    51: {"fr": "Bruine légère", "icone": "🌦️"},
    53: {"fr": "Bruine modérée", "icone": "🌦️"},
    55: {"fr": "Bruine dense", "icone": "🌧️"},
    56: {"fr": "Bruine verglaçante légère", "icone": "🌧️"},
    57: {"fr": "Bruine verglaçante dense", "icone": "🌧️"},
    61: {"fr": "Pluie légère", "icone": "🌦️"},
    63: {"fr": "Pluie modérée", "icone": "🌧️"},
    65: {"fr": "Pluie forte", "icone": "🌧️"},
    66: {"fr": "Pluie verglaçante légère", "icone": "🌧️"},
    67: {"fr": "Pluie verglaçante forte", "icone": "🌧️"},
    71: {"fr": "Neige légère", "icone": "🌨️"},
    73: {"fr": "Neige modérée", "icone": "❄️"},
    75: {"fr": "Neige forte", "icone": "❄️"},
    77: {"fr": "Grains de neige", "icone": "❄️"},
    80: {"fr": "Averses légères", "icone": "🌦️"},
    81: {"fr": "Averses modérées", "icone": "🌧️"},
    82: {"fr": "Averses violentes", "icone": "⛈️"},
    85: {"fr": "Averses de neige légères", "icone": "🌨️"},
    86: {"fr": "Averses de neige fortes", "icone": "❄️"},
    95: {"fr": "Orage", "icone": "⛈️"},
    96: {"fr": "Orage avec grêle légère", "icone": "⛈️"},
    99: {"fr": "Orage avec grêle forte", "icone": "⛈️"},
}


def fetch_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "hourly": "temperature_2m,precipitation,weathercode,cloudcover",
        "timezone": "auto",
        "forecast_days": 5,
    }
    response = requests.get(WEATHER_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def build_daily_forecast(data: dict) -> list[dict]:
    daily = data["daily"]
    forecast = []
    for i in range(len(daily["time"])):
        code = daily["weathercode"][i]
        meteo = WEATHER_CODES.get(code, {"fr": "Inconnu", "icone": "❓"})
        forecast.append({
            "date": daily["time"][i],
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "precipitation": daily["precipitation_sum"][i],
            "weathercode": code,
            "condition": meteo["fr"],
            "icone": meteo["icone"],
        })
    return forecast


def build_hourly_forecast(data: dict) -> list[dict]:
    hourly = data["hourly"]
    forecast = []
    for i in range(len(hourly["time"])):
        code = hourly["weathercode"][i]
        meteo = WEATHER_CODES.get(code, {"fr": "Inconnu", "icone": "❓"})
        forecast.append({
            "datetime": hourly["time"][i],
            "temperature": hourly["temperature_2m"][i],
            "precipitation": hourly["precipitation"][i],
            "couverture_nuageuse": hourly["cloudcover"][i],
            "weathercode": code,
            "condition": meteo["fr"],
            "icone": meteo["icone"],
        })
    return forecast


def main():
    Path("data/weather").mkdir(parents=True, exist_ok=True)

    for ville, (lat, lon) in VILLES_COORDS.items():
        print(f"Récupération météo pour {ville}...")
        data = fetch_weather(lat, lon)

        daily_forecast = build_daily_forecast(data)
        with open(f"data/weather/{ville}.json", "w", encoding="utf-8") as f:
            json.dump(daily_forecast, f, ensure_ascii=False, indent=2)
        print(f"  -> {len(daily_forecast)} jours sauvegardés dans {ville}.json")

        hourly_forecast = build_hourly_forecast(data)
        with open(f"data/weather/{ville}_hourly.json", "w", encoding="utf-8") as f:
            json.dump(hourly_forecast, f, ensure_ascii=False, indent=2)
        print(f"  -> {len(hourly_forecast)} points horaires sauvegardés dans {ville}_hourly.json")


if __name__ == "__main__":
    main()