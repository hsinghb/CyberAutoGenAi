"""OpenAI client wrapper with rate limiting."""
import time
import logging
import asyncio
from typing import Optional, Dict, Any, List
import copy
import openai
from openai import AsyncOpenAI
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimitedOpenAI:
    """OpenAI client with rate limiting and retry logic."""
    
    def __init__(
        self,
        api_key: str,
        max_retries: int = 5,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
        rate_limit_reset: int = 60
    ):
        self.api_key = api_key
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay
        self.rate_limit_reset = rate_limit_reset
        self.last_request_time = datetime.now()
        self.requests_remaining = None
        self.client = AsyncOpenAI(api_key=api_key)

    def __deepcopy__(self, memo):
        """Implement deepcopy support."""
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        
        for k, v in self.__dict__.items():
            if k == 'client':
                # Create a new client instance
                setattr(result, k, AsyncOpenAI(api_key=self.api_key))
            else:
                setattr(result, k, copy.deepcopy(v, memo))
        return result

    async def _wait_for_rate_limit(self, retry_after: Optional[float] = None):
        """Wait for rate limit to reset."""
        if retry_after is not None:
            wait_time = float(retry_after)
        else:
            wait_time = self.rate_limit_reset
            
        logger.info(f"Rate limit hit. Waiting {wait_time} seconds...")
        await asyncio.sleep(wait_time)

    async def chat_completions_create(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-4",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a chat completion with retry logic."""
        retries = 0
        last_error = None
        
        while retries <= self.max_retries:
            try:
                # Add delay between requests if we're close to rate limit
                if self.requests_remaining is not None and self.requests_remaining < 5:
                    await asyncio.sleep(1.0)
                
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    **kwargs
                )
                
                # Update rate limit info from headers if available
                self.requests_remaining = int(getattr(response, 'headers', {}).get('x-ratelimit-remaining', -1))
                self.last_request_time = datetime.now()
                
                return response
                
            except openai.RateLimitError as e:
                retries += 1
                last_error = e
                
                if retries > self.max_retries:
                    logger.error(f"Max retries ({self.max_retries}) exceeded")
                    raise
                
                # Get retry time from response headers or use exponential backoff
                retry_after = getattr(e, 'response', {}).get('headers', {}).get('retry-after')
                if retry_after:
                    await self._wait_for_rate_limit(float(retry_after))
                else:
                    delay = min(
                        self.initial_retry_delay * (2 ** (retries - 1)),
                        self.max_retry_delay
                    )
                    await self._wait_for_rate_limit(delay)
                    
            except Exception as e:
                logger.error(f"Error in chat completion: {str(e)}")
                raise
                
        raise last_error or Exception("Max retries exceeded") 