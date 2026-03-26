import asyncio
import cv2
import numpy as np
from typing import Any, TYPE_CHECKING

# Avoid a runtime import of WebSocketServer to prevent circular import.
# Import only for type checking (no runtime dependency).
if TYPE_CHECKING:
    from ..server.server import WebSocketServer

from ..utils.logger import logger
from ..bus import AsyncEventBus
class websocket_worker:
    
    def __init__(self, bus: AsyncEventBus, server: Any):
        logger.info("WebSocket worker started, waiting for connections...")
        self.bus = bus
        self.server: Any = server
        self.sending = False
        self.last_send_time = 0.0
        self.min_send_interval = 0.05  # 80ms between sends (allows up to ~12 FPS)

    # def _process_image(self, image: Any) -> tuple[bool, Any]:
    #     image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    #     # height, width = image_bgr.shape[:2]
    #     # new_width = 1024
    #     # new_height = int(height * (new_width / width))
    #     # image_resized = cv2.resize(image_bgr, (new_width, new_height))
    #     # encode_param = [int(cv2.IMWRITE_WEBP_QUALITY), 100]
    #     # is_success, buffer = cv2.imencode(".webp", image_resized, encode_param)
    #     is_success, buffer = cv2.imencode(".jpg", image_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    #     return is_success, buffer

    def _process_image(self, image: Any) -> tuple[bool, Any]:
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # ── Exposure correction ───────────────────────────────────────────────
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        mean_brightness = float(np.mean(gray))

        if mean_brightness >= 100:
            # CLAHE on L channel — recovers local contrast on blown-out signs
            # without darkening the rest of the frame
            lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l_corrected = clahe.apply(l)
            lab_corrected = cv2.merge([l_corrected, a, b])
            image_bgr = cv2.cvtColor(lab_corrected, cv2.COLOR_LAB2BGR)

            # Extra gamma pass for severely overexposed frames
            if mean_brightness > 200:
                lut = np.array(
                    [(i / 255.0) ** 0.5 * 255 for i in range(256)],
                    dtype=np.uint8
                )
                image_bgr = cv2.LUT(image_bgr, lut)

        is_success, buffer = cv2.imencode(".jpg", image_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        return is_success, buffer


    async def forward_rgb(self):
        """Forwards RGB frames to connected WebSocket clients."""
        loop = asyncio.get_event_loop()
        frame_count = 0

        try:
            async for event in self.bus.subscribe("rgb_frame", latest_only=True):
                # Skip if no client
                if not self.server.connected_client:
                    logger.debug("No client connected, skipping")
                    continue
                
                # Skip if still sending previous frame
                if self.sending:
                    logger.debug("Still sending previous frame, skipping")
                    continue
                
                # Rate limiting
                current_time = loop.time()
                time_since_last = current_time - self.last_send_time
                # if self.last_send_time > 0 and time_since_last < self.min_send_interval or frame_count == 0:
                #     logger.debug(f"Rate limiting: {time_since_last*1000:.0f}ms since last")
                #     continue
                
                self.sending = True
                frame_start = loop.time()
                
                try:
                    image_np = event.payload["image"]
                    
                    # Encode
                    encode_start = loop.time()
                    is_success, buffer = await loop.run_in_executor(
                        None, self._process_image, image_np
                    )
                    encode_time = loop.time() - encode_start
                    
                    if not is_success:
                        logger.warning("Failed to encode image")
                        continue
                    
                    image_bytes = buffer.tobytes()
                    image_size_kb = len(image_bytes) / 1024
                    frame_count += 1
                    
                    # Send with generous timeout
                    send_start = loop.time()
                    try:
                        await asyncio.wait_for(
                            self.server.send(image_bytes),
                            timeout=2.0  # Increased to 2 seconds for stability
                        )
                        finish_time = loop.time()
                        
                        # Calculate interval from last frame
                        interval_since_last_frame = (finish_time - self.last_send_time) if self.last_send_time > 0 else 0
                        
                        # Update timestamp
                        self.last_send_time = finish_time
                        
                        send_time = finish_time - send_start
                        total_proc_time = finish_time - frame_start
                        
                        logger.info(
                            f"Frame #{frame_count}: {image_size_kb:.1f}KB | "
                            f"Encode: {encode_time*1000:.0f}ms | "
                            f"Send: {send_time*1000:.0f}ms | "
                            f"Total: {total_proc_time*1000:.0f}ms | "
                            f"Interval: {interval_since_last_frame*1000:.0f}ms"
                        )
                        
                        if send_time > 100:
                            logger.warning(f"Slow send: {send_time*1000:.0f}ms")
                            
                    except asyncio.TimeoutError:
                        logger.warning(f"Frame #{frame_count} send timeout (>2s) - dropping")
                        # Don't update last_send_time on failure
                        
                except Exception as e:
                    logger.error(f"Error processing frame: {e}", exc_info=True)
                finally:
                    self.sending = False  
                    
        except asyncio.CancelledError:
            logger.info("WebSocket RGB forwarder shutting down.")