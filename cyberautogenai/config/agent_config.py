"""Configuration for AI agents."""
import os
from typing import List, Dict, Any
from ..utils.logger import logger

def get_openai_config() -> List[Dict[str, Any]]:
    """
    Get OpenAI configuration for agents.
    
    Returns:
        List of configuration dictionaries for OpenAI
    
    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable is not set")
        raise ValueError("OpenAI API key is required")

    return [{
        "model": "gpt-4",
        "api_key": api_key,
        "temperature": 0.7,
        "max_tokens": 2000,
        "functions": None
    }]

def get_agent_config(agent_type: str) -> Dict[str, Any]:
    """
    Get configuration for specific agent types.
    
    Args:
        agent_type: Type of agent (e.g., 'chat', 'analysis', 'threat')
    
    Returns:
        Configuration dictionary for the agent
    """
    base_config = {
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }
    
    # Agent-specific configurations
    configs = {
        "chat": {
            **base_config,
            "temperature": 0.8,  # Slightly more creative for chat
            "max_tokens": 1000  # Shorter responses for chat
        },
        "analysis": {
            **base_config,
            "temperature": 0.5,  # More focused for analysis
            "max_tokens": 2000  # Longer responses for detailed analysis
        },
        "threat": {
            **base_config,
            "temperature": 0.3,  # More conservative for threat assessment
            "max_tokens": 3000  # Very detailed threat analysis
        }
    }
    
    return configs.get(agent_type, base_config)

def get_api_key(service_name: str) -> str:
    """Get API key for a specific service."""
    config = ConfigValidator.get_config()
    return config['security_apis'].get(service_name.lower()) 