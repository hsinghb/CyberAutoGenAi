"""Type definitions for Model Context Protocol."""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

class ContextType(Enum):
    """Types of context that can be managed."""
    SECURITY_ANALYSIS = "security_analysis"
    THREAT_DETECTION = "threat_detection"
    VULNERABILITY_ASSESSMENT = "vulnerability_assessment"
    INCIDENT_RESPONSE = "incident_response"
    API_INTERACTION = "api_interaction"

@dataclass
class ModelResponse:
    """Structure for model responses."""
    content: str
    confidence: float
    metadata: Dict[str, Any]
    context_type: ContextType
    references: List[str] = None
    
@dataclass
class ContextWindow:
    """Represents a context window for model interactions."""
    max_tokens: int
    content: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    
@dataclass
class SecurityContext:
    """Security-specific context information."""
    target_type: str
    target_value: str
    risk_level: Optional[str] = None
    findings: List[str] = None
    recommendations: List[str] = None 