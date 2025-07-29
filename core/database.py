from supabase import create_client, Client
from models.scraped_court_data import ScrapedCourtData
from typing import Optional


class SupabaseDB:
    """Supabase database client for pickleball courts."""
    
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)
    
    def save_court_data(self, court_data: ScrapedCourtData) -> Optional[dict]:
        """Save ScrapedCourtData to database."""
        try:
            data = court_data.to_dict(include_image_data=True)
            result = self.client.table('pickleball_courts').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error saving to database: {e}")
            return None
    
    def address_exists(self, address: str) -> bool:
        """Check if address already exists in database."""
        try:
            result = self.client.table('pickleball_courts').select('id').eq('address', address).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error checking address: {e}")
            return False
    
    def get_all_courts(self) -> list:
        """Get all courts from database."""
        try:
            result = self.client.table('pickleball_courts').select('*').execute()
            return result.data
        except Exception as e:
            print(f"Error fetching courts: {e}")
            return []