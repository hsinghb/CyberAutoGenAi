"""Entry point for the Streamlit application."""
import os
import sys
from pathlib import Path
import asyncio
import nest_asyncio

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Import and run the app
from cyberautogenai.ui.streamlit_app import main

if __name__ == "__main__":
    # Ensure we have an event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    main() 