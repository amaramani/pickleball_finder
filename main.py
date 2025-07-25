import os
from utils.config import load_config
from core.google_places_api import GooglePlacesAPI
from core.data_processor import DataProcessor
from utils.url_formatter import PickleheadsURLFormatter
from scraper.pickleheads_scraper import PickleheadsScraper
from models.scraped_court_data import ScrapedCourtData
import time
from bs4 import BeautifulSoup
import requests
import base64


def extract_chakra_links(html_content):
    """Extract href values from anchor tags with class 'chakra-link css-13arwou' inside div with class 'chakra-stack css-1iym7wy'."""
    soup = BeautifulSoup(html_content, "html.parser")
    target_div = soup.find("div", class_="chakra-stack css-1iym7wy")
    if target_div:
        anchor_tags = target_div.find_all("a", class_="chakra-link css-13arwou")
        base_url = "https://www.pickleheads.com"
        href_links = []
        for tag in anchor_tags:
            href = tag.get("href")
            if href:
                full_url = base_url + href if href.startswith("/") else href
                href_links.append(full_url)
        print(f"Target div found. Found {len(href_links)} href links.")
        return href_links
    else:
        print("Target <div> with class 'chakra-stack css-1iym7wy' not found.")
        return []


def extract_h1_heading(html_content):
    """Extract h1 tag value with class 'chakra-heading css-1ub50s6' under div with class 'css-199v8ro'."""
    soup = BeautifulSoup(html_content, "html.parser")
    parent_div = soup.find("div", class_="css-199v8ro")
    if parent_div:
        h1_tag = parent_div.find("h1", class_="chakra-heading css-1ub50s6")
        if h1_tag:
            return h1_tag.get_text(strip=True)
    return None


def extract_anchor_links(html_content):
    """Extract anchor tags with class 'chakra-link css-1kon4c3' from three div containers with class 'chakra-stack css-1gwmid'."""
    soup = BeautifulSoup(html_content, "html.parser")
    parent_div = soup.find("div", class_="css-199v8ro")

    if parent_div:
        stack_divs = parent_div.find_all("div", class_="chakra-stack css-1igwmid")
        if stack_divs:
            anchor_data = []
            for i, div in enumerate(stack_divs[:3]):  # Limit to first 3 divs
                anchor = div.find("a", class_="chakra-link css-1kon4c3")
                if anchor:
                    href_value = anchor.get("href", "")
                    text_value = anchor.get_text(strip=True)

                    # Add base URL if href is relative
                    if href_value and href_value.startswith("/"):
                        href_value = "https://www.pickleheads.com" + href_value

                    anchor_data.append({"href": href_value, "text": text_value})
            return anchor_data
    return []


def extract_and_download_image(html_content):
    """Extract img tag with class 'chakra-image css-8938v5' under button with class 'css-13wp03w' and download image."""
    soup = BeautifulSoup(html_content, "html.parser")
    button = soup.find("button", class_="css-13wp03w")

    if button:
        img_tag = button.find("img", class_="chakra-image css-8938v5")
        if img_tag:
            img_src = img_tag.get("src")
            if img_src:
                # Handle relative URLs
                if img_src.startswith("/"):
                    img_src = "https://www.pickleheads.com" + img_src

                try:
                    # Download image
                    response = requests.get(img_src, timeout=10)
                    if response.status_code == 200:
                        # Convert to base64 for database storage
                        image_base64 = base64.b64encode(response.content).decode(
                            "utf-8"
                        )
                        return {
                            "src": img_src,
                            "image_data": image_base64,
                            "content_type": response.headers.get(
                                "content-type", "image/jpeg"
                            ),
                        }
                    else:
                        print(f"Failed to download image: HTTP {response.status_code}")
                except Exception as e:
                    print(f"Error downloading image: {e}")
            else:
                print("Image src attribute not found")
        else:
            print("Image tag with class 'chakra-image css-8938v5' not found")
    else:
        print("Button with class 'css-13wp03w' not found")

    return None


