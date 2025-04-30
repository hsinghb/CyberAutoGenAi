"""Integration tests for UI and backend components."""
import pytest
from cyberautogenai.ui.app import main
from cyberautogenai.agents.orchestrator import SecurityOrchestrator

@pytest.mark.integration
def test_full_analysis_flow(mock_orchestrator, mock_session_state):
    """Test complete analysis flow from UI to backend."""
    test_data = {
        "type": "ip",
        "value": "8.8.8.8"
    }
    
    result = mock_orchestrator.analyze_sync(test_data)
    assert result is not None
    assert result.get("status") in ["success", "error"]
    
    if result.get("status") == "success":
        assert "ai_summary" in result
        assert "specialized_data" in result

@pytest.mark.integration
def test_chat_to_analysis_flow(mock_orchestrator, mock_session_state):
    """Test flow from chat input to analysis results."""
    chat_input = "analyze IP 8.8.8.8"
    result = mock_orchestrator.process_chat_message(chat_input)
    
    assert result is not None
    assert "status" in result
    if result.get("status") == "success":
        assert "response" in result 