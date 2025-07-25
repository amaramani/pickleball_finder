# Create test_scraper.py
from scraper.pickleheads_scraper import PickleheadsScraper

try:
    scraper = PickleheadsScraper(headless=False)  # Visible browser for debugging
    print("✓ Firefox initialized successfully")

    # Test simple navigation
    scraper.driver.get("https://www.google.com")
    print(f"✓ Navigation works - Title: {scraper.driver.title}")
    print(f"✓ Navigation works - PageSource: {scraper.driver.page_source}")

    scraper.driver.get(
        "https://www.pickleheads.com/search?q=Irvine%2C+California%2C+United+States&lat=33.6846&lng=-117.8263&z=10.0"
    )
    print(f"✓ Navigation works - Title: {scraper.driver.title}")
    print(f"✓ Navigation works - PageSource: {scraper.driver.page_source}")
    scraper.close()
except Exception as e:
    print(f"✗ Firefox failed: {e}")
