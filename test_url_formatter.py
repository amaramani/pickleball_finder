# Create test_url_formatter.py
from utils.url_formatter import PickleheadsURLFormatter
from utils.config import load_config

config = load_config()
formatter = PickleheadsURLFormatter(config.get("Maps_API_KEY"))

url = formatter.generate_pickleheads_url("Irvine", "CA", "USA", 33.6846, -117.8265)
print(f"Generated URL: {url}")
