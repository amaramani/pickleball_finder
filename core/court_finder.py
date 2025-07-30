"""
Court Finder - Finds pickleball court URLs using Google Places API
"""
from core.google_places_api import GooglePlacesAPI
from core.data_processor import DataProcessor
from utils.url_formatter import PickleheadsURLFormatter
from scraper.pickleheads_scraper import PickleheadsScraper
from utils.scraping_helpers import extract_chakra_links


class CourtFinder:
    """Finds pickleball court URLs for given zip codes."""
    
    def __init__(self, google_api_key: str):
        self.google_api = GooglePlacesAPI(google_api_key)
        self.data_processor = DataProcessor()
        self.url_formatter = PickleheadsURLFormatter(google_api_key)
        self.scraper = PickleheadsScraper()
    
    def find_courts_in_zipcode(self, zip_code: str) -> list:
        """Find all court URLs for a given zip code."""
        try:
            # Get coordinates for zip code
            geocode_result = self.google_api.geocode_zip_code(zip_code)
            if not geocode_result:
                return []
            
            # Search for courts using Google Places
            places_data = self.google_api.search_pickleball_courts(
                geocode_result["lat"], geocode_result["lng"]
            )
            
            if not places_data:
                return []
            
            # Process places data
            courts_in_zip = self.data_processor.process_places_data(places_data)
            if not courts_in_zip:
                return []
            
            # Get court URLs from each location
            all_court_urls = []
            for court in courts_in_zip:
                court_urls = self._get_court_urls_for_location(court)
                all_court_urls.extend(court_urls)
            
            return all_court_urls
            
        except Exception as e:
            print(f"Error finding courts in {zip_code}: {e}")
            return []
    
    def _get_court_urls_for_location(self, court: dict) -> list:
        """Get individual court URLs for a location."""
        try:
            # Generate search URL for this location
            reverse_geocode_info = self.google_api.reverse_geocode_coordinates(
                court["latitude"], court["longitude"]
            )
            
            city = reverse_geocode_info.get("city", "")
            state = reverse_geocode_info.get("state", "")
            country = reverse_geocode_info.get("country", "")
            
            search_url = self.url_formatter.generate_pickleheads_url(
                city, state, country, court["latitude"], court["longitude"]
            )
            
            # Scrape the search page for individual court links
            scraped_data = self.scraper.scrape_page_data(search_url)
            if not scraped_data:
                return []
            
            # Extract court links
            court_urls = extract_chakra_links(scraped_data["page_source"], search_url)
            return court_urls
            
        except Exception as e:
            print(f"Error getting court URLs for location: {e}")
            return []
    
    def close(self):
        """Clean up resources."""
        if self.scraper:
            self.scraper.close()