import asyncio
import cv2
import io

from websockets import WebSocketServer
from ..utils.logger import logger
from ..bus import AsyncEventBus

class websocket_worker:
    
    def __init__(self, bus: AsyncEventBus, server: WebSocketServer):
        """
        Worker that handles WebSocket connections and broadcasts messages.
        """
        logger.info("WebSocket worker started, waiting for connections...")
        self.bus = bus
        self.server = server

    async def forward_rgb(self):
        """Forwards RGB frames to connected WebSocket clients."""
        try:
            async for event in self.bus.subscribe("rgb_frame"):
                image_np = event.payload["image"]
            
                # Encode image to JPEG in memory
                # We need to convert from RGB (from camera) to BGR (for cv2)
                image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
                is_success, buffer = cv2.imencode(".jpg", image_bgr)
                if not is_success:
                    logger.warning("Failed to encode image to JPG")
                    continue
                
                image_bytes = io.BytesIO(buffer)
                await self.server.broadcast(image_bytes)
        except asyncio.CancelledError:
            logger.info("WebSocket RGB forwarder shutting down.")

