from .logger import logger
from .config import config
from ..bus import AsyncEventBus,Event

import aria.sdk as aria
import asyncio
import numpy as np
from typing import Sequence

from projectaria_tools.core.sensor_data import (
    BarometerData,
    ImageDataRecord,
    MotionData,
    AudioDataRecord,
)

class StreamingObserver():
    """Streaming observer that handles incoming streaming data."""

    def __init__(self, bus: AsyncEventBus, loop: asyncio.AbstractEventLoop) -> None:
        self.rgb_counter = 0
        self.loop = loop
        self.bus = bus


    def on_image_received(self, image: np.array, record: ImageDataRecord) -> None:
        if record.camera_id == aria.CameraId.Rgb:
            self.rgb_counter += 1
            # --- Only send every Nth frame to avoid overwhelming the server ---
            if self.rgb_counter % 30 == 0: # e.g., send one frame per second
                logger.debug(f"Queueing RGB frame {self.rgb_counter} for inference")

                # Apply rotation
                image_to_send = np.rot90(image, 1, (1, 0)) # Rotate 90 degrees clockwise

                event = Event(event_type="image_received", payload={"image": image_to_send, "record": record})
                # asyncio.create_task(self.bus.publish(event))
                asyncio.run_coroutine_threadsafe(self.bus.publish(event),self. loop)

    def on_imu_received(self, samples: Sequence[MotionData], imu_idx: int) -> None:
        pass

    def on_magneto_received(self, sample: MotionData) -> None:
        pass

    def on_baro_received(self, sample: BarometerData) -> None:
        pass

    def on_audio_received(self, audio_and_record: AudioDataRecord) -> None:
        pass

    def on_streaming_client_failure(self, reason: aria.ErrorCode, message: str) -> None:
        pass


