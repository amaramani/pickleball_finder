import os
import time
import json
from datetime import datetime
from utils.config import load_config
from core.google_places_api import GooglePlacesAPI
from core.data_processor import DataProcessor


class ZipcodeFilter:
    """Advanced zipcode filtering with progress tracking and resume capability."""
    
    def __init__(self):
        config = load_config()
        self.google_api_key = config.get("Maps_API_KEY")
        if not self.google_api_key:
            raise ValueError("Maps_API_KEY not found in .env file")
        
        self.google_api = GooglePlacesAPI(self.google_api_key)
        self.data_processor = DataProcessor()
        self.progress_file = "data/filter_progress.json"
    
    def save_progress(self, processed_zipcodes: set, valid_zipcodes: list, current_index: int):
        """Save current progress to resume later."""
        progress = {
            'processed_zipcodes': list(processed_zipcodes),
            'valid_zipcodes': valid_zipcodes,
            'current_index': current_index,
            'timestamp': datetime.now().isoformat()
        }
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f)
    
    def load_progress(self):
        """Load previous progress if exists."""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)
                return (
                    set(progress.get('processed_zipcodes', [])),
                    progress.get('valid_zipcodes', []),
                    progress.get('current_index', 0)
                )
        return set(), [], 0
    
    def check_zipcode_has_courts(self, zip_code: str) -> tuple:
        """Check if zipcode has pickleball courts. Returns (has_courts, court_count)."""
        try:
            geocode_result = self.google_api.geocode_zip_code(zip_code)
            if not geocode_result:
                return False, 0
            
            places_data = self.google_api.search_pickleball_courts(
                geocode_result["lat"], geocode_result["lng"]
            )
            
            if places_data:
                courts = self.data_processor.process_places_data(places_data)
                return len(courts) > 0, len(courts)
            
            return False, 0
            
        except Exception as e:
            print(f"Error checking {zip_code}: {e}")
            return False, 0
    
    def filter_zipcodes(self, input_file: str, output_file: str, batch_size: int = 50):
        """Filter zip codes with progress tracking and batching."""
        
        # Read all zip codes
        if not os.path.exists(input_file):
            print(f"Error: Input file {input_file} not found.")
            return
        
        with open(input_file, 'r') as f:
            all_zipcodes = [line.strip() for line in f if line.strip()]
        
        # Load previous progress
        processed_zipcodes, valid_zipcodes, start_index = self.load_progress()
        total_courts_found = 0
        
        print(f"Total zip codes to process: {len(all_zipcodes)}")
        print(f"Starting from index: {start_index}")
        print(f"Previously found valid zip codes: {len(valid_zipcodes)}")
        
        start_time = time.time()
        
        for i in range(start_index, len(all_zipcodes)):
            zip_code = all_zipcodes[i]
            
            if zip_code in processed_zipcodes:
                continue
            
            zipcode_start = time.time()
            print(f"[{i+1}/{len(all_zipcodes)}] Checking {zip_code}...", end=" ")
            
            has_courts, court_count = self.check_zipcode_has_courts(zip_code)
            zipcode_time = time.time() - zipcode_start
            processed_zipcodes.add(zip_code)
            
            if has_courts:
                valid_zipcodes.append(zip_code)
                total_courts_found += court_count
                print(f"✅ {court_count} courts ({zipcode_time:.1f}s)")
            else:
                print(f"❌ No courts ({zipcode_time:.1f}s)")
            
            # Save progress every batch_size iterations
            if (i + 1) % batch_size == 0:
                self.save_progress(processed_zipcodes, valid_zipcodes, i + 1)
                elapsed = time.time() - start_time
                rate = (i + 1 - start_index) / elapsed
                remaining = len(all_zipcodes) - i - 1
                eta = remaining / rate if rate > 0 else 0
                
                print(f"\n📊 Progress: {i+1}/{len(all_zipcodes)} ({(i+1)/len(all_zipcodes)*100:.1f}%)")
                print(f"⏱️  Rate: {rate:.1f} zip codes/sec, ETA: {eta/60:.1f} minutes")
                print(f"✅ Valid zip codes found so far: {len(valid_zipcodes)}")
                print(f"🏈 Total courts found so far: {total_courts_found}\n")
            
            # Rate limiting
            time.sleep(0.1)
        
        # Save final results
        with open(output_file, 'w') as f:
            for zip_code in valid_zipcodes:
                f.write(f"{zip_code}\n")
        
        # Clean up progress file
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
        
        total_time = time.time() - start_time
        print(f"\n🎉 Filtering complete!")
        print(f"Total processing time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"Average time per zipcode: {total_time/len(all_zipcodes):.1f} seconds")
        print(f"Total zip codes processed: {len(all_zipcodes)}")
        print(f"Zip codes with courts: {len(valid_zipcodes)} ({len(valid_zipcodes)/len(all_zipcodes)*100:.1f}%)")
        print(f"Total courts found: {total_courts_found}")
        print(f"Average courts per valid zipcode: {total_courts_found/len(valid_zipcodes):.1f}" if valid_zipcodes else "")
        print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    input_file = os.path.join("data", "zip_codes.txt")
    output_file = os.path.join("data", "zip_codes_with_courts.txt")
    
    try:
        filter_tool = ZipcodeFilter()
        filter_tool.filter_zipcodes(input_file, output_file)
    except Exception as e:
        print(f"Error: {e}")