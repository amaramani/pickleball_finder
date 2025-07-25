from scraper.pickleheads_scraper import PickleheadsScraper
import time
from bs4 import BeautifulSoup


def extract_chakra_links(html_content):
    """Extract anchor tags with class 'chakra-link css-13arwou' inside div with class 'chakra-stack css-1iym7wy'."""
    soup = BeautifulSoup(html_content, "html.parser")
    target_div = soup.find("div", class_="chakra-stack css-1iym7wy")
    if target_div:
        anchor_tags = target_div.find_all("a", class_="chakra-link css-13arwou")
        print(
            f"Target div found. Found {len(anchor_tags)} anchor tags with class 'chakra-link css-13arwou'."
        )
        return anchor_tags
    else:
        print("Target <div> with class 'chakra-stack css-1iym7wy' not found.")
        return []


def debug_scrape_url(url):
    """Debug a specific URL scraping process."""
    print(f"\n=== DEBUG SCRAPING: {url} ===")

    scraper = PickleheadsScraper(headless=False)  # Visible for debugging

    try:
        print("1. Navigating to URL...")
        scraper.driver.get(url)

        print("2. Waiting for initial load...")
        time.sleep(3)

        print(f"3. Current URL: {scraper.driver.current_url}")
        print(f"4. Page title: {scraper.driver.title}")

        print("5. Checking page source...")
        page_source = scraper.driver.page_source
        print(f"   - Page source length: {len(page_source)}")

        # Check for common indicators
        source_lower = page_source.lower()
        indicators = {
            "Cloudflare": "cloudflare" in source_lower,
            "Browser check": "checking your browser" in source_lower,
            "403 Forbidden": "403 forbidden" in source_lower,
            "Access denied": "access denied" in source_lower,
            "CAPTCHA": "captcha" in source_lower,
        }

        print("6. Page indicators:")
        for indicator, found in indicators.items():
            status = "✓ FOUND" if found else "✗ Not found"
            print(f"   - {indicator}: {status}")

        print("\n7. Waiting for user input...")
        input("Press Enter to continue (check browser window)...")

        # Try the full scraping method
        print("8. Testing full scrape method...")
        data = scraper.scrape_page_data(url)

        if data:
            print("✓ Scraping successful!")
            print(f"   - Title: {data['title']}")
            print(f"   - Final URL: {data['url']}")
            print(f"   - Source length: {len(data['page_source'])}")

            # Extract and display chakra links
            print("\n9. Extracting chakra links...")
            chakra_links = extract_chakra_links(data["page_source"])
            if chakra_links:
                print(f"Found {len(chakra_links)} chakra links:")
                # for i, link in enumerate(chakra_links):
                #    print(f"   {i+1}. {link}")
            else:
                print("No chakra links found.")
        else:
            print("✗ Scraping failed")

    except Exception as e:
        print(f"ERROR: {e}")

    finally:
        scraper.close()


if __name__ == "__main__":
    # Test with a sample pickleheads URL
    test_url = "https://www.pickleheads.com/search?q=Irvine+CA+USA&lat=33.6846&lng=-117.8265&z=10.0"
    debug_scrape_url(test_url)
