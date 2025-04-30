"""Specialized Threat Hunting Agent with advanced detection capabilities."""
from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime
import autogen
from ..utils.quota_manager import QuotaManager
from ..utils.logger import logger
from .base_agent import BaseSecurityAgent
from ..api.threat_intel import ThreatIntelAPI
from ..exceptions import ValidationError, ProcessingError
from ..config.agent_config import get_openai_config
from ..config.code_execution_config import code_execution_config

class ThreatHuntingAgent(BaseSecurityAgent):
    """Agent for threat hunting and analysis."""
    
    def __init__(self, api_key: str = None):
        """Initialize threat hunting agent."""
        super().__init__(
            name="threat_hunter",
            expertise="threat hunting and analysis",
            api_key=api_key
        )
        self.threat_intel_api = ThreatIntelAPI()
        self.threat_patterns = self._load_threat_patterns()
        
        # Initialize OpenAI configuration
        self.config_list = get_openai_config()
        
        # Create intelligent assistant for this agent
        self.assistant = autogen.AssistantAgent(
            name="threat_hunting_assistant",
            system_message=self._get_system_message(),
            llm_config={
                "config_list": self.config_list,
                "timeout": 60,
                "cache_seed": None  # Disable caching for real-time analysis
            }
        )
        
        # Create user proxy for analysis
        self.user_proxy = autogen.UserProxyAgent(
            name="threat_hunting_proxy",
            human_input_mode="NEVER",
            code_execution_config=False
        )

    def _get_system_message(self) -> str:
        """Generate specialized system message for threat hunting."""
        return """You are an expert threat hunting analyst. Your capabilities include:
        1. Understanding and interpreting security-related queries
        2. Analyzing behavioral patterns and indicators of compromise
        3. Identifying potential threats and attack patterns
        4. Providing detailed threat assessments
        5. Generating actionable security recommendations
        
        Focus on identifying:
        - Command & Control patterns
        - Data exfiltration indicators
        - Lateral movement signs
        - Privilege escalation attempts
        - Persistence mechanisms
        """

    def _load_threat_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load threat patterns from configuration."""
        return {
            "ip": [
                {
                    "pattern": "0.0.0.0",
                    "description": "Invalid IP address",
                    "severity": "medium"
                }
            ],
            "domain": [
                {
                    "pattern": ".temp.",
                    "description": "Temporary domain",
                    "severity": "low"
                }
            ],
            "url": [
                {
                    "pattern": "http://",
                    "description": "Insecure protocol",
                    "severity": "medium"
                }
            ]
        }

    async def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data."""
        if not isinstance(data, dict):
            return False
        
        required_fields = ["type", "value"]
        if not all(field in data for field in required_fields):
            return False
            
        valid_types = ["ip", "domain", "url", "behavior"]
        if data["type"] not in valid_types:
            return False
            
        return True

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the provided data."""
        try:
            if not await self.validate_input(data):
                raise ValueError("Invalid input data")

            # Perform analysis
            result = await self._perform_analysis(data)
            
            return {
                "status": "success",
                "timestamp": self._get_timestamp(),
                "type": data["type"],
                "value": data["value"],
                "analysis": result
            }
            
        except Exception as e:
            logger.error(f"Threat hunting analysis failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _check_known_threats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for known threats."""
        try:
            value = data["value"]
            threat_type = data["type"]
            
            # Prepare prompt for threat analysis
            prompt = f"""
            Analyze this indicator for known threats:
            Type: {threat_type}
            Value: {value}
            
            Consider:
            1. Known malicious patterns
            2. Common attack techniques
            3. Historical threat data
            4. Threat intelligence feeds
            
            Provide:
            1. Threat classification
            2. Confidence level
            3. Associated malicious activities
            4. Potential impact
            """
            
            # Use AutoGen for analysis
            chat_response = await self.user_proxy.a_initiate_chat(
                self.assistant,
                message=prompt
            )
            
            # Extract response
            response = chat_response.messages[-1]["content"] if chat_response.messages else ""
            
            # Parse the response
            return {
                "matches": self._extract_threat_matches(response),
                "confidence": self._calculate_confidence(response),
                "classification": self._extract_classification(response),
                "potential_impact": self._extract_impact(response)
            }
            
        except Exception as e:
            logger.error(f"Error checking known threats: {e}")
            return {
                "matches": [],
                "confidence": 0.0,
                "classification": "unknown",
                "potential_impact": "unknown"
            }

    async def _match_threat_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Match against known threat patterns."""
        try:
            value = data["value"]
            patterns = self.threat_patterns.get(data["type"], [])
            
            matches = []
            for pattern in patterns:
                if pattern["pattern"] in str(value):
                    matches.append({
                        "pattern": pattern["pattern"],
                        "description": pattern["description"],
                        "severity": pattern["severity"]
                    })
            
            return {
                "matches": matches,
                "total_matches": len(matches),
                "highest_severity": max([m["severity"] for m in matches]) if matches else "none"
            }
            
        except Exception as e:
            logger.error(f"Error matching threat patterns: {e}")
            return {
                "matches": [],
                "total_matches": 0,
                "highest_severity": "none"
            }

    async def _gather_threat_intelligence(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Gather threat intelligence."""
        try:
            value = data["value"]
            threat_type = data["type"]
            
            # Prepare prompt for threat intelligence gathering
            prompt = f"""
            Gather threat intelligence for:
            Type: {threat_type}
            Value: {value}
            
            Consider:
            1. Recent threat reports
            2. Known malicious activities
            3. Associated threat actors
            4. Common attack patterns
            
            Provide:
            1. Threat intelligence summary
            2. Risk indicators
            3. Related threats
            4. Recommended actions
            """
            
            # Use AutoGen for analysis
            chat_response = await self.user_proxy.a_initiate_chat(
                self.assistant,
                message=prompt
            )
            
            # Extract response
            response = chat_response.messages[-1]["content"] if chat_response.messages else ""
            
            # Parse the response
            return {
                "summary": self._extract_summary(response),
                "risk_indicators": self._extract_risk_indicators(response),
                "related_threats": self._extract_related_threats(response),
                "recommendations": self._extract_recommendations(response)
            }
            
        except Exception as e:
            logger.error(f"Error gathering threat intelligence: {e}")
            return {
                "summary": "Failed to gather threat intelligence",
                "risk_indicators": [],
                "related_threats": [],
                "recommendations": []
            }

    def _extract_threat_matches(self, response: str) -> List[Dict[str, Any]]:
        """Extract threat matches from response."""
        matches = []
        try:
            if "malicious" in response.lower():
                matches.append({
                    "type": "malicious_indicator",
                    "confidence": 0.8
                })
            if "suspicious" in response.lower():
                matches.append({
                    "type": "suspicious_activity",
                    "confidence": 0.6
                })
        except Exception:
            pass
        return matches

    def _calculate_confidence(self, response: str) -> float:
        """Calculate confidence score from response."""
        try:
            if "high confidence" in response.lower():
                return 0.9
            elif "medium confidence" in response.lower():
                return 0.6
            elif "low confidence" in response.lower():
                return 0.3
            return 0.0
        except Exception:
            return 0.0

    def _extract_classification(self, response: str) -> str:
        """Extract threat classification from response."""
        try:
            if "malware" in response.lower():
                return "malware"
            elif "phishing" in response.lower():
                return "phishing"
            elif "spam" in response.lower():
                return "spam"
            return "unknown"
        except Exception:
            return "unknown"

    def _extract_impact(self, response: str) -> str:
        """Extract potential impact from response."""
        try:
            if "critical" in response.lower():
                return "critical"
            elif "high" in response.lower():
                return "high"
            elif "medium" in response.lower():
                return "medium"
            elif "low" in response.lower():
                return "low"
            return "unknown"
        except Exception:
            return "unknown"

    def _extract_summary(self, response: str) -> str:
        """Extract summary from response."""
        try:
            sentences = response.split('.')
            return sentences[0].strip() if sentences else "No summary available"
        except Exception:
            return "No summary available"

    def _extract_risk_indicators(self, response: str) -> List[str]:
        """Extract risk indicators from response."""
        indicators = []
        try:
            lines = response.split('\n')
            for line in lines:
                if any(word in line.lower() for word in ["risk", "threat", "indicator", "warning"]):
                    indicators.append(line.strip())
        except Exception:
            pass
        return indicators

    def _extract_related_threats(self, response: str) -> List[str]:
        """Extract related threats from response."""
        threats = []
        try:
            lines = response.split('\n')
            for line in lines:
                if any(word in line.lower() for word in ["related", "associated", "similar"]):
                    threats.append(line.strip())
        except Exception:
            pass
        return threats

    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract recommendations from response."""
        recommendations = []
        try:
            lines = response.split('\n')
            for line in lines:
                if any(word in line.lower() for word in ["recommend", "suggest", "should", "must"]):
                    recommendations.append(line.strip())
        except Exception:
            pass
        return recommendations

    async def _perform_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform threat hunting analysis on the provided data.
        
        Args:
            data: Dictionary containing data to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            analysis_type = data["type"]
            value = data["value"]
            
            # Initialize results
            results = {
                "status": "success",
                "type": analysis_type,
                "timestamp": datetime.utcnow().isoformat(),
                "analysis": {}
            }
            
            # Perform appropriate analysis based on type
            if analysis_type == "behavior":
                results["analysis"] = await self._analyze_behavior(data)
            else:
                # For other types, perform threat intelligence gathering
                threat_analysis = await self._analyze_threats(data)
                iocs = await self._identify_iocs(data)
                
                results["analysis"] = {
                    "threat_analysis": threat_analysis,
                    "indicators_of_compromise": iocs
                }
            
            # Generate recommendations
            results["recommendations"] = await self._generate_recommendations(
                results["analysis"],
                self._calculate_risk_level(results["analysis"])
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Threat hunting analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _analyze_threats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze potential threats."""
        analysis = {
            "known_threats": await self._check_known_threats(data),
            "threat_patterns": await self._match_threat_patterns(data),
            "threat_intelligence": await self._gather_threat_intelligence(data)
        }
        return analysis

    async def _identify_iocs(self, data: Dict[str, Any]) -> Dict[str, List]:
        """Identify indicators of compromise."""
        iocs = {
            "ip_addresses": [],
            "domains": [],
            "urls": [],
            "file_hashes": [],
            "patterns": []
        }
        
        # Extract IOCs based on data type
        if data["type"] == "ip":
            iocs["ip_addresses"].append(data["value"])
        elif data["type"] == "domain":
            iocs["domains"].append(data["value"])
        elif data["type"] == "url":
            iocs["urls"].append(data["value"])
        elif data["type"] == "file":
            iocs["file_hashes"].append(data["value"])
            
        return iocs

    async def _analyze_behavior(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze behavioral patterns in threat intelligence data."""
        try:
            # Prepare analysis prompt
            prompt = f"""
            Analyze this security data for potential threats:
            {json.dumps(data, indent=2)}
            
            Consider:
            1. Command & Control patterns
            2. Data exfiltration indicators
            3. Lateral movement signs
            4. Privilege escalation attempts
            5. Persistence mechanisms
            
            Provide a detailed analysis with:
            - Identified patterns
            - Risk assessment
            - Potential impact
            - Recommended actions
            """
            
            # Use the correct method for async chat
            chat_response = await self.user_proxy.a_initiate_chat(
                self.assistant,
                message=prompt
            )
            
            # Extract the response content
            response = chat_response.messages[-1]["content"] if chat_response.messages else ""
            
            # Parse and structure the response
            analysis = {
                "timestamp": datetime.utcnow().isoformat(),
                "patterns_identified": await self._identify_patterns(response),
                "risk_assessment": await self._identify_risk_factors(response),
                "potential_impact": await self._assess_impact(response),
                "recommendations": await self._extract_recommendations(response)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Behavior analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _identify_patterns(self, response: str) -> List[Dict[str, Any]]:
        """Extract identified patterns from the analysis response."""
        patterns = []
        try:
            # Basic pattern extraction
            if "pattern" in response.lower():
                pattern_sections = response.split("pattern")
                for section in pattern_sections[1:]:
                    end = section.find(".")
                    if end != -1:
                        pattern = section[:end].strip()
                        if pattern:
                            patterns.append({
                                "type": "behavioral",
                                "pattern": pattern,
                                "confidence": 0.8
                            })
        except Exception as e:
            logger.error(f"Pattern identification failed: {e}")
        return patterns

    async def _identify_risk_factors(self, response: str) -> Dict[str, Any]:
        """Extract risk factors from the analysis response."""
        risk_factors = {
            "severity": "unknown",
            "confidence": 0.0,
            "factors": []
        }
        
        try:
            # Look for severity indicators
            severity_keywords = {
                "critical": ["critical", "severe", "extreme"],
                "high": ["high", "significant", "major"],
                "medium": ["medium", "moderate", "intermediate"],
                "low": ["low", "minor", "minimal"]
            }
            
            response_lower = response.lower()
            
            # Determine severity
            for severity, keywords in severity_keywords.items():
                if any(keyword in response_lower for keyword in keywords):
                    risk_factors["severity"] = severity
                    break
            
            # Extract risk factors
            risk_sections = response.split("risk")
            for section in risk_sections[1:]:
                end = section.find(".")
                if end != -1:
                    factor = section[:end].strip()
                    if factor:
                        risk_factors["factors"].append(factor)
            
            # Set confidence based on the amount of information
            risk_factors["confidence"] = min(0.9, 0.5 + (len(risk_factors["factors"]) * 0.1))
            
        except Exception as e:
            logger.error(f"Risk factor identification failed: {e}")
        
        return risk_factors

    async def _assess_impact(self, response: str) -> Dict[str, Any]:
        """Assess potential impact from the analysis response."""
        impact = {
            "level": "unknown",
            "areas_affected": [],
            "likelihood": 0.0
        }
        
        try:
            # Look for impact indicators
            impact_keywords = {
                "critical": ["catastrophic", "severe impact", "major breach"],
                "high": ["significant impact", "substantial", "major"],
                "medium": ["moderate impact", "limited", "partial"],
                "low": ["minor impact", "minimal", "negligible"]
            }
            
            response_lower = response.lower()
            
            # Determine impact level
            for level, keywords in impact_keywords.items():
                if any(keyword in response_lower for keyword in keywords):
                    impact["level"] = level
                    break
            
            # Extract affected areas
            if "impact" in response_lower:
                impact_section = response_lower.split("impact")[1].split(".")[0]
                areas = [area.strip() for area in impact_section.split(",")]
                impact["areas_affected"] = [area for area in areas if area]
            
            # Calculate likelihood
            impact["likelihood"] = self._calculate_likelihood(response)
            
        except Exception as e:
            logger.error(f"Impact assessment failed: {e}")
        
        return impact

    def _calculate_likelihood(self, response: str) -> float:
        """Calculate likelihood score from response content."""
        try:
            likelihood_keywords = {
                "certain": 1.0,
                "likely": 0.8,
                "possible": 0.6,
                "unlikely": 0.4,
                "rare": 0.2
            }
            
            response_lower = response.lower()
            
            for keyword, score in likelihood_keywords.items():
                if keyword in response_lower:
                    return score
                    
            return 0.5  # Default to medium likelihood
            
        except Exception as e:
            logger.error(f"Likelihood calculation failed: {e}")
            return 0.0

    async def _generate_threat_report(
        self,
        threat_analysis: Dict[str, Any],
        iocs: Dict[str, List],
        behavior_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive threat report."""
        
        # Calculate threat score
        threat_score = self._calculate_threat_score(
            threat_analysis,
            iocs,
            behavior_analysis
        )
        
        # Determine threat level
        threat_level = self._determine_threat_level(threat_score)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            threat_analysis,
            threat_level
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "threat_score": threat_score,
            "threat_level": threat_level,
            "findings": {
                "threats": threat_analysis,
                "iocs": iocs,
                "behavior": behavior_analysis
            },
            "recommendations": recommendations
        }

    def _calculate_threat_score(
        self,
        threat_analysis: Dict[str, Any],
        iocs: Dict[str, List],
        behavior_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall threat score."""
        score = 0
        
        # Add scoring logic based on findings
        # Score from 0-10
        return min(score, 10)

    def _determine_threat_level(self, threat_score: float) -> str:
        """Determine threat level based on score."""
        if threat_score >= 8:
            return "critical"
        elif threat_score >= 6:
            return "high"
        elif threat_score >= 4:
            return "medium"
        elif threat_score >= 2:
            return "low"
        return "info"

    async def _generate_recommendations(
        self,
        threat_analysis: Dict[str, Any],
        threat_level: str
    ) -> List[str]:
        """Generate security recommendations."""
        recommendations = []
        
        # Add recommendations based on threat level and findings
        if threat_level in ["critical", "high"]:
            recommendations.append("Immediate investigation and response required")
            
        if threat_level in ["medium", "high", "critical"]:
            recommendations.append("Implement additional monitoring and controls")
            
        return recommendations

    def _calculate_risk_level(self, findings: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk level based on correlated findings."""
        risk_factors = {
            "critical": ["remote code execution", "data breach", "backdoor"],
            "high": ["exploit", "malware", "unauthorized access"],
            "medium": ["suspicious activity", "unusual behavior"],
            "low": ["informational", "minor anomaly"]
        }
        
        content = str(findings.get("content", "")).lower()
        max_risk_level = "low"
        
        for level, factors in risk_factors.items():
            if any(factor in content for factor in factors):
                max_risk_level = level
                break
        
        return {
            "level": max_risk_level,
            "score": self._risk_level_to_score(max_risk_level),
            "factors": self._identify_risk_factors(content, risk_factors)
        }

    def _risk_level_to_score(self, level: str) -> float:
        """Convert risk level to numerical score."""
        return {
            "critical": 1.0,
            "high": 0.75,
            "medium": 0.5,
            "low": 0.25
        }.get(level, 0.0) 