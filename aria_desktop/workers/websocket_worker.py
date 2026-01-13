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

    def _process_image(self, image: Any) -> tuple[bool, Any]:
        # Encode image to JPEG in memory
        # We need to convert from RGB (from camera) to BGR (for cv2)
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # RESIZE: Downscale to 640px width (maintaining aspect ratio)
        # This drastically reduces USB/Network load
        height, width = image_bgr.shape[:2]
        new_width = 800
        new_height = int(height * (new_width / width))
        image_resized = cv2.resize(image_bgr, (new_width, new_height))

        # 3. Compress
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95]

        # is_success, buffer = cv2.imencode(".webp", image_resized, encode_param)
        is_success, buffer = cv2.imencode(".jpg", image_resized, encode_param)
        return is_success, buffer

    async def forward_rgb(self):
        """Forwards RGB frames to connected WebSocket clients."""
        loop = asyncio.get_event_loop()

        try:
            async for event in self.bus.subscribe("rgb_frame"):
                image_np = event.payload["image"]
                start = asyncio.get_event_loop().time()
                is_success, buffer = await loop.run_in_executor(
                    None, self._process_image, image_np
                )
                end = asyncio.get_event_loop().time()
                # logger.debug(f"Image processing took {end - start:.3f} seconds")
                if not is_success:
                    logger.warning("Failed to encode image to JPG")
                    continue
                
                image_bytes = buffer.tobytes()

                # logger.debug("Broadcasting RGB frame to WebSocket clients")
                # Send with Timeout (Prevents server from hanging if network is full)
                try:
                    asyncio.create_task(self.server.send(image_bytes))
                    # await asyncio.wait_for(asyncio.sleep(0), timeout=0
                except asyncio.TimeoutError:
                    logger.warning("Network busy, skipping frame")
        except asyncio.CancelledError:
            logger.info("WebSocket RGB forwarder shutting down.")

