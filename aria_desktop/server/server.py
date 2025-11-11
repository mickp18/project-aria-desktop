import websockets
import asyncio

from typing import Set

from ..utils.logger import logger
from ..bus import AsyncEventBus, Event
from ..utils.config import config


class WebSocketServer:
    def __init__(self, bus: AsyncEventBus):
        self.bus = bus
        self.port = config.getint('websocket', 'port', fallback=8088)

        # Allow possible multiple clients connections 
        # self.connected_clients = set()
        self.connected_client = None
        
    async def handle_message(self, message: str):
        """Process incoming messages from clients."""
        logger.debug(f"Handling message: {message}")

        if message.lower() == "start":
            event = Event(event_type="start_command")
            await self.bus.publish(event)

        elif message.lower() == "stop":
            event = Event(event_type="stop_command")
            await self.bus.publish(event)
        
        else:
            logger.warning(f"Unknown message received: {message}")
        
    
    async def client_handler(self, websocket):
        logger.info("client connected")
        # self.connected_clients.add(websocket)
        self.connected_client = websocket
        try:
            async for message in websocket:
                logger.info(f"Received message: {message}")
                # handle commands from client if any
                await self.handle_message(message)


        except websockets.exceptions.ConnectionClosed:
            logger.info("client disconnected")
        finally:
            # self.connected_clients.remove(websocket)
            self.connected_client = None

    async def broadcast(self, data: bytes):
        """Sends data to connected client"""
        # We use asyncio.wait to send to all clients concurrently
        if self.connected_client:
            task = self.connected_client.send(data)
            await asyncio.wait(task)

    async def start(self):
        """Start the WebSocket server."""
        logger.info(f"Starting WebSocket server on ws://0.0.0.0:{self.port}")
        server = await websockets.serve(self.client_handler, "0.0.0.0", self.port)
        await server.wait_closed()
