import os
import shutil
import tempfile

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class PickleheadsScraper:
    def __init__(self):
        # and set up the webdriver.
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
        chrome_options.add_argument(
            "--window-size=1920,1080"
        )  # Set window size to avoid mobile view
        chrome_options.add_argument("--disable-extensions")  # Disable extensions
        chrome_options.add_argument("--disable-notifications")  # Disable notifications

        # Create a unique user data directory for each instance
        self.user_data_dir = tempfile.mkdtemp()
        chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
        chrome_options.add_argument("--profile-directory=Default")  # Specify profile directory

        self.driver = webdriver.Chrome(
            executable_path=ChromeDriverManager().install(),
            options=chrome_options,
        )

        )
        self.wait = WebDriverWait(self.driver, 10)

        """
        self.driver.quit()
        print("Webdriver closed")
        # Clean up the temporary user data directory
        shutil.rmtree(self.user_data_dir, ignore_errors=True)

    def scrape_page_title(self, url):
        """
