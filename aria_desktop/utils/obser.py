from utils.logger import logger
from utils.config import config
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

    def __init__(self, bus: AsyncEventBus):
        self.bus = bus


    def on_image_received(self, image: np.array, record: ImageDataRecord) -> None:
        event = Event(event_type="image_received", payload={"image": image, "record": record})
        asyncio.create_task(self.bus.publish(event))

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


