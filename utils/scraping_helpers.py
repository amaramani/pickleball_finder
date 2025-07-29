from bs4 import BeautifulSoup
import requests
import base64
from typing import Optional, Dict, Any
from utils.performance_helpers import retry_on_failure, safe_extract, validate_url, logger


@retry_on_failure(max_retries=2, delay=1.0)
def process_court_link(scraper, link: str, db) -> Optional[Dict[str, Any]]:
    """Process individual court link with error handling and retries."""
    import time
    start_time = time.time()
    
    try:
        if not validate_url(link):
            logger.warning(f"Invalid URL: {link}")
            return None
            
        link_data = scraper.scrape_page_data(link)
        if not link_data:
            return None
            
        # Extract data with safe extraction
        h1_heading = safe_extract(extract_h1_heading, link_data["page_source"])
        anchor_links = safe_extract(extract_anchor_links, link_data["page_source"]) or []
        
        # Check for duplicate address before processing image (expensive operation)
        if anchor_links and db:
            # Get address from anchor links (usually first one is address)
            address = None
            for anchor in anchor_links:
                if 'address' in anchor.get('text', '').lower() or len(anchor.get('text', '')) > 10:
                    address = anchor.get('text', '').strip()
                    break
            
            if address and db.address_exists(address):
                processing_time = time.time() - start_time
                return {
                    'duplicate': True,
                    'address': address,
                    'url': link,
                    'processing_time': processing_time
                }
        
        # Only extract image if not duplicate
        image_data = safe_extract(extract_and_download_image, link_data["page_source"])
        
        # Create court data object
        from models.scraped_court_data import ScrapedCourtData
        court_data = ScrapedCourtData.from_scraped_data(h1_heading, anchor_links, image_data)
        
        # Save to database if available
        saved_court = None
        if db:
            try:
                saved_court = db.save_court_data(court_data)
            except Exception as e:
                logger.error(f"Database save failed: {e}")
        
        processing_time = time.time() - start_time
        return {
            'link_data': link_data,
            'court_data': court_data,
            'saved_court': saved_court,
            'h1_heading': h1_heading,
            'anchor_links': anchor_links,
            'image_data': image_data,
            'url': link,
            'title': link_data['title'],
            'final_url': link_data['url'],
            'page_source': link_data['page_source'],
            'processing_time': processing_time
        }
    except Exception as e:
        logger.error(f"Error processing court link {link}: {e}")
        return None


def analyze_court_data(court_data) -> tuple:
    """Analyze court data completeness and image availability."""
    try:
        name, address, phone = court_data.name, court_data.address, court_data.telephone
        has_complete_info = bool(name and address and phone)
        has_image = bool(court_data.image_data)
        
        fields = {
            'Complete info': 'Yes' if has_complete_info else 'No',
            'Has image': 'Yes' if has_image else 'No',
            'Name': '✓' if name else '✗',
            'Address': '✓' if address else '✗',
            'Phone': '✓' if phone else '✗',
            'Website': '✓' if court_data.websitetext else '✗'
        }
        
        print("   ✓ Data Analysis:")
        for field, value in fields.items():
            print(f"     - {field}: {value}")
        
        return has_complete_info, has_image
    except Exception as e:
        logger.error(f"Error analyzing court data: {e}")
        return False, False


def update_court_statistics(stats: Dict[str, Any], court_data, zipcode: str = None):
    """Update statistics for processed court data."""
    stats['total_courts'] += 1
    
    # Analyze court data
    has_complete_info, has_image = analyze_court_data(court_data)
    
    # Update statistics
    if has_complete_info:
        stats['courts_with_complete_info'] += 1
    else:
        stats['courts_with_missing_info'] += 1
        missing_fields = []
        if not court_data.name:
            missing_fields.append('name')
        if not court_data.address:
            missing_fields.append('address')
        if not court_data.telephone:
            missing_fields.append('telephone')
        
        stats['missing_info_courts'].append({
            'name': court_data.name or 'N/A',
            'address': court_data.address or 'N/A',
            'missing_fields': missing_fields,
            'zipcode': zipcode
        })
    
    if has_image:
        stats['courts_with_image'] += 1
    else:
        stats['courts_without_image'] += 1
    
    return has_complete_info, has_image


