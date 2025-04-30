"""Test AutoGen integration."""
import os
from dotenv import load_dotenv
import autogen
from cyberautogenai.config.agent_config import get_openai_config

def test_autogen():
    """Test AutoGen agent creation and basic interaction."""
    # Load environment variables
    load_dotenv()
    
    try:
        # Get OpenAI config
        config_list = get_openai_config()
        
        # Create assistant with simplified config
        assistant = autogen.AssistantAgent(
            name="test_assistant",
            system_message="You are a helpful assistant for testing.",
            llm_config={
                "config_list": config_list,
                "temperature": 0.7,
                "timeout": 60  # Use timeout instead of request_timeout
            }
        )
        
        # Create user proxy
        user_proxy = autogen.UserProxyAgent(
            name="test_user",
            human_input_mode="NEVER"
        )
        
        # Test interaction
        response = user_proxy.initiate_chat(
            assistant,
            message="Say 'AutoGen test successful!' if you can hear me."
        )
        
        print("✅ AutoGen test successful!")
        print("\nResponse:")
        if hasattr(response, 'messages') and response.messages:
            print(response.messages[-1]["content"])
        else:
            print("No response received")
        
    except Exception as e:
        print(f"❌ Error testing AutoGen: {str(e)}")
        print("""
        Common issues:
        1. OpenAI API key not configured
        2. AutoGen package not installed correctly
        3. Configuration issues
        """)

if __name__ == "__main__":
    test_autogen() 