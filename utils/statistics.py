"""
Statistics tracking for pickleball court scraping
"""
import csv
import os
from typing import Dict, List


class ScrapingStats:
    """Track and save scraping statistics."""
    
    def __init__(self):
        self.zip_stats: Dict[str, Dict] = {}
    
    def add_zip_stats(self, zip_code: str, court_urls_found: int, courts_scraped: int):
        """Add statistics for a zip code."""
        self.zip_stats[zip_code] = {
            'court_urls_found': court_urls_found,
            'courts_scraped': courts_scraped,
            'success_rate': round((courts_scraped / court_urls_found * 100) if court_urls_found > 0 else 0, 1)
        }
    
    def save_stats(self, filename: str = 'scraping_stats.csv'):
        """Save statistics to CSV file."""
        if not self.zip_stats:
            return
            
        try:
            os.makedirs('data', exist_ok=True)
            filepath = os.path.join('data', filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Zip Code', 'URLs Found', 'Courts Scraped', 'Success Rate %'])
                
                for zip_code, stats in self.zip_stats.items():
                    writer.writerow([
                        zip_code,
                        stats['court_urls_found'],
                        stats['courts_scraped'],
                        stats['success_rate']
                    ])
            
            print(f"✓ Saved statistics to {filepath}")
        except (OSError, IOError, PermissionError) as e:
            print(f"❌ Error saving statistics: {e}")
    
    def print_summary(self):
        """Print summary statistics."""
        if not self.zip_stats:
            return
            
        total_urls = sum(stats['court_urls_found'] for stats in self.zip_stats.values())
        total_scraped = sum(stats['courts_scraped'] for stats in self.zip_stats.values())
        overall_rate = round((total_scraped / total_urls * 100) if total_urls > 0 else 0, 1)
        
        print(f"\n📊 SCRAPING SUMMARY:")
        print(f"   Total zip codes processed: {len(self.zip_stats)}")
        print(f"   Total court URLs found: {total_urls}")
        print(f"   Total courts scraped: {total_scraped}")
        print(f"   Overall success rate: {overall_rate}%")