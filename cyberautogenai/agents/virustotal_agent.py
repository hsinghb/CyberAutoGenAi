"""VirusTotal integration for domain and URL analysis."""
from typing import Dict, Any
import aiohttp
import logging
from .mcp_agent_base import MCPAgentBase

# Debug: Print the file path to ensure correct file is loaded
print("DEBUG: Loaded VirusTotalAgent from:", __file__)

logger = logging.getLogger(__name__)

class VirusTotalAgent(MCPAgentBase):
    """Agent for domain and URL analysis using VirusTotal."""
    
    API_BASE = "https://www.virustotal.com/api/v3"
    
    def __init__(self, api_key: str, agent_id: str = "virustotal_agent", mcp_client=None):
        print("VirusTotalAgent __init__ called with:", api_key, agent_id, mcp_client)  # Debug print
        super().__init__(agent_id=agent_id, mcp_client=mcp_client)
        self.api_key = api_key
        self.base_url = "https://www.virustotal.com/api/v3"
    
    async def analyze(self, request: dict) -> dict:
        value = request.get("value")
        req_type = request.get("type")
        if isinstance(value, list):
            results = {}
            for v in value:
                results[v] = await self.analyze({"type": req_type, "value": v})
            return results
        if req_type == "domain":
            return await self.check_domain(value)
        elif req_type == "url":
            # Try to get the URL report, if not found, submit for scanning
            vt_result = await self.check_url(value)
            # Check for NotFoundError and submit if needed
            if (
                vt_result.get("status") == "error"
                and "NotFoundError" in vt_result.get("error", "")
            ):
                submit_result = await self.submit_url(value)
                if "error" in submit_result:
                    return {
                        "status": "error",
                        "error": f"URL not found in VirusTotal. Submission failed: {submit_result['error']}",
                    }
                # Get the analysis_id from the submission response
                analysis_id = submit_result.get("data", {}).get("id")
                if not analysis_id:
                    return {
                        "status": "error",
                        "error": "URL submitted for analysis, but no analysis ID returned.",
                    }
                # Optionally, you can poll for the result here, but for now just return submission info
                return {
                    "status": "submitted",
                    "message": "URL not found in VirusTotal. Submitted for analysis.",
                    "analysis_id": analysis_id,
                }
            return vt_result
        else:
            return {"status": "error", "error": f"Unsupported type: {req_type}"}

    async def check_domain(self, domain: str) -> dict:
        url = f"{self.base_url}/domains/{domain}"
        headers = {"x-apikey": self.api_key}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {"status": "success", "data": data}
                    else:
                        error = await resp.text()
                        logger.error(f"VirusTotal domain error: {error}")
                        return {"status": "error", "error": error}
        except Exception as e:
            logger.error(f"VirusTotal domain exception: {e}")
            return {"status": "error", "error": str(e)}

    async def check_url(self, url_to_check: str) -> dict:
        url_id = self._url_id(url_to_check)
        url = f"{self.base_url}/urls/{url_id}"
        headers = {"x-apikey": self.api_key}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {"status": "success", "data": data}
                    else:
                        error = await resp.text()
                        logger.error(f"VirusTotal URL error: {error}")
                        return {"status": "error", "error": error}
        except Exception as e:
            logger.error(f"VirusTotal URL exception: {e}")
            return {"status": "error", "error": str(e)}

    def _url_id(self, url: str) -> str:
        import base64
        url_bytes = url.encode("utf-8")
        b64 = base64.urlsafe_b64encode(url_bytes).decode("utf-8")
        return b64.rstrip("=")

    async def handle_message(self, message):
        """
        Handle incoming MCP messages.
        This method is called by the MCP framework.
        """
        content = message.content
        if content.get("type") in ["domain", "url"]:
            result = await self.analyze(content)
            await self.send_response(message, result)
        else:
            await self.send_response(message, {"status": "error", "error": "Unsupported type"})

    async def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data."""
        if not isinstance(data, dict):
            return False
        
        value = data.get("value")
        if not value or not isinstance(value, str):
            return False
            
        # Check if it's a domain or URL
        return self._is_domain(value) or self._is_url(value)

    async def _check_api_access(self):
        """Check if the API access is valid."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "x-apikey": self.api_key,
                    "accept": "application/json"
                }
                
                url = f"{self.API_BASE}/domains/google.com"
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"API access check failed with status {response.status}")
                        
            return True
        except Exception as e:
            logger.error(f"API access check failed: {str(e)}")
            return False

    def _parse_response(self, response: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        """Parse VirusTotal response."""
        try:
            data = response.get("data", {})
            attributes = data.get("attributes", {})
            
            result = {
                "timestamp": self._get_timestamp(),
                "type": endpoint,
                "target": data.get("id", ""),
                "stats": {
                    "harmless": attributes.get("last_analysis_stats", {}).get("harmless", 0),
                    "malicious": attributes.get("last_analysis_stats", {}).get("malicious", 0),
                    "suspicious": attributes.get("last_analysis_stats", {}).get("suspicious", 0),
                    "undetected": attributes.get("last_analysis_stats", {}).get("undetected", 0)
                },
                "reputation": attributes.get("reputation", 0),
                "total_votes": {
                    "harmless": attributes.get("total_votes", {}).get("harmless", 0),
                    "malicious": attributes.get("total_votes", {}).get("malicious", 0)
                }
            }
            
            # Add domain-specific data
            if endpoint == "domains":
                result.update({
                    "registrar": attributes.get("registrar", ""),
                    "creation_date": attributes.get("creation_date", ""),
                    "last_update_date": attributes.get("last_update_date", ""),
                    "last_dns_records_date": attributes.get("last_dns_records_date", ""),
                    "whois": attributes.get("whois", "")
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            raise

    @staticmethod
    def _is_domain(value: str) -> bool:
        """Check if value is a domain."""
        import re
        domain_pattern = r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$'
        return bool(re.match(domain_pattern, value.lower()))

    @staticmethod
    def _is_url(value: str) -> bool:
        """Check if value is a URL."""
        import re
        url_pattern = r'^https?:\/\/'
        return bool(re.match(url_pattern, value.lower()))

    async def submit_url(self, url_to_submit: str) -> dict:
        url = f"{self.base_url}/urls"
        headers = {
            "x-apikey": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = f"url={url_to_submit}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        error = await resp.text()
                        return {"status": "error", "error": error}
        except Exception as e:
            return {"status": "error", "error": str(e)}