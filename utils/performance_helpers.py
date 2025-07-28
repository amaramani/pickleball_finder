import time
import logging
from functools import wraps
from typing import Optional, Dict, Any

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
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
            return None
        return wrapper
    return decorator

def safe_extract(func, *args, **kwargs) -> Optional[Any]:
    """Safely execute extraction function with error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Extraction failed in {func.__name__}: {e}")
        return None

def validate_url(url: str) -> bool:
    """Validate URL format."""
    return url and url.startswith(('http://', 'https://')) and len(url) > 10

class PerformanceTracker:
    """Track performance metrics."""
    def __init__(self):
        self.start_time = None
        self.metrics = {}
    
    def start(self, operation: str):
        self.start_time = time.time()
        self.metrics[operation] = {'start': self.start_time}
    
    def end(self, operation: str):
        if operation in self.metrics:
            self.metrics[operation]['duration'] = time.time() - self.metrics[operation]['start']
    
    def get_summary(self) -> Dict[str, float]:
        return {op: data.get('duration', 0) for op, data in self.metrics.items()}