#!/bin/bash

# Create necessary directories
mkdir -p cyberautogenai/state
mkdir -p cyberautogenai/data

# Copy the files
cp db_manager.py cyberautogenai/state/
cp react_agent_base.py cyberautogenai/agents/
cp threat_hunting_react_agent.py cyberautogenai/agents/

# Install required packages
pip install nest-asyncio sqlite3

# Create __init__.py files
touch cyberautogenai/state/__init__.py

# Set up database directory
mkdir -p data

# Restart services
./restart_services.sh 