"""
Batch Processor - Process zip codes in batches with progress tracking
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class BatchProcessor:
    """Process zip codes in batches for better performance monitoring."""
    
    def __init__(self, batch_size: int = 10, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers
    
    def process_batches(self, zip_codes: list, process_func, *args) -> list:
        """Process zip codes in batches with progress tracking."""
        all_results = []
        total_batches = (len(zip_codes) + self.batch_size - 1) // self.batch_size
        
        for batch_num in range(0, len(zip_codes), self.batch_size):
            batch = zip_codes[batch_num:batch_num + self.batch_size]
            current_batch = (batch_num // self.batch_size) + 1
            
            print(f"\n--- Batch {current_batch}/{total_batches} ({len(batch)} zip codes) ---")
            batch_start = time.time()
            
            batch_results = self._process_batch(batch, process_func, *args)
            all_results.extend(batch_results)
            
            batch_time = time.time() - batch_start
            print(f"Batch {current_batch} completed in {batch_time:.1f}s")
            print(f"Progress: {current_batch}/{total_batches} batches ({current_batch/total_batches*100:.1f}%)")
        
        return all_results
    
    def _process_batch(self, batch: list, process_func, *args) -> list:
        """Process a single batch in parallel."""
        batch_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_item = {
                executor.submit(process_func, item, *args): item 
                for item in batch
            }
            
            for future in as_completed(future_to_item):
                try:
                    result = future.result()
                    if result:
                        batch_results.extend(result)
                except Exception as e:
                    item = future_to_item[future]
                    print(f"Error processing {item}: {e}")
        
        return batch_results