"""Configuration for AutoGen code execution."""
from typing import Dict, Any
import os
from dotenv import load_dotenv

def get_code_execution_config() -> Dict[str, Any]:
    """
    Get the code execution configuration.
    Returns a dictionary with the configuration settings.
    """
    load_dotenv()  # Load environment variables from .env file
    
    return {
        "use_docker": False,  # Explicitly disable Docker usage
        "work_dir": "workspace",  # Directory for code execution
        "timeout": 60,  # Timeout in seconds
        "stream_output": True,  # Stream output in real-time
    }

# Create a singleton instance of the config
code_execution_config = get_code_execution_config() 