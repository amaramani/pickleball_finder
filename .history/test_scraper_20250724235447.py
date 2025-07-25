# Create test_scraper.py
from scraper.pickleheads_scraper import PickleheadsScraper

try:
    scraper = PickleheadsScraper(headless=False)  # Visible browser for debugging
    print("✓ Firefox initialized successfully")

    # Test simple navigation
    scraper.driver.get("https://www.google.com")
    print(f"✓ Navigation works - Title: {scraper.driver.title}")

    scraper.close()
except Exception as e:
    print(f"✗ Firefox failed: {e}")
