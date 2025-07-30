"""
Scraped Court Data Model - Data structure for court information
"""
from dataclasses import dataclass
from typing import Optional
import csv
import os


@dataclass
class ScrapedCourtData:
    """Data model for pickleball court information."""
    
    name: Optional[str] = None
    address: Optional[str] = None
    courtlink: Optional[str] = None
    
    @classmethod
    def from_scraped_data(cls, court_name: str, anchor_links: list, court_url: str):
        """Create court data from scraped information."""
        address = anchor_links[0]['text'] if anchor_links else None
        
        return cls(
            name=court_name,
            address=address,
            courtlink=court_url
        )
    
    def to_csv_row(self) -> list:
        """Convert to CSV row format."""
        return [
            self.name or '',
            self.address or '',
            self.courtlink or ''
        ]
    
    @staticmethod
    def save_to_csv(courts: list, filename: str = 'pickleball_courts.csv'):
        """Save list of courts to CSV file."""
        try:
            os.makedirs('data', exist_ok=True)
            filepath = os.path.join('data', filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Name', 'Address', 'Courtlink'])
                
                for court in courts:
                    writer.writerow(court.to_csv_row())
            
            print(f"✓ Saved {len(courts)} courts to {filepath}")
        except (OSError, IOError, PermissionError) as e:
            print(f"❌ Error saving CSV file: {e}")
            raise
    
    @staticmethod
    def append_to_csv(courts: list, filename: str = 'pickleball_courts.csv'):
        """Append courts to existing CSV file."""
        if not courts:
            return
            
        try:
            os.makedirs('data', exist_ok=True)
            filepath = os.path.join('data', filename)
            
            file_exists = os.path.exists(filepath)
            
            with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                if not file_exists:
                    writer.writerow(['Name', 'Address', 'Courtlink'])
                
                for court in courts:
                    writer.writerow(court.to_csv_row())
            
            print(f"✓ Appended {len(courts)} courts to {filepath}")
        except (OSError, IOError, PermissionError) as e:
            print(f"❌ Error appending to CSV file: {e}")
            raise
    
    def __str__(self) -> str:
        return f"Court(name='{self.name}', address='{self.address}')"