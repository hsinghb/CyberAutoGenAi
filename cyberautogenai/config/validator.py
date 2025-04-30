"""Configuration validator for API keys and settings."""
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import requests
import openai
from openai import OpenAI

class ConfigValidator:
    """Validates configuration settings and API keys."""

    @staticmethod
    def check_openai_key() -> Dict[str, Any]:
        """
        Check if OpenAI API key is valid.
        Returns dict with status and message.
        """
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            return {
                "status": "error",
                "message": "OpenAI API key not found in .env file"
            }
        
        if not api_key.startswith('sk-'):
            return {
                "status": "error",
                "message": "Invalid OpenAI API key format. Key should start with 'sk-'"
            }

        try:
            # Initialize OpenAI client
            client = OpenAI(api_key=api_key)
            
            # Test the API key with a minimal request
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            
            return {
                "status": "success",
                "message": "OpenAI API key is valid",
                "model": response.model
            }
            
        except openai.AuthenticationError:
            return {
                "status": "error",
                "message": "Invalid OpenAI API key"
            }
        except openai.RateLimitError:
            return {
                "status": "error",
                "message": "OpenAI API rate limit exceeded"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"OpenAI API error: {str(e)}"
            }

    @staticmethod
    def get_config() -> Dict[str, Any]:
        """
        Get configuration settings from .env file.
        Returns dict with all settings.
        """
        load_dotenv()
        
        return {
            "openai": {
                "api_key": os.getenv('OPENAI_API_KEY'),
                "model": os.getenv('OPENAI_MODEL', 'gpt-4'),
                "temperature": float(os.getenv('TEMPERATURE', '0.7')),
                "max_tokens": int(os.getenv('MAX_TOKENS', '2000'))
            },
            "security_apis": {
                "virustotal": os.getenv('VIRUSTOTAL_API_KEY'),
                "shodan": os.getenv('SHODAN_API_KEY'),
                "abuseipdb": os.getenv('ABUSEIPDB_API_KEY')
            }
        }

    @staticmethod
    def validate_all() -> Dict[str, Any]:
        """
        Validate all configuration settings.
        Returns dict with validation results.
        """
        results = {
            "openai": ConfigValidator.check_openai_key(),
            "security_apis": {}
        }
        
        # Check security API keys
        security_apis = {
            "virustotal": os.getenv('VIRUSTOTAL_API_KEY'),
            "shodan": os.getenv('SHODAN_API_KEY'),
            "abuseipdb": os.getenv('ABUSEIPDB_API_KEY')
        }
        
        for api, key in security_apis.items():
            if not key:
                results["security_apis"][api] = {
                    "status": "warning",
                    "message": f"{api.upper()} API key not found in .env file"
                }
            else:
                results["security_apis"][api] = {
                    "status": "success",
                    "message": f"{api.upper()} API key found"
                }
        
        return results 