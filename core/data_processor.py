class DataProcessor:
    """
    Processes raw data received from Google Places API.
    """

    def process_places_data(self, places_data: list) -> list:
        """
        Extracts relevant pickleball court information from raw Places API results.

        Args:
            places_data (list): A list of dictionaries, where each dictionary
                                represents a place result from the Places API.

        Returns:
            list: A list of dictionaries, each containing 'name', 'address',
                  'latitude', and 'longitude' for a pickleball court.
        """
        courts = []
        for place in places_data:
            name = place.get("name")
            address = place.get("vicinity") or place.get(
                "formatted_address"
            )  # 'vicinity' is often more concise
            geometry = place.get("geometry", {}).get("location", {})
            latitude = geometry.get("lat")
            longitude = geometry.get("lng")

            if all([name, address, latitude, longitude]):
                courts.append(
                    {
                        "name": name,
                        "address": address,
                        "latitude": latitude,
                        "longitude": longitude,
                    }
                )
        return courts
    
    def has_any_courts(self, places_data: list) -> bool:
        """Check if places data contains at least one valid pickleball court (optimized for filtering)."""
        for place in places_data:
            name = place.get("name")
            address = place.get("vicinity") or place.get("formatted_address")
            geometry = place.get("geometry", {}).get("location", {})
            latitude = geometry.get("lat")
            longitude = geometry.get("lng")

            if all([name, address, latitude, longitude]):
                return True  # Found at least one valid court, return immediately
        return False
