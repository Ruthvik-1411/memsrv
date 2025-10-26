"""Contains code for retry logic"""
import random
import asyncio
import functools
from memsrv.utils.logger import get_logger

logger = get_logger(__name__)

def retry_with_backoff(max_retries: int = 5,
                       backoff_factor: int = 2,
                       base_delay: float = 0.5,
                       max_delay: float = 8.0,
                       retry_on_exceptions: tuple = (Exception,)):
    """
    Decorator for retrying a function with exponential backoff.
    If any exceptions are provided, when raised, they will be retried.
    If not provided, all exceptions will be retried.

    Args:
        max_retries: Maximum number of retries.
        backoff_factor: The exponential increase value.
        base_delay: Initial delay in seconds.
        max_delay: Max delay between retries.
        retry_on_exceptions: Exceptions to retry, can be customized like aiohttp.ClientError..

    Usage:
        @retry_with_backoff(args)
        async def call_external_service_func():
            ...
    """
    def decorator(func):
        # for now writing only for async functions
        @functools.wraps(func)
        async def _wrapper(*args, **kwargs):
            attempt = 0
            delay = base_delay
            
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_on_exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"[Retry]: Max retries exceeded for {func.__name__}",
                                     exc_info=True)
                        raise
                    sleep_time = min(delay, max_delay)
                    # We are using jitter so that concurrent tasks will not retry at same time
                    # We can not use this, but for distributed components, this helps
                    sleep_time = sleep_time * (0.5 + random.random() / 2)  

                    logger.warning(
                        f"[Retry]: {func.__name__} failed on attempt {attempt},"
                        f" retrying in {sleep_time:.2f}s. Error: {e}"
                    )
                    await asyncio.sleep(sleep_time)
                    delay *= backoff_factor  # exp increase, default is 2
        return _wrapper
    return decorator

def rate_limited(calls_per_second: float):
    """
    Decorator to limit async function call rate.

    Ensures that the decorated async function is not called
    more than `calls_per_second` times per second.
    
    Args:
        calls_per_second: Maximum number of allowed calls per second.
    
    Usage:
        @rate_limited(2.0)  # 2 calls per second (120 per minute)
        async def call_external_service_func(...):
            ...
    """
    min_interval = 1.0 / calls_per_second
    last_call = {"time": 0.0}
    # protects shared timing state
    lock = asyncio.Lock()

    def decorator(func):
        @functools.wraps(func)
        async def _wrapper(*args, **kwargs):
            loop = asyncio.get_running_loop()
            async with lock:
                now = loop.time()
                elapsed = now - last_call["time"]
                wait_time = min_interval - elapsed
                if wait_time > 0:
                    logger.warning(
                        f"Rate limit exceeded for {func.__name__}, "
                        f"sleeping {wait_time:.3f}s to respect limit."
                    )
                    await asyncio.sleep(wait_time)
                # Make note of the new call time
                last_call["time"] = loop.time()
            # execute the actual function after rate check
            return await func(*args, **kwargs)
        return _wrapper
    return decorator
