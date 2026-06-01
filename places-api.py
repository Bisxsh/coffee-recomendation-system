import requests
import json
import os

def get_places():
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise ValueError("Missing GOOGLE_PLACES_API_KEY secret.")

    url = "https://places.googleapis.com/v1/places:searchText"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.primaryType,places.types"
    }
    
    queries = [
        "coffee shop near Soho Square London",
        "bakery near Soho Square London",
        "matcha cafe near Soho Square London",
        "bubble tea near Soho Square London"
    ]
    
    all_places = {}

    for query in queries:
        payload = {
            "textQuery": query,
            "locationRestriction": {
                "rectangle": {
                    "low": {"latitude": 51.5110, "longitude": -0.1380},
                    "high": {"latitude": 51.5180, "longitude": -0.1280}
                }
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                places = response.json().get("places", [])
                for place in places:
                    all_places[place["id"]] = place
            else:
                print(f"❌ Error fetching '{query}': {response.status_code}")
        except requests.exceptions.HTTPError as err:
            print(f"Skipping query due to error: {err}")

    unique_places = list(all_places.values())
    print(f"✅ Success! Ingested {len(unique_places)} unique places from Soho Square.")

    os.makedirs("public", exist_ok=True)
    with open("public/venues.json", "w", encoding="utf-8") as f:
        json.dump(unique_places, f, indent=2)

if __name__ == "__main__":
    get_places()