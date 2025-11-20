import asyncio
import httpx
import cv2
import io


from .core.client import AriaClient
from .core.streaming_handler import StreamingHandler
from .utils.logger import logger
from .utils.config import config
from .bus import AsyncEventBus
from .workers.local_yolo import yolo_worker
from .server.server import WebSocketServer

async def main():
    """Main function to run the desktop app."""

    logger.info("Starting Project Aria Desktop App")
    evnet_bus = AsyncEventBus()

    server = WebSocketServer(evnet_bus)
    await server.start()

    

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Caught Ctrl+C at the very top. Exiting.")