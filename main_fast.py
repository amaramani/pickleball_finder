"""
Fast Pickleball Court Scraper - Optimized for large zip code lists
"""
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.config import load_config
from core.court_finder import CourtFinder
from core.court_scraper import CourtScraper
from models.scraped_court_data import ScrapedCourtData


def process_zip_code_fast(zip_code: str, google_api_key: str) -> list:
    """Process a single zip code with dedicated resources."""
    print(f"Processing {zip_code}...")
    
    # Each thread gets its own instances to avoid conflicts
    court_finder = CourtFinder(google_api_key)
    court_scraper = CourtScraper()
    
    try:
        start_time = time.time()
        
        # Find and scrape courts
        print(f"  {zip_code}: Searching for courts...")
        court_urls = court_finder.find_courts_in_zipcode(zip_code)
        if not court_urls:
            print(f"  {zip_code}: No court URLs found")
            return []
        
        print(f"  {zip_code}: Found {len(court_urls)} court URLs")
        
        courts = []
        for i, url in enumerate(court_urls, 1):
            print(f"  {zip_code}: Processing court {i}/{len(court_urls)}: {url}")
            court_data = court_scraper.scrape_court(url)
            if court_data:
                courts.append(court_data)
                print(f"    ✓ {court_data.name or 'Unnamed'}")
            else:
                print(f"    ✗ Failed to process court {i}")
        
        duration = time.time() - start_time
        print(f"✓ {zip_code}: {len(courts)} courts in {duration:.1f}s")
        return courts
        
    except Exception as e:
        print(f"✗ {zip_code}: Error - {e}")
        return []
    finally:
        court_finder.close()
        court_scraper.close()


def main():
    """Main application with parallel processing."""
    print("Fast Pickleball Court Scraper Starting...")
    
    config = load_config()
    google_api_key = config.get("Maps_API_KEY")
    
    if not google_api_key:
        print("Error: Maps_API_KEY not found in .env file.")
        return
    
    # Load zip codes
    zip_codes_file = os.path.join("data", "zip_codes.txt")
    if not os.path.exists(zip_codes_file):
        print(f"Error: Zip codes file not found at {zip_codes_file}")
        return
    
    with open(zip_codes_file, "r") as f:
        zip_codes = [line.strip() for line in f if line.strip()]
    
    print(f"Processing {len(zip_codes)} zip codes with parallel processing...")
    
    all_courts = []
    start_time = time.time()
    
    # Process zip codes in parallel (2 threads to avoid overwhelming server)
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit all tasks
        future_to_zipcode = {
            executor.submit(process_zip_code_fast, zip_code, google_api_key): zip_code 
            for zip_code in zip_codes
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_zipcode):
            zip_code = future_to_zipcode[future]
            try:
                courts = future.result()
                all_courts.extend(courts)
            except Exception as e:
                print(f"✗ {zip_code}: Exception - {e}")
    
    # Save results
    total_time = time.time() - start_time
    
    if all_courts:
        ScrapedCourtData.save_to_csv(all_courts)
        print(f"\n✅ Completed in {total_time:.1f}s!")
        print(f"Total courts: {len(all_courts)}")
        avg_time = total_time/len(zip_codes) if zip_codes else 0
        print(f"Average time per zip code: {avg_time:.1f}s")
        if avg_time > 0:
            print(f"Speed improvement: ~{600//avg_time:.0f}x faster")
    else:
        print("\n❌ No courts found")


if __name__ == "__main__":
    main()