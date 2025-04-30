#!/bin/bash

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Add the project root to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$DIR

# Run the Streamlit app
streamlit run cyberautogenai/ui/streamlit_app.py
