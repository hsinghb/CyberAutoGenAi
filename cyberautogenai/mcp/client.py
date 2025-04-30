"""MCP Client for agent communication."""

import asyncio
import json
import logging
from typing import Dict, Set, Callable, Awaitable, Optional
from .message import Message
import uuid
from ..utils.logger import logger
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class MCPClient:
    """Message Control Protocol Client for agent communication."""
    
    def __init__(self, client_id: Optional[str] = None):
        """Initialize MCP client."""
        self.client_id = client_id or str(uuid.uuid4())
        self.host = "localhost"
        self.port = 8765
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.message_handlers: Dict[str, Set[Callable[[Message], Awaitable[None]]]] = {}
        self.connected = False
        self._receive_task: Optional[asyncio.Task] = None
        self.message_queue = asyncio.Queue()
        logger.info(f"Initialized MCP client with ID: {self.client_id}")

    async def connect(self, max_retries=3, retry_delay=1.0):
        """Connect to MCP server with retries."""
        for attempt in range(max_retries):
            try:
                self.reader, self.writer = await asyncio.open_connection(
                    self.host, self.port
                )
                
                # Send registration
                registration = {
                    "client_id": self.client_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.writer.write(json.dumps(registration).encode() + b"\n")
                await self.writer.drain()
                
                # Start message receiving
                self._receive_task = asyncio.create_task(self._receive_messages())
                self.connected = True
                
                logger.info(f"Client {self.client_id} connected to MCP server")
                return
                
            except ConnectionRefusedError:
                if attempt < max_retries - 1:
                    logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to MCP server after all retries")
                    raise

    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.connected:
            self.connected = False
            if self._receive_task:
                self._receive_task.cancel()
                try:
                    await self._receive_task
                except asyncio.CancelledError:
                    pass
            if self.writer:
                self.writer.close()
                try:
                    await self.writer.wait_closed()
                except Exception as e:
                    logger.error(f"Error closing writer: {e}")

    async def send_message(self, message: Message):
        """Send a message to another agent through the MCP server."""
        if not self.connected:
            await self.connect()
            
        try:
            message_data = message.to_dict()
            self.writer.write(json.dumps(message_data).encode() + b"\n")
            await self.writer.drain()
            logger.debug(f"Sent message: {message_data}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    async def _receive_messages(self):
        """Handle incoming messages from the MCP server."""
        try:
            while self.connected:
                if not self.reader:
                    logger.error("Reader not initialized")
                    break
                    
                try:
                    data = await self.reader.readline()
                    if not data:
                        logger.warning("Received empty data, connection might be closed")
                        break

                    raw_msg = data.decode()
                    logger.debug(f"Received raw message: {raw_msg}")

                    msg_data = json.loads(raw_msg)
                    message = Message.from_dict(msg_data)
                    
                    # Handle the message
                    await self._handle_message(message)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON format: {e}\nRaw message: {raw_msg}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except asyncio.CancelledError:
            logger.info(f"Message receiving cancelled for client {self.client_id}")
        except Exception as e:
            logger.error(f"Error in receive loop: {str(e)}")
        finally:
            await self.disconnect()

    async def _handle_message(self, message: Message):
        """Process incoming messages using registered handlers."""
        try:
            handlers = self.message_handlers.get(message.message_type, set())
            if not handlers:
                logger.warning(f"No handlers registered for message type: {message.message_type}")
                return
                
            for handler in handlers:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")
                    
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def register_handler(self, message_type: str, 
                        handler: Callable[[Message], Awaitable[None]]):
        """Register a handler for a specific message type."""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = set()
        self.message_handlers[message_type].add(handler)

    def unregister_handler(self, message_type: str, 
                          handler: Callable[[Message], Awaitable[None]]):
        """Unregister a handler for a specific message type."""
        if message_type in self.message_handlers:
            self.message_handlers[message_type].discard(handler)

    async def receive_message(self) -> Optional[Message]:
        """Receive message from MCP server."""
        if not self.connected:
            await self.connect()
        try:
            return await self.message_queue.get()
        except asyncio.QueueEmpty:
            return None

    def generate_message_id(self) -> str:
        """Generate unique message ID."""
        return f"{self.client_id}_{str(uuid.uuid4())}" 