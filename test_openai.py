"""Test OpenAI API key configuration."""
import os
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st

def test_openai_connection():
    """Test OpenAI API connection and display results."""
    st.title("OpenAI API Key Test")
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        st.error("❌ OpenAI API key not found in .env file")
        st.info("Please set your API key in the .env file:")
        st.code("OPENAI_API_KEY=your_api_key_here")
        return
    
    # Display masked API key
    masked_key = f"sk-...{api_key[-4:]}"
    st.write(f"Testing API key: {masked_key}")
    
    try:
        with st.spinner("Testing OpenAI API connection..."):
            # Initialize OpenAI client
            client = OpenAI(api_key=api_key)
            
            # Test API with a simple completion
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello, testing!' if you can hear me."}
                ],
                max_tokens=20
            )
            
            # Display success message
            st.success("✅ OpenAI API connection successful!")
            
            # Display response details
            st.subheader("Test Response:")
            st.json({
                "model": response.model,
                "response": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            })
            
            # Display available models
            with st.expander("Available Models"):
                models = client.models.list()
                st.write([model.id for model in models.data])
            
    except Exception as e:
        st.error(f"❌ Error testing OpenAI API: {str(e)}")
        st.info("""
        Common issues:
        1. Invalid API key format
        2. API key has expired
        3. API key has no credits
        4. Network connectivity issues
        
        Get your API key from: https://platform.openai.com/account/api-keys
        """)

if __name__ == "__main__":
    test_openai_connection() 