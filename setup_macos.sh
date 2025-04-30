#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages
log_message() {
    echo -e "${2}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    log_message "Homebrew is not installed. Installing Homebrew..." "$YELLOW"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install system dependencies
log_message "Installing system dependencies..." "$YELLOW"
brew install libomp
brew install cmake

# Set environment variables for OpenMP
export CFLAGS="-I/opt/homebrew/opt/libomp/include"
export CXXFLAGS="-I/opt/homebrew/opt/libomp/include"
export LDFLAGS="-L/opt/homebrew/opt/libomp/lib"
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/libomp/lib:$DYLD_LIBRARY_PATH"

# Create and activate virtual environment
log_message "Creating virtual environment..." "$YELLOW"
python3.9 -m venv venv
source venv/bin/activate

# Upgrade pip
log_message "Upgrading pip..." "$YELLOW"
pip install --upgrade pip

# Install build dependencies
log_message "Installing build dependencies..." "$YELLOW"
pip install wheel setuptools

# Install core dependencies in order
log_message "Installing core dependencies..." "$YELLOW"
pip install numpy
pip install scipy
pip install pandas
pip install scikit-learn

# Install XGBoost with OpenMP support
log_message "Installing XGBoost..." "$YELLOW"
pip uninstall -y xgboost  # Remove any existing installation
pip install --no-cache-dir xgboost

# Install FLAML
log_message "Installing FLAML..." "$YELLOW"
pip install 'flaml[automl]'

# Install other requirements
log_message "Installing other dependencies..." "$YELLOW"
pip install python-dotenv>=1.0.0
pip install streamlit>=1.30.0
pip install requests>=2.31.0
pip install aiohttp>=3.9.1
pip install 'urllib3<2.0.0'
pip install pyautogen>=0.2.0
pip install openai>=1.6.1

# Create necessary directories
log_message "Creating project directories..." "$YELLOW"
mkdir -p logs
mkdir -p workspace
mkdir -p config

# Create a test script
cat > test_setup.py << EOL
"""Test the setup by importing all required packages."""
import sys
import os
import xgboost
import flaml
import autogen
import streamlit
import numpy
import pandas
import scipy
import sklearn

def test_imports():
    """Test all imports and print versions."""
    print(f"Python version: {sys.version}")
    print(f"XGBoost version: {xgboost.__version__}")
    print(f"FLAML version: {flaml.__version__}")
    print(f"AutoGen version: {autogen.__version__}")
    print(f"Streamlit version: {streamlit.__version__}")
    print(f"NumPy version: {numpy.__version__}")
    print(f"Pandas version: {pandas.__version__}")
    print(f"SciPy version: {scipy.__version__}")
    print(f"Scikit-learn version: {sklearn.__version__}")
    
    # Test XGBoost functionality
    print("\nTesting XGBoost functionality...")
    import numpy as np
    data = np.random.rand(5, 3)
    label = np.random.randint(2, size=5)
    dtrain = xgboost.DMatrix(data, label=label)
    param = {'max_depth': 2, 'eta': 1, 'objective': 'binary:logistic'}
    bst = xgboost.train(param, dtrain, 1)
    print("XGBoost test successful!")

if __name__ == "__main__":
    test_imports()
EOL

# Add environment variables to virtual environment activation script
cat >> venv/bin/activate << EOL

# Add OpenMP environment variables
export CFLAGS="-I/opt/homebrew/opt/libomp/include"
export CXXFLAGS="-I/opt/homebrew/opt/libomp/include"
export LDFLAGS="-L/opt/homebrew/opt/libomp/lib"
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/libomp/lib:\$DYLD_LIBRARY_PATH"
EOL

# Run the test script
log_message "Running test script..." "$YELLOW"
python test_setup.py && log_message "Setup completed successfully!" "$GREEN" || log_message "Setup encountered some issues." "$RED"

# Create a convenience script to run the application
cat > run_app.sh << EOL
#!/bin/bash
source venv/bin/activate
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/libomp/lib:\$DYLD_LIBRARY_PATH"
python -m cyberautogenai.ui.app
EOL

chmod +x run_app.sh

log_message "Setup complete! You can now run the application using ./run_app.sh" "$GREEN" 