import aria.sdk as aria
import auth
from typing import Optional
import utils.handler as handler
import sys
import asyncio
from ..utils.config import config


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

        
    async def connect(self):
        """Connect to the Aria device using the specified connection method."""
        try:
            if self.update_iptables and sys.platform.startswith("linux"):
                handler.update_iptables()
        
            if self.ip_address:
                self.device_client_config.ip_v4_address = self.ip_address

            self.device_client.set_client_config(self.device_client_config)

            device = self.device_client.connect()

        except Exception as e:
            print(f"Failed to connect to device: {e}")
            raise
        
        print(f"Connected to device: {device}")

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
            print("Existing pairing found.")

    

    async def fetch_data(self, endpoint: str):
        # Placeholder for data fetching logic
        pass

    async def start_streaming(self):
        # Placeholder for starting streaming logic
        pass

    async def stop_streaming(self):
        # Placeholder for stopping streaming logic
        pass
    
if __name__ == "__main__":
    client = AriaClient()
    asyncio.run(client.pair())
