"""Test VirusTotal agent functionality."""
import os
import pytest
from dotenv import load_dotenv
import asyncio
from cyberautogenai.agents.orchestrator import SecurityOrchestrator
from cyberautogenai.utils.logger import logger

# Load environment variables
load_dotenv()

# Test cases
TEST_CASES = {
    "domain": [
        {"value": "google.com", "description": "Known safe domain"},
        {"value": "microsoft.com", "description": "Known safe domain"},
        {"value": "malware-test.com", "description": "Test malicious domain"},
    ],
    "url": [
        {"value": "https://www.python.org", "description": "Known safe URL"},
        {"value": "https://github.com", "description": "Known safe URL"},
        {"value": "http://malware-test.com/test", "description": "Test malicious URL"},
    ]
}

@pytest.fixture
def orchestrator():
    """Create a SecurityOrchestrator instance for testing."""
    config = {
        "VIRUSTOTAL_API_KEY": os.getenv("VIRUSTOTAL_API_KEY"),
    }
    
    # Log if API key is available
    if config["VIRUSTOTAL_API_KEY"]:
        logger.info("VirusTotal API key found")
    else:
        logger.warning("VirusTotal API key not found")
    
    return SecurityOrchestrator(config=config)

@pytest.mark.asyncio
async def test_virustotal_domain(orchestrator):
    """Test VirusTotal agent with domains."""
    if "domain" not in orchestrator.agents:
        pytest.skip("VirusTotal agent not available")
    
    for test in TEST_CASES["domain"]:
        logger.info(f"\nTesting domain: {test['value']} ({test['description']})")
        
        test_data = {
            "type": "domain",
            "value": test["value"]
        }
        
        try:
            result = await orchestrator.agents["domain"].analyze(test_data)
            logger.info(f"Analysis result: {result}")
            
            assert result is not None
            assert "type" in result
            assert "stats" in result
            assert "reputation" in result
            assert "total_votes" in result
            
            # Log detailed stats
            if "stats" in result:
                stats = result["stats"]
                logger.info(f"Detection stats:")
                logger.info(f"- Harmless: {stats.get('harmless', 0)}")
                logger.info(f"- Malicious: {stats.get('malicious', 0)}")
                logger.info(f"- Suspicious: {stats.get('suspicious', 0)}")
                logger.info(f"- Undetected: {stats.get('undetected', 0)}")
            
        except Exception as e:
            logger.error(f"Test failed for {test['value']}: {str(e)}")
            raise

@pytest.mark.asyncio
async def test_virustotal_url(orchestrator):
    """Test VirusTotal agent with URLs."""
    if "url" not in orchestrator.agents:
        pytest.skip("VirusTotal agent not available")
    
    for test in TEST_CASES["url"]:
        logger.info(f"\nTesting URL: {test['value']} ({test['description']})")
        
        test_data = {
            "type": "url",
            "value": test["value"]
        }
        
        try:
            result = await orchestrator.agents["url"].analyze(test_data)
            logger.info(f"Analysis result: {result}")
            
            assert result is not None
            assert "type" in result
            assert "stats" in result
            assert "reputation" in result
            assert "total_votes" in result
            
            # Log detailed stats
            if "stats" in result:
                stats = result["stats"]
                logger.info(f"Detection stats:")
                logger.info(f"- Harmless: {stats.get('harmless', 0)}")
                logger.info(f"- Malicious: {stats.get('malicious', 0)}")
                logger.info(f"- Suspicious: {stats.get('suspicious', 0)}")
                logger.info(f"- Undetected: {stats.get('undetected', 0)}")
            
        except Exception as e:
            logger.error(f"Test failed for {test['value']}: {str(e)}")
            raise

if __name__ == "__main__":
    # Run tests
    asyncio.run(test_virustotal_domain(orchestrator()))
    asyncio.run(test_virustotal_url(orchestrator())) 