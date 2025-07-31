"""
Count court URLs only - no scraping
"""
import os
from utils.config import load_config
from core.court_finder import CourtFinder
from utils.statistics import ScrapingStats


def load_zip_codes(filename: str = "zip_codes.txt") -> list:
    """Load zip codes from file."""
    zip_codes_file = os.path.join("data", filename)
    with open(zip_codes_file, "r") as f:
        return [line.strip() for line in f if line.strip()]


def main():
    """Count court URLs for each zip code."""
    print("Counting court URLs...")
    
    config = load_config()
    google_api_key = config.get("Maps_API_KEY")
    
    if not google_api_key:
        print("Error: Maps_API_KEY not found in .env file.")
        return
    
    court_finder = CourtFinder(google_api_key)
    stats = ScrapingStats()
    
    try:
        zip_codes = load_zip_codes()
        print(f"Processing {len(zip_codes)} zip codes...\n")
        
        for i, zip_code in enumerate(zip_codes, 1):
            try:
                court_urls = court_finder.find_courts_in_zipcode(zip_code)
                unique_urls = list(set(court_urls))
                total_count = len(court_urls)
                unique_count = len(unique_urls)
                duplicates = total_count - unique_count
                print(f"[{i}/{len(zip_codes)}] {zip_code}: Total={total_count}, Unique={unique_count}, Duplicates={duplicates}")
                for j, url in enumerate(unique_urls, 1):
                    print(f"  {j}. {url}")
                stats.add_zip_stats(zip_code, unique_count, 0)
            except Exception as e:
                print(f"[{i}/{len(zip_codes)}] {zip_code}: Error - {e}")
                stats.add_zip_stats(zip_code, 0, 0)
        
        stats.save_stats("url_counts.csv")
        print(f"\n✓ Counts saved to data/url_counts.csv")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        court_finder.close()


if __name__ == "__main__":
    main()