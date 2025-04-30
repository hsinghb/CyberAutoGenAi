"""Intelligent Message Control Protocol Handler."""
from typing import Dict, Any, List
import asyncio
from .message import Message
from ..agents.base_agent import BaseSecurityAgent
from datetime import datetime

class MCPHandler:
    """Intelligent handler for agent communication and coordination."""
    
    def __init__(self):
        self.registered_agents: Dict[str, BaseSecurityAgent] = {}
        self.active_conversations: Dict[str, List[Message]] = {}
        self.message_queue = asyncio.Queue()
        self.rate_limits: Dict[str, datetime] = {}
        self.min_message_interval = 1.0  # Minimum seconds between messages

    async def register_agent(self, agent: BaseSecurityAgent) -> None:
        """Register a new agent with the MCP."""
        self.registered_agents[agent.name] = agent

    async def process_message(self, message: Message) -> Message:
        """Process and route messages between agents intelligently."""
        try:
            # Validate message
            if not self._can_process_message(message):
                return self._create_rate_limit_response(message)

            # Check for meaningful content
            if not message.is_meaningful():
                return Message(
                    sender_id="mcp",
                    recipient_id=message.sender_id,
                    message_type="error",
                    content={
                        "error": "Empty or meaningless message content",
                        "status": "rejected"
                    },
                    correlation_id=message.correlation_id
                )

            message.validate()
            
            # Store in conversation history
            self._store_conversation(message)
            
            # Get target agent
            target_agent = self.registered_agents.get(message.recipient_id)
            if not target_agent:
                raise ValueError(f"Unknown recipient: {message.recipient_id}")
            
            # Process request with target agent
            response_data = await target_agent.process_request(message.content)
            
            # Create response message
            response = Message(
                sender_id=message.recipient_id,
                recipient_id=message.sender_id,
                message_type="response",
                content=response_data,
                correlation_id=message.correlation_id
            )
            
            # Update rate limit tracking
            self._update_rate_limit(message)
            
            # Store response in conversation history
            self._store_conversation(response)
            
            return response
            
        except ValueError as e:
            return self._create_error_response(message, str(e))
        except Exception as e:
            return self._create_error_response(message, f"Unexpected error: {str(e)}")

    def _can_process_message(self, message: Message) -> bool:
        """Check if message can be processed based on rate limits."""
        sender_recipient = f"{message.sender_id}-{message.recipient_id}"
        current_time = datetime.utcnow()
        
        if sender_recipient in self.rate_limits:
            time_diff = (current_time - self.rate_limits[sender_recipient]).total_seconds()
            return time_diff >= self.min_message_interval
        return True

    def _update_rate_limit(self, message: Message):
        """Update rate limit tracking for a sender-recipient pair."""
        sender_recipient = f"{message.sender_id}-{message.recipient_id}"
        self.rate_limits[sender_recipient] = datetime.utcnow()

    def _create_rate_limit_response(self, message: Message) -> Message:
        """Create a rate limit error response."""
        return Message(
            sender_id="mcp",
            recipient_id=message.sender_id,
            message_type="error",
            content={
                "error": "Rate limit exceeded",
                "status": "rate_limited",
                "retry_after": self.min_message_interval
            },
            correlation_id=message.correlation_id
        )

    def _create_error_response(self, message: Message, error_msg: str) -> Message:
        """Create a standardized error response."""
        return Message(
            sender_id="mcp",
            recipient_id=message.sender_id,
            message_type="error",
            content={
                "error": error_msg,
                "status": "error"
            },
            correlation_id=message.correlation_id
        )

    def _store_conversation(self, message: Message) -> None:
        """Store message in conversation history."""
        conversation_id = message.correlation_id
        if conversation_id not in self.active_conversations:
            self.active_conversations[conversation_id] = []
        self.active_conversations[conversation_id].append(message)

    async def get_conversation_history(
        self,
        correlation_id: str
    ) -> List[Message]:
        """Retrieve conversation history."""
        return self.active_conversations.get(correlation_id, [])

    async def broadcast_alert(
        self,
        alert_type: str,
        content: Dict[str, Any]
    ) -> None:
        """Broadcast security alerts to all agents."""
        alert = Message(
            sender_id="mcp",
            recipient_id="broadcast",
            message_type="alert",
            content={
                "type": alert_type,
                "data": content
            }
        )
        
        # Queue alert for all agents
        for agent_name in self.registered_agents:
            await self.message_queue.put(
                alert.copy(new_recipient_id=agent_name)
            ) 