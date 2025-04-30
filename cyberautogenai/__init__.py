"""CyberAutoGenAI package."""
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
load_dotenv()

# Version information
__version__ = '0.1.0'

# Import order matters - import independent modules first
from . import utils  # Import utils first as it contains logger
from . import exceptions  # Add exceptions import
from . import config  # Import config before agents
from . import api
from . import mcp

# Import agents last to avoid circular imports
from . import agents
from . import ui

__all__ = [
    'agents',
    'utils',
] 