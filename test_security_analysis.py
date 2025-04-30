"""Test security analysis with various indicators."""
import os
from dotenv import load_dotenv
import asyncio
import json
from datetime import datetime
from cyberautogenai.agents.orchestrator import SecurityOrchestrator
from typing import Dict, Any

# Test cases
TEST_CASES = {
    "ip": [
        {"value": "8.8.8.8", "description": "Google DNS"},
        {"value": "1.1.1.1", "description": "Cloudflare DNS"},
        {"value": "185.143.223.12", "description": "Known malicious"},
        {"value": "103.35.74.74", "description": "Reported attacks"},
        {"value": "0.0.0.0", "description": "Invalid IP"},
        {"value": "127.0.0.1", "description": "Localhost"}
    ],
    "domain": [
        {"value": "google.com", "description": "Google"},
        {"value": "microsoft.com", "description": "Microsoft"},
        {"value": "temp.suspicious-domain.com", "description": "Suspicious temp"},
        {"value": "free-bitcoin-wallet.com", "description": "Crypto suspicious"},
        {"value": "google-security.temp.com", "description": "Typosquatting"},
        {"value": "secure-bank-login.com", "description": "Potential phishing"}
    ],
    "url": [
        {"value": "https://www.python.org", "description": "Python official"},
        {"value": "https://github.com", "description": "GitHub"},
        {"value": "http://unsecure-login.com/bank", "description": "Unsecure login"},
        {"value": "https://bit.ly/suspicious-link", "description": "Shortened URL"},
        {"value": "http://banking.secure-login.temp.com/login", "description": "Phishing pattern"},
        {"value": "https://download.free-software.temp.com/exe", "description": "Suspicious download"}
    ]
}

async def test_security_analysis():
    """Run security analysis tests."""
    # Load environment variables
    load_dotenv()
    
    # Initialize orchestrator
    config = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "VIRUSTOTAL_API_KEY": os.getenv("VIRUSTOTAL_API_KEY"),
        "ABUSEIPDB_API_KEY": os.getenv("ABUSEIPDB_API_KEY")
    }
    
    orchestrator = SecurityOrchestrator(config=config)
    
    # Create results directory
    os.makedirs("test_results", exist_ok=True)
    
    # Run tests for each type
    for test_type, test_cases in TEST_CASES.items():
        print(f"\nTesting {test_type.upper()} indicators")
        print("=" * 50)
        
        results = []
        for test in test_cases:
            print(f"\nAnalyzing: {test['value']} ({test['description']})")
            
            try:
                # Prepare request
                request = {
                    "type": test_type,
                    "value": test["value"],
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Perform analysis
                result = await orchestrator.analyze(request)
                
                # Add test info to result
                result["test_info"] = test
                results.append(result)
                
                # Display summary
                print(f"Status: {result.get('status', 'unknown')}")
                if result.get('status') == 'success':
                    analysis = result.get('analysis', {})
                    print(f"Risk Level: {analysis.get('risk_level', 'unknown')}")
                    if 'recommendations' in analysis:
                        print("\nRecommendations:")
                        for rec in analysis['recommendations']:
                            print(f"- {rec}")
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                print(f"Error analyzing {test['value']}: {str(e)}")
                results.append({
                    "status": "error",
                    "error": str(e),
                    "test_info": test
                })
            
            print("-" * 30)
        
        # Save results
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results/{test_type}_analysis_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(test_security_analysis()) 