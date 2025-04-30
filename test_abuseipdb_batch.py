import asyncio
from cyberautogenai.agents.abuseipdb_agent import AbuseIPDBAgent

# Replace with your actual API key
API_KEY = "8c2c050efe79f7249d9ecd91e811b2f89cc0cf82e259cd128e06417aef272b034bb322af3fcd09c3"

async def main():
    agent = AbuseIPDBAgent(api_key=API_KEY)
    # Prepare a batch of IP requests
    batch_requests = [
        {"type": "ip", "value": "8.8.8.8"},
        {"type": "ip", "value": "1.1.1.1"},
        {"type": "ip", "value": "4.4.4.4"},
        {"type": "ip", "value": "256.256.256.256"},  # This will fail, but format is correct
    ]
    results = await agent.analyze_batch(batch_requests)
    print("Results:", results)
    if results is None:
        print("analyze_batch returned None!")
        return
    for ip, result in results.items():
        print(f"Result for {ip}:")
        print(result)
        print("-" * 40)
    print("Batch results:", results)

if __name__ == "__main__":
    asyncio.run(main()) 