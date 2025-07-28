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
    # Test URLs list
    #"https://www.pickleheads.com/search?q=Irvine+CA+USA&lat=33.6846&lng=-117.8265&z=10.0",
    #"https://www.pickleheads.com/search?q=Monrovia%2C+California%2C+United+States&lat=34.1470&lng=-118.0010&z=10.0",
    test_urls = [
        "https://www.pickleheads.com/search?q=111+East+Dewey+Avenue%2C+Wharton%2C+New+Jersey+07885%2C+US&lat=40.9078&lng=-74.5733&z=10.0"
    ]
    
    total_results = []
    url_timings = []
    
    for i, test_url in enumerate(test_urls, 1):
        url_start_time = time.time()
        try:
            print(f"\n{'='*60}")
            print(f"PROCESSING URL {i}/{len(test_urls)}")
            print(f"{'='*60}")
            
            result = debug_scrape_url(test_url)
            url_duration = time.time() - url_start_time
            result['url_processing_time'] = url_duration
            total_results.append(result)
            url_timings.append(url_duration)
            
            print(f"\n⏱️ URL {i} processing time: {url_duration:.2f} seconds")
            
            if not result.get('success', False):
                logger.warning(f"No courts found for URL {i}")
                
        except Exception as e:
            url_duration = time.time() - url_start_time
            logger.error(f"Failed to process URL {i}: {e}")
            total_results.append({'error': str(e), 'success': False, 'url_processing_time': url_duration})
            url_timings.append(url_duration)
            print(f"\n⏱️ URL {i} processing time (failed): {url_duration:.2f} seconds")
    
    # Final summary
    successful_runs = sum(1 for r in total_results if r.get('success', False))
    total_courts = sum(r.get('stats', {}).get('total_courts', 0) for r in total_results)
    total_time = sum(url_timings)
    avg_time = total_time / len(url_timings) if url_timings else 0
    
    print(f"\n{'='*60}")
    print("FINAL EXECUTION SUMMARY")
    print(f"{'='*60}")
    print(f"URLs processed: {len(test_urls)}")
    print(f"Successful runs: {successful_runs}")
    print(f"Total courts found: {total_courts}")
    print(f"\nTiming Summary:")
    print(f"Total processing time: {total_time:.2f} seconds")
    print(f"Average time per URL: {avg_time:.2f} seconds")
    for i, timing in enumerate(url_timings, 1):
        print(f"  URL {i}: {timing:.2f}s")
    print(f"{'='*60}")