import asyncio
from cyberautogenai.state.db_manager import StateManager
from cyberautogenai.agents.threat_hunting_react_agent import ThreatHuntingReActAgent

async def test_react():
    # Initialize state manager
    state_manager = StateManager()
    
    # Create threat hunting agent
    agent = ThreatHuntingReActAgent(state_manager)
    
    # Test memory storage
    await agent.remember( 