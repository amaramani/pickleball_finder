import os
import time
from utils.config import load_config
from core.google_places_api import GooglePlacesAPI
from core.data_processor import DataProcessor


def filter_zipcodes_with_courts(input_file: str, output_file: str):
    """Filter zip codes that have at least one pickleball court."""
    
    # Load configuration
    config = load_config()
    google_api_key = config.get("Maps_API_KEY")
    
    if not google_api_key:
        print("Error: Maps_API_KEY not found in .env file.")
        return
    
    # Initialize APIs
    google_api = GooglePlacesAPI(google_api_key)
    data_processor = DataProcessor()
    
    # Read zip codes
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found.")
        return
    
    with open(input_file, 'r') as f:
        zip_codes = [line.strip() for line in f if line.strip()]
    
    print(f"Processing {len(zip_codes)} zip codes...")
    
    # Filter zip codes with courts
    valid_zipcodes = []
    processed_count = 0
    total_courts_found = 0
    start_time = time.time()
    
    for zip_code in zip_codes:
        processed_count += 1
        zipcode_start = time.time()
        print(f"Checking {zip_code} ({processed_count}/{len(zip_codes)})...", end=" ")
        
        try:
            # Get coordinates for zip code
            geocode_result = google_api.geocode_zip_code(zip_code)
            if not geocode_result:
                print("❌ Invalid zip code")
                continue
            
            # Search for pickleball courts
            places_data = google_api.search_pickleball_courts(
                geocode_result["lat"], geocode_result["lng"]
            )
            
            if places_data:
                if data_processor.has_any_courts(places_data):
                    # Only process full data if we need the count
                    courts = data_processor.process_places_data(places_data)
                    valid_zipcodes.append(zip_code)
                    total_courts_found += len(courts)
                    zipcode_time = time.time() - zipcode_start
                    print(f"✅ Found {len(courts)} courts ({zipcode_time:.1f}s)")
                else:
                    zipcode_time = time.time() - zipcode_start
                    print(f"❌ No valid courts ({zipcode_time:.1f}s)")
            else:
                zipcode_time = time.time() - zipcode_start
                print(f"❌ No courts found ({zipcode_time:.1f}s)")
                
        except Exception as e:
            zipcode_time = time.time() - zipcode_start
            print(f"❌ Error: {e} ({zipcode_time:.1f}s)")
        
        # Rate limiting
        time.sleep(0.1)
    
    # Save filtered zip codes
    with open(output_file, 'w') as f:
        for zip_code in valid_zipcodes:
            f.write(f"{zip_code}\n")
    
    total_time = time.time() - start_time
    
    print(f"\n✅ Filtering complete!")
    print(f"Total processing time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"Average time per zipcode: {total_time/len(zip_codes):.1f} seconds")
    print(f"Total zip codes processed: {len(zip_codes)}")
    print(f"Zip codes with courts: {len(valid_zipcodes)}")
    print(f"Total courts found: {total_courts_found}")
    print(f"Average courts per valid zipcode: {total_courts_found/len(valid_zipcodes):.1f}" if valid_zipcodes else "")
    print(f"Filtered zip codes saved to: {output_file}")


if __name__ == "__main__":
    input_file = os.path.join("data", "zip_codes.txt")
    output_file = os.path.join("data", "zip_codes_with_courts.txt")
    
    filter_zipcodes_with_courts(input_file, output_file)