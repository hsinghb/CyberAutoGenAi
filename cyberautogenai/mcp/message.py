"""Message class for Model Context Protocol (MCP)."""
from typing import Dict, Any, Optional
import json
from datetime import datetime
import uuid
from dataclasses import dataclass


@dataclass
class Message:
    """Message class for MCP communication."""
    
    id: str
    type: str
    content: Dict[str, Any]
    timestamp: datetime
    sender: str
    recipient: str
    priority: int = 0

    @property
    def is_valid(self) -> bool:
        """Check if message is valid."""
        return all([
            self.id,
            self.type,
            self.content,
            self.timestamp,
            self.sender,
            self.recipient
        ])

    def __init__(
        self,
        sender_id: str,
        recipient_id: str,
        message_type: str,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.message_type = message_type
        self.content = content
        self.context = context or {}
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.message_id = str(uuid.uuid4())
        self.last_message_time = {}  # Track last message time per sender-recipient pair

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type,
            "content": self.content,
            "context": self.context,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

    def to_json(self) -> str:
        """Convert message to JSON string."""
        try:
            return json.dumps(self.to_dict())
        except Exception as e:
            # Ensure we never return invalid JSON
            return json.dumps({
                "message_type": "error",
                "content": {"error": f"JSON serialization error: {str(e)}"},
                "sender_id": self.sender_id,
                "recipient_id": self.recipient_id,
                "message_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat()
            })

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create a Message instance from a dictionary."""
        return cls(
            sender_id=data["sender_id"],
            recipient_id=data["recipient_id"],
            message_type=data["message_type"],
            content=data["content"],
            context=data.get("context"),
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata")
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create a Message instance from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def validate(self) -> bool:
        """Validate the message format and content."""
        # Check required fields
        required_fields = ["sender_id", "recipient_id", "message_type", "content"]
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Missing required field: {field}")

        # Validate content is not empty
        if isinstance(self.content, dict):
            if not self.content or all(not val for val in self.content.values()):
                raise ValueError("Empty message content")
        elif isinstance(self.content, str):
            if not self.content.strip():
                raise ValueError("Empty message content")
        elif self.content is None:
            raise ValueError("Message content cannot be None")

        # Rate limiting check
        sender_recipient = f"{self.sender_id}-{self.recipient_id}"
        current_time = datetime.utcnow()
        
        if sender_recipient in self.last_message_time:
            time_diff = (current_time - self.last_message_time[sender_recipient]).total_seconds()
            if time_diff < 1.0:  # Minimum 1 second between messages
                raise ValueError("Message rate limit exceeded")
        
        self.last_message_time[sender_recipient] = current_time
        return True

    def is_meaningful(self) -> bool:
        """Check if the message contains meaningful content."""
        if isinstance(self.content, dict):
            # Check if any value in the dictionary is meaningful
            return any(
                isinstance(v, str) and v.strip() or 
                isinstance(v, (dict, list)) and v
                for v in self.content.values()
            )
        elif isinstance(self.content, str):
            # Check if string content is meaningful
            return bool(self.content.strip())
        return bool(self.content)

    def create_response(
        self,
        content: Dict[str, Any],
        message_type: str = "response"
    ) -> 'Message':
        """Create a response message."""
        return Message(
            sender_id=self.recipient_id,
            recipient_id=self.sender_id,
            message_type=message_type,
            content=content,
            context=self.context,
            correlation_id=self.correlation_id,
            metadata={
                "in_response_to": self.message_id,
                "original_timestamp": self.timestamp
            }
        )

    def __str__(self) -> str:
        """String representation of the message."""
        return (f"Message(type={self.message_type}, "
                f"sender={self.sender_id}, "
                f"recipient={self.recipient_id})") 