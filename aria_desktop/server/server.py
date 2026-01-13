import websockets
import asyncio
import cv2
import numpy as np

from typing import Set

from ..utils.logger import logger
from ..bus import AsyncEventBus, Event
from ..utils.config import config
from ..core.client import AriaClient
from ..core.streaming_handler import StreamingHandler
from ..workers.websocket_worker import  websocket_worker as ws_worker
from ..utils.config import config


DEBUG = config.getboolean('debug', 'enabled', fallback=False)



class WebSocketServer:
    def __init__(self, bus: AsyncEventBus):
        self.bus = bus
        self.port = config.getint('websocket', 'port', fallback=8080)
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
            await client.pair()
            
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
                try:
                    await worker_task # Wait for the worker to actually cancel
                except asyncio.CancelledError:
                    pass # Expected
            if self.connected_client:
                await self.connected_client.send('{"type": "STATUS_UPDATE", "payload": {"status": "stopped", "reason": "application shutdown"}}')
    
            logger.info("Application has shut down.")

    async def _run_app_debug(self):
        """Debug version, uses pre-recorded videostream."""
        logger.debug("Starting debug version of the application.")
        
        video_path = config.get('debug', 'video_path', fallback='debug_video.mp4')
        
        # Start the worker
        _ws_worker = ws_worker(self.bus, self)
        worker_task = asyncio.create_task(_ws_worker.forward_rgb())

        try:
            video_source = cv2.VideoCapture(video_path)
            if not video_source.isOpened():
                logger.error(f"Could not open video file at {video_path}. Exiting debug mode.")
                return

            # Get video FPS to simulate real-time playback
            fps = video_source.get(cv2.CAP_PROP_FPS)
            if fps <= 0: fps = 30 # fallback default
            frame_delay = 1.0 / fps

            success, image = video_source.read()
            frame_counter = 0
            
            logger.info(f"Starting playback of {video_path} at {fps} FPS")

            while success:
                # Check if we should stop (e.g. if task cancelled)
                if self.stop.is_set():
                    break

                if frame_counter % 10 == 0: # Adjust sampling as needed
                    logger.debug(f"Queueing RGB frame {frame_counter} for inference")
                    
                    # image_to_send = np.rot90(image, 1, (1, 0))
                    event = Event(event_type="rgb_frame", payload={"image": image, "record": None})
                   
                    # Use await here effectively or create_task, but sleep is crucial below
                    await self.bus.publish(event)

                # CRITICAL: Sleep to mimic frame rate AND yield control to asyncio loop
                # This allows the worker_task to wake up and send the frame
                await asyncio.sleep(frame_delay)

                success, image = video_source.read()
                frame_counter += 1

            logger.info(f"Finished processing video frames: {frame_counter}")
            
            # Keep server alive after video ends, until externally stopped
            await asyncio.Event().wait()
            
        except asyncio.CancelledError:
            logger.info("Debug application stopped.")
        except Exception as e:
            logger.critical("An error occurred during debug application startup.", exc_info=True)
        finally:
            logger.info("Cleaning up tasks and connections...")
            if worker_task:
                worker_task.cancel()
                try:
                    await worker_task
                except asyncio.CancelledError:
                    pass
            
            if self.connected_client:
                # Use a fire-and-forget approach or short timeout for cleanup to prevent hanging
                close_msg = '{"type": "STATUS_UPDATE", "payload": {"status": "stopped", "reason": "application shutdown"}}'
                asyncio.create_task(self.connected_client.send(close_msg))
    
            logger.info("Debug application has shut down.")


    async def handle_start(self):
        """Handle start command from client."""
        # event = Event(event_type="start_command")
        # await self.bus.publish(event)

        # check if already running
        if self.task and not self.task.done():
            logger.warning("Received 'start' command, but application is already running.")
            if self.connected_client:
                # Optional: Send feedback to client
                # await self.connected_client.send('{"status": "error", "message": "Application is already running."}')
                await self.connected_client.send('{"type": "ERROR_MSG", "payload": {"error": "already running", "reason": "Application is already running, can\'t start again.""}}')
    
            return
        
        if self.connected_client:
            await self.connected_client.send('{"type": "STATUS_UPDATE", "payload": {"status": "starting"}}')
    
        
        # Create task to start main desktop app functionality
        if DEBUG:
            logger.debug("Starting application in DEBUG mode.")
            self.task = asyncio.create_task(self._run_app_debug())
        else:
            logger.info("Starting application in normal mode.")
            self.task = asyncio.create_task(self._run_app())

    async def handle_stop(self):
        """Handle stop command from client."""
        if self.task and not self.task.done():
                self.task.cancel()
                if self.connected_client:
                    await self.connected_client.send('{"type": "STATUS_UPDATE", "payload": {"status": "stopped", "reason": "stop was requested by client"}}')
    
        else:
            logger.warning("Received 'stop' command, but application is not running.")
            if self.connected_client:
                await self.connected_client.send('{"type": "ERROR_MSG", "payload": {"error": "app not running", "reason": "Received stop command, but application is not running"}}')
    

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
                await self.connected_client.send('{"type": "ERROR_MSG", "payload": {"error": "received unkown command", "reason": """}}')
    
    
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

    async def send(self, data: bytes):
        """Sends data to connected client"""
        if self.connected_client:
            try:
                await self.connected_client.send(data)
                logger.debug("sent frame to client..")
                #  asyncio.create_task(self.connected_client.send(data))
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Tried to send to a client that has disconnected.")
                self.connected_client = None # Clear the disconnected client

    async def start(self):
        """Start the WebSocket server."""
        logger.info(f"Starting WebSocket server on ws://0.0.0.0:{self.port}")
        server = await websockets.serve(self.client_handler, "0.0.0.0", self.port)
        await server.wait_closed()
