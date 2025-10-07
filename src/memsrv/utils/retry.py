"""Contains code for retry logic"""
import time
import asyncio
import functools
from memsrv.utils.logger import get_logger

logger = get_logger(__name__)

def retry_with_backoff(max_retries: int = 5, base_delay: float = 0.5, max_delay: float = 8.0):
    """
    Decorator for retrying a function with exponential backoff.

    Args:
        max_retries: Maximum number of retries.
        base_delay: Initial delay in seconds.
        max_delay: Max delay between retries.

    Usage:
        @retry_with_backoff()
        async def call_external_service():
            ...
    """
    def decorator(func):
        # for now writing only for async functions
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            delay = base_delay
            
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt > max_retries:
                        logger.error(f"Max retries exceeded for {func.__name__}")
                        raise
                    sleep_time = min(delay, max_delay)

                    logger.warning(f"{func.__name__} failed on attempt {attempt}, retrying in {sleep_time:.2f}s. Error: {e}")
                    await asyncio.sleep(sleep_time)
                    delay *= 2  # exp increase, backoff = 2
        return wrapper
    return decorator

def rate_limited(calls_per_second: float):
    """Rate limit the number of calls per second and wait if exceeds"""
    min_interval = 1.0 / calls_per_second
    last_call = {"time": 0.0}

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time.monotonic() - last_call["time"]
            wait_time = min_interval - elapsed
            if wait_time > 0:
                logger.warning(f"Rate limit exceeded for {func.__name__}, slowing down.")
                await asyncio.sleep(wait_time)
            last_call["time"] = time.monotonic()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3, base_delay=1)
@rate_limited(calls_per_second=2)  # 120 calls per min
async def foo():
    # Original function
    pass