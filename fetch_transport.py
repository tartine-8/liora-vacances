import pandas as pd
import numpy as np
import json

def haversine_distance(lat1, lon1, lat2_array, lon2_array):
    """Distance en mètres entre un point et un tableau de points (formule vectorisée)."""
    R = 6371000  # rayon de la Terre en mètres
    lat1, lon1 = np.radians(lat1), np.radians(lon1)
    lat2_array = np.radians(lat2_array)
    lon2_array = np.radians(lon2_array)

    dlat = lat2_array - lat1
    dlon = lon2_array - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2_array) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def load_stops(transport: str) -> pd.DataFrame:
    stops = pd.read_csv(f"{transport}/stops.txt")
    # On garde uniquement les colonnes utiles et on filtre les lignes sans coordonnées
    stops = stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]].dropna()
    return stops

def find_nearest_stop(poi_lat: float, poi_lon: float, stops: pd.DataFrame) -> dict:
    distances = haversine_distance(
        poi_lat, poi_lon,
        stops["stop_lat"].values, stops["stop_lon"].values
    )
    idx_min = np.argmin(distances)
    return {
        "stop_id": stops.iloc[idx_min]["stop_id"],
        "stop_name": stops.iloc[idx_min]["stop_name"],
        "distance_m": round(float(distances[idx_min]), 1),
    }

def main():
    stops = load_stops("data/transport")
    print(f"{len(stops)} arrêts chargés depuis le GTFS")

    with open("data/cleaned/paris_cleaned.json", "r", encoding="utf-8") as f:
        pois = json.load(f)

    enriched = []
    for poi in pois:
        nearest = find_nearest_stop(poi["lat"], poi["lon"], stops)
        poi["arret_proche"] = nearest
        enriched.append(poi)

    with open("data/cleaned/paris_with_stops.json", "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"{len(enriched)} POI enrichis avec leur arrêt le plus proche")
    print("Exemple :", enriched[0])

if __name__ == "__main__":
    main()