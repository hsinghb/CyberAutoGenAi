"""UI package for CyberAutoGenAI."""

# Only export the main function
__all__ = ['run_app']

def run_app():
    """Run the Streamlit application."""
    from .app import main
    main() 