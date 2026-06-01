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
        "X-Goog-FieldMask": (
            "places.id,"
            "places.displayName,"
            "places.location,"
            "places.primaryType,"
            "places.types,"
            "places.rating,"
            "places.userRatingCount,"
            "places.currentOpeningHours,"
            "places.editorialSummary,"
            "places.generativeSummary,"
            "places.reviews,"
            "places.shortFormattedAddress,"
            "places.postalAddress,"
            "places.googleMapsUri,"
            "places.websiteUri,"
            "places.photos,"
            "places.priceLevel,"
            "places.reviewSummary,"
            "places.consumerAlert,"
            "places.takeout,"
            "places.servesCoffee"
        )
    }
    
    queries = {
        "coffee": "coffee near Soho Square London",
        "bakery": "bakery near Soho Square London",
        "matcha": "matcha near Soho Square London",
        "bubble_tea": "bubble tea near Soho Square London"
    }
    
    all_places = {}

    for tag, query in queries.items():
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
                    place_id = place["id"]
                    
                    if place_id not in all_places:
                        place["tags"] = set()
                        all_places[place_id] = place
                    
                    all_places[place_id]["tags"].add(tag)
            else:
                print(f"❌ Error fetching '{query}' | Status Code: {response.status_code}")
                print(f"❌ Server Response Payload Error: {response.text}")
                response.raise_for_status()
                    
        except requests.exceptions.HTTPError as err:
            print(f"Halted processing loop for '{query}' due to HTTP Error: {err}")
            raise

    for place in all_places.values():
        place["tags"] = list(place["tags"])

    unique_places = list(all_places.values())
    print(f"✅ Success! Ingested {len(unique_places)} unique places with query-based tags.")

    os.makedirs("public", exist_ok=True)
    with open("public/venues.json", "w", encoding="utf-8") as f:
        json.dump(unique_places, f, indent=2)

if __name__ == "__main__":
    get_places()