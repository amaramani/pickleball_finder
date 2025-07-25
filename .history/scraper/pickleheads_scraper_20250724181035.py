import shutil
import tempfile
import time

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class PickleheadsScraper:
    """
    A scraper for Pickleheads using Selenium.
    Manages a Chrome WebDriver instance.
    """

    def __init__(self):
        self.user_data_dir = tempfile.mkdtemp()
        self.driver = self._initialize_driver()

    def _initialize_driver(self):
        """Initializes the Selenium WebDriver."""
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument(f"--user-data-dir={self.user_data_dir}")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except WebDriverException as e:
            print(f"Failed to initialize WebDriver: {e}")
            self.close()
            raise

    def scrape_page_title(self, url: str) -> str:
        """Scrapes the title of the page for a given URL."""
        self.driver.get(url)
        time.sleep(1)  # Simple wait for page to load
        return self.driver.title

    def close(self):
        """Closes the WebDriver and cleans up temporary directories."""
        if self.driver:
            self.driver.quit()
        if self.user_data_dir:
            shutil.rmtree(self.user_data_dir, ignore_errors=True)
