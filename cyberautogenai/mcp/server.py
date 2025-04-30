"""MCP Server implementation."""
import asyncio
import json
import logging
import sys
from typing import Dict, Set, Callable, Awaitable
from .message import Message
import uuid
from datetime import datetime
from ..utils.logger import logger

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detail
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class MCPServer:
    """Model Context Protocol Server."""
    
    def __init__(self, host: str = 'localhost', port: int = 8765):
        """Initialize MCP server."""
        self.host = host
        self.port = port
        self.clients: Dict[str, Set[asyncio.Queue]] = {}
        self.message_queue = asyncio.Queue()
        self.server = None
        self._server_task = None
        self._process_task = None
        self._running = False
        
    async def start(self):
        """Start the MCP server."""
        if self._running:
            return

        try:
            # Start the server
            self.server = await asyncio.start_server(
                self.handle_client,
                self.host,
                self.port
            )
            
            logger.info(f"MCP Server started on {self.host}:{self.port}")
            
            # Start message processing in background task
            self._process_task = asyncio.create_task(self._process_messages())
            
            # Start server in background task
            self._server_task = asyncio.create_task(self.server.serve_forever())
            
            self._running = True
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise
        
    async def _process_messages(self):
        """Process messages in the queue."""
        while True:
            message = await self.message_queue.get()
            if message.recipient in self.clients:
                for queue in self.clients[message.recipient]:
                    await queue.put(message)
            self.message_queue.task_done()
            
    async def register_client(self, client_id: str, queue: asyncio.Queue):
        """Register a new client."""
        if client_id not in self.clients:
            self.clients[client_id] = set()
        self.clients[client_id].add(queue)
        
    async def unregister_client(self, client_id: str, queue: asyncio.Queue):
        """Unregister a client."""
        if client_id in self.clients:
            self.clients[client_id].remove(queue)
            if not self.clients[client_id]:
                del self.clients[client_id]

    async def stop(self):
        """Stop the server gracefully."""
        if not self._running:
            return

        logger.info("Stopping MCP server...")
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
                
        if self._server_task:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass
            
        self._running = False
        logger.info("MCP server stopped")

    async def handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ):
        """Handle individual client connections."""
        client_id = None
        try:
            # Handle client registration
            data = await reader.readline()
            if not data:
                return
                
            raw_data = data.decode()
            logger.debug(f"Received registration data: {raw_data}")
            
            registration = json.loads(raw_data)
            client_id = registration.get("client_id")
            
            if not client_id:
                logger.error("Client registration missing client_id")
                return
                
            queue = asyncio.Queue()
            await self.register_client(client_id, queue)
            logger.info(f"Client {client_id} connected")

            # Handle incoming messages
            while True:
                try:
                    data = await reader.readline()
                    if not data:
                        break
                    
                    raw_msg = data.decode()
                    logger.debug(f"Received raw message: {raw_msg}")
                    
                    message = Message.from_json(raw_msg)
                    await self.handle_message(message)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid message format from {client_id}: {e}")
                    # Send properly formatted error JSON
                    error_msg = {
                        "message_id": str(uuid.uuid4()),
                        "sender_id": "server",
                        "recipient_id": client_id,
                        "message_type": "error",
                        "content": {
                            "error": "Invalid JSON format",
                            "details": str(e)
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    writer.write(json.dumps(error_msg).encode() + b"\n")
                    await writer.drain()
                except Exception as e:
                    logger.error(f"Error processing message from {client_id}: {e}")

        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            if client_id and client_id in self.clients:
                await self.unregister_client(client_id, queue)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                logger.error(f"Error closing connection to {client_id}: {e}")
            logger.info(f"Client {client_id} disconnected")

    async def handle_message(self, message: Message):
        """Process and route messages."""
        try:
            # Validate message
            message.validate()
            
            # Route to recipient if connected
            if message.recipient in self.clients:
                for queue in self.clients[message.recipient]:
                    await queue.put(message)
            else:
                logger.warning(f"No clients connected to recipient {message.recipient}")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            # Send error response as properly formatted JSON
            try:
                error_response = {
                    "message_id": str(uuid.uuid4()),
                    "sender_id": "server",
                    "recipient_id": message.sender,
                    "message_type": "error",
                    "content": {
                        "error": str(e),
                        "details": "Error processing message"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                json_error = json.dumps(error_response)
                logger.debug(f"Sending error response: {json_error}")
                
                if message.sender in self.clients:
                    for queue in self.clients[message.sender]:
                        await queue.put(Message(
                            id=str(uuid.uuid4()),
                            type="error",
                            content=error_response,
                            timestamp=datetime.utcnow(),
                            sender="server",
                            recipient=message.sender
                        ))
            except Exception as send_error:
                logger.error(f"Error sending error response: {send_error}")

    def register_handler(
        self,
        message_type: str,
        handler: Callable[[Message], Awaitable[None]]
    ):
        """Register a message handler."""
        # This method is not used in the new implementation
        pass

    def unregister_handler(
        self,
        message_type: str,
        handler: Callable[[Message], Awaitable[None]]
    ):
        """Unregister a message handler."""
        # This method is not used in the new implementation
        pass

async def main():
    """Main entry point for the server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    server = MCPServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        await server.stop()
    except Exception as e:
        logger.error(f"Server error: {e}")
        await server.stop()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1) 