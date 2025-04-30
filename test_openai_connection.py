"""Test OpenAI API key configuration."""
import os
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st

def test_openai_connection():
    """Test OpenAI API connection and display results."""
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ OpenAI API key not found in .env file")
        print("Please set your API key in the .env file:")
        print("OPENAI_API_KEY=your_api_key_here")
        return
    
    try:
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
        
        print("✅ OpenAI API connection successful!")
        print("\nTest Response:")
        print(f"Model: {response.model}")
        print(f"Response: {response.choices[0].message.content}")
        print("\nUsage:")
        print(f"Prompt tokens: {response.usage.prompt_tokens}")
        print(f"Completion tokens: {response.usage.completion_tokens}")
        print(f"Total tokens: {response.usage.total_tokens}")
        
    except Exception as e:
        print(f"❌ Error testing OpenAI API: {str(e)}")
        print("""
        Common issues:
        1. Invalid API key format
        2. API key has expired
        3. API key has no credits
        4. Network connectivity issues
        
        Get your API key from: https://platform.openai.com/account/api-keys
        """)

if __name__ == "__main__":
    test_openai_connection() 