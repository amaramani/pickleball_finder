from urllib.parse import urlencode, quote_plus
from core.google_places_api import (
    GooglePlacesAPI,
)  # To reuse geocoding if needed, but Nominatim is better for reverse.


class PickleheadsURLFormatter:
    """
    Generates and encodes URLs for pickleheads.com.
    """

    BASE_URL = "https://www.pickleheads.com/search"

    def __init__(self, google_api_key: str):
        # We might not strictly need the Google API key here if Nominatim is used for reverse geocoding
        # elsewhere, but keeping it as an option or for consistency.
        self.google_api_key = google_api_key

    def generate_pickleheads_url(
        self, city: str, state: str, country: str, lat: float, lng: float
    ) -> str:
        """
        Generates and URL-encodes the pickleheads.com search URL.

        Args:
            city (str): The city name.
            state (str): The state name.
            country (str): The country name.
            lat (float): Latitude.
            lng (float): Longitude.

        Returns:
            str: The fully encoded URL.
        """
        # Note: The format in the prompt says lng=-{lang}. This seems like a typo
        # and should likely be lng={lng} or lng={longitude}. I'll assume it's a typo
        # and use lng directly. If it truly needs to be negative, you can add `-lng`.
        query_string = f"{city} {state} {country}".strip()

        # The 'q' parameter in the URL requires space as '+', which urlencode handles.
        # It's safer to use a dictionary and urlencode.
        params = {
            "q": query_string,
            "lat": f"{lat}",
            "lng": f"{lng}",  # Assuming no negative sign needed here unless specified
            "z": "10.0",
        }

        # urlencode will handle encoding spaces to + and other special characters.
        encoded_params = urlencode(params, quote_via=quote_plus)

        return f"{self.BASE_URL}?{encoded_params}"
