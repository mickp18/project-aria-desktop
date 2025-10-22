import aria.sdk as aria
from typing import Optional
import sys
import asyncio

from . import auth
from ..utils import handler
from ..utils.config import config
from ..utils.logger import logger

class AriaClient:
    def __init__(self):
        self.connection = config.get('aria', 'connection_type', fallback='wifi')
        self.ip_address = config.get('aria', 'ip_address', fallback=None)
        self.update_iptables = config.getboolean('aria', 'update_iptables', fallback=True)
        
         #  Optional: Set SDK's log level to Trace or Debug for more verbose logs. Defaults to Info
        aria.set_log_level(aria.Level.Info)
        
        # Create DeviceClient instance, setting the IP address if specified
        self.device_client = aria.DeviceClient()
        self.device_client_config = aria.DeviceClientConfig()

        
    async def connect(self) -> Optional[aria.Device]:
        """Connect to the Aria device using the specified connection method."""
        try:
            if self.update_iptables and sys.platform.startswith("linux"):
                handler.update_iptables()
        
            if self.ip_address:
                logger.info(f"Cnnecting to device at IP address: {self.ip_address}")
                self.device_client_config.ip_v4_address = self.ip_address

            self.device_client.set_client_config(self.device_client_config)

            device = self.device_client.connect()

        except Exception as e:
            logger.error(f"Failed to connect to device: {e}")
            raise
        
        logger.info(f"Connected to device: {device}")

        return device
    



    async def pair(self):
        # Placeholder for pairing logic
        print("Checking for existing pairing...")
        if not auth.AriaAuth.check():
            print("No existing pairing found. Starting pairing process...")
            auth.AriaAuth.pair()
            # check again after pairing 15 seconds
            await asyncio.sleep(15)
            if not auth.AriaAuth.check():
                raise RuntimeError("Pairing failed or was not completed.")
            print("Pairing successful.")

        else:
            logger.info("Existing pairing found.")

    def get_status(self, device: aria.Device )-> aria.DeviceStatus:
        """Retrieve the current status of the device."""
        logger.info(f"Retrieving status from device")
        status = device.status
        return status
    
    def get_battery_level(self, device: aria.Device) -> int:
        """Retrieve the battery level of the device."""
        status = self.get_status(device)
        battery_level = status.battery_level
        # logger.debug(f"Battery level: {battery_level}%")
        return battery_level

    async def fetch_data(self, endpoint: str):
        # Placeholder for data fetching logic
        pass

    async def start_streaming(self):
        # Placeholder for starting streaming logic
        pass

    async def stop_streaming(self):
        # Placeholder for stopping streaming logic
        pass
    
