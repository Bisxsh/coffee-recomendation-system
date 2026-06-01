import requests
import json
import os

def run_scraper():
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise ValueError("Missing GOOGLE_PLACES_API_KEY secret.")

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName.text,places.location,places.primaryType,places.types"
    }
    payload = {
        "textQuery": "coffee bakery matcha bubble tea near Soho Square London",
        "locationRestriction": {
            "circle": {
                "center": {"latitude": 51.5146, "longitude": -0.1332},
                "radius": 500.0
            }
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    places = response.json().get("places", [])

    os.makedirs("public", exist_ok=True)
    with open("public/venues.json", "w", encoding="utf-8") as f:
        json.dump(places, f, indent=2)

if __name__ == "__main__":
    run_scraper()