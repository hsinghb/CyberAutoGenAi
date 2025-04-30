#!/bin/bash

# Set up logging
LOG_DIR="logs"
STREAMLIT_LOG="$LOG_DIR/streamlit.log"
MAIN_LOG="$LOG_DIR/restart.log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$MAIN_LOG"
}

# Function to check if a process is running
is_process_running() {
    local pattern="$1"
    pgrep -f "$pattern" >/dev/null
    return $?
}

# Function to kill a process
kill_process() {
    local pattern="$1"
    local name="$2"
    if is_process_running "$pattern"; then
        log "Stopping $name..."
        pkill -f "$pattern"
        sleep 2
    else
        log "$name is not running"
    fi
}

# Function to start Streamlit
start_streamlit() {
    log "Starting Streamlit UI..."
    
    # Get the absolute path to the project root
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Add project root to PYTHONPATH
    export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"
    
    # Create and activate Python environment variables
    export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
    export PYTHONUNBUFFERED=1
    
    # Start Streamlit with the entry point script
    streamlit run run_streamlit.py \
        --server.port=8501 \
        --server.address=0.0.0.0 \
        --logger.level=debug \
        --logger.messageFormat="%(asctime)s - %(name)s - %(levelname)s - %(message)s" \
        > "$STREAMLIT_LOG" 2>&1 &
    
    # Wait for Streamlit to start
    local max_attempts=10
    local attempt=1
    while ! curl -s http://localhost:8501 >/dev/null; do
        if [ $attempt -ge $max_attempts ]; then
            log "ERROR: Streamlit failed to start after $max_attempts attempts"
            return 1
        fi
        log "Waiting for Streamlit to start (attempt $attempt/$max_attempts)..."
        sleep 2
        ((attempt++))
    done
    log "Streamlit UI is running"
}

# Function to check environment variables
check_environment() {
    local required_vars=("OPENAI_API_KEY" "ABUSEIPDB_API_KEY" "SHODAN_API_KEY")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        log "WARNING: Missing environment variables: ${missing_vars[*]}"
        log "Some features may be limited"
    else
        log "All required environment variables are set"
    fi
}

# Function to clean up on exit
cleanup() {
    log "Cleaning up..."
    kill_process "streamlit run" "Streamlit"
    log "Cleanup complete"
}

# Register cleanup function to run on script exit
trap cleanup EXIT

# Main script
log "Starting services..."

# Create required directories
mkdir -p data config

# Load environment variables
if [ -f .env ]; then
    log "Loading environment variables from .env"
    source .env
else
    log "WARNING: .env file not found"
fi

# Check environment variables
check_environment

# Kill any existing processes
kill_process "streamlit run" "existing Streamlit"

# Start services
start_streamlit

if [ $? -eq 0 ]; then
    log "All services started successfully"
    log "Access the UI at http://localhost:8501"
    
    # Keep the script running and monitor services
    while true; do
        if ! is_process_running "streamlit run"; then
            log "ERROR: Streamlit process died unexpectedly"
            exit 1
        fi
        sleep 5
    done
else
    log "ERROR: Failed to start services"
    exit 1
fi 