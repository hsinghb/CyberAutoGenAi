from typing import Dict, Any, Optional
import asyncio
import json
from ..mcp.client import MCPClient
from ..mcp.message import Message
from ..utils.logger import logger

class MCPAgentBase:
    """Base class for agents that use MCP for communication."""
    
    def __init__(self, agent_id: str = "base_agent", mcp_client=None):
        """Initialize the MCP agent.
        
        Args:
            agent_id: Unique name for this agent
            mcp_client: MCPClient instance
        """
        self.agent_id = agent_id
        self.mcp_client = mcp_client
        self.response_futures: Dict[str, asyncio.Future] = {}
        
    async def start(self):
        """Start the agent and connect to MCP server."""
        try:
            await self.mcp_client.connect()
            # Register message handler
            self.mcp_client.register_handler("response", self._handle_response)
            self.mcp_client.register_handler("request", self._handle_request)
            logger.info(f"Agent {self.agent_id} started and connected to MCP")
        except Exception as e:
            logger.error(f"Failed to start agent {self.agent_id}: {e}")
            raise

    async def stop(self):
        """Stop the agent and disconnect from MCP."""
        await self.mcp_client.disconnect()
        logger.info(f"Agent {self.agent_id} stopped")

    async def send_request(self, recipient: str, content: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        """Send a request to another agent and wait for response."""
        message = Message(
            sender_id=self.agent_id,
            recipient_id=recipient,
            message_type="request",
            content=content
        )
        
        # Create future for response
        future = asyncio.Future()
        self.response_futures[message.correlation_id] = future
        
        try:
            # Send message
            await self.mcp_client.send_message(message)
            
            # Wait for response
            response = await asyncio.wait_for(future, timeout)
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Request to {recipient} timed out after {timeout} seconds")
            raise
        finally:
            # Clean up future
            self.response_futures.pop(message.correlation_id, None)

    async def _handle_response(self, message: Message):
        """Handle response messages."""
        if message.correlation_id in self.response_futures:
            future = self.response_futures[message.correlation_id]
            if not future.done():
                future.set_result(message.content)

    async def _handle_request(self, message: Message):
        """Handle incoming request messages."""
        try:
            # Process request
            response_content = await self.process_request(message.content)
            
            # Send response
            response = message.create_response(response_content)
            await self.mcp_client.send_message(response)
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            error_response = message.create_response(
                {
                    "error": str(e),
                    "status": "error"
                },
                message_type="error"
            )
            await self.mcp_client.send_message(error_response)

    async def process_request(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request and return a response.
        
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement process_request") 