import requests
import json
import time
from pathlib import Path

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "ItineraireApp/1.0 (contact@tonapp.com)"}

VILLES_BBOX = {
    "paris": (48.815, 2.225, 48.902, 2.470),
    # "rome": (41.800, 12.400, 41.980, 12.600),
    # "barcelona": (41.320, 2.050, 41.470, 2.230),
    #"tokyo": (35.550, 139.600, 35.820, 139.920),
}

def build_query(bbox: tuple) -> str:
    s, w, n, e = bbox
    bbox_str = f"{s},{w},{n},{e}"
    return f"""
    [out:json][timeout:120];
    (
      node["tourism"="museum"]({bbox_str});
      way["tourism"="museum"]({bbox_str});
      node["amenity"="restaurant"]({bbox_str});
      way["amenity"="restaurant"]({bbox_str});
      node["leisure"="park"]({bbox_str});
      way["leisure"="park"]({bbox_str});
    );
    out center tags;
    """

def fetch_ville(bbox: tuple, retries: int = 3) -> list[dict]:
    query = build_query(bbox)
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                OVERPASS_URL,
                data={"data": query},
                headers=HEADERS,
                timeout=150,  # timeout côté client, doit être > timeout Overpass
            )
            response.raise_for_status()
            data = response.json()
            break
        except (requests.HTTPError, requests.Timeout) as e:
            print(f"  Tentative {attempt}/{retries} échouée : {e}")
            if attempt == retries:
                raise
            time.sleep(10)

    pois = []
    for el in data["elements"]:
        tags = el.get("tags", {})
        pois.append({
            "id": el["id"],
            "categorie": tags.get("tourism") or tags.get("amenity") or tags.get("leisure"),
            "nom": tags.get("name"),
            "lat": el.get("lat") or el.get("center", {}).get("lat"),
            "lon": el.get("lon") or el.get("center", {}).get("lon"),
            "horaires": tags.get("opening_hours"),
            "adresse": tags.get("addr:street"),
        })
    return pois

def main():
    Path("data/city").mkdir(parents=True, exist_ok=True)

    for ville, bbox in VILLES_BBOX.items():
        print(f"Récupération des données pour {ville}...")
        try:
            pois = fetch_ville(bbox)
            with open(f"data/city/{ville}.json", "w", encoding="utf-8") as f:
                json.dump(pois, f, ensure_ascii=False, indent=2)
            print(f"  -> {len(pois)} lieux sauvegardés dans data/city/{ville}.json")
        except requests.HTTPError as e:
            print(f"  Erreur définitive pour {ville} : {e}")

        time.sleep(5)

if __name__ == "__main__":
    main()