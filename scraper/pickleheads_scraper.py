from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.firefox import GeckoDriverManager
import time
import random


class PickleheadsScraper:
    """Robust Firefox-based scraper with Cloudflare bypass."""

    def __init__(self, headless: bool = False):
        self.driver = None
        self.last_request_time = 0
        self._initialize_driver(headless)

    def _initialize_driver(self, headless):
        """Initialize Firefox with stealth options."""
        options = Options()
        
        if headless:
            options.add_argument("--headless")
        
        # Firefox preferences for stealth
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0")
        
        try:
            service = Service(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=options)
            
            # Apply stealth JavaScript
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except Exception as e:
            raise RuntimeError(f"Firefox failed: {e}")

    def _wait_for_page_load(self, timeout=30):
        """Wait for Cloudflare and page to load."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                page_source = self.driver.page_source.lower()
                
                # Check if still loading Cloudflare
                cf_loading = any(indicator in page_source for indicator in [
                    "checking your browser", "please wait", "ddos protection",
                    "cf-browser-verification", "challenge-form"
                ])
                
                if not cf_loading and "body" in page_source:
                    return True
                    
                time.sleep(2)
                
            except Exception:
                time.sleep(2)
        
        return False

    def scrape_page_data(self, url: str) -> dict | None:
        """Scrape complete page data including title and source."""
        if not self.driver:
            return None
        
        # Rate limiting
        current_time = time.time()
        if current_time - self.last_request_time < 5:
            sleep_time = 5 - (current_time - self.last_request_time) + random.uniform(1, 2)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        
        try:
            # Navigate to page
            self.driver.get(url)
            time.sleep(random.uniform(2, 4))
            
            # Wait for page to fully load (including Cloudflare)
            if not self._wait_for_page_load():
                print(f"  Page load timeout for {url}")
                return None
            
            # Additional wait for dynamic content
            time.sleep(random.uniform(1, 3))
            
            # Get page source
            page_source = self.driver.page_source
            
            # Check for blocking
            if any(block in page_source.lower() for block in ["403 forbidden", "access denied", "blocked"]):
                print(f"  Access blocked for {url}")
                return None
            
            # Return comprehensive page data
            return {
                "title": self.driver.title.strip() if self.driver.title else None,
                "page_source": page_source,
                "url": self.driver.current_url
            }
            
        except Exception as e:
            print(f"  Error scraping {url}: {e}")
            return None
    
    def scrape_page_title(self, url: str) -> str | None:
        """Scrape page title only (for backward compatibility)."""
        data = self.scrape_page_data(url)
        return data["title"] if data else None

    def close(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()