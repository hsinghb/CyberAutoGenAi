import pytest
import asyncio
from cyberautogenai.agents.abuseipdb_agent import AbuseIPDBAgent
from cyberautogenai.agents.orchestrator import SecurityOrchestrator
from cyberautogenai.ui.security_app import SecurityApp
import streamlit as st
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_data_types(data, path=""):
    """Helper function to check data types in response."""
    if isinstance(data, dict):
        for k, v in data.items():
            current_path = f"{path}.{k}" if path else k
            if isinstance(v, bool):
                logger.warning(f"Boolean found at path: {current_path}, value: {v}")
            check_data_types(v, current_path)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            current_path = f"{path}[{i}]"
            if isinstance(v, bool):
                logger.warning(f"Boolean found at path: {current_path}, value: {v}")
            check_data_types(v, current_path)

@pytest.mark.asyncio
async def test_abuseipdb_direct():
    """Test AbuseIPDB agent directly."""
    api_key = os.getenv('ABUSEIPDB_API_KEY')
    if not api_key:
        pytest.skip("ABUSEIPDB_API_KEY not found in environment")
    
    agent = AbuseIPDBAgent(api_key)
    
    try:
        # Test with a known IP
        test_ip = "8.8.8.8"
        response = await agent.check_ip(test_ip)
        
        # Log the response for debugging
        logger.debug(f"AbuseIPDB direct response: {response}")
        
        # Basic response structure checks
        assert response is not None
        assert isinstance(response, dict)
        assert 'status' in response
        assert response['status'] == 'success'
        
        # Verify data structure
        assert 'data' in response
        data = response['data']
        assert isinstance(data, dict)
        
        # Verify no boolean values in response
        def check_no_booleans(value):
            if isinstance(value, dict):
                for k, v in value.items():
                    check_no_booleans(v)
            elif isinstance(value, list):
                for item in value:
                    check_no_booleans(item)
            else:
                assert not isinstance(value, bool), f"Found boolean value: {value}"
        
        check_no_booleans(response)
        
        # Log all values and their types for debugging
        def log_types(d, path=""):
            if isinstance(d, dict):
                for k, v in d.items():
                    current_path = f"{path}.{k}" if path else k
                    logger.debug(f"Path: {current_path}, Type: {type(v)}, Value: {v}")
                    log_types(v, current_path)
            elif isinstance(d, list):
                for i, v in enumerate(d):
                    log_types(v, f"{path}[{i}]")
        
        log_types(response)
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_orchestrator_integration():
    """Test AbuseIPDB through the orchestrator."""
    api_keys = {
        'ABUSEIPDB_API_KEY': os.getenv('ABUSEIPDB_API_KEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'SHODAN_API_KEY': os.getenv('SHODAN_API_KEY')
    }
    
    if not api_keys['ABUSEIPDB_API_KEY']:
        pytest.skip("ABUSEIPDB_API_KEY not found in environment")

    orchestrator = SecurityOrchestrator(api_keys)
    
    try:
        await orchestrator.start()
        
        test_ip = "8.8.8.8"
        response = await orchestrator.analyze_ip(test_ip)
        
        logger.debug(f"Orchestrator response: {response}")
        
        # Check response structure
        assert response is not None
        assert isinstance(response, dict)
        assert 'results' in response
        
        # Check AbuseIPDB results specifically
        results = response['results']
        assert 'abuseipdb' in results
        abuseipdb_result = results['abuseipdb']
        
        # Check for boolean values
        check_data_types(response)
        
        # Verify specific fields in AbuseIPDB response
        if abuseipdb_result.get('status') == 'success':
            data = abuseipdb_result.get('data', {})
            for key, value in data.items():
                if isinstance(value, bool):
                    pytest.fail(f"Boolean value found in AbuseIPDB data for key {key}: {value}")
    
    finally:
        await orchestrator.stop()

def test_security_app_display():
    """Test SecurityApp display functionality."""
    # Initialize session state as Streamlit would
    if 'orchestrator_initialized' not in st.session_state:
        st.session_state.orchestrator_initialized = False
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = []
    
    app = SecurityApp()
    
    # Create a sample response with string values (not booleans)
    test_response = {
        'status': 'success',
        'timestamp': '2024-01-01T00:00:00',
        'target': '8.8.8.8',
        'type': 'ip_analysis',
        'results': {
            'abuseipdb': {
                'status': 'success',
                'data': {
                    'isPublic': 'true',  # String instead of boolean
                    'isWhitelisted': 'false',  # String instead of boolean
                    'abuseConfidenceScore': 0,
                    'countryCode': 'US'
                }
            }
        }
    }
    
    # Test display function
    try:
        app.display_analysis_results(test_response)
        assert True  # If we get here without error, test passes
    except Exception as e:
        logger.error(f"Error in display: {e}")
        raise

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 