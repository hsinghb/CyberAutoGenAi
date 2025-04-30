"""Network Security Analysis Agent."""
from typing import Dict, Any, Optional, List
import ipaddress
import socket
import asyncio
import aiohttp
import logging
from ..utils.quota_manager import QuotaManager
from ..utils.logger import logger
from .base_agent import SecurityAgent
from ..exceptions import ValidationError, ProcessingError
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetworkSecurityAgent(SecurityAgent):
    """Network security analysis agent."""
    
    def __init__(self, api_key: str = None, quota_manager: Optional[QuotaManager] = None):
        """Initialize Network Security agent."""
        super().__init__(api_key)
        self.quota_manager = quota_manager or QuotaManager()
        self.supported_types = ["ip", "domain", "url", "network"]

    async def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data."""
        required_fields = ["type", "value"]
        if not all(field in data for field in required_fields):
            return False
        return data["type"].lower() in self.supported_types

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform network security analysis."""
        try:
            if not await self.validate_input(data):
                return {"error": "Invalid input data"}

            target_type = data["type"].lower()
            target_value = data["value"]

            # Extract network indicators
            indicators = await self._extract_network_indicators(target_type, target_value)
            
            # Analyze network security
            analysis_results = await self._analyze_network_security(indicators)
            
            return {
                "network_security": {
                    "indicators": indicators,
                    "analysis": analysis_results,
                    "risk_assessment": await self._assess_risk(analysis_results)
                }
            }

        except Exception as e:
            logger.error(f"Network security analysis failed: {str(e)}")
            return {"error": f"Analysis failed: {str(e)}"}

    async def _extract_network_indicators(self, target_type: str, target_value: str) -> Dict[str, Any]:
        """Extract network security indicators."""
        indicators = {
            "ip_addresses": [],
            "domains": [],
            "urls": [],
            "ports": [],
            "protocols": []
        }

        try:
            if target_type == "ip":
                # Validate and add IP
                ipaddress.ip_address(target_value)
                indicators["ip_addresses"].append(target_value)
            
            elif target_type == "domain":
                indicators["domains"].append(target_value)
            
            elif target_type == "url":
                indicators["urls"].append(target_value)
                # Extract domain from URL if possible
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(target_value)
                    if parsed.netloc:
                        indicators["domains"].append(parsed.netloc)
                except Exception:
                    pass

            elif target_type == "network":
                # Validate and add network
                network = ipaddress.ip_network(target_value, strict=False)
                indicators["ip_addresses"].extend([str(ip) for ip in network.hosts()][:10])

        except Exception as e:
            logger.error(f"Error extracting indicators: {str(e)}")

        return indicators

    async def _analyze_network_security(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network security based on indicators."""
        analysis = {
            "exposure_analysis": {
                "exposed_services": [],
                "potential_vulnerabilities": [],
                "security_recommendations": []
            },
            "threat_indicators": {
                "suspicious_patterns": [],
                "known_threats": [],
                "risk_factors": []
            },
            "security_posture": {
                "strengths": [],
                "weaknesses": [],
                "recommendations": []
            }
        }

        # Analyze IP addresses
        if indicators.get("ip_addresses"):
            analysis["exposure_analysis"]["exposed_services"].append(
                "IP address exposure analysis completed"
            )
            analysis["security_posture"]["recommendations"].append(
                "Implement IP-based access controls"
            )

        # Analyze domains
        if indicators.get("domains"):
            analysis["exposure_analysis"]["security_recommendations"].append(
                "Implement DNS security measures"
            )
            analysis["security_posture"]["recommendations"].append(
                "Monitor domain reputation regularly"
            )

        # Analyze URLs
        if indicators.get("urls"):
            analysis["threat_indicators"]["suspicious_patterns"].append(
                "URL pattern analysis completed"
            )
            analysis["security_posture"]["recommendations"].append(
                "Implement URL filtering and monitoring"
            )

        return analysis

    async def _assess_risk(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall risk level based on analysis results."""
        risk_assessment = {
            "risk_level": "low",
            "confidence": 0.0,
            "factors": [],
            "recommendations": []
        }

        # Count security issues
        issues_count = len(analysis_results.get("threat_indicators", {}).get("known_threats", []))
        vulnerabilities_count = len(analysis_results.get("exposure_analysis", {}).get("potential_vulnerabilities", []))

        # Determine risk level
        if issues_count > 5 or vulnerabilities_count > 3:
            risk_assessment["risk_level"] = "high"
            risk_assessment["confidence"] = 0.8
        elif issues_count > 2 or vulnerabilities_count > 1:
            risk_assessment["risk_level"] = "medium"
            risk_assessment["confidence"] = 0.6
        else:
            risk_assessment["risk_level"] = "low"
            risk_assessment["confidence"] = 0.7

        # Add risk factors
        risk_assessment["factors"] = [
            "Number of known threats: " + str(issues_count),
            "Number of potential vulnerabilities: " + str(vulnerabilities_count)
        ]

        # Add recommendations from analysis
        risk_assessment["recommendations"].extend(
            analysis_results.get("security_posture", {}).get("recommendations", [])
        )

        return risk_assessment

    async def _perform_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform network security analysis on the provided data.
        
        Args:
            data: Dictionary containing data to analyze. Expected keys:
                - 'type': str - Type of data ('ip', 'domain', 'url', 'network')
                - 'value': str - The actual value to analyze
                
        Returns:
            Dict containing analysis results with the following structure:
            {
                'risk_level': str,
                'findings': List[Dict],
                'recommendations': List[str],
                'network_info': Dict,
                'timestamp': str
            }
        """
        try:
            # Validate input data
            if not isinstance(data, dict) or 'type' not in data or 'value' not in data:
                raise ValidationError("Invalid input data format")

            data_type = data['type'].lower()
            value = data['value']

            # Initialize results structure
            results = {
                'risk_level': 'unknown',
                'findings': [],
                'recommendations': [],
                'network_info': {},
                'timestamp': self._get_timestamp()
            }

            # Perform analysis based on data type
            if data_type == 'ip':
                results.update(await self._analyze_ip(value))
            elif data_type == 'domain':
                results.update(await self._analyze_domain(value))
            elif data_type == 'url':
                results.update(await self._analyze_url(value))
            elif data_type == 'network':
                results.update(await self._analyze_network(value))
            else:
                raise ValidationError(f"Unsupported data type: {data_type}")

            # Calculate overall risk level based on findings
            results['risk_level'] = self._calculate_risk_level(results['findings'])
            
            return results

        except ValidationError as e:
            logger.error(f"Validation error in network security analysis: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error performing network security analysis: {str(e)}")
            raise ProcessingError(f"Network security analysis failed: {str(e)}")

    async def _analyze_ip(self, ip: str) -> Dict[str, Any]:
        """Analyze an IP address."""
        try:
            # Validate IP address
            ipaddress.ip_address(ip)
            
            findings = []
            recommendations = []
            network_info = {'ip': ip}

            # Basic network checks
            try:
                hostname = socket.gethostbyaddr(ip)[0]
                network_info['hostname'] = hostname
            except socket.herror:
                network_info['hostname'] = 'Not available'
                
            # Check if IP is private
            if ipaddress.ip_address(ip).is_private:
                findings.append({
                    'severity': 'info',
                    'description': 'IP address is in private range'
                })
                recommendations.append('Ensure private IP is not exposed to internet')

            return {
                'findings': findings,
                'recommendations': recommendations,
                'network_info': network_info
            }

        except ValueError:
            raise ValidationError(f"Invalid IP address: {ip}")

    async def _analyze_domain(self, domain: str) -> Dict[str, Any]:
        """Analyze a domain name."""
        try:
            findings = []
            recommendations = []
            network_info = {'domain': domain}

            # Basic DNS resolution
            try:
                ip_addresses = socket.gethostbyname_ex(domain)[2]
                network_info['ip_addresses'] = ip_addresses
                
                if len(ip_addresses) > 1:
                    findings.append({
                        'severity': 'info',
                        'description': f'Multiple IP addresses found: {len(ip_addresses)}'
                    })
            except socket.gaierror:
                findings.append({
                    'severity': 'warning',
                    'description': 'Domain resolution failed'
                })
                recommendations.append('Verify domain name is correct and accessible')

            return {
                'findings': findings,
                'recommendations': recommendations,
                'network_info': network_info
            }

        except Exception as e:
            raise ProcessingError(f"Domain analysis failed: {str(e)}")

    async def _analyze_url(self, url: str) -> Dict[str, Any]:
        """Analyze a URL."""
        try:
            findings = []
            recommendations = []
            network_info = {'url': url}

            # Basic URL validation and analysis
            if not url.startswith(('http://', 'https://')):
                findings.append({
                    'severity': 'warning',
                    'description': 'URL does not specify protocol'
                })
                recommendations.append('Use HTTPS protocol for secure communication')

            if 'http://' in url:
                findings.append({
                    'severity': 'high',
                    'description': 'Insecure HTTP protocol in use'
                })
                recommendations.append('Switch to HTTPS protocol')

            return {
                'findings': findings,
                'recommendations': recommendations,
                'network_info': network_info
            }

        except Exception as e:
            raise ProcessingError(f"URL analysis failed: {str(e)}")

    async def _analyze_network(self, network: str) -> Dict[str, Any]:
        """Analyze a network range."""
        try:
            # Validate network range
            network_obj = ipaddress.ip_network(network)
            
            findings = []
            recommendations = []
            network_info = {
                'network': str(network_obj),
                'total_hosts': network_obj.num_addresses,
                'network_address': str(network_obj.network_address),
                'broadcast_address': str(network_obj.broadcast_address)
            }

            # Basic network analysis
            if network_obj.is_private:
                findings.append({
                    'severity': 'info',
                    'description': 'Network range is private'
                })
                recommendations.append('Ensure private network is properly segmented')

            if network_obj.num_addresses > 256:
                findings.append({
                    'severity': 'warning',
                    'description': 'Large network range detected'
                })
                recommendations.append('Consider subdividing network for better management')

            return {
                'findings': findings,
                'recommendations': recommendations,
                'network_info': network_info
            }

        except ValueError:
            raise ValidationError(f"Invalid network range: {network}")

    def _calculate_risk_level(self, findings: List[Dict]) -> str:
        """Calculate overall risk level based on findings."""
        severity_scores = {
            'critical': 4,
            'high': 3,
            'warning': 2,
            'info': 1
        }
        
        max_severity = 0
        for finding in findings:
            severity = finding.get('severity', 'info').lower()
            score = severity_scores.get(severity, 0)
            max_severity = max(max_severity, score)
        
        risk_levels = {
            4: 'critical',
            3: 'high',
            2: 'medium',
            1: 'low',
            0: 'info'
        }
        
        return risk_levels[max_severity]

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat() 