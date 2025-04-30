"""Factory for creating security agents."""
from typing import Dict, Any, Optional
from ..utils.quota_manager import AsyncQuotaManager
from ..utils.logger import logger

# Import all agent types
from .virustotal_agent import VirusTotalAgent
from .shodan_agent import ShodanAgent
from .abuseipdb_agent import AbuseIPDBAgent
from .network_security_agent import NetworkSecurityAgent
from .malware_analysis_agent import MalwareAnalysisAgent
from .threat_hunting_agent import ThreatHuntingAgent
from .threat_hunting_react_agent import ThreatHuntingReActAgent

def create_agent(agent_type: str, api_key: str, quota_manager: Optional[AsyncQuotaManager] = None):
    """
    Create a security agent of the specified type.
    
    Args:
        agent_type: Type of agent to create
        api_key: Optional API key for the agent
        quota_manager: Optional quota manager instance
        
    Returns:
        Initialized security agent
        
    Raises:
        ValueError: If agent_type is unknown
    """
    # Map of agent types to their classes
    agent_classes = {
        # API-based agents
        "virustotal": VirusTotalAgent,
        "shodan": ShodanAgent,
        "abuseipdb": AbuseIPDBAgent,
        
        # Specialized analysis agents
        "network": NetworkSecurityAgent,
        "malware": MalwareAnalysisAgent,
        "threat": ThreatHuntingAgent,
        "threat_react": ThreatHuntingReActAgent
    }
    
    # Get the agent class
    agent_class = agent_classes.get(agent_type.lower())
    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    try:
        # Initialize the agent
        agent = agent_class(
            api_key=api_key,
            quota_manager=quota_manager
        )
        
        logger.info(f"Created agent of type: {agent_type}")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create agent of type {agent_type}: {e}")
        raise
