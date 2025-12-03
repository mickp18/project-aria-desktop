import asyncio
import cv2
from typing import Any, TYPE_CHECKING

# Avoid a runtime import of WebSocketServer to prevent circular import.
# Import only for type checking (no runtime dependency).
if TYPE_CHECKING:
    from ..server.server import WebSocketServer

from ..utils.logger import logger
from ..bus import AsyncEventBus

class websocket_worker:
    
    def __init__(self, bus: AsyncEventBus, server: Any):
        """
        Worker that handles WebSocket connections and broadcasts messages.
        """
        logger.info("WebSocket worker started, waiting for connections...")
        self.bus = bus
        # Use a forward-referenced type for annotation above; accept Any at runtime.
        self.server: Any = server

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
                
                image_bytes = buffer.tobytes()
                logger.info("Broadcasting RGB frame to WebSocket clients")
                await self.server.broadcast(image_bytes)
                logger.info("sent frame to clients")
        except asyncio.CancelledError:
            logger.info("WebSocket RGB forwarder shutting down.")

