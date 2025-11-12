import websockets
import asyncio

from typing import Set

from ..utils.logger import logger
from ..bus import AsyncEventBus, Event
from ..utils.config import config
from ..core.client import AriaClient
from ..core.streaming_handler import StreamingHandler
from ..workers.websocket_worker import websocket_worker as ws_worker


class WebSocketServer:
    def __init__(self, bus: AsyncEventBus):
        self.bus = bus
        self.port = config.getint('websocket', 'port', fallback=8088)
        self.task : asyncio.Task | None = None
        self.stop = asyncio.Event() 
        self.connected_client = None
        
        # Allow possible multiple clients connections 
        # self.connected_clients = set()
    
    async def _run_app(self):
        """Main application logic to run the WebSocket server and handle connections."""
        _ws_worker = ws_worker(self.bus, self)
        streaming_handler = None
        
        loop = asyncio.get_running_loop()

        # Start the worker task
        worker_task = asyncio.create_task(_ws_worker.forward_rgb())

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
                    streaming_handler = StreamingHandler(device, self.bus, loop)
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
    
            if streaming_handler:
                logger.info("Main ensuring stream is stopped.")
                # This call is synchronous and cleans up
                streaming_handler.stop_streaming() 
            logger.info("Application has shut down.")

    async def handle_start(self):
        """Handle start command from client."""
        # event = Event(event_type="start_command")
        # await self.bus.publish(event)

        # check if already running
        if self.task and not self.task.done():
            logger.warning("Received 'start' command, but application is already running.")
            if self.connected_client:
                # Optional: Send feedback to client
                await self.connected_client.send('{"status": "error", "message": "Application is already running."}')
            return
        
        if self.connected_client:
            await self.connected_client.send('{"status": "starting"}')
        
        # Create task to start main desktop app functionality
        self.task = asyncio.create_task(self._run_app())

    async def handle_stop(self):
        """Handle stop command from client."""
        if self.task and not self.task.done():
                self.task.cancel()
                if self.connected_client:
                    await self.connected_client.send('{"status": "stopping"}')
            else:
                logger.warning("Received 'stop' command, but application is not running.")
                if self.connected_client:
                    await self.connected_client.send('{"status": "error", "message": "Application is not running."}')


    async def handle_message(self, message: str):
        """Process incoming messages from clients."""
        logger.debug(f"Handling message: {message}")

        if message.lower() == "start":
            logger.debug("Received start command from client")
            await self.handle_start()            
            

        elif message.lower() == "stop":
            logger.debug("Received stop command from client")
            await self.handle_stop()
                    
        else:
            logger.warning(f"Unknown message received: {message}")
            if self.connected_client:
                await self.connected_client.send('{"status": "error", "message": "No application running to stop."}')
        
    
    async def client_handler(self, websocket):
        logger.info("client connected")
        # self.connected_clients.add(websocket)
        self.connected_client = websocket
        try:
            async for message in websocket:
                logger.info(f"Received message: {message}")
                # handle commands from client if any
                await self.handle_message(message)


        except websockets.exceptions.ConnectionClosed:
            logger.info("client disconnected")
        finally:
            # self.connected_clients.remove(websocket)
            self.connected_client = None

    async def broadcast(self, data: bytes):
        """Sends data to connected client"""
        # We use asyncio.wait to send to all clients concurrently
        if self.connected_client:
            task = self.connected_client.send(data)
            await asyncio.wait(task)

    async def start(self):
        """Start the WebSocket server."""
        logger.info(f"Starting WebSocket server on ws://0.0.0.0:{self.port}")
        server = await websockets.serve(self.client_handler, "0.0.0.0", self.port)
        await server.wait_closed()
