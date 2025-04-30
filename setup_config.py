"""Configuration setup script."""
import os
from getpass import getpass
import json

def setup_configuration():
    """Interactive configuration setup."""
    print("CyberAutoGenAI Configuration Setup")
    print("==================================")
    
    config = {
        "OPENAI_API_KEY": "",
        "OPENAI_MODEL": "gpt-4",
        "TEMPERATURE": "0.7",
        "MAX_TOKENS": "2000",
        "VIRUSTOTAL_API_KEY": "",
        "SHODAN_API_KEY": "",
        "ABUSEIPDB_API_KEY": ""
    }
    
    # Get OpenAI configuration
    print("\nOpenAI Configuration:")
    config["OPENAI_API_KEY"] = getpass("Enter your OpenAI API key: ")
    config["OPENAI_MODEL"] = input("Enter OpenAI model (default: gpt-4): ") or config["OPENAI_MODEL"]
    
    # Get security API keys
    print("\nSecurity APIs Configuration:")
    config["VIRUSTOTAL_API_KEY"] = getpass("Enter your VirusTotal API key (optional): ") or ""
    config["SHODAN_API_KEY"] = getpass("Enter your Shodan API key (optional): ") or ""
    config["ABUSEIPDB_API_KEY"] = getpass("Enter your AbuseIPDB API key (optional): ") or ""
    
    # Write configuration to .env file
    with open(".env", "w") as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")
    
    print("\nConfiguration saved to .env file!")

if __name__ == "__main__":
    setup_configuration() 