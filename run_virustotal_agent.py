import asyncio
import os
from cyberautogenai.agents.virustotal_agent import VirusTotalAgent
from cyberautogenai.mcp.client import MCPClient

async def main():
    api_key = os.getenv("VIRUSTOTAL_API_KEY")
    if not api_key:
        raise RuntimeError("VIRUSTOTAL_API_KEY not set in environment.")
    mcp_client = MCPClient(agent_id="virustotal_agent")
    agent = VirusTotalAgent(api_key=api_key, mcp_client=mcp_client)
    await agent.run()  # This should start the MCP event loop for the agent

if __name__ == "__main__":
    asyncio.run(main()) 