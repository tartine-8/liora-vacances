import requests

OSRM_URL = "https://routing.openstreetmap.de/routed-foot/route/v1/foot"
PRIM_BASE_URL = "https://prim.iledefrance-mobilites.fr/marketplace/v2"
PRIM_TOKEN = "vbWAvpv8buv4y7hVwmsCe4UkeD71QnqK"  # remplace par ton vrai token généré sur prim.iledefrance-mobilites.fr


def get_walking_route(lat1, lon1, lat2, lon2):
    url = f"{OSRM_URL}/{lon1},{lat1};{lon2},{lat2}"
    params = {"overview": "false"}

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Erreur OSRM : {e}")
        return None

    print(f"  DEBUG OSRM response code : {data.get('code')}")  # ligne temporaire

    if data.get("code") != "Ok":
        return None

    route = data["routes"][0]
    duree_min = route["duration"] / 60
    distance_m = route["distance"]

    vitesse_kmh = (distance_m / 1000) / (duree_min / 60) if duree_min > 0 else 0
    print(f"  DEBUG vitesse calculée : {vitesse_kmh:.1f} km/h")  # ligne temporaire
    if vitesse_kmh > 7:
        print(f"  Attention : vitesse incohérente détectée ({vitesse_kmh:.1f} km/h) — donnée OSRM suspecte")
        return None

    return {
        "mode": "pied",
        "duree_min": round(duree_min, 1),
        "distance_m": round(distance_m, 0),
    }


def get_transit_journey(lat1, lon1, lat2, lon2, datetime_str="20260911T090000"):
    """Calcule un itinéraire en transport en commun via l'API Navitia (PRIM)."""
    url = f"{PRIM_BASE_URL}/navitia/journeys"
    params = {
        "from": f"{lon1};{lat1}",
        "to": f"{lon2};{lat2}",
        "datetime": datetime_str,
    }
    headers = {"apiKey": PRIM_TOKEN}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Erreur Navitia : {e}")
        return None

    if not data.get("journeys"):
        return None

    journey = data["journeys"][0]
    return {
        "mode": "transport_commun",
        "duree_min": round(journey["duration"] / 60, 1),
        "nb_correspondances": journey.get("nb_transfers", 0),
        "sections": [
            {
                "type": s.get("mode") or s.get("type"),
                "duree_min": round(s["duration"] / 60, 1),
            }
            for s in journey.get("sections", [])
        ],
    }


def get_itineraire(poi_from: dict, poi_to: dict) -> dict:
    """Compare marche et transport en commun, retourne les deux options triées par durée."""
    walking = get_walking_route(poi_from["lat"], poi_from["lon"], poi_to["lat"], poi_to["lon"])
    transit = get_transit_journey(poi_from["lat"], poi_from["lon"], poi_to["lat"], poi_to["lon"])

    options = []
    if walking:
        options.append(walking)
    if transit:
        options.append(transit)

    options.sort(key=lambda x: x["duree_min"])

    return {
        "de": poi_from["nom"],
        "vers": poi_to["nom"],
        "options": options,
        "recommande": options[0]["mode"] if options else None,
    }