import asyncio

from .core.client import AriaClient
from .core.streaming_handler import StreamingHandler
from .utils.logger import logger

async def main():
    """Main function to run the desktop app."""
    logger.info("Starting Project Aria Desktop App")
    
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

            if battery_level < 20:
                logger.warning("Battery level is below 20%. Please charge the device soon.")
            else :
                logger.info("Battery level is sufficient, ready to go.")

                # start streaming
                streaming_handler = StreamingHandler(device)
                streaming_handler.start_streaming()
                
            
    except Exception as e:
        logger.critical(f"An error occurred during application startup: {e}")

if __name__ == "__main__":
    asyncio.run(main())