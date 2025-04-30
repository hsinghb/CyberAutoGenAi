#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}Installing libmagic using Homebrew...${NC}"
    if ! command -v brew &> /dev/null; then
        echo -e "${RED}Homebrew not found. Please install Homebrew first.${NC}"
        exit 1
    fi
    brew install libmagic
fi

# Setup project structure
echo -e "${YELLOW}Setting up project structure...${NC}"
python scripts/setup_project_structure.py

# Create and activate virtual environment
echo -e "${YELLOW}Setting up virtual environment...${NC}"
python -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}Setup completed successfully${NC}" 