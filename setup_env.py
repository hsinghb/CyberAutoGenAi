"""Setup environment variables."""
import os
from getpass import getpass

def setup_env():
    """Setup environment variables interactively."""
    print("Setting up OpenAI API key...")
    
    # Get API key securely
    api_key = getpass("Enter your OpenAI API key (starts with 'sk-'): ")
    
    # Validate API key format
    if not api_key.startswith('sk-'):
        print("Error: OpenAI API key should start with 'sk-'")
        return
    
    # Write to .env file
    with open('.env', 'w') as f:
        f.write(f'OPENAI_API_KEY={api_key}\n')
    
    print("\n.env file created successfully!")
    print("You can now start the application.")

if __name__ == "__main__":
    setup_env() 