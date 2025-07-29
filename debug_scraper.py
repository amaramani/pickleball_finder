from scraper.pickleheads_scraper import PickleheadsScraper
from models.scraped_court_data import ScrapedCourtData
from core.database import SupabaseDB
from utils.config import load_config
from utils.scraping_helpers import extract_chakra_links, process_court_link, analyze_court_data, update_court_statistics
from utils.performance_helpers import safe_extract, validate_url, PerformanceTracker, logger
import time
from typing import Dict, Any


def debug_scrape_url(url: str) -> Dict[str, Any]:
    """Debug a specific URL scraping process with optimizations."""
    if not validate_url(url):
        logger.error(f"Invalid URL provided: {url}")
        return {'error': 'Invalid URL'}
        
    print(f"\n=== DEBUG SCRAPING: {url} ===")
    tracker = PerformanceTracker()
    tracker.start('total_scraping')
    
    # Initialize counters
    stats = {
        'total_courts': 0,
        'courts_with_complete_info': 0,
        'courts_with_missing_info': 0,
        'courts_with_image': 0,
        'courts_without_image': 0,
        'missing_info_courts': [],
        'processed_courts': []
    }
    
    # Initialize database with error handling
    db = None
    try:
        config = load_config()
        supabase_url = config.get("SUPABASE_URL")
        supabase_key = config.get("SUPABASE_KEY")
        
        if supabase_url and supabase_key:
            db = SupabaseDB(supabase_url, supabase_key)
            print("✓ Database initialized")
        else:
            print("⚠ Database not configured - data won't be saved")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        print("✗ Database initialization failed")

    scraper = None
    try:
        scraper = PickleheadsScraper(headless=False)
        print("✓ Scraper initialized")
    except Exception as e:
        logger.error(f"Scraper initialization failed: {e}")
        return {'error': 'Scraper initialization failed'}

    try:
        tracker.start('initial_navigation')
        print("1. Navigating to URL...")
        scraper.driver.get(url)
        time.sleep(2)
        tracker.end('initial_navigation')

        print(f"2. Current URL: {scraper.driver.current_url}")
        print(f"3. Page title: {scraper.driver.title or 'No title'}")

        tracker.start('page_analysis')
        print("4. Analyzing page...")
        page_source = scraper.driver.page_source
        print(f"   - Page source length: {len(page_source):,} characters")

        # Optimized indicator checking
        source_lower = page_source.lower()
        indicators = [
            ("Cloudflare", "cloudflare"),
            ("Browser check", "checking your browser"),
            ("403 Forbidden", "403 forbidden"),
            ("Access denied", "access denied"),
            ("CAPTCHA", "captcha")
        ]
        
        print("5. Page indicators:")
        for name, pattern in indicators:
            found = pattern in source_lower
            status = "✓ FOUND" if found else "✗ Not found"
            print(f"   - {name}: {status}")
        tracker.end('page_analysis')

        print("\n6. Waiting for user input...")
        input("Press Enter to continue (check browser window)...")

        tracker.start('main_scraping')
        print("7. Starting main scraping...")
        data = scraper.scrape_page_data(url)

        if data:
            print("✓ Scraping successful!")
            print(f"   - Title: {data['title']}")
            print(f"   - Final URL: {data['url']}")
            print(f"   - Source length: {len(data['page_source']):,} characters")
            tracker.end('main_scraping')

            # Extract chakra links
            tracker.start('link_extraction')
            chakra_links = safe_extract(extract_chakra_links, data["page_source"], url) or []
            tracker.end('link_extraction')
            
            if chakra_links:
                print(f"\n8. Found {len(chakra_links)} court links")
                
                # Process courts sequentially for debugging
                tracker.start('court_processing')
                for i, link in enumerate(chakra_links, 1):
                    print(f"\nProcessing court {i}/{len(chakra_links)}: {link}")
                    
                    court_result = process_court_link(scraper, link, db)
                    if court_result:
                        if court_result.get('duplicate'):
                            print(f"   ⚠ Skipping duplicate address: {court_result['address']}")
                        else:
                            court_data = court_result['court_data']
                            stats['processed_courts'].append(court_result)
                            
                            # Update statistics using shared function
                            update_court_statistics(stats, court_data)
                            
                            # Print results
                            print(f"   ✓ Processed: {court_data.name or 'Unnamed Court'}")
                            if court_result['saved_court']:
                                print(f"   ✓ Saved to DB: {court_result['saved_court'].get('id')}")
                            else:
                                print("   ⚠ Not saved to database")
                    else:
                        print(f"   ✗ Failed to process court {i}")
                        
                tracker.end('court_processing')
            else:
                print("\n8. No court links found")
        else:
            print("✗ Initial scraping failed")
            tracker.end('main_scraping')

    except KeyboardInterrupt:
        print("\n⚠ Scraping interrupted by user")
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error during scraping: {e}")
        print(f"✗ Scraping failed: {e}")
    finally:
        if scraper:
            try:
                scraper.close()
                print("✓ Scraper closed")
            except Exception as e:
                logger.error(f"Error closing scraper: {e}")
        
        tracker.end('total_scraping')
        
        # Print optimized summary
        print_summary(stats, tracker)
        
        return {
            'stats': stats,
            'performance': tracker.get_summary(),
            'success': stats['total_courts'] > 0
        }


