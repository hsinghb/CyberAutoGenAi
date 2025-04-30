"""AbuseIPDB API integration."""
import os
import logging
from typing import Dict, Any
import aiohttp
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AbuseIPDBAPI:
    """AbuseIPDB API client."""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('ABUSEIPDB_API_KEY')
        self.base_url = "https://api.abuseipdb.com/api/v2"

    async def check_ip(self, ip: str) -> Dict[str, Any]:
        """Check IP address."""
        try:
            if not self.api_key:
                return {"error": "AbuseIPDB API key not configured"}

            headers = {
                "Accept": "application/json",
                "Key": self.api_key
            }
            
            params = {
                "ipAddress": ip,
                "maxAgeInDays": 90,
                "verbose": True
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/check",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_check_results(data)
                    return {"error": f"API request failed: {response.status}"}

        except Exception as e:
            logger.error(f"AbuseIPDB check error: {str(e)}")
            return {"error": str(e)}

    def _process_check_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process check results."""
        try:
            return {
                "check_results": {
                    "ip": data.get("ipAddress"),
                    "abuse_confidence_score": data.get("abuseConfidenceScore"),
                    "country_code": data.get("countryCode"),
                    "usage_type": data.get("usageType"),
                    "isp": data.get("isp"),
                    "domain": data.get("domain"),
                    "total_reports": data.get("totalReports"),
                    "num_distinct_users": data.get("numDistinctUsers"),
                    "last_reported_date": data.get("lastReportedDate"),
                    "reports": data.get("reports", [])
                },
                "metadata": {
                    "type": data.get("data", {}).get("type"),
                    "id": data.get("data", {}).get("id"),
                    "first_seen": data.get("data", {}).get("attributes", {}).get("firstSeen"),
                    "last_seen": data.get("data", {}).get("attributes", {}).get("lastSeen"),
                    "reputation": data.get("data", {}).get("attributes", {}).get("reputation", 0),
                    "tags": data.get("data", {}).get("attributes", {}).get("tags", [])
                }
            }

        except Exception as e:
            logger.error(f"Error processing check results: {str(e)}")
            return {"error": "Failed to process check results"} 