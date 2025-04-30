#!/bin/bash

# Function to check if Python virtual environment exists
check_venv() {
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
}

# Function to activate virtual environment
activate_venv() {
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "Error: Virtual environment not found"
        exit 1
    fi
}

# Function to install dependencies
install_deps() {
    pip install -e .
}

# Function to setup environment
setup_env() {
    python setup_env.py
}

# Function to start the application
start_app() {
    streamlit run main.py
}

case "$1" in
    "setup")
        check_venv
        activate_venv
        install_deps
        setup_env
        ;;
    "start")
        activate_venv
        start_app
        ;;
esac 