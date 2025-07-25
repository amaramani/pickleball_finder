from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random


class PickleheadsScraper:
    """
    Scrapes data from pickleheads.com using Selenium WebDriver.
    Includes strategies to avoid 403 Forbidden errors.
    """

    def __init__(self):
        self.driver = None
        self._initialize_driver()

    def _initialize_driver(self):
        """Initializes the Chrome WebDriver with anti-detection options."""
        options = Options()

        # Headless mode: Runs Chrome without opening a visible browser window.
        # Uncomment this line for production or if you don't need to see the browser.
        # options.add_argument("--headless")

        # Bypass OS-level security measures (useful in some environments)
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument(
            "--start-maximized"
        )  # Start maximized to avoid issues with element visibility

        # User-Agent spoofing: Mimic a real browser. Rotate if possible.
        # You can get up-to-date user agents from sites like whatismybrowser.com
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/126.0.0.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            # Add more user agents
        ]
        options.add_argument(f"user-agent={random.choice(user_agents)}")

        # Prevent detection of automated Browse
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        # Add a custom header (Referer is often useful)
        options.add_argument(
            "--referer=https://www.google.com/"
        )  # Mimic coming from a Google search

        # For adding specific request headers *before* the request is made (more advanced, often requires Selenium Wire)
        # Selenium WebDriver itself doesn't offer a direct way to set HTTP request headers for initial page load.
        # The User-Agent and Referer are set via arguments. For more complex header manipulation,
        # you'd typically use `selenium-wire` or a proxy that allows header modification.
        # For simplicity, we'll rely on common arguments here.

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )  # Evade webdriver detection

    def scrape_page_title(self, url: str) -> str | None:
        """
        Loads a URL and attempts to scrape the page title.

        Args:
            url (str): The URL to scrape.

        Returns:
            str | None: The page title if found, otherwise None.
        """
        try:
            self.driver.get(url)

            # Wait for the page to load and specific elements to be present.
            # This is crucial for dynamic content and avoiding "403 Forbidden" if content loads later.
            # Adjust the expected condition based on what you expect to load on pickleheads.com
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.TAG_NAME, "body")
                )  # Wait for the body to be present
                # EC.presence_of_element_located((By.CSS_SELECTOR, "h1.page-title")) # More specific element
            )

            # Add a small, random delay to mimic human behavior
            time.sleep(random.uniform(1, 3))

            # Check for common "403 Forbidden" indicators in the page source
            if (
                "403 Forbidden" in self.driver.page_source
                or "Access Denied" in self.driver.page_source
            ):
                print(
                    f"  Warning: Page returned a 403 Forbidden or Access Denied for {url}"
                )
                return None

            return self.driver.title

        except Exception as e:
            print(f"  Error scraping {url}: {e}")
            return None

    def close(self):
        """Closes the WebDriver."""
        if self.driver:
            self.driver.quit()
