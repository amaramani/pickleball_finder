"""
Pickleball Court Scraper - Main Application
Scrapes court data from pickleheads.com and saves to CSV
"""
import os
from utils.config import load_config
from core.court_finder import CourtFinder
from core.court_scraper import CourtScraper
from models.scraped_court_data import ScrapedCourtData


def load_zip_codes(filename: str = "zip_codes.txt") -> list:
    """Load zip codes from file."""
    zip_codes_file = os.path.join("data", filename)
    if not os.path.exists(zip_codes_file):
        raise FileNotFoundError(f"Zip codes file not found at {zip_codes_file}")
    
    with open(zip_codes_file, "r") as f:
        return [line.strip() for line in f if line.strip()]


def process_zip_code(zip_code: str, court_finder: CourtFinder, court_scraper: CourtScraper) -> list:
    """Process a single zip code and return list of court data."""
    print(f"\nProcessing zip code: {zip_code}")
    
    try:
        # Find court URLs for this zip code
        court_urls = court_finder.find_courts_in_zipcode(zip_code)
        
        if not court_urls:
            print(f"No courts found in {zip_code}")
            return []
        
        print(f"Found {len(court_urls)} court URLs in {zip_code}")
        
        # Scrape each court URL
        courts = []
        for i, url in enumerate(court_urls, 1):
            print(f"  Processing court {i}/{len(court_urls)}: {url}")
            
            court_data = court_scraper.scrape_court(url)
            if court_data:
                courts.append(court_data)
                print(f"    ✓ {court_data.name or 'Unnamed'}")
            else:
                print(f"    ✗ Failed to process court {i}")
        
        print(f"✓ Zip code {zip_code} completed - {len(courts)} courts scraped")
        return courts
        
    except Exception as e:
        print(f"Error processing {zip_code}: {e}")
        return []


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
    
    try:
        # Load zip codes
        zip_codes = load_zip_codes()
        print(f"Loaded {len(zip_codes)} zip codes")
        
        # Process all zip codes
        all_courts = []
        for zip_code in zip_codes:
            courts = process_zip_code(zip_code, court_finder, court_scraper)
            all_courts.extend(courts)
        
        # Save results
        if all_courts:
            ScrapedCourtData.save_to_csv(all_courts)
            print(f"\n✅ Scraped {len(all_courts)} courts successfully!")
        else:
            print("\n❌ No courts found")
    
    except Exception as e:
        print(f"Application error: {e}")
    
    finally:
        court_scraper.close()


if __name__ == "__main__":
    main()