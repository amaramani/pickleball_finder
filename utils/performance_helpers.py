import time
import logging
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry function on failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Function {func.__name__} failed after {max_retries} attempts: {e}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying...")
                    time.sleep(delay * (attempt + 1))
            return None
        return wrapper
    return decorator

def safe_extract(func, *args, **kwargs):
    """Safely execute extraction function with error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Extraction failed in {func.__name__}: {e}")
        return None

def validate_url(url: str) -> bool:
    """Validate URL format."""
    return url and url.startswith(('http://', 'https://')) and len(url) > 10