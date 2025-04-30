#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Setting up CyberAutoGenAI environment...${NC}"

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -r requirements.txt

# Verify installations
echo -e "${GREEN}Verifying installations...${NC}"
python3 -c "import nest_asyncio; import autogen; import openai; import streamlit; print('All dependencies installed successfully!')"

# Create necessary directories
mkdir -p logs
mkdir -p workspace
mkdir -p config

echo -e "${GREEN}Setup complete!${NC}" 