# Create test_google_api.py
from utils.config import load_config
from core.google_places_api import GooglePlacesAPI

config = load_config()
api = GooglePlacesAPI(config.get("Maps_API_KEY"))

# Test geocoding
result = api.geocode_zip_code("92604")
print(f"Geocode result: {result}")

# Test places search
if result:
    places = api.search_pickleball_courts(result["lat"], result["lng"])
    print(f"Found {len(places) if places else 0} places")
