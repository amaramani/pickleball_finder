import os
from dotenv import load_dotenv


def load_config() -> dict:
    """
    Loads environment variables from the .env file.

    Returns:
        dict: A dictionary containing loaded environment variables.
    """
    load_dotenv()  # Load variables from .env file
    return {
        "Maps_API_KEY": os.getenv("Maps_API_KEY"),
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY")
    }
