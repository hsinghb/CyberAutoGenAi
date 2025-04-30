"""Quota management for API rate limiting."""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import threading
import json
import os
from pathlib import Path
from .logger import logger
from ..exceptions import QuotaExceededException, QuotaExceededError
from collections import defaultdict

class QuotaManager:
    """Manages API quotas and rate limits."""
    
    def __init__(self):
        """Initialize quota manager."""
        self.quotas = {
            "virustotal": {"daily": 500, "minute": 4},
            "abuseipdb": {"daily": 1000, "minute": 60},
            "shodan": {"daily": 100, "minute": 1}
        }
        self.usage = defaultdict(lambda: {"daily": 0, "minute": 0})
        self.last_reset = defaultdict(lambda: {"daily": None, "minute": None})
        self.reset_interval = timedelta(hours=1)
        self.lock = threading.Lock()
        self._load_quota_state()

    def check_quota(self, service: str) -> bool:
        """Check if quota is available for a service."""
        try:
            if service not in self.quotas:
                logger.warning(f"No quota defined for service: {service}")
                return True  # Allow if no quota defined
            
            now = datetime.utcnow()
            
            # Initialize or reset daily counter
            if (not self.last_reset[service]["daily"] or 
                (now - self.last_reset[service]["daily"]).days >= 1):
                self.usage[service]["daily"] = 0
                self.last_reset[service]["daily"] = now
            
            # Initialize or reset minute counter
            if (not self.last_reset[service]["minute"] or 
                (now - self.last_reset[service]["minute"]).seconds >= 60):
                self.usage[service]["minute"] = 0
                self.last_reset[service]["minute"] = now
            
            # Check both daily and minute quotas
            daily_available = self.usage[service]["daily"] < self.quotas[service]["daily"]
            minute_available = self.usage[service]["minute"] < self.quotas[service]["minute"]
            
            return daily_available and minute_available
            
        except Exception as e:
            logger.error(f"Error checking quota for {service}: {e}")
            return False  # Fail safe - deny if error

    def increment_usage(self, service: str) -> None:
        """Increment usage counter for a service."""
        try:
            if service not in self.quotas:
                logger.warning(f"No quota defined for service: {service}")
                return
            
            self.usage[service]["daily"] += 1
            self.usage[service]["minute"] += 1
            
            logger.debug(f"Incremented usage for {service}: daily={self.usage[service]['daily']}, minute={self.usage[service]['minute']}")
            
        except Exception as e:
            logger.error(f"Error incrementing usage for {service}: {e}")

    def get_remaining_quota(self, service: str) -> Dict[str, int]:
        """Get remaining quota for a service."""
        try:
            if service not in self.quotas:
                return {"daily": -1, "minute": -1}  # -1 indicates no quota
            
            daily_remaining = self.quotas[service]["daily"] - self.usage[service]["daily"]
            minute_remaining = self.quotas[service]["minute"] - self.usage[service]["minute"]
            
            return {
                "daily": max(0, daily_remaining),
                "minute": max(0, minute_remaining)
            }
            
        except Exception as e:
            logger.error(f"Error getting remaining quota for {service}: {e}")
            return {"daily": 0, "minute": 0}  # Fail safe - report no quota if error

    def _reset_if_needed(self, service: str):
        """Reset quota if reset interval has passed."""
        now = datetime.utcnow()
        if service not in self.last_reset:
            self.last_reset[service] = now
            self.usage[service] = 0
            return

        if now - self.last_reset[service] >= self.reset_interval:
            self.usage[service] = 0
            self.last_reset[service] = now
            self._save_quota_state()

    def _load_quota_state(self):
        """Load quota state from file."""
        try:
            quota_file = Path('data/quota_state.json')
            if quota_file.exists():
                with open(quota_file, 'r') as f:
                    state = json.load(f)
                    self.quotas = state.get('quotas', self.quotas)
                    self.usage = state.get('usage', self.usage)
                    self.last_reset = {
                        service: datetime.fromisoformat(date) 
                        for service, date in state.get('last_reset', {}).items()
                    }
        except Exception as e:
            logger.error(f"Error loading quota state: {e}")

    def _save_quota_state(self):
        """Save quota state to file."""
        try:
            quota_file = Path('data/quota_state.json')
            quota_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(quota_file, 'w') as f:
                json.dump({
                    'quotas': self.quotas,
                    'usage': self.usage,
                    'last_reset': {
                        service: date.isoformat() 
                        for service, date in self.last_reset.items()
                    }
                }, f)
        except Exception as e:
            logger.error(f"Error saving quota state: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass

class QuotaAwareClient:
    """Base class for API clients with quota awareness."""
    
    def __init__(self, service_name: str, quota_manager: Optional[QuotaManager] = None):
        """
        Initialize quota-aware client.
        
        Args:
            service_name: Name of the service
            quota_manager: Optional quota manager instance
        """
        self.service_name = service_name
        self.quota_manager = quota_manager or QuotaManager()
        
    async def check_quota(self) -> bool:
        """Check if within quota limits."""
        return await self.quota_manager.check_quota(self.service_name)
        
    async def increment_usage(self):
        """Increment usage counter."""
        await self.quota_manager.increment_usage(self.service_name)
        
    async def get_remaining_quota(self) -> Dict[str, int]:
        """Get remaining quota information."""
        return await self.quota_manager.get_remaining_quota(self.service_name)

class AsyncQuotaManager:
    """Async wrapper for QuotaManager."""
    
    def __init__(self, quota_manager: Optional[QuotaManager] = None):
        """Initialize with optional QuotaManager instance."""
        self.quota_manager = quota_manager or QuotaManager()
        
    async def check_quota(self, service: str) -> bool:
        """Async wrapper for check_quota."""
        return self.quota_manager.check_quota(service)
        
    async def increment_usage(self, service: str):
        """Async wrapper for increment_usage."""
        self.quota_manager.increment_usage(service)
        
    async def get_remaining_quota(self, service: str) -> Dict[str, int]:
        """Async wrapper for get_remaining_quota."""
        return self.quota_manager.get_remaining_quota(service)
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass 