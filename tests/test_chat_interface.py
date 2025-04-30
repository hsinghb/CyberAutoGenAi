"""Tests for chat interface functionality."""
import pytest
import streamlit as st
from unittest.mock import MagicMock, patch
from cyberautogenai.ui.app import process_chat_message

@pytest.fixture
def mock_chat_message():
    return "analyze IP 8.8.8.8"

def test_chat_message_processing(mock_orchestrator, mock_chat_message):
    """Test processing of chat messages."""
    with patch('streamlit.chat_input', return_value=mock_chat_message):
        with patch('streamlit.chat_message') as mock_chat:
            result = process_chat_message(mock_chat_message, mock_orchestrator)
            assert result is not None
            assert "status" in result

def test_chat_history_management(mock_session_state):
    """Test chat history management."""
    # Add a message
    st.session_state.messages.append({
        "role": "user",
        "content": "test message"
    })
    assert len(st.session_state.messages) == 1
    assert st.session_state.messages[0]["role"] == "user"

def test_error_handling_in_chat(mock_orchestrator):
    """Test error handling in chat interface."""
    with patch('streamlit.error') as mock_error:
        result = process_chat_message("invalid input", mock_orchestrator)
        assert result.get("status") == "error"
        mock_error.assert_called() 