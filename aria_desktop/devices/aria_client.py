import aria.sdk as aria
import aria_auth as auth


class AriaClient:
    def __init__(self, connection: str = "wifi"):
        self.connection = connection

    async def pair(self):
        # Placeholder for pairing logic
        print("Checking for existing pairing...")
        if not auth.AriaAuth.check():
            print("No existing pairing found. Starting pairing process...")
            auth.AriaAuth.pair()
            # check again after pairing 30 seconds
            await asyncio.sleep(30)
            if not auth.AriaAuth.check():
                raise RuntimeError("Pairing failed or was not completed.")
            print("Pairing successful.")

        else:
            print("Existing pairing found.")

    async def fetch_data(self, endpoint: str):
        # Placeholder for data fetching logic
        pass

    async def start_steaming(self):
        # Placeholder for starting streaming logic
        pass

    async def stop_streaming(self):
        # Placeholder for stopping streaming logic
        pass
    
if __name__ == "__main__":
    import asyncio

    client = AriaClient()
    asyncio.run(client.pair())