def main():
    """
    Main function to orchestrate reading zip codes, fetching pickleball courts,
    generating scrape URLs, and scraping additional info.
    """
    config = load_config()
    google_api_key = config.get("Maps_API_KEY")

    if not google_api_key:
        print("Error: Maps_API_KEY not found in .env file.")
        print(
            'Please create a .env file and add your API key: Maps_API_KEY="YOUR_API_KEY"'
        )
        return

    google_api = GooglePlacesAPI(google_api_key)
    data_processor = DataProcessor()
    url_formatter = PickleheadsURLFormatter(
        google_api_key
    )  # Pass API key for reverse geocoding
    pickleheads_scraper = None  # Will be initialized in the try block

    try:
        pickleheads_scraper = PickleheadsScraper()  # Initialize the scraper

        zip_codes_file = os.path.join("data", "zip_codes.txt")

        if not os.path.exists(zip_codes_file):
            print(f"Error: Zip codes file not found at {zip_codes_file}.")
            return

        with open(zip_codes_file, "r") as f:
            zip_codes = [line.strip() for line in f if line.strip()]

    except Exception as init_e:
        print(f"An error occurred during initialization: {init_e}")
        return

    all_pickleball_courts = []

    for zip_code in zip_codes:
        print(f"\nSearching for pickleball courts in zip code: {zip_code}...")
        try:
            geocode_result = google_api.geocode_zip_code(zip_code)
            if not geocode_result:
                print(f"Could not find coordinates for zip code: {zip_code}")
                continue

            latitude = geocode_result["lat"]
            longitude = geocode_result["lng"]
            print(f"Coordinates for {zip_code}: Lat={latitude}, Lng={longitude}")

            places_data = google_api.search_pickleball_courts(latitude, longitude)
            if places_data:
                courts_in_zip = data_processor.process_places_data(places_data)
                if courts_in_zip:
                    print(
                        f"Found {len(courts_in_zip)} potential courts in {zip_code}. Getting details..."
                    )
                    for court in courts_in_zip:
                        # Get city, state, country for the URL
                        reverse_geocode_info = google_api.reverse_geocode_coordinates(
                            court["latitude"], court["longitude"]
                        )
                        city = reverse_geocode_info.get("city", "")
                        state = reverse_geocode_info.get("state", "")
                        country = reverse_geocode_info.get("country", "")

                        scrape_url = url_formatter.generate_pickleheads_url(
                            city, state, country, court["latitude"], court["longitude"]
                        )
                        court["scrape_url"] = scrape_url
                        print(f"  Generated URL for {court['name']}: {scrape_url}")
                        all_pickleball_courts.append(court)

                        # --- Scraping part ---
                        # IMPORTANT: Due to robots.txt, this part is highly experimental
                        # and might be blocked or lead to IP bans.
                        # Proceed with caution and ethical consideration.
                        try:
                            print(f"  Attempting to scrape: {scrape_url}")
                            # Scrape complete page data
                            scraped_data = pickleheads_scraper.scrape_page_data(
                                scrape_url
                            )
                            if scraped_data:
                                print(f"  Scraped Title: {scraped_data['title']}")
                                court["scraped_title"] = scraped_data["title"]
                                court["page_source"] = scraped_data["page_source"]
                                court["final_url"] = scraped_data["url"]

                                # Extract chakra-link anchor tags
                                chakra_links = extract_chakra_links(
                                    scraped_data["page_source"]
                                )
                                court["chakra_links"] = chakra_links
                                print(f"  Found {len(chakra_links)} href links:")
                                for i, link in enumerate(chakra_links):
                                    print(f"    {i+1}. {link}")

                                # Scrape all href URLs
                                court["scraped_hrefs"] = []
                                for i, link in enumerate(chakra_links):
                                    print(f"  Scraping href {i+1}: {link}")
                                    try:
                                        href_data = (
                                            pickleheads_scraper.scrape_page_data(link)
                                        )
                                        if href_data:
                                            # Extract h1 heading
                                            h1_heading = extract_h1_heading(
                                                href_data["page_source"]
                                            )

                                            # Extract anchor links
                                            anchor_links = extract_anchor_links(
                                                href_data["page_source"]
                                            )

                                            # Extract and download image
                                            image_data = extract_and_download_image(
                                                href_data["page_source"]
                                            )
                                            
                                            # Create ScrapedCourtData object
                                            court_data = ScrapedCourtData.from_scraped_data(
                                                h1_heading, anchor_links, image_data
                                            )

                                            court["scraped_hrefs"].append(
                                                {
                                                    "url": link,
                                                    "title": href_data["title"],
                                                    "final_url": href_data["url"],
                                                    "page_source": href_data[
                                                        "page_source"
                                                    ],
                                                    "h1_heading": h1_heading,
                                                    "anchor_links": anchor_links,
                                                    "image_data": image_data,
                                                    "court_data": court_data
                                                }
                                            )
                                            print(
                                                f"    ✓ Scraped: {href_data['title']}"
                                            )
                                            if h1_heading:
                                                print(f"    ✓ H1 Heading: {h1_heading}")
                                            if anchor_links:
                                                for j, anchor in enumerate(
                                                    anchor_links
                                                ):
                                                    print(
                                                        f"    ✓ Anchor {j+1} - Text: {anchor['text']}, Href: {anchor['href']}"
                                                    )
                                            else:
                                                print(f"    ✗ No anchor links found")
                                            if image_data:
                                                print(
                                                    f"    ✓ Image downloaded: {image_data['src']}"
                                                )
                                                print(
                                                    f"    ✓ Image size: {len(image_data['image_data'])} bytes (base64)"
                                                )
                                            else:
                                                print(f"    ✗ No image found")
                                            
                                            # Display court data object
                                            print(f"    ✓ Court Data: {court_data}")
                                            print(f"    ✓ Court Dict: {court_data.to_dict()}")
                                        else:
                                            print(f"    ✗ Failed to scrape {link}")
                                    except Exception as href_e:
                                        print(f"    ✗ Error scraping {link}: {href_e}")
                            else:
                                print("  Failed to scrape page data.")
                        except Exception as scrape_e:
                            print(f"  Error during scraping {scrape_url}: {scrape_e}")
                        # --- End Scraping part ---

                else:
                    print(f"No pickleball courts found in {zip_code}.")
            else:
                print(f"No place data returned for {zip_code}.")

        except Exception as e:
            print(f"An error occurred while processing zip code {zip_code}: {e}")

    print("\n--- All Found Pickleball Courts with Scrape URLs ---")
    if all_pickleball_courts:
        for i, court in enumerate(all_pickleball_courts):
            print(f"Court {i+1}:")
            print(f"  Name: {court['name']}")
            print(f"  Address: {court['address']}")
            print(f"  Latitude: {court['latitude']}")
            print(f"  Longitude: {court['longitude']}")
            if "scrape_url" in court:
                print(f"  Scrape URL: {court['scrape_url']}")
            if "scraped_title" in court:
                print(f"  Scraped Title: {court['scraped_title']}")
            if "page_source" in court:
                print(f"  Page Source Length: {len(court['page_source'])} characters")
            if "final_url" in court:
                print(f"  Final URL: {court['final_url']}")
            if "chakra_links" in court:
                print(f"  Href Links Found: {len(court['chakra_links'])}")
                for i, link in enumerate(court["chakra_links"]):
                    print(f"    {i+1}. {link}")
            if "scraped_hrefs" in court:
                print(f"  Scraped Href Pages: {len(court['scraped_hrefs'])}")
                for i, href_data in enumerate(court["scraped_hrefs"]):
                    print(f"    {i+1}. {href_data['title']} - {href_data['final_url']}")
                    print(
                        f"       Source length: {len(href_data['page_source'])} characters"
                    )
                    if href_data.get("h1_heading"):
                        print(f"       H1 Heading: {href_data['h1_heading']}")
                    else:
                        print(f"       H1 Heading: Not found")
                    if href_data.get("anchor_links"):
                        print(
                            f"       Anchor Links: {len(href_data['anchor_links'])} found"
                        )
                        for j, anchor in enumerate(href_data["anchor_links"]):
                            print(
                                f"         {j+1}. Text: {anchor['text']}, Href: {anchor['href']}"
                            )
                    else:
                        print(f"       Anchor Links: Not found")
                    if href_data.get("image_data"):
                        print(f"       Image: {href_data['image_data']['src']}")
                        print(
                            f"       Image Type: {href_data['image_data']['content_type']}"
                        )
                        print(
                            f"       Image Size: {len(href_data['image_data']['image_data'])} bytes"
                        )
                    else:
                        print(f"       Image: Not found")
                    if href_data.get("court_data"):
                        court_obj = href_data['court_data']
                        print(f"       Court Object: {court_obj}")
                        print(f"       Court Dict: {court_obj.to_dict()}")
                        if court_obj.image_data:
                            print(f"       Image Data: Available ({len(court_obj.image_data.get('image_data', ''))} bytes)")
                    else:
                        print(f"       Court Object: Not created")
            print("=" * 30)
    else:
        print("No pickleball courts found across all provided zip codes.")

    # Clean up scraper resources
    try:
        pickleheads_scraper.close()
    except Exception as cleanup_e:
        print(f"Error during scraper cleanup: {cleanup_e}")


if __name__ == "__main__":
    main()
