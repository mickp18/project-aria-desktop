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

async def main():
    """Main function to run the desktop app."""
    logger.info("Starting Project Aria Desktop App")

    streaming_handler = None
    evnet_bus = AsyncEventBus()

    http_client = httpx.AsyncClient(timeout=5.0) # 5 sec timeout
    
    loop = asyncio.get_running_loop()

    # Start the worker task
    worker_task = asyncio.create_task(yolo_worker(evnet_bus, http_client))

    try:
        # Initialize the client (it will load settings from config.ini)
        client = AriaClient()
        
        # Start the pairing process
        # await client.pair()
        
        # Connect to the device
        device = await client.connect()
        
        if device:
            logger.info("Successfully connected to the Aria device.")
          
            battery_level = client.get_battery_level(device)
            logger.info(f"Battery level : {battery_level}%")

            if battery_level < config.getint('streaming', 'min_battery_level', fallback=20):
                logger.warning("Battery level is below 20%. Please charge the device soon.")
            else :
                logger.info("Battery level is sufficient, ready to go.")

                # start streaming
                streaming_handler = StreamingHandler(device, evnet_bus, loop)
                await streaming_handler.start_streaming()

        else:
            logger.error("Could not connect to device. Exiting.")

        
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Application interrupted. Shutting down...")
    except Exception as e:
        logger.critical(f"An error occurred during application startup: {e}")
    finally:
        # --- CLEAN UP WORKER AND HTTP CLIENT ---
        logger.info("Cleaning up tasks and connections...")
        if worker_task:
            worker_task.cancel()
        if http_client:
            await http_client.aclose()

        if streaming_handler:
            logger.info("Main ensuring stream is stopped.")
            # This call is synchronous and cleans up
            streaming_handler.stop_streaming() 
        logger.info("Application has shut down.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Caught Ctrl+C at the very top. Exiting.")