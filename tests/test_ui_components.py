"""Tests for UI components and display functions."""
import pytest
import streamlit as st
from unittest.mock import MagicMock, patch
from cyberautogenai.ui.app import display_analysis_results, init_orchestrator

def test_display_analysis_results_error(monkeypatch):
    """Test error display in analysis results."""
    # Mock streamlit functions
    mock_error = MagicMock()
    mock_info = MagicMock()
    monkeypatch.setattr(st, "error", mock_error)
    monkeypatch.setattr(st, "info", mock_info)
    
    # Test quota exceeded error
    results = {
        "status": "error",
        "message": "API quota exceeded",
        "error_type": "QuotaError"
    }
    display_analysis_results(results)
    mock_error.assert_called_with("⚠️ API Quota Exceeded")
    
    # Test API key error
    results = {
        "status": "error",
        "message": "Invalid API key",
        "error_type": "APIKeyError"
    }
    display_analysis_results(results)
    mock_error.assert_called_with("🔑 API Key Error")

def test_display_analysis_results_success(monkeypatch):
    """Test successful analysis results display."""
    # Mock streamlit functions
    mock_subheader = MagicMock()
    mock_markdown = MagicMock()
    mock_expander = MagicMock()
    mock_json = MagicMock()
    
    monkeypatch.setattr(st, "subheader", mock_subheader)
    monkeypatch.setattr(st, "markdown", mock_markdown)
    monkeypatch.setattr(st, "expander", mock_expander)
    monkeypatch.setattr(st, "json", mock_json)
    
    results = {
        "status": "success",
        "ai_summary": "Test summary",
        "specialized_data": {
            "ip": {"result": "test_ip_data"},
            "domain": {"result": "test_domain_data"}
        }
    }
    
    display_analysis_results(results)
    mock_subheader.assert_any_call("🤖 Quick Analysis")
    mock_markdown.assert_called_with("Test summary")

def test_init_orchestrator(mock_env_vars, mock_session_state):
    """Test orchestrator initialization."""
    orchestrator = init_orchestrator()
    assert orchestrator is not None
    assert orchestrator.config.get("OPENAI_API_KEY") == "test_openai_key" 