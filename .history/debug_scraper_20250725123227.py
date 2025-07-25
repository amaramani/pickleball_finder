from scraper.pickleheads_scraper import PickleheadsScraper
import time
from bs4 import BeautifulSoup


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
        else:
            print("H1 tag with class 'chakra-heading css-1ub50s6' not found.")
    else:
        print("Parent <div> with class 'css-199v8ro' not found.")
    return None


def extract_anchor_links(html_content):
    """Extract anchor tags with class 'chakra-link css-1kon4c3' from three div containers with class 'chakra-stack css-1gwmid'."""
    soup = BeautifulSoup(html_content, "html.parser")
    # parent_div = soup.find("div", class_="chakra-stack css-199v8ro")
    parent_div = soup.find("div", class_="chakra-stack css-11nrrcx")

    if parent_div:
        stack_divs = parent_div.find_all("div", class_="chakra-stack css-1gwmid")
        if stack_divs:
            print(
                f"Found {len(stack_divs)} div containers with class 'chakra-stack css-1gwmid'"
            )
        else:
            print("Div containers with class 'chakra-stack css-1igwmid' not found.")
            return []
        if len(stack_divs) >= 3:
            print("Found 3 div containers with class 'chakra-stack css-1gwmid'")
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
                    print(f"Anchor {i+1} - Href: {href_value}, Text: {text_value}")
                else:
                    print(
                        f"Anchor tag with class 'chakra-link css-1kon4c3' not found in div {i+1}"
                    )

            return anchor_data
        else:
            print("Div containers with class 'chakra-stack css-1gwmid' not found.")
    else:
        print("Parent <div> with class 'css-199v8ro' not found.")

    return []


def debug_scrape_url(url):
    """Debug a specific URL scraping process."""
    print(f"\n=== DEBUG SCRAPING: {url} ===")

    scraper = PickleheadsScraper(headless=False)  # Visible for debugging

    try:
        print("1. Navigating to URL...")
        scraper.driver.get(url)

        print("2. Waiting for initial load...")
        time.sleep(3)

        print(f"3. Current URL: {scraper.driver.current_url}")
        print(f"4. Page title: {scraper.driver.title}")

        print("5. Checking page source...")
        page_source = scraper.driver.page_source
        print(f"   - Page source length: {len(page_source)}")

        # Check for common indicators
        source_lower = page_source.lower()
        indicators = {
            "Cloudflare": "cloudflare" in source_lower,
            "Browser check": "checking your browser" in source_lower,
            "403 Forbidden": "403 forbidden" in source_lower,
            "Access denied": "access denied" in source_lower,
            "CAPTCHA": "captcha" in source_lower,
        }

        print("6. Page indicators:")
        for indicator, found in indicators.items():
            status = "✓ FOUND" if found else "✗ Not found"
            print(f"   - {indicator}: {status}")

        print("\n7. Waiting for user input...")
        input("Press Enter to continue (check browser window)...")

        # Try the full scraping method
        print("8. Testing full scrape method...")
        data = scraper.scrape_page_data(url)

        if data:
            print("✓ Scraping successful!")
            print(f"   - Title: {data['title']}")
            print(f"   - Final URL: {data['url']}")
            print(f"   - Source length: {len(data['page_source'])}")

            # Extract and display chakra links
            print("\n9. Extracting chakra links...")
            chakra_links = extract_chakra_links(data["page_source"])
            if chakra_links:
                print(f"Found {len(chakra_links)} href links:")
                for i, link in enumerate(chakra_links):
                    print(f"   {i+1}. {link}")

                # Scrape all href URLs
                print("\n10. Scraping all href URLs...")
                for i, link in enumerate(chakra_links):
                    print(f"\nScraping URL {i+1}: {link}")
                    try:
                        link_data = scraper.scrape_page_data(link)
                        if link_data:
                            print(f"   ✓ Title: {link_data['title']}")
                            print(f"   ✓ Final URL: {link_data['url']}")

                            # Extract h1 heading
                            h1_heading = extract_h1_heading(link_data["page_source"])
                            if h1_heading:
                                print(f"   ✓ H1 Heading: {h1_heading}")
                            else:
                                print("   ✗ H1 heading not found")

                            # Extract anchor links
                            print("   Extracting anchor links...")
                            anchor_links = extract_anchor_links(
                                link_data["page_source"]
                            )
                            if anchor_links:
                                for j, anchor in enumerate(anchor_links):
                                    anchor_href = anchor["href"]
                                    anchor_text = anchor["text"]
                                    print(f"   ✓ Anchor {j+1} - Href: {anchor_href}")
                                    print(f"   ✓ Anchor {j+1} - Text: {anchor_text}")
                            else:
                                print("   ✗ No anchor links found")
                        else:
                            print("   ✗ Failed to scrape")
                    except Exception as e:
                        print(f"   ✗ Error: {e}")
            else:
                print("No chakra links found.")
        else:
            print("✗ Scraping failed")

    except Exception as e:
        print(f"ERROR: {e}")

    finally:
        scraper.close()


if __name__ == "__main__":
    # Test with a sample pickleheads URL
    test_url = "https://www.pickleheads.com/search?q=Irvine+CA+USA&lat=33.6846&lng=-117.8265&z=10.0"
    debug_scrape_url(test_url)
