import aria.sdk as aria
import asyncio

from ..utils import handler
from ..utils.config import config
from ..utils.logger import logger
from ..utils.observer import StreamingObserver
from ..bus import AsyncEventBus


class StreamingHandler:
    def __init__(self, device : aria.Device, event_bus: AsyncEventBus):
        self.device = device
        self.streaming_manager = self.device.streaming_manager
        self.streaming_client = self.streaming_manager.streaming_client
        self.event_bus = event_bus

        # Configure streaming settings
        streaming_config = aria.StreamingConfig()
        logger.info("Configuring streaming settings")
        
        profile_name = config.get('streaming', 'profile_name', fallback='profile8')
        logger.debug(f"Using streaming profile: {profile_name}")
        
        # check for usb streaming interface set
        if config.get('streaming', 'streaming_interface', fallback='wifi') == 'usb':
            logger.debug("Setting streaming interface to USB")
            streaming_config.streaming_interface = aria.StreamingInterface.Usb

        streaming_config.profile_name = profile_name
        
        streaming_interface = config.get('streaming', 'streaming_interface', fallback='wifi')
        logger.debug(f"Using streaming interface: {streaming_interface}")   

        if streaming_interface == 'usb':
            streaming_config.streaming_interface = aria.StreamingInterface.Usb
       
        #    Use ephemeral streaming certificates
        streaming_config.security_options.use_ephemeral_certs = True
        
        self.streaming_manager.streaming_config = streaming_config


    def get_streaming_manager(self) -> aria.StreamingManager:
        """Return the streaming manager instance."""
        return self.streaming_manager
    
    def get_streaming_client(self) -> str:
        """Return the streaming client instance."""
        return self.streaming_client
    
    
    def stop_streaming(self):
        """Stop the streaming session."""
        try:
            logger.info("Unsubscribing from stream")
            self.streaming_client.unsubscribe()
            logger.info("Successfully unsubscribed from streaming")

            logger.info("Stopping streaming session...")
            self.streaming_manager.stop_streaming()
            logger.info("Streaming session stopped successfully.")


        except Exception as e:
            logger.error(f"Failed to stop streaming: {e}")
            # raise

    async def start_streaming(self):
        """Start the streaming session.Wait untill exit command to stop stream"""
        try:
            logger.info("Starting streaming session...")
            self.streaming_manager.start_streaming()
            logger.info("Streaming session started successfully.")

            # set observer
          
            observer = StreamingObserver(bus=self.event_bus)
            self.streaming_client.set_streaming_client_observer(observer)

            self.streaming_client.subscribe()
            logger.info("Subscribed to streaming data successfully.")
         

            logger.info("Streaming data... Press Ctrl+C to stop.")
           

            # This will wait forever until the task is cancelled (by Ctrl+C)
            await asyncio.Event().wait()

        except (asyncio.CancelledError, KeyboardInterrupt):
            logger.info("Stop signal received.")
        except Exception as e:
            logger.error(f"Failed to start streaming: {e}")
        finally:
            # Ensure we always stop the stream on exit
            logger.info("Cleaning up and stopping stream...")
            self.stop_streaming()

    def get_streaming_state(self) -> aria.StreamingState:
        """Return the current streaming state."""
        logger.debug("Retrieving current streaming state")
        print(f"Streaming state: {self.streaming_manager.streaming_state}")
        return self.streaming_manager.streaming_state


    
