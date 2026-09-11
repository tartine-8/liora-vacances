import json
from math import radians, sin, cos, sqrt, asin
from routing import get_itineraire


AFFINITE_METEO = {
    "museum":     {"favorable_exterieur": 0.6, "neutre": 1.0, "pluie": 1.6, "neige": 1.6, "orage": 1.8, "visibilite_reduite": 1.3},
    "park":       {"favorable_exterieur": 1.8, "neutre": 1.0, "pluie": 0.2, "neige": 0.3, "orage": 0.1, "visibilite_reduite": 0.6},
    "restaurant": {"favorable_exterieur": 1.0, "neutre": 1.0, "pluie": 1.0, "neige": 1.0, "orage": 1.0, "visibilite_reduite": 1.0},
    "cinema":     {"favorable_exterieur": 0.7, "neutre": 1.0, "pluie": 1.4, "neige": 1.4, "orage": 1.5, "visibilite_reduite": 1.2},
}


def get_weather_category(weathercode: int) -> str:
    """Regroupe les codes WMO en grandes catégories utiles pour la recommandation."""
    if weathercode in [0, 1, 2]:
        return "favorable_exterieur"
    elif weathercode == 3:
        return "neutre"
    elif weathercode in [45, 48]:
        return "visibilite_reduite"
    elif weathercode in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
        return "pluie"
    elif weathercode in [71, 73, 75, 77, 85, 86]:
        return "neige"
    elif weathercode in [95, 96, 99]:
        return "orage"
    return "neutre"


def score_pois(pois: list[dict], weather_category: str) -> list[dict]:
    """Ajoute un score météo à chaque POI selon sa catégorie et la météo du jour."""
    for poi in pois:
        affinite = AFFINITE_METEO.get(poi["categorie"], {}).get(weather_category, 1.0)
        poi["score_meteo"] = affinite
    return pois


def haversine_distance_simple(lat1, lon1, lat2, lon2):
    """Distance en mètres entre deux points GPS."""
    R = 6371000
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return R * 2 * asin(sqrt(a))


def pick_best_by_score(candidats: list[dict], exclude_ids: set = None) -> dict:
    """Retourne le candidat au meilleur score météo, en excluant certains ids déjà choisis."""
    exclude_ids = exclude_ids or set()
    disponibles = [c for c in candidats if c["id"] not in exclude_ids]
    if not disponibles:
        return None
    return max(disponibles, key=lambda p: p["score_meteo"])


def pick_nearest(reference: dict, candidats: list[dict], top_n: int = 15) -> dict:
    """Parmi les top_n meilleurs candidats (par score), retourne le plus proche du point de référence."""
    if not candidats:
        return None
    meilleurs = sorted(candidats, key=lambda p: p["score_meteo"], reverse=True)[:top_n]
    return min(
        meilleurs,
        key=lambda p: haversine_distance_simple(reference["lat"], reference["lon"], p["lat"], p["lon"])
    )


DEFAULT_PREFERENCES = {
    "categories_activite": ["museum", "park", "cinema"],  # catégories autorisées pour les créneaux "activité"
    "nb_activites": 2,                                     # nombre de créneaux d'activité dans la journée
    "inclure_dejeuner": True,                              # ajouter ou non une pause repas
}


def filter_pois_by_preferences(pois: list[dict], preferences: dict) -> tuple[list[dict], list[dict]]:
    """Sépare les POI en deux pools : activités autorisées, et restaurants (si déjeuner souhaité)."""
    categories_ok = set(preferences.get("categories_activite", []))

    activites = [p for p in pois if p["categorie"] in categories_ok]
    restaurants = [p for p in pois if p["categorie"] == "restaurant"] if preferences.get("inclure_dejeuner", True) else []

    return activites, restaurants


def build_day_structure(pois: list[dict], weather_category: str, preferences: dict = None) -> list[dict]:
    """Construit une journée flexible : N activités choisies selon les préférences, avec pause repas optionnelle."""
    preferences = {**DEFAULT_PREFERENCES, **(preferences or {})}
    scored = score_pois(pois, weather_category)

    activites, restaurants = filter_pois_by_preferences(scored, preferences)

    if not activites:
        raise ValueError("Aucune activité disponible pour les catégories demandées")

    nb_activites = preferences["nb_activites"]
    etapes = []
    exclude_ids = set()

    # Première activité : la mieux notée selon la météo
    premiere = pick_best_by_score(activites, exclude_ids)
    if not premiere:
        raise ValueError("Impossible de sélectionner une première activité")
    etapes.append(premiere)
    exclude_ids.add(premiere["id"])

    # Insère le déjeuner après la première activité si demandé
    if preferences["inclure_dejeuner"] and restaurants:
        dejeuner = pick_nearest(etapes[-1], restaurants, top_n=20)
        if dejeuner:
            etapes.append({**dejeuner, "categorie": "restaurant"})

    # Complète avec les activités suivantes, en variant les catégories quand c'est possible
    while len([e for e in etapes if e["categorie"] != "restaurant"]) < nb_activites:
        reference = etapes[-1]
        derniere_categorie = [e["categorie"] for e in etapes if e["categorie"] != "restaurant"][-1]

        candidats_diff = [a for a in activites if a["categorie"] != derniere_categorie and a["id"] not in exclude_ids]
        candidats = candidats_diff if candidats_diff else [a for a in activites if a["id"] not in exclude_ids]

        suivante = pick_nearest(reference, candidats, top_n=15)
        if not suivante:
            break  # plus de candidats disponibles, on s'arrête avec ce qu'on a

        etapes.append(suivante)
        exclude_ids.add(suivante["id"])

    return etapes


def generate_day_plan(pois_file: str, weather_file: str, date_cible: str, preferences: dict = None) -> dict:
    """Génère un plan de journée personnalisé selon les préférences de l'utilisateur."""
    with open(pois_file, "r", encoding="utf-8") as f:
        pois = json.load(f)

    with open(weather_file, "r", encoding="utf-8") as f:
        weather = json.load(f)

    jour_meteo = next((j for j in weather if j["date"] == date_cible), None)
    if not jour_meteo:
        raise ValueError(f"Pas de météo trouvée pour {date_cible}")

    weather_category = get_weather_category(jour_meteo["weathercode"])
    print(f"Météo du {date_cible} : {jour_meteo['condition']} -> catégorie '{weather_category}'")

    etapes = build_day_structure(pois, weather_category, preferences)

    trajets = []
    for i in range(len(etapes) - 1):
        print(f"Calcul du trajet étape {i + 1} -> étape {i + 2}...")
        trajet = get_itineraire(etapes[i], etapes[i + 1])
        trajets.append(trajet)

    return {
        "date": date_cible,
        "meteo": jour_meteo["condition"],
        "programme": [{"nom": e["nom"], "categorie": e["categorie"]} for e in etapes],
        "trajets": trajets,
    }