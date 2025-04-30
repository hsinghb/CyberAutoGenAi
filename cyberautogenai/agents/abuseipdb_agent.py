"""AbuseIPDB agent implementation."""
from typing import Dict, Any, Optional, Union
import ipaddress
from datetime import datetime
import aiohttp
from ..utils.quota_manager import QuotaManager
from ..utils.logger import logger
from ..exceptions import ValidationError, ProcessingError
from .mcp_agent_base import MCPAgentBase
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

class AbuseIPDBAgent(MCPAgentBase):
    """Agent for AbuseIPDB API integration."""
    
    def __init__(self, api_key: str):
        """Initialize AbuseIPDB agent."""
        super().__init__("abuseipdb_agent")
        self.api_key = api_key
        self.quota_manager = QuotaManager()
        self.base_url = "https://api.abuseipdb.com/api/v2"
        self.headers = {
            'Key': api_key,
            'Accept': 'application/json'
        }
        logger.info("AbuseIPDB agent initialized")

    def _sanitize_value(self, value: Any) -> Union[str, int, float]:
        """Convert values to appropriate types for the API."""
        if isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return value
        elif isinstance(value, list):
            return ','.join(str(item) for item in value)
        elif isinstance(value, datetime):
            return value.isoformat()
        elif value is None:
            return ''
        return str(value)

    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Union[str, int, float]]:
        """Sanitize request parameters."""
        return {
            key: self._sanitize_value(value)
            for key, value in params.items()
        }

    async def start(self):
        """Start the agent and connect to MCP."""
        try:
            # Start MCP client
            await super().start()
            logger.info("AbuseIPDB agent started and connected to MCP")
        except Exception as e:
            logger.error(f"Failed to start AbuseIPDB agent: {e}")
            raise

    async def stop(self):
        """Stop the agent and disconnect from MCP."""
        try:
            await super().stop()
            logger.info("AbuseIPDB agent stopped")
        except Exception as e:
            logger.error(f"Error stopping AbuseIPDB agent: {e}")
            raise

    async def process_request(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming requests."""
        logger.info(f"Processing AbuseIPDB request: {content}")
        
        try:
            # Handle both direct IP and structured requests
            if isinstance(content, dict) and 'ip' in content:
                ip_address = content['ip']
            elif isinstance(content, str):
                ip_address = content
            else:
                raise ValueError("Invalid request format. Expected IP address string or dict with 'ip' key")
                
            return await self.check_ip(ip_address)

        except Exception as e:
            logger.error(f"Error processing AbuseIPDB request: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def _convert_bools(self, obj: Any) -> Any:
        """Convert boolean values to strings in a nested structure."""
        if isinstance(obj, bool):
            return "true" if obj else "false"
        elif isinstance(obj, dict):
            return {k: self._convert_bools(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_bools(item) for item in obj]
        return obj

    def _safe_str(self, value: Any) -> str:
        """Convert any value to a string safely."""
        if isinstance(value, bool):
            return str(value).lower()
        if value is None:
            return ""
        return str(value)

    def _safe_int(self, value: Any) -> int:
        """Convert any value to an integer safely."""
        try:
            return int(value) if value is not None else 0
        except (ValueError, TypeError):
            return 0

    def _bool_to_string(self, obj: Any) -> Any:
        """Convert boolean values to strings in a JSON object."""
        if isinstance(obj, bool):
            return str(obj).lower()
        elif isinstance(obj, dict):
            return {k: self._bool_to_string(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._bool_to_string(item) for item in obj]
        return obj

    def _format_value(self, key: str, value: Any) -> str:
        """Convert any value to a human-readable string format."""
        if value is None:
            return "Not available"
        
        # Boolean conversions
        if isinstance(value, bool):
            if key == "isPublic":
                return "Public IP" if value else "Private IP"
            if key == "isWhitelisted":
                return "Whitelisted" if value else "Not whitelisted"
            return "Yes" if value else "No"
        
        # Handle empty values
        if value == "":
            return "Not available"
        
        # Format dates
        if key == "lastReportedAt" and value:
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except:
                return str(value)
        
        # Format numbers
        if isinstance(value, (int, float)):
            if key == "abuseConfidenceScore":
                return f"{value}%"
            if key == "totalReports":
                return str(value)
        
        # Lists to comma-separated string
        if isinstance(value, list):
            return ", ".join(map(str, value)) if value else "None"
        
        return str(value)

    async def check_ip(self, ip: str) -> Dict[str, Any]:
        """Check IP address against AbuseIPDB."""
        # Validate IP before making the API call
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            logger.error(f"Invalid IP address: {ip}")
            return {
                'status': 'error',
                'error': f"Invalid IP address: {ip}"
            }

        url = f"{self.base_url}/check"
        params = {
            'ipAddress': ip,
            'maxAgeInDays': '90',  # Convert to string
            'verbose': '1'  # Use '1' instead of True
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    logger.debug(f"AbuseIPDB API response status: {response.status}")
                    
                    if response.status == 200:
                        json_response = await response.json()
                        logger.debug(f"AbuseIPDB API raw response: {json_response}")
                        
                        data = json_response.get('data', {})
                        
                        # Ensure all values are properly sanitized and converted to strings
                        sanitized_data = {
                            'abuseConfidenceScore': str(data.get('abuseConfidenceScore', '0')),
                            'countryCode': str(data.get('countryCode', '')),
                            'countryName': str(data.get('countryName', '')),
                            'domain': str(data.get('domain', '')),
                            'hostnames': [str(h) for h in data.get('hostnames', [])],
                            'ipAddress': str(data.get('ipAddress', '')),
                            'isPublic': '1' if data.get('isPublic') else '0',
                            'isWhitelisted': '1' if data.get('isWhitelisted') else '0',
                            'isp': str(data.get('isp', '')),
                            'lastReportedAt': str(data.get('lastReportedAt', '')),
                            'totalReports': str(data.get('totalReports', '0')),
                            'usageType': str(data.get('usageType', '')),
                            'ipVersion': str(data.get('ipVersion', ''))
                        }
                        
                        logger.info(f"AbuseIPDB check successful for IP: {ip}")
                        logger.debug(f"Sanitized data: {sanitized_data}")
                        
                        return {
                            'status': 'success',
                            'data': sanitized_data
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"AbuseIPDB API error: {response.status} - {error_text}")
                        return {
                            'status': 'error',
                            'error': f"API error: {response.status} - {error_text}"
                        }
                        
        except Exception as e:
            logger.error(f"AbuseIPDB request failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': f"Request failed: {str(e)}"
            }

    async def analyze(self, request: dict) -> dict:
        """
        Analyze a single value or batch of values for AbuseIPDB.
        Supports both single IP and list of IPs.
        """
        value = request.get("value")
        req_type = request.get("type")

        # Batch: If value is a list, process each item
        if isinstance(value, list):
            results = {}
            for v in value:
                if req_type == "ip":
                    results[v] = await self.check_ip(v)
                else:
                    results[v] = {"error": f"Unsupported type: {req_type}"}
            return results

        # Batch: If value is a dict with multiple types (e.g., {"ips": [...], ...})
        if isinstance(value, dict):
            results = {}
            for key, values in value.items():
                item_type = key[:-1] if key.endswith('s') else key
                if isinstance(values, list):
                    results[key] = {}
                    for v in values:
                        if item_type == "ip":
                            results[key][v] = await self.check_ip(v)
                        else:
                            results[key][v] = {"error": f"Unsupported type: {item_type}"}
                else:
                    if item_type == "ip":
                        results[key] = await self.check_ip(values)
                    else:
                        results[key] = {"error": f"Unsupported type: {item_type}"}
            return results

        # Single value logic (call the API)
        if req_type == "ip":
            return await self.check_ip(value)
        # Add more types as needed

        return {"error": f"Unsupported type: {req_type}"}

    async def _check_ip(self, ip: str) -> Dict[str, Any]:
        """Check IP using AbuseIPDB API."""
        # Validate IP before making the API call
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            logger.error(f"Invalid IP address: {ip}")
            return {
                'status': 'error',
                'error': f"Invalid IP address: {ip}"
            }

        try:
            logger.info(f"Checking IP {ip} with AbuseIPDB")
            url = f"{self.base_url}/check"
            params = self._sanitize_params({
                'ipAddress': ip,
                'maxAgeInDays': '90',
                'verbose': '1'
            })

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"AbuseIPDB response received for {ip}")
                        return {
                            'status': 'success',
                            'data': data.get('data', {}),
                            'score': data.get('data', {}).get('abuseConfidenceScore', 0),
                            'total_reports': data.get('data', {}).get('totalReports', 0),
                            'last_reported': data.get('data', {}).get('lastReportedAt', None)
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"AbuseIPDB API error: {error_text}")
                        return {
                            'status': 'error',
                            'error': f"API returned status {response.status}",
                            'details': error_text
                        }

        except Exception as e:
            logger.error(f"Error checking IP with AbuseIPDB: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def _get_reports(self, ip: str) -> Dict[str, Any]:
        """Get IP reports from AbuseIPDB API."""
        url = f"{self.base_url}/reports"
        headers = {
            "Key": self.api_key,
            "Accept": "application/json"
        }
        params = {
            "ipAddress": ip
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    raise ProcessingError(f"API request failed: {response.status}")
                return await response.json()

    def _validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data."""
        if not isinstance(data, dict):
            return False
        
        if "type" not in data or "value" not in data:
            return False
            
        if data["type"] != "ip":
            return False
            
        try:
            ipaddress.ip_address(data["value"])
            return True
        except ValueError:
            return False

    async def analyze_batch(self, requests: list[dict]) -> dict:
        """
        Analyze a batch of IPs using AbuseIPDB, processing one at a time (sequentially).
        Each request in the list should be a dict with at least {"type": "ip", "value": "<ip_address>"}.
        Returns a dict mapping each IP to its analysis result.
        """
        results = {}
        for request in requests:
            ip = request.get("value")
            if not ip:
                results[ip] = {"status": "error", "error": "Missing IP value"}
                continue
            result = await self.analyze(request)
            results[ip] = result
        return results 