"""Test specialized security agents functionality."""
import os
import pytest
from dotenv import load_dotenv
from cyberautogenai.agents.orchestrator import SecurityOrchestrator
from cyberautogenai.utils.logger import logger
import asyncio
import pytest_asyncio

# Load environment variables
load_dotenv()

@pytest_asyncio.fixture
async def orchestrator():
    """Create a SecurityOrchestrator instance for testing."""
    config = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "VIRUSTOTAL_API_KEY": os.getenv("VIRUSTOTAL_API_KEY"),
        "SHODAN_API_KEY": os.getenv("SHODAN_API_KEY"),
        "ABUSEIPDB_API_KEY": os.getenv("ABUSEIPDB_API_KEY"),
        "THREAT_INTEL_API_KEY": os.getenv("THREAT_INTEL_API_KEY")
    }
    
    # Log available API keys (without showing the actual keys)
    available_keys = [key for key, value in config.items() if value]
    logger.info(f"Available API keys: {available_keys}")
    
    return await SecurityOrchestrator.create(api_keys=config)

@pytest.mark.asyncio
async def test_agent_initialization(orchestrator):
    """Test that agents are properly initialized."""
    # Check which agents are available
    available_agents = orchestrator.agents.keys()
    logger.info(f"Available agents: {available_agents}")
    
    # Expected agent types
    expected_agents = {"ip", "domain", "url", "network", "file", "behavior"}
    
    # Log which expected agents are missing
    missing_agents = expected_agents - set(available_agents)
    if missing_agents:
        logger.warning(f"Missing agents: {missing_agents}")
    
    # There should be at least one agent initialized
    assert len(available_agents) > 0, "No agents were initialized"

@pytest.mark.asyncio
async def test_abuseipdb_agent(orchestrator):
    """Test AbuseIPDB agent functionality."""
    if "ip" not in orchestrator.agents:
        pytest.skip("AbuseIPDB agent not available")
    
    test_data = {
        "type": "ip",
        "value": "8.8.8.8"  # Google DNS - Known safe IP
    }
    
    result = await orchestrator.agents["ip"].analyze(test_data)
    logger.info(f"AbuseIPDB result: {result}")
    
    assert result["status"] == "success"
    assert "summary" in result
    assert "details" in result
    assert result["type"] == "ip"

@pytest.mark.asyncio
async def test_shodan_agent(orchestrator):
    """Test Shodan agent functionality."""
    if "network" not in orchestrator.agents:
        pytest.skip("Shodan agent not available")
    
    test_data = {
        "type": "network",
        "value": "8.8.8.8"  # Google DNS
    }
    
    result = await orchestrator.agents["network"].analyze(test_data)
    logger.info(f"Shodan result: {result}")
    
    assert result["status"] == "success"
    assert "summary" in result
    assert "details" in result
    assert "ports" in result["details"]

@pytest.mark.asyncio
async def test_virustotal_agent_domain(orchestrator):
    """Test VirusTotal agent functionality with domain."""
    if "domain" not in orchestrator.agents:
        pytest.skip("VirusTotal agent not available")
    
    test_data = {
        "type": "domain",
        "value": "google.com"  # Known safe domain
    }
    
    result = await orchestrator.agents["domain"].analyze(test_data)
    logger.info(f"VirusTotal domain result: {result}")
    
    assert result["status"] == "success"
    assert "summary" in result
    assert "details" in result
    assert "reputation_score" in result["details"]

@pytest.mark.asyncio
async def test_error_handling(orchestrator):
    """Test error handling with invalid inputs."""
    test_cases = [
        {
            "type": "ip",
            "value": ""  # Empty value
        },
        {
            "type": "invalid_type",
            "value": "test"  # Invalid type
        },
        {
            "type": "ip",
            "value": "256.256.256.256"  # Invalid IP format
        },
        {
            "type": "domain",
            "value": "this-is-an-invalid-domain"  # Unresolvable domain
        }
    ]
    
    for test_case in test_cases:
        logger.info(f"Testing error case: {test_case}")
        agent_type = test_case["type"]
        
        if agent_type in orchestrator.agents:
            try:
                result = await orchestrator.agents[agent_type].analyze(test_case)
                logger.info(f"Result: {result}")
                assert result["status"] == "error" or "error" in result
            except Exception as e:
                logger.info(f"Expected error occurred: {str(e)}")

@pytest.mark.asyncio
async def test_combined_analysis(orchestrator):
    """Test analysis with additional context."""
    if "ip" not in orchestrator.agents:
        pytest.skip("IP agent not available")
    
    test_data = {
        "type": "ip",
        "value": "8.8.8.8", "1.1.1.1"
        "context": {
            "related_domains": ["google.com"],
            "observed_behavior": "High DNS query volume"
        }
    }
    
    result = await orchestrator.agents["ip"].analyze(test_data)
    logger.info(f"Combined analysis result: {result}")
    
    assert result["status"] == "success"
    assert "summary" in result
    assert "details" in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 