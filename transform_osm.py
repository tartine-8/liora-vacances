import json
from pathlib import Path

def clean_pois(raw_pois: list[dict]) -> list[dict]:
    cleaned = []
    seen_ids = set()

    for poi in raw_pois:
        # Ignore les lieux sans nom (inexploitables pour l'utilisateur)
        if not poi.get("nom"):
            continue

        # Ignore les lieux sans coordonnées
        if poi.get("lat") is None or poi.get("lon") is None:
            continue

        # Ignore les doublons (même id déjà vu)
        if poi["id"] in seen_ids:
            continue
        seen_ids.add(poi["id"])

        # Ignore les catégories non reconnues
        if poi.get("categorie") is None:
            continue

        cleaned.append({
            "id": poi["id"],
            "nom": poi["nom"].strip(),
            "categorie": poi["categorie"],
            "lat": round(poi["lat"], 6),
            "lon": round(poi["lon"], 6),
            "horaires": poi.get("horaires"),
            "adresse": poi.get("adresse"),
            "ville": "paris",
        })

    return cleaned

def main():
    with open("data/city/paris.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    print(f"Avant nettoyage : {len(raw)} lieux")
    cleaned = clean_pois(raw)
    print(f"Après nettoyage : {len(cleaned)} lieux")

    Path("data/cleaned").mkdir(parents=True, exist_ok=True)
    with open("data/cleaned/paris_cleaned.json", "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()