"""
Court Scraper - Scrapes individual court data from pickleheads.com
"""
from scraper.pickleheads_scraper import PickleheadsScraper
from utils.scraping_helpers import extract_h1_heading, extract_anchor_links
from utils.performance_helpers import safe_extract, validate_url, logger
from models.scraped_court_data import ScrapedCourtData


class CourtScraper:
    """Scrapes individual court data from court URLs."""
    
    def __init__(self):
        self.scraper = PickleheadsScraper()
    
    def scrape_court(self, court_url: str) -> ScrapedCourtData:
        """Scrape data for a single court."""
        try:
            if not validate_url(court_url):
                logger.warning(f"Invalid URL: {court_url}")
                return None
            
            # Get page data
            page_data = self.scraper.scrape_page_data(court_url)
            if not page_data:
                return None
            
            # Extract court information
            court_name = safe_extract(extract_h1_heading, page_data["page_source"])
            anchor_links = safe_extract(extract_anchor_links, page_data["page_source"]) or []
            
            # Create court data object
            court_data = ScrapedCourtData.from_scraped_data(
                court_name, anchor_links, court_url
            )
            
            return court_data
            
        except Exception as e:
            logger.error(f"Error scraping court {court_url}: {e}")
            return None
    
    def close(self):
        """Clean up resources."""
        if self.scraper:
            self.scraper.close()