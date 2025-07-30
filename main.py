"""
Pickleball Court Scraper - Main Application
Scrapes court data from pickleheads.com and saves to CSV
"""
import os
import time
from utils.config import load_config
from core.court_finder import CourtFinder
from core.court_scraper import CourtScraper
from models.scraped_court_data import ScrapedCourtData
from utils.statistics import ScrapingStats


def load_zip_codes(filename: str = "zip_codes.txt") -> list:
    """Load zip codes from file."""
    zip_codes_file = os.path.join("data", filename)
    if not os.path.exists(zip_codes_file):
        raise FileNotFoundError(f"Zip codes file not found at {zip_codes_file}")
    
    with open(zip_codes_file, "r") as f:
        return [line.strip() for line in f if line.strip()]


def process_zip_code(zip_code: str, court_finder: CourtFinder, court_scraper: CourtScraper, stats: ScrapingStats) -> None:
    """Process a single zip code and save results immediately."""
    zip_start = time.time()
    print(f"\nProcessing zip code: {zip_code}")
    
    try:
        # Find court URLs for this zip code
        places_start = time.time()
        court_urls = court_finder.find_courts_in_zipcode(zip_code)
        places_time = time.time() - places_start
        unique_urls = list(set(court_urls))
        total_count = len(court_urls)
        unique_count = len(unique_urls)
        duplicates = total_count - unique_count
        
        print(f"Found {total_count} court URLs in {zip_code} (Unique: {unique_count}, Duplicates: {duplicates}) - {places_time:.2f}s")
        
        if not unique_urls:
            stats.add_zip_stats(zip_code, 0, 0)
            return
        
        # Scrape each unique court URL
        courts = []
        for i, url in enumerate(unique_urls, 1):
            court_start = time.time()
            print(f"  Processing court {i}/{unique_count}: {url}")
            
            try:
                court_data = court_scraper.scrape_court(url)
                court_time = time.time() - court_start
                if court_data:
                    courts.append(court_data)
                    print(f"    ✓ {court_data.name or 'Unnamed'} - {court_time:.2f}s")
                else:
                    print(f"    ✗ Failed to process court {i} - {court_time:.2f}s")
            except Exception as e:
                court_time = time.time() - court_start
                print(f"    ❌ Error scraping court {i}: {e} - {court_time:.2f}s")
        
        courts_scraped = len(courts)
        stats.add_zip_stats(zip_code, unique_count, courts_scraped)
        
        # Save immediately after processing this zip code
        zip_time = time.time() - zip_start
        if courts:
            try:
                ScrapedCourtData.append_to_csv(courts)
                print(f"✓ Zip code {zip_code} completed - {courts_scraped}/{unique_count} courts saved - {zip_time:.2f}s")
            except Exception as e:
                print(f"❌ Failed to save courts for {zip_code}: {e} - {zip_time:.2f}s")
        else:
            print(f"✗ Zip code {zip_code} completed - no courts to save - {zip_time:.2f}s")
        
    except Exception as e:
        zip_time = time.time() - zip_start
        print(f"❌ Error processing {zip_code}: {e} - {zip_time:.2f}s")
        stats.add_zip_stats(zip_code, 0, 0)


def main():
    """Main application entry point."""
    print("Pickleball Court Scraper Starting...")
    
    # Load configuration
    config = load_config()
    google_api_key = config.get("Maps_API_KEY")
    
    if not google_api_key:
        print("Error: Maps_API_KEY not found in .env file.")
        return
    
    # Initialize components
    court_finder = CourtFinder(google_api_key)
    court_scraper = CourtScraper()
    stats = ScrapingStats()
    
    try:
        # Load zip codes
        zip_codes = load_zip_codes()
        print(f"Loaded {len(zip_codes)} zip codes")
        
        # Initialize CSV file
        try:
            # Create empty CSV with headers
            ScrapedCourtData.save_to_csv([])
            print("\n✓ Initialized CSV file")
        except Exception as e:
            print(f"\n❌ Failed to initialize CSV file: {e}")
            return
        
        # Process all zip codes
        total_processed = 0
        for i, zip_code in enumerate(zip_codes, 1):
            print(f"\n[{i}/{len(zip_codes)}] Processing zip codes...")
            try:
                process_zip_code(zip_code, court_finder, court_scraper, stats)
                total_processed += 1
            except Exception as e:
                print(f"❌ Critical error processing {zip_code}: {e}")
        
        # Save statistics and show summary
        try:
            stats.save_stats()
            stats.print_summary()
        except Exception as e:
            print(f"❌ Error saving statistics: {e}")
        
        print(f"\n✅ Processing complete! {total_processed}/{len(zip_codes)} zip codes processed")
    
    except KeyboardInterrupt:
        print("\n❌ Application interrupted by user")
    except Exception as e:
        print(f"\n❌ Critical application error: {e}")
    
    finally:
        try:
            court_scraper.close()
            print("\n✓ Cleanup completed")
        except Exception as e:
            print(f"\n❌ Error during cleanup: {e}")


if __name__ == "__main__":
    main()