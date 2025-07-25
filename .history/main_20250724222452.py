import os
from utils.config import load_config
from core.google_places_api import GooglePlacesAPI
from core.data_processor import DataProcessor
from utils.url_formatter import PickleheadsURLFormatter
from scraper.pickleheads_scraper import PickleheadsScraper
import time


def main():
    """
    Main function to orchestrate reading zip codes, fetching pickleball courts,
    generating scrape URLs, and scraping additional info.
    """
    config = load_config()
    google_api_key = config.get("Maps_API_KEY")

    if not google_api_key:
        print("Error: Maps_API_KEY not found in .env file.")
        print(
            'Please create a .env file and add your API key: Maps_API_KEY="YOUR_API_KEY"'
        )
        return

    google_api = GooglePlacesAPI(google_api_key)
    data_processor = DataProcessor()
    url_formatter = PickleheadsURLFormatter(
        google_api_key
    )  # Pass API key for reverse geocoding
    pickleheads_scraper = None  # Will be initialized in the try block

    try:
        pickleheads_scraper = PickleheadsScraper()  # Initialize the scraper

        zip_codes_file = os.path.join("data", "zip_codes.txt")

        if not os.path.exists(zip_codes_file):
            print(f"Error: Zip codes file not found at {zip_codes_file}.")
            return

        with open(zip_codes_file, "r") as f:
            zip_codes = [line.strip() for line in f if line.strip()]

    except Exception as init_e:
        print(f"An error occurred during initialization: {init_e}")
        return

    all_pickleball_courts = []

    for zip_code in zip_codes:
        print(f"\nSearching for pickleball courts in zip code: {zip_code}...")
        try:
            geocode_result = google_api.geocode_zip_code(zip_code)
            if not geocode_result:
                print(f"Could not find coordinates for zip code: {zip_code}")
                continue

            latitude = geocode_result["lat"]
            longitude = geocode_result["lng"]
            print(f"Coordinates for {zip_code}: Lat={latitude}, Lng={longitude}")

            places_data = google_api.search_pickleball_courts(latitude, longitude)
            if places_data:
                courts_in_zip = data_processor.process_places_data(places_data)
                if courts_in_zip:
                    print(
                        f"Found {len(courts_in_zip)} potential courts in {zip_code}. Getting details..."
                    )
                    for court in courts_in_zip:
                        # Get city, state, country for the URL
                        reverse_geocode_info = google_api.reverse_geocode_coordinates(
                            court["latitude"], court["longitude"]
                        )
                        city = reverse_geocode_info.get("city", "")
                        state = reverse_geocode_info.get("state", "")
                        country = reverse_geocode_info.get("country", "")

                        scrape_url = url_formatter.generate_pickleheads_url(
                            city, state, country, court["latitude"], court["longitude"]
                        )
                        court["scrape_url"] = scrape_url
                        print(f"  Generated URL for {court['name']}: {scrape_url}")
                        all_pickleball_courts.append(court)

                        # --- Scraping part ---
                        # IMPORTANT: Due to robots.txt, this part is highly experimental
                        # and might be blocked or lead to IP bans.
                        # Proceed with caution and ethical consideration.
                        try:
                            print(f"  Attempting to scrape: {scrape_url}")
                            # Example: scrape the page title
                            scraped_title = pickleheads_scraper.scrape_page_title(
                                scrape_url
                            )
                            if scraped_title:
                                print(f"  Scraped Title: {scraped_title}")
                                court["scraped_title"] = scraped_title
                            else:
                                print("  Failed to scrape title or title not found.")
                            # Add a delay between scrapes to be polite and avoid detection
                            time.sleep(2)
                        except Exception as scrape_e:
                            print(f"  Error during scraping {scrape_url}: {scrape_e}")
                        # --- End Scraping part ---

                else:
                    print(f"No pickleball courts found in {zip_code}.")
            else:
                print(f"No place data returned for {zip_code}.")

        except Exception as e:
            print(f"An error occurred while processing zip code {zip_code}: {e}")

    print("\n--- All Found Pickleball Courts with Scrape URLs ---")
    if all_pickleball_courts:
        for i, court in enumerate(all_pickleball_courts):
            print(f"Court {i+1}:")
            print(f"  Name: {court['name']}")
            print(f"  Address: {court['address']}")
            print(f"  Latitude: {court['latitude']}")
            print(f"  Longitude: {court['longitude']}")
            if "scrape_url" in court:
                print(f"  Scrape URL: {court['scrape_url']}")
            if "scraped_title" in court:
                print(f"  Scraped Title: {court['scraped_title']}")
            print("=" * 30)
    else:
        print("No pickleball courts found across all provided zip codes.")

    # Clean up scraper resources
    try:
        pickleheads_scraper.close()
    except Exception as cleanup_e:
        print(f"Error during scraper cleanup: {cleanup_e}")


if __name__ == "__main__":
    main()
