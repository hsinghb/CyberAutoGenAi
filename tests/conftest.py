"""Test configuration and fixtures for UI testing."""
import pytest
import os
import sys
from pathlib import Path
import streamlit as st
from typing import Dict, Any, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from cyberautogenai.agents.orchestrator import SecurityOrchestrator
from cyberautogenai.ui.app import init_orchestrator

@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    os.environ.update({
        "OPENAI_API_KEY": "test_openai_key",
        "VIRUSTOTAL_API_KEY": "test_vt_key",
        "SHODAN_API_KEY": "test_shodan_key",
        "ABUSEIPDB_API_KEY": "test_abuseipdb_key",
        "THREAT_INTEL_API_KEY": "test_threat_key"
    })
    yield
    # Clean up
    for key in ["OPENAI_API_KEY", "VIRUSTOTAL_API_KEY", "SHODAN_API_KEY", 
                "ABUSEIPDB_API_KEY", "THREAT_INTEL_API_KEY"]:
        os.environ.pop(key, None)

@pytest.fixture
def mock_session_state():
    """Mock Streamlit session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = None
    return st.session_state

@pytest.fixture
def mock_orchestrator(mock_env_vars):
    """Create a mock orchestrator for testing."""
    config = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "VIRUSTOTAL_API_KEY": os.getenv("VIRUSTOTAL_API_KEY"),
        "SHODAN_API_KEY": os.getenv("SHODAN_API_KEY"),
        "ABUSEIPDB_API_KEY": os.getenv("ABUSEIPDB_API_KEY"),
        "THREAT_INTEL_API_KEY": os.getenv("THREAT_INTEL_API_KEY")
    }
    return SecurityOrchestrator(config=config) 