"""Test threat hunting capabilities."""
import os
from dotenv import load_dotenv
import asyncio
from cyberautogenai.agents.threat_hunting_agent import ThreatHuntingAgent

async def test_threat_hunting():
    """Test threat hunting analysis."""
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize threat hunting agent
        agent = ThreatHuntingAgent(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Test data
        test_cases = [
            {
                "type": "ip",
                "value": "8.8.8.8",
                "description": "Known safe IP (Google DNS)"
            },
            {
                "type": "domain",
                "value": "example.com",
                "description": "Sample domain"
            },
            {
                "type": "behavior",
                "value": "Multiple failed login attempts from different IPs",
                "description": "Potential brute force attack"
            }
        ]
        
        # Run tests
        for test in test_cases:
            print(f"\nTesting: {test['description']}")
            print("=" * 50)
            
            try:
                # Validate input
                is_valid = await agent.validate_input(test)
                print(f"Input validation: {'✅ Passed' if is_valid else '❌ Failed'}")
                
                if is_valid:
                    # Perform analysis
                    result = await agent._perform_analysis(test)
                    
                    # Print results
                    print("\nAnalysis Results:")
                    print(f"Status: {result.get('status', 'unknown')}")
                    
                    if result.get('status') == 'success':
                        analysis = result.get('analysis', {})
                        print("\nFindings:")
                        if 'patterns_identified' in analysis:
                            print("Patterns:", len(analysis['patterns_identified']))
                        if 'risk_assessment' in analysis:
                            print("Risk Level:", analysis['risk_assessment'].get('level', 'unknown'))
                        if 'recommendations' in analysis:
                            print("\nRecommendations:")
                            for rec in analysis['recommendations']:
                                print(f"- {rec}")
                    else:
                        print(f"Error: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                print(f"❌ Test failed: {str(e)}")
            
            print("\n" + "=" * 50)
    
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_threat_hunting()) 