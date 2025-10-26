import aria.sdk as aria

from ..utils import handler
from ..utils.config import config
from ..utils.logger import logger
from ..utils.visualizer import AriaVisualizer, AriaVisualizerStreamingClientObserver

class StreamingHandler:
    def __init__(self, device : aria.Device):
        self.device = device
        self.streaming_manager = self.device.streaming_manager
        self.streaming_client = self.streaming_manager.streaming_client
        self.visualizer = AriaVisualizer()
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
            raise

    def start_streaming(self):
        """Start the streaming session.Wait untill exit command to stop stream"""
        try:
            logger.info("Starting streaming session...")
            self.streaming_manager.start_streaming()
            logger.info("Streaming session started successfully.")

            # set observer
            
            observer = AriaVisualizerStreamingClientObserver(self.visualizer)
            self.streaming_client.set_streaming_client_observer(observer)

            self.streaming_client.subscribe()



            with handler.ctrl_c_handler() as ctrl:
                while not ctrl:
                    self.visualizer.render_loop()
                    # pass  # Keep streaming until Ctrl+C is pressed

            
            logger.info("exit command recognized")
            self.stop_streaming()

        except Exception as e:
            logger.error(f"Failed to start streaming: {e}")
            raise

    def get_streaming_state(self) -> aria.StreamingState:
        """Return the current streaming state."""
        logger.debug("Retrieving current streaming state")
        print(f"Streaming state: {self.streaming_manager.streaming_state}")
        return self.streaming_manager.streaming_state


    
