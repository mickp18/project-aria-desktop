import asyncio
import httpx
import cv2
import io

from ..utils.logger import logger
from ..bus import AsyncEventBus


async def yolo_worker(bus: AsyncEventBus, client: httpx.AsyncClient):
    """
    Subscribes to the event bus and sends images to the YOLO server.
    """
    logger.info("YOLO worker started, waiting for images...")
    try:
        async for event in bus.subscribe("image_received"): #
            try:
                image_np = event.payload["image"]
                
                # Encode image to JPEG in memory
                # We need to convert from RGB (from camera) to BGR (for cv2)
                image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
                is_success, buffer = cv2.imencode(".jpg", image_bgr)
                if not is_success:
                    logger.warning("Failed to encode image to JPG")
                    continue
                
                image_bytes = io.BytesIO(buffer)
                
                # Send to YOLO server (non-blocking)
                response = await client.post(
                    "http://127.0.0.1:8008/infer/",
                    files={"file": ("image.jpg", image_bytes, "image/jpeg")}
                )
                
                if response.status_code == 200:
                    detections = response.json().get("detections", [])
                    if detections:
                        logger.info(f"--- YOLO Detections ---")
                        for det in detections:
                            logger.info(f"  > Found '{det['class_name']}' (Conf: {det['confidence']:.2f})")
                    else:
                        logger.info("No objects detected by YOLO.")
                else:
                    logger.error(f"YOLO server returned error: {response.status_code}")

            except httpx.ConnectError:
                logger.error("Could not connect to YOLO server. Is it running?")
                # Stop worker for 10s to avoid spamming
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Error in YOLO worker: {e}")
                
    except asyncio.CancelledError:
        logger.info("YOLO worker shutting down.")