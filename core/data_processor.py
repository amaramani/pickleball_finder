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
