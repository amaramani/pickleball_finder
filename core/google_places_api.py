import requests
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


class GooglePlacesAPI:
    """
    Handles interactions with the Google Maps Places and Geocoding APIs.
    """

    GEOCODE_API_ENDPOINT = "https://maps.googleapis.com/maps/api/geocode/json"
    PLACES_NEARBY_SEARCH_ENDPOINT = (
        "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    )

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Google Maps API key cannot be empty.")
        self.api_key = api_key
        # Initialize Nominatim for reverse geocoding (alternative to Google Geocoding for this part)
        # Be sure to set a user_agent string.
        self.geolocator = Nominatim(user_agent="pickleball_finder_app")

    def geocode_zip_code(self, zip_code: str) -> dict | None:
        """
        Converts a zip code into latitude and longitude coordinates using the Geocoding API.

        Args:
            zip_code (str): The zip code to geocode.

        Returns:
            dict | None: A dictionary with 'lat' and 'lng' if successful, otherwise None.
        """
        params = {"address": zip_code, "key": self.api_key}
        try:
            response = requests.get(self.GEOCODE_API_ENDPOINT, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            if data.get("status") == "OK" and data["results"]:
                location = data["results"][0]["geometry"]["location"]
                return {"lat": location["lat"], "lng": location["lng"]}
            else:
                print(
                    f"Geocoding API Error for {zip_code}: {data.get('status')}. Message: {data.get('error_message', 'No error message.')}"
                )
                return None
        except requests.exceptions.RequestException as e:
            print(f"Network or API request error during geocoding for {zip_code}: {e}")
            return None
        except KeyError as e:
            print(
                f"Unexpected JSON structure from Geocoding API for {zip_code}: Missing key {e}"
            )
            return None

    def reverse_geocode_coordinates(self, lat: float, lng: float) -> dict:
        """
        Converts latitude and longitude into city, state, and country using Nominatim.
        This uses Nominatim (OpenStreetMap) as it's often more straightforward for reverse geocoding
        than Google's Geocoding API for basic address components.

        Args:
            lat (float): Latitude.
            lng (float): Longitude.

        Returns:
            dict: A dictionary containing 'city', 'state', 'country', defaults to empty string if not found.
        """
        try:
            location = self.geolocator.reverse(
                f"{lat},{lng}", exactly_one=True, timeout=10
            )
            if location:
                address = location.raw.get("address", {})
                city = address.get(
                    "city", address.get("town", address.get("village", ""))
                )
                state = address.get("state", "")
                country = address.get("country", "")
                return {"city": city, "state": state, "country": country}
            else:
                return {"city": "", "state": "", "country": ""}
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Error during reverse geocoding for {lat},{lng}: {e}")
            return {"city": "", "state": "", "country": ""}
        except Exception as e:
            print(f"An unexpected error occurred during reverse geocoding: {e}")
            return {"city": "", "state": "", "country": ""}

    def search_pickleball_courts(
        self, latitude: float, longitude: float, radius: int = 5000
    ) -> list | None:
        """
        Searches for pickleball courts near a given latitude and longitude using the Places API.

        Args:
            latitude (float): The latitude of the search center.
            longitude (float): The longitude of the search center.
            radius (int): The search radius in meters (default: 5000 meters = 5 km).

        Returns:
            list | None: A list of place results if successful, otherwise None.
        """
        params = {
            "location": f"{latitude},{longitude}",
            "radius": radius,
            "keyword": "pickleball court",
            "type": "point_of_interest",  # Consider other types like "park" if needed
            "key": self.api_key,
        }
        try:
            response = requests.get(self.PLACES_NEARBY_SEARCH_ENDPOINT, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "OK" and data["results"]:
                return data["results"]
            elif data.get("status") == "ZERO_RESULTS":
                return []  # No results found, but the request was successful
            else:
                print(
                    f"Places API Error for Lat/Lng ({latitude},{longitude}): {data.get('status')}. Message: {data.get('error_message', 'No error message.')}"
                )
                return None
        except requests.exceptions.RequestException as e:
            print(
                f"Network or API request error during places search for ({latitude},{longitude}): {e}"
            )
            return None
        except KeyError as e:
            print(
                f"Unexpected JSON structure from Places API for ({latitude},{longitude}): Missing key {e}"
            )
            return None
        finally:
            time.sleep(0.5)  # Add a small delay between requests
