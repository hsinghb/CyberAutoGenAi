"""Shodan API integration."""
import os
import logging
from typing import Dict, Any
import shodan
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShodanAPI:
    """Shodan API client."""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('SHODAN_API_KEY')
        self.api = shodan.Shodan(self.api_key) if self.api_key else None

    async def search_host(self, ip: str) -> Dict[str, Any]:
        """Search for host information."""
        try:
            if not self.api:
                return {"error": "Shodan API key not configured"}

            host = self.api.host(ip)
            return self._process_host_info(host)

        except Exception as e:
            logger.error(f"Shodan host search error: {str(e)}")
            return {"error": str(e)}

    async def search_domain(self, domain: str) -> Dict[str, Any]:
        """Search for domain information."""
        try:
            if not self.api:
                return {"error": "Shodan API key not configured"}

            results = self.api.search(f'hostname:{domain}')
            return self._process_search_results(results)

        except Exception as e:
            logger.error(f"Shodan domain search error: {str(e)}")
            return {"error": str(e)}

    def _process_host_info(self, host_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process host information."""
        return {
            "host_info": {
                "ip": host_info.get("ip_str"),
                "ports": host_info.get("ports", []),
                "hostnames": host_info.get("hostnames", []),
                "organization": host_info.get("org", "N/A"),
                "country": host_info.get("country_name", "N/A"),
                "os": host_info.get("os", "N/A"),
                "vulns": host_info.get("vulns", []),
                "services": [
                    {
                        "port": service.get("port"),
                        "protocol": service.get("transport", "unknown"),
                        "product": service.get("product", "unknown"),
                        "version": service.get("version", "unknown")
                    }
                    for service in host_info.get("data", [])
                ]
            }
        }

    def _process_search_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Process search results."""
        return {
            "search_results": {
                "total": results.get("total", 0),
                "matches": [
                    {
                        "ip": match.get("ip_str"),
                        "port": match.get("port"),
                        "org": match.get("org"),
                        "country": match.get("country_name")
                    }
                    for match in results.get("matches", [])
                ]
            }
        } 