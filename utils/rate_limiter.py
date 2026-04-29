import time
import asyncio
from utils.logger import get_logger

logger = get_logger(__name__)

class RateLimiter:
    """Limits API call rate to stay within free tier limits (e.g., 30 RPM for Groq)."""
    def __init__(self, min_interval: float = 0.7):
        self.min_interval = min_interval  # seconds between calls
        self.last_call = 0.0

    def wait_sync(self):
        """Block until enough time has passed since last call."""
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            logger.debug(f"Rate limiter: waiting {wait_time:.2f}s")
            time.sleep(wait_time)
        self.last_call = time.time()

    async def wait_async(self):
        """Async version for use with asyncio."""
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            logger.debug(f"Rate limiter: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        self.last_call = time.time()
