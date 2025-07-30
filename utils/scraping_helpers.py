"""
Scraping Helper Functions - HTML parsing utilities
"""
from bs4 import BeautifulSoup


def extract_chakra_links(html_content: str, url: str = None) -> list:
    """Extract court URLs from search page."""
    soup = BeautifulSoup(html_content, "html.parser")
    anchor_tags = soup.find_all("a", class_="chakra-link css-13arwou")
    
    base_url = "https://www.pickleheads.com"
    court_urls = []
    
    for tag in anchor_tags:
        href = tag.get("href")
        if href:
            full_url = base_url + href if href.startswith("/") else href
            court_urls.append(full_url)
    
    print(f"Found {len(court_urls)} court URLs")
    return court_urls


def extract_h1_heading(html_content: str) -> str:
    """Extract court name from h1 tag."""
    soup = BeautifulSoup(html_content, "html.parser")
    parent_div = soup.find("div", class_="css-199v8ro")
    
    if parent_div:
        h1_tag = parent_div.find("h1", class_="chakra-heading css-1ub50s6")
        if h1_tag:
            return h1_tag.get_text(strip=True)
    
    return None


def extract_anchor_links(html_content: str) -> list:
    """Extract address information from anchor tags."""
    soup = BeautifulSoup(html_content, "html.parser")
    parent_div = soup.find("div", class_="css-199v8ro")
    
    if not parent_div:
        return []
    
    stack_divs = parent_div.find_all("div", class_="chakra-stack css-1igwmid")
    if not stack_divs:
        return []
    
    anchor_data = []
    # Only get first anchor (address)
    for div in stack_divs[:1]:
        anchor = div.find("a", class_="chakra-link css-1kon4c3")
        if anchor:
            href_value = anchor.get("href", "")
            text_value = anchor.get_text(strip=True)
            
            if href_value and href_value.startswith("/"):
                href_value = "https://www.pickleheads.com" + href_value
            
            anchor_data.append({"href": href_value, "text": text_value})
    
    return anchor_data