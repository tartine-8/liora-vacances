import json
from recommendation import generate_day_plan

if __name__ == "__main__":
    # Exemple 1 : utilisateur qui ne veut ni musée ni parc, seulement resto + cinéma
    preferences = {
    "categories_activite": ["museum", "cinema"],
    "nb_activites": 2,
    "inclure_dejeuner": True,
}

    plan = generate_day_plan(
        pois_file="data/cleaned/paris_with_stops.json",
        weather_file="data/weather/paris.json",
        date_cible="2026-09-12",
        preferences=preferences,
    )

    with open("data/day_plan_test.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    print("Plan de journée généré dans data/day_plan_test.json")