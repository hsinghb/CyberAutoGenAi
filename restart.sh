#!/bin/bash

# Set the working directory to the script's directory
cd "$(dirname "$0")"

# Ensure the Python virtual environment is activated if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Create required directories
mkdir -p logs data config

# Run the Python restart script
python scripts/restart.py 