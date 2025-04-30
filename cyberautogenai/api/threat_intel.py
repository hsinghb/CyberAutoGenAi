"""Threat Intelligence API Integration."""
from typing import Dict, Any, List
import aiohttp
import json

class ThreatIntelAPI:
    """Intelligent Threat Intelligence API integration."""
    
    def __init__(self):
        self.api_endpoints = self._load_api_config()
        self.session = None

    def _load_api_config(self) -> Dict[str, str]:
        """Load API configuration."""
        try:
            with open('config/api_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def query_indicators(
        self,
        indicators: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Query threat intelligence for indicators."""
        await self._ensure_session()
        results = {}
        
        for indicator in indicators:
            indicator_type = indicator.get('type')
            value = indicator.get('value')
            
            if not indicator_type or not value:
                continue
                
            endpoint = self.api_endpoints.get(indicator_type)
            if not endpoint:
                continue
                
            try:
                async with self.session.get(
                    endpoint,
                    params={'query': value}
                ) as response:
                    if response.status == 200:
                        results[value] = await response.json()
                    else:
                        results[value] = {
                            'error': f'API error: {response.status}'
                        }
            except Exception as e:
                results[value] = {'error': str(e)}
        
        return results

    async def close(self):
        """Close the API session."""
        if self.session:
            await self.session.close()
            self.session = None 