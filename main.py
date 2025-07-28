import os
from utils.config import load_config
from core.google_places_api import GooglePlacesAPI
from core.data_processor import DataProcessor
from core.database import SupabaseDB
from utils.url_formatter import PickleheadsURLFormatter
from scraper.pickleheads_scraper import PickleheadsScraper
from models.scraped_court_data import ScrapedCourtData
from utils.scraping_helpers import extract_chakra_links, process_court_link, update_court_statistics
import time


class ScrapingStats:
    """Track scraping statistics."""
    def __init__(self):
        self.total_zipcodes = 0
        self.total_courts = 0
        self.courts_with_complete_info = 0
        self.courts_with_missing_info = 0
        self.courts_with_image = 0
        self.courts_without_image = 0
        self.zipcode_stats = {}
    
    def add_zipcode(self, zipcode):
        self.total_zipcodes += 1
        self.zipcode_stats[zipcode] = {
            'courts_found': 0,
            'complete_info': 0,
            'missing_info': 0,
            'with_image': 0,
            'without_image': 0,
            'missing_info_courts': []
        }
    
    def add_court(self, zipcode, court_data):
        """Add court using shared statistics function."""
        from utils.scraping_helpers import update_court_statistics
        
        # Initialize missing_info_courts if not exists
        if 'missing_info_courts' not in self.__dict__:
            self.missing_info_courts = []
        
        # Use shared function
        update_court_statistics(self.__dict__, court_data, zipcode)
        
        # Update zipcode-specific stats
        self.zipcode_stats[zipcode]['courts_found'] += 1
        
        # Check completeness for zipcode stats
        has_complete_info = all([court_data.name, court_data.address, court_data.telephone])
        if has_complete_info:
            self.zipcode_stats[zipcode]['complete_info'] += 1
        else:
            self.zipcode_stats[zipcode]['missing_info'] += 1
        
        # Check image for zipcode stats
        if court_data.image_data:
            self.zipcode_stats[zipcode]['with_image'] += 1
        else:
            self.zipcode_stats[zipcode]['without_image'] += 1
    
    def print_zipcode_summary(self, zipcode):
        stats = self.zipcode_stats[zipcode]
        print(f"\n--- ZIPCODE {zipcode} SCRAPING SUMMARY ---")
        print(f"Courts found: {stats['courts_found']}")
        print(f"Complete info: {stats['complete_info']}")
        print(f"Missing info: {stats['missing_info']}")
        print(f"With image: {stats['with_image']}")
        print(f"Without image: {stats['without_image']}")
        
        # Print missing info details
        if stats['missing_info_courts']:
            print(f"\n--- COURTS WITH MISSING INFO (ZIPCODE {zipcode}) ---")
            for i, court in enumerate(stats['missing_info_courts'], 1):
                print(f"{i}. Name: {court['name']}")
                print(f"   Address: {court['address']}")
                print(f"   Missing fields: {', '.join(court['missing_fields'])}")
        
        print("=" * 45)
    
    def print_final_summary(self, zipcode_timings=None):
        print(f"\n{'='*50}")
        print("FINAL SCRAPING SUMMARY")
        print(f"{'='*50}")
        print(f"Total zipcodes processed: {self.total_zipcodes}")
        print(f"Total courts found: {self.total_courts}")
        print(f"Courts with complete info: {self.courts_with_complete_info}")
        print(f"Courts with missing info: {self.courts_with_missing_info}")
        print(f"Courts with image: {self.courts_with_image}")
        print(f"Courts without image: {self.courts_without_image}")
        
        if zipcode_timings:
            total_time = sum(timing for _, timing in zipcode_timings)
            avg_time = total_time / len(zipcode_timings) if zipcode_timings else 0
            print(f"\nTiming Summary:")
            print(f"Total processing time: {total_time:.2f} seconds")
            print(f"Average time per zipcode: {avg_time:.2f} seconds")
            for zipcode, timing in zipcode_timings:
                print(f"  {zipcode}: {timing:.2f}s")
        
        print(f"{'='*50}")


def main():
    """
    Main function to orchestrate reading zip codes, fetching pickleball courts,
    generating scrape URLs, and scraping additional info.
    """
    config = load_config()
    google_api_key = config.get("Maps_API_KEY")
    supabase_url = config.get("SUPABASE_URL")
    supabase_key = config.get("SUPABASE_KEY")

    if not google_api_key:
        print("Error: Maps_API_KEY not found in .env file.")
        print(
            'Please create a .env file and add your API key: Maps_API_KEY="YOUR_API_KEY"'
        )
        return
    
    if not supabase_url or not supabase_key:
        print("Error: Supabase credentials not found in .env file.")
        print('Please add: SUPABASE_URL="your_url" and SUPABASE_KEY="your_key"')
        return

    google_api = GooglePlacesAPI(google_api_key)
    data_processor = DataProcessor()
    url_formatter = PickleheadsURLFormatter(
        google_api_key
    )  # Pass API key for reverse geocoding
    db = SupabaseDB(supabase_url, supabase_key)
    stats = ScrapingStats()
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
    processed_courts = set()  # Track processed courts to avoid duplicates

    zipcode_timings = []
    
    for zip_code in zip_codes:
        zipcode_start_time = time.time()
        print(f"\nSearching for pickleball courts in zip code: {zip_code}...")
        stats.add_zipcode(zip_code)
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
                places_in_zip = data_processor.process_places_data(places_data)
                if places_in_zip:
                    print(
                        f"Found {len(places_in_zip)} potential places in {zip_code}. Getting details..."
                    )
                    for place in places_in_zip:
                        # Create unique identifier for court to avoid duplicates
                        court_id = f"{place['name']}_{place['latitude']:.6f}_{place['longitude']:.6f}"
                        
                        if court_id in processed_courts:
                            print(f"  Skipping duplicate place: {place['name']}")
                            continue
                        
                        processed_courts.add(court_id)
                        
                        # Get city, state, country for the URL
                        reverse_geocode_info = google_api.reverse_geocode_coordinates(
                            place["latitude"], place["longitude"]
                        )
                        city = reverse_geocode_info.get("city", "")
                        state = reverse_geocode_info.get("state", "")
                        country = reverse_geocode_info.get("country", "")

                        scrape_url = url_formatter.generate_pickleheads_url(
                            city, state, country, place["latitude"], place["longitude"]
                        )
                        place["scrape_url"] = scrape_url
                        print(f"  Generated Scraping URL for {place['name']}: {scrape_url}")
                        all_pickleball_courts.append(place)

                        # --- Scraping part ---
                        # IMPORTANT: Due to robots.txt, this part is highly experimental
                        # and might be blocked or lead to IP bans.
                        # Proceed with caution and ethical consideration.
                        try:
                            print(f"  Attempting to scrape: {scrape_url}")
                            # Scrape complete page data
                            scraped_data = pickleheads_scraper.scrape_page_data(
                                scrape_url
                            )
                            if scraped_data:
                                print(f"  Scraped Title: {scraped_data['title']}")
                                place["scraped_title"] = scraped_data["title"]
                                place["page_source"] = scraped_data["page_source"]
                                place["final_url"] = scraped_data["url"]

                                # Extract chakra-link anchor tags
                                chakra_links = extract_chakra_links(
                                    scraped_data["page_source"], scrape_url
                                )
                                place["chakra_links"] = chakra_links
                                print(f"  Found {len(chakra_links)} court links for scrape-URL:{scrape_url}")
                                for i, link in enumerate(chakra_links):
                                    print(f"    {i+1}. {link}")

                                # Process courts using debug_scraper approach
                                place["scraped_hrefs"] = []
                                for i, link in enumerate(chakra_links, 1):
                                    print(f"  Processing court {i}/{len(chakra_links)}: {link}")
                                    
                                    # Use the superior processing approach
                                    court_result = process_court_link(pickleheads_scraper, link, db)
                                    
                                    if court_result:
                                        court_data = court_result['court_data']
                                        
                                        # Update statistics
                                        stats.add_court(zip_code, court_data)
                                        
                                        place["scraped_hrefs"].append(court_result)
                                        
                                        print(f"    ✓ Processed: {court_data.name or 'Unnamed Court'}")
                                        if court_result['saved_court']:
                                            print(f"    ✓ Saved to DB: {court_result['saved_court'].get('id')}")
                                        else:
                                            print("    ⚠ Not saved to database")
                                    else:
                                        print(f"    ✗ Failed to process court {i}")
                            else:
                                print("  Failed to scrape page data.")
                        except Exception as scrape_e:
                            print(f"  Error during scraping {scrape_url}: {scrape_e}")
                        # --- End Scraping part ---

                else:
                    print(f"No pickleball courts found in {zip_code}.")
            else:
                print(f"No place data returned for {zip_code}.")

        except Exception as e:
            print(f"An error occurred while processing zip code {zip_code}: {e}")
        
        # Calculate and display timing
        zipcode_duration = time.time() - zipcode_start_time
        zipcode_timings.append((zip_code, zipcode_duration))
        print(f"\n⏱️ Zipcode {zip_code} processing time: {zipcode_duration:.2f} seconds")
        
        # Print zipcode summary
        stats.print_zipcode_summary(zip_code)

    print(f"\n--- PROCESSING COMPLETE ---")
    print(f"Total courts processed: {len(all_pickleball_courts)}")
    if not all_pickleball_courts:
        print("No pickleball courts found across all provided zip codes.")

    # Print final summary
    stats.print_final_summary(zipcode_timings)
    
    # Clean up scraper resources
    try:
        pickleheads_scraper.close()
    except Exception as cleanup_e:
        print(f"Error during scraper cleanup: {cleanup_e}")


if __name__ == "__main__":
    main()
