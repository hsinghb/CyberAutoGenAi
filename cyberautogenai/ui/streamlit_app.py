import streamlit as st

# This must be the first Streamlit command
st.set_page_config(
    page_title="Security Analysis Chat",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Use absolute import instead of relative import
from cyberautogenai.ui.security_app import SecurityApp

def main():
    """Main entry point for the Streamlit application."""
    app = SecurityApp()
    app.run()

if __name__ == "__main__":
    main() 