def extract_chakra_links(html_content, url=None):
    """Extract href values from anchor tags with class 'chakra-link css-13arwou'."""
    soup = BeautifulSoup(html_content, "html.parser")
    anchor_tags = soup.find_all("a", class_="chakra-link css-13arwou")
    
    base_url = "https://www.pickleheads.com"
    href_links = []
    
    for tag in anchor_tags:
        href = tag.get("href")
        if href:
            full_url = base_url + href if href.startswith("/") else href
            href_links.append(full_url)
        else:
            print("   ⚠ Found anchor tag but no href attribute")
    
    print(f"Found {len(href_links)} href links.")
    if len(href_links) == 0 and url:
        print(f"   📍 URL: {url}")
    
    return href_links


def extract_h1_heading(html_content):
    """Extract h1 tag value with class 'chakra-heading css-1ub50s6'."""
    soup = BeautifulSoup(html_content, "html.parser")
    parent_div = soup.find("div", class_="css-199v8ro")
    if parent_div:
        h1_tag = parent_div.find("h1", class_="chakra-heading css-1ub50s6")
        if h1_tag:
            return h1_tag.get_text(strip=True)
        else:
            print("   ✗ H1 tag with required class not found")
            return None
    else:
        print("   ✗ Parent div with class 'css-199v8ro' not found")
        return None


def extract_anchor_links(html_content):
    """Extract anchor tags with class 'chakra-link css-1kon4c3'."""
    soup = BeautifulSoup(html_content, "html.parser")
    parent_div = soup.find("div", class_="css-199v8ro")

    if parent_div:
        stack_divs = parent_div.find_all("div", class_="chakra-stack css-1igwmid")
        if stack_divs:
            anchor_data = []
            for i, div in enumerate(stack_divs[:3]):
                anchor = div.find("a", class_="chakra-link css-1kon4c3")
                if anchor:
                    href_value = anchor.get("href", "")
                    text_value = anchor.get_text(strip=True)

                    if href_value and href_value.startswith("/"):
                        href_value = "https://www.pickleheads.com" + href_value

                    anchor_data.append({"href": href_value, "text": text_value})
                else:
                    print(f"   ⚠ No anchor found in stack div {i+1}")
            return anchor_data
        else:
            print("   ✗ No stack divs with required class found")
            return []
    else:
        print("   ✗ Parent div not found for anchor extraction")
        return []


def extract_and_download_image(html_content):
    """Extract and download court image."""
    soup = BeautifulSoup(html_content, "html.parser")
    button = soup.find("button", class_="css-13wp03w")

    if button:
        img_tag = button.find("img", class_="chakra-image css-8938v5")
        if img_tag:
            img_src = img_tag.get("src")
            if img_src:
                if img_src.startswith("/"):
                    img_src = "https://www.pickleheads.com" + img_src

                try:
                    response = requests.get(img_src, timeout=10)
                    if response.status_code == 200:
                        image_base64 = base64.b64encode(response.content).decode("utf-8")
                        return {
                            "src": img_src,
                            "image_data": image_base64,
                            "content_type": response.headers.get("content-type", "image/jpeg"),
                        }
                    else:
                        print(f"   ✗ Failed to download image: HTTP {response.status_code}")
                        return None
                except Exception as e:
                    print(f"   ✗ Error downloading image: {e}")
                    return None
            else:
                print("   ✗ Image src attribute not found")
                return None
        else:
            print("   ✗ Image tag with required class not found")
            return None
    else:
        print("   ✗ Button with required class not found")
        return None