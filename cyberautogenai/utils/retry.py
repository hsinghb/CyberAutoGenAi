"""Retry utilities with exponential backoff for OpenAI API."""
import time
import random
import logging
from functools import wraps
from typing import Type, Tuple, Optional, Callable
import openai
from openai import RateLimitError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def openai_retry(
    max_retries: int = 5,
    min_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
):
    """
    Decorator for handling OpenAI API rate limits with smart retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        min_delay: Minimum delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential calculation
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            
            while True:
                try:
                    return await func(*args, **kwargs)
                    
                except RateLimitError as e:
                    retries += 1
                    
                    # Check if we've exceeded max retries
                    if retries > max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded. "
                            f"Last error: {str(e)}"
                        )
                        raise
                    
                    # Get retry-after time from OpenAI response or calculate backoff
                    try:
                        # Try to get retry-after from error response
                        retry_after = float(e.response.headers.get('retry-after', 0))
                    except (AttributeError, ValueError):
                        # If no retry-after header, use exponential backoff
                        retry_after = min(
                            min_delay * (exponential_base ** (retries - 1)),
                            max_delay
                        )
                    
                    # Add small random jitter (±10% of delay)
                    jitter = random.uniform(-0.1 * retry_after, 0.1 * retry_after)
                    delay = max(min_delay, retry_after + jitter)
                    
                    logger.warning(
                        f"OpenAI rate limit hit. Attempt {retries}/{max_retries}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    # Sleep before retry
                    time.sleep(delay)
                    continue
                    
                except Exception as e:
                    # Don't retry other types of exceptions
                    logger.error(f"Non-rate-limit error occurred: {str(e)}")
                    raise
                    
        return wrapper
    return decorator

def is_rate_limit_error(error: Exception) -> bool:
    """Check if the error is a rate limit error."""
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code == 429
    return False 