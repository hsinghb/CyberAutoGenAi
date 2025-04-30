"""Configuration package for CyberAutoGenAI."""

from .code_execution_config import code_execution_config
from .agent_config import get_openai_config, get_agent_config, get_api_key
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

default_config: Dict[str, Any] = {
    # API Keys
    "VIRUSTOTAL_API_KEY": os.getenv("VIRUSTOTAL_API_KEY"),
    "SHODAN_API_KEY": os.getenv("SHODAN_API_KEY"),
    "ABUSEIPDB_API_KEY": os.getenv("ABUSEIPDB_API_KEY"),
    "THREAT_INTEL_API_KEY": os.getenv("THREAT_INTEL_API_KEY"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    
    # Service Configuration
    "MAX_RETRIES": 3,
    "TIMEOUT": 30,
    "BATCH_SIZE": 100,
    
    # Quota Limits
    "QUOTA_LIMITS": {
        "virustotal": 500,
        "shodan": 100,
        "abuseipdb": 1000,
        "openai": 100
    },
    
    # MCP Configuration
    "MCP_HOST": "localhost",
    "MCP_PORT": 5000,
    
    # Logging Configuration
    "LOG_LEVEL": "INFO",
    "LOG_FILE": "security_analysis.log"
}

__all__ = [
    'default_config',
    'code_execution_config',
    'get_openai_config',
    'get_agent_config',
    'get_api_key'
]
