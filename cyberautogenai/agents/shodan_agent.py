"""Shodan security agent implementation."""
from typing import Dict, Any, Optional, List
import shodan
import ipaddress
import socket
import asyncio
from ..utils.quota_manager import QuotaManager
from ..utils.logger import logger
from .mcp_agent_base import MCPAgentBase
from ..exceptions import APIKeyError, ValidationError, ProcessingError

class ShodanAgent(MCPAgentBase):
    """Agent for Shodan API integration."""
    
    def __init__(self, api_key: str = None):
        """Initialize Shodan agent."""
        super().__init__("shodan_agent")
        self.api_key = api_key
        self.quota_manager = QuotaManager()
        try:
            self.api = shodan.Shodan(api_key) if api_key else None
            logger.info("Shodan agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Shodan API: {e}")
            self.api = None

    async def start(self):
        """Start the agent and connect to MCP."""
        try:
            # Start MCP client
            await super().start()
            logger.info("Shodan agent started and connected to MCP")
        except Exception as e:
            logger.error(f"Failed to start Shodan agent: {e}")
            raise

    async def stop(self):
        """Stop the agent and disconnect from MCP."""
        try:
            await super().stop()
            logger.info("Shodan agent stopped")
        except Exception as e:
            logger.error(f"Error stopping Shodan agent: {e}")
            raise

    async def process_request(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming requests."""
        logger.info(f"Processing Shodan request: {content}")
        
        try:
            # Handle both direct IP and structured requests
            if isinstance(content, dict) and 'ip' in content:
                ip_address = content['ip']
            elif isinstance(content, str):
                ip_address = content
            else:
                raise ValueError("Invalid request format. Expected IP address string or dict with 'ip' key")
                
            result = await self.lookup_ip(ip_address)
            logger.info(f"Shodan lookup completed for {ip_address}")
            return result

        except Exception as e:
            logger.error(f"Error processing Shodan request: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def lookup_ip(self, ip: str) -> Dict[str, Any]:
        """Look up IP information on Shodan."""
        try:
            results = self.api.host(ip)
            return {
                'ip': results.get('ip_str'),
                'ports': results.get('ports', []),
                'hostnames': results.get('hostnames', []),
                'org': results.get('org'),
                'country': results.get('country_name'),
                'vulns': results.get('vulns', [])
            }
        except Exception as e:
            logger.error(f"Shodan IP lookup failed: {str(e)}")
            raise

    async def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data."""
        if not isinstance(data, dict):
            return False
            
        if "type" not in data or "value" not in data:
            return False
            
        valid_types = ["ip", "domain", "hostname", "network"]
        return data["type"].lower() in valid_types

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze target using Shodan. Supports batch input as list or dict.
        """
        value = data.get("value")
        analysis_type = data.get("type", "").lower()

        # Batch: If value is a dict (e.g., {"ips": [...], ...})
        if isinstance(value, dict):
            results = {}
            for key, values in value.items():
                item_type = key[:-1] if key.endswith('s') else key
                if isinstance(values, list):
                    results[key] = {}
                    for v in values:
                        if item_type == "ip":
                            results[key][v] = await self._analyze_ip(v)
                        elif item_type == "domain":
                            results[key][v] = await self._analyze_domain(v)
                        elif item_type == "hostname":
                            results[key][v] = await self._analyze_hostname(v)
                        elif item_type == "network":
                            results[key][v] = await self._analyze_network(v)
                        else:
                            results[key][v] = {"error": f"Unsupported type: {item_type}"}
                else:
                    if item_type == "ip":
                        results[key] = await self._analyze_ip(values)
                    elif item_type == "domain":
                        results[key] = await self._analyze_domain(values)
                    elif item_type == "hostname":
                        results[key] = await self._analyze_hostname(values)
                    elif item_type == "network":
                        results[key] = await self._analyze_network(values)
                    else:
                        results[key] = {"error": f"Unsupported type: {item_type}"}
            return results

        # Batch: If value is a list, process each item
        if isinstance(value, list):
            results = {}
            for v in value:
                if analysis_type == "ip":
                    results[v] = await self._analyze_ip(v)
                elif analysis_type == "domain":
                    results[v] = await self._analyze_domain(v)
                elif analysis_type == "hostname":
                    results[v] = await self._analyze_hostname(v)
                elif analysis_type == "network":
                    results[v] = await self._analyze_network(v)
                else:
                    results[v] = {"error": f"Unsupported type: {analysis_type}"}
            return results

        # Single value logic (call the API)
        if analysis_type == "ip":
            return await self._analyze_ip(value)
        elif analysis_type == "domain":
            return await self._analyze_domain(value)
        elif analysis_type == "hostname":
            return await self._analyze_hostname(value)
        elif analysis_type == "network":
            return await self._analyze_network(value)
        else:
            return {"error": f"Unsupported analysis type: {analysis_type}"}

    async def _analyze_ip(self, ip: str) -> Dict:
        """Analyze an IP address using Shodan."""
        try:
            logger.info(f"Looking up IP {ip} with Shodan")
            
            # Run Shodan lookup in a thread pool since it's synchronous
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.api.host, ip)
            
            logger.info(f"Shodan response received for {ip}")
            return {
                'status': 'success',
                'data': {
                    'ip': result.get('ip_str'),
                    'ports': result.get('ports', []),
                    'hostnames': result.get('hostnames', []),
                    'org': result.get('org'),
                    'country': result.get('country_name'),
                    'vulns': result.get('vulns', []),
                    'last_update': result.get('last_update'),
                    'os': result.get('os'),
                    'tags': result.get('tags', [])
                }
            }

        except shodan.APIError as e:
            logger.error(f"Shodan API error: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Error in Shodan lookup: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def _analyze_domain(self, domain: str) -> Dict:
        """Analyze a domain using Shodan."""
        try:
            # Resolve domain to IP
            try:
                ip = socket.gethostbyname(domain)
            except socket.gaierror:
                raise ValidationError(f"Could not resolve domain: {domain}")
            
            # Get domain information using thread pool
            loop = asyncio.get_event_loop()
            dns_info = await loop.run_in_executor(
                None, self.api.dns.domain_info, domain
            )
            
            # Get host information for resolved IP
            host_info = await self._analyze_ip(ip)
            
            return {
                'domain': domain,
                'resolved_ip': ip,
                'dns_info': dns_info,
                'host_info': host_info
            }
        except Exception as e:
            raise ProcessingError(f"Domain analysis failed: {str(e)}")

    async def _analyze_hostname(self, hostname: str) -> Dict:
        """Analyze a hostname using Shodan."""
        try:
            # Run search in thread pool
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(
                None,
                self.api.search,
                f'hostname:{hostname}'
            )
            
            # Get DNS information
            try:
                dns_info = await loop.run_in_executor(
                    None,
                    self.api.dns.resolve,
                    hostname
                )
            except:
                dns_info = {}
            
            return {
                'hostname': hostname,
                'search_results': search_results,
                'dns_info': dns_info,
                'total_results': search_results.get('total', 0)
            }
        except Exception as e:
            raise ProcessingError(f"Hostname analysis failed: {str(e)}")

    async def _analyze_network(self, network: str) -> Dict:
        """Analyze a network using Shodan."""
        try:
            # Run search in thread pool
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(
                None,
                self.api.search,
                f'net:{network}'
            )
            
            return {
                'network': network,
                'search_results': search_results,
                'total_hosts': search_results.get('total', 0)
            }
        except Exception as e:
            raise ProcessingError(f"Network analysis failed: {str(e)}")

    def _generate_summary(self, results: Dict, analysis_type: str) -> Dict:
        """Generate a summary of the analysis results."""
        summary = {
            'total_services': 0,
            'open_ports': 0,
            'vulnerabilities': 0,
            'last_update': None
        }
        
        if analysis_type == "ip":
            host_info = results.get('data', {})
            summary.update({
                'total_services': len(results.get('ports', [])),
                'open_ports': len(results.get('ports', [])),
                'vulnerabilities': len(results.get('vulns', [])),
                'last_update': host_info.get('last_update')
            })
        elif analysis_type in ["domain", "hostname"]:
            summary.update({
                'total_results': results.get('total_results', 0),
                'resolved_ips': len(results.get('dns_info', {}).get('ips', []))
            })
        elif analysis_type == "network":
            summary.update({
                'total_hosts': results.get('total_hosts', 0)
            })
            
        return summary

    def _extract_details(self, results: Dict, analysis_type: str) -> Dict:
        """Extract detailed information from results."""
        details = {}
        
        if analysis_type == "ip":
            host_info = results.get('data', {})
            details.update({
                'organization': host_info.get('org'),
                'isp': host_info.get('isp'),
                'operating_system': host_info.get('os'),
                'ports': results.get('ports', []),
                'vulnerabilities': results.get('vulns', []),
                'location': {
                    'country': host_info.get('country'),
                    'city': host_info.get('city'),
                    'coordinates': [
                        host_info.get('latitude'),
                        host_info.get('longitude')
                    ]
                }
            })
        elif analysis_type in ["domain", "hostname"]:
            details.update({
                'dns_records': results.get('dns_info', {}),
                'resolved_ips': results.get('dns_info', {}).get('ips', []),
                'search_results': results.get('search_results', {}).get('matches', [])
            })
        elif analysis_type == "network":
            details.update({
                'hosts': results.get('search_results', {}).get('matches', [])
            })
            
        return details 