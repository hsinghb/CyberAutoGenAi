import streamlit as st

def init_page_config():
    st.set_page_config(
        page_title="Security Analysis Chat",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="collapsed"
    ) 