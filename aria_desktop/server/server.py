import websockets
import asyncio

from ..utils.logger import logger
from ..bus import AsyncEventBus

PORT = 8088

logger.info(f"Starting WebSocket server on port {PORT}...")

async def hadnler(websocket, path):
    logger.info("client connected")
    async for message in websocket:
        logger.info(f"Received message: {message}")
        await websocket.send(f"Echo: {message}")


start_server = websockets.serve(handler=, "localhost", PORT)

asyncio.get_event_loop().run_until_complete(start_server)
