"""Main entry point for the CyberAutoGenAI application."""
import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from cyberautogenai.ui.app import main

if __name__ == "__main__":
    main() 