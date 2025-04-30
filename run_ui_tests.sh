#!/bin/bash

# Set up environment
source venv/bin/activate

# Set test environment variables
export PYTHONPATH=$PYTHONPATH:$(pwd)
export TESTING=true

# Run tests with pytest
echo "Running UI tests..."
pytest tests/test_ui_components.py -v
pytest tests/test_chat_interface.py -v
pytest tests/test_integration.py -v -m "integration"

# Generate coverage report
pytest --cov=cyberautogenai.ui tests/ --cov-report=html

# Clean up
deactivate 