def print_summary(stats: Dict[str, Any], tracker: PerformanceTracker):
    """Print optimized summary with performance metrics."""
    print(f"\n{'='*50}")
    print("DEBUG SCRAPING SUMMARY")
    print(f"{'='*50}")
    
    # Performance metrics
    perf = tracker.get_summary()
    print("Performance Metrics:")
    for operation, duration in perf.items():
        print(f"  {operation}: {duration:.2f}s")
    
    print(f"\nCourt Statistics:")
    print(f"  Total courts processed: {stats['total_courts']}")
    print(f"  Courts with complete info: {stats['courts_with_complete_info']}")
    print(f"  Courts with missing info: {stats['courts_with_missing_info']}")
    print(f"  Courts with image: {stats['courts_with_image']}")
    print(f"  Courts without image: {stats['courts_without_image']}")
    
    # Missing info details
    if stats['missing_info_courts']:
        print(f"\n--- COURTS WITH MISSING INFO ---")
        for i, court in enumerate(stats['missing_info_courts'], 1):
            print(f"{i}. Name: {court['name']}")
            print(f"   Address: {court['address']}")
            print(f"   Missing fields: {', '.join(court['missing_fields'])}")
    
    print(f"{'='*50}")


if __name__ == "__main__":
    # Test zip codes for debugging
    #test_zipcodes = ["30044", "92604", "10001"]
    #test_zipcodes = ["70055"] #no places
    #test_zipcodes = ["95419"] #2 places
    test_zipcodes = ["30044"] #1 place
    
    from core.google_places_api import GooglePlacesAPI
    from core.data_processor import DataProcessor
    from utils.url_formatter import PickleheadsURLFormatter
    from utils.config import load_config
    
    # Initialize APIs
    config = load_config()
    google_api_key = config.get("Maps_API_KEY")
    if not google_api_key:
        print("Error: Maps_API_KEY not found in .env file.")
        exit(1)
    
    google_api = GooglePlacesAPI(google_api_key)
    data_processor = DataProcessor()
    url_formatter = PickleheadsURLFormatter(google_api_key)
    
    total_results = []
    zipcode_timings = []
    
    for i, zip_code in enumerate(test_zipcodes, 1):
        zipcode_start_time = time.time()
        try:
            print(f"\n{'='*60}")
            print(f"PROCESSING ZIPCODE {i}/{len(test_zipcodes)}: {zip_code}")
            print(f"{'='*60}")
            
            # Get coordinates for zip code
            geocode_result = google_api.geocode_zip_code(zip_code)
            if not geocode_result:
                print(f"Could not find coordinates for zip code: {zip_code}")
                continue
            
            # Search for courts
            places_data = google_api.search_pickleball_courts(
                geocode_result["lat"], geocode_result["lng"]
            )
            
            if places_data and data_processor.has_any_courts(places_data):
                pickleballplaces = data_processor.process_places_data(places_data)
                print(f"Found {len(pickleballplaces)} Pickleball Places in {zip_code}")
                
                # Generate URL for first court
                first_court = pickleballplaces[0]
                reverse_geocode_info = google_api.reverse_geocode_coordinates(
                    first_court["latitude"], first_court["longitude"]
                )
                city = reverse_geocode_info.get("city", "")
                state = reverse_geocode_info.get("state", "")
                country = reverse_geocode_info.get("country", "")
                
                test_url = url_formatter.generate_pickleheads_url(
                    city, state, country, first_court["latitude"], first_court["longitude"]
                )
                
                print(f"Generated Scraping URL: {test_url}")
                
                # Debug scrape the URL
                result = debug_scrape_url(test_url)
                zipcode_duration = time.time() - zipcode_start_time
                result['zipcode_processing_time'] = zipcode_duration
                result['zipcode'] = zip_code
                total_results.append(result)
                zipcode_timings.append(zipcode_duration)
                
                print(f"\n⏱️ Zipcode {zip_code} processing time: {zipcode_duration:.2f} seconds")
                
                if not result.get('success', False):
                    logger.warning(f"No courts processed for zipcode {zip_code}")
            else:
                print(f"No courts found in zipcode {zip_code}")
                zipcode_duration = time.time() - zipcode_start_time
                zipcode_timings.append(zipcode_duration)
                
        except Exception as e:
            zipcode_duration = time.time() - zipcode_start_time
            logger.error(f"Failed to process zipcode {zip_code}: {e}")
            total_results.append({'error': str(e), 'success': False, 'zipcode_processing_time': zipcode_duration, 'zipcode': zip_code})
            zipcode_timings.append(zipcode_duration)
            print(f"\n⏱️ Zipcode {zip_code} processing time (failed): {zipcode_duration:.2f} seconds")
    
    # Final summary
    successful_runs = sum(1 for r in total_results if r.get('success', False))
    total_courts = sum(r.get('stats', {}).get('total_courts', 0) for r in total_results)
    total_time = sum(zipcode_timings)
    avg_time = total_time / len(zipcode_timings) if zipcode_timings else 0
    
    print(f"\n{'='*60}")
    print("FINAL EXECUTION SUMMARY")
    print(f"{'='*60}")
    print(f"Zipcodes processed: {len(test_zipcodes)}")
    print(f"Successful runs: {successful_runs}")
    print(f"Total courts found: {total_courts}")
    print(f"\nTiming Summary:")
    print(f"Total processing time: {total_time:.2f} seconds")
    print(f"Average time per zipcode: {avg_time:.2f} seconds")
    for i, timing in enumerate(zipcode_timings, 1):
        zipcode = test_zipcodes[i-1] if i <= len(test_zipcodes) else f"Zipcode {i}"
        print(f"  {zipcode}: {timing:.2f}s")
    print(f"{'='*60}")