from utils.config import load_config
from core.database import SupabaseDB

config = load_config()
db = SupabaseDB(config["SUPABASE_URL"], config["SUPABASE_KEY"])

# Test connection
courts = db.get_all_courts()
print(f"Database connected! Found {len(courts)} existing courts.")