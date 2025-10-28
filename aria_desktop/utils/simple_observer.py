import aria.sdk as aria
import cv2
from pathlib import Path


from ..utils.visualizer import BaseStreamingClientObserver
from ..utils.logger import logger

import numpy as np
from typing import Sequence
from projectaria_tools.core.sensor_data import (
    BarometerData,
    ImageDataRecord,
    MotionData,
)

class SimplePrintObserver(BaseStreamingClientObserver):
    """
    A simple observer that just logs to the console
    to prove data is being received.
    """
    def __init__(self):
        self.img_counter = 0
        self.imu_counter = 0

        # Create a directory to save frames
        self.save_path = Path("./saved_frames")
        self.save_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving frames to {self.save_path.resolve()}")

    def on_image_received(self, image: np.array, record: ImageDataRecord) -> None:
        self.img_counter += 1
        if self.img_counter % 100 == 0: # Log every 100th image
            logger.info(
                f"Received image #{self.img_counter} from {record.camera_id}"
            )
        try:
            # Apply the same rotation as the visualizer for correct orientation
            if record.camera_id != aria.CameraId.EyeTrack:
                image_to_save = np.rot90(image)
            else:
                image_to_save = np.rot90(image, 2)
            
            # Convert RGB to BGR for cv2.imwrite if it's a color image
            if image_to_save.ndim == 3 and image_to_save.shape[2] == 3:
                image_to_save = cv2.cvtColor(image_to_save, cv2.COLOR_RGB2BGR)

            # Create a unique filename
            filename = self.save_path / f"{record.camera_id}_{self.img_counter:06d}.png"
            
            # Save the image
            cv2.imwrite(str(filename), image_to_save)

        except Exception as e:
            logger.error(f"Failed to save image: {e}")


    def on_imu_received(self, samples: Sequence[MotionData], imu_idx: int) -> None:
        self.imu_counter += 1
        if self.imu_counter % 500 == 0: # Log every 500th IMU batch
            logger.info(
                f"Received IMU batch #{self.imu_counter} from IMU {imu_idx}"
            )

        
    def on_magneto_received(self, sample: MotionData) -> None:
        logger.info("Received Magnetometer data")

    def on_baro_received(self, sample: BarometerData) -> None:
        logger.info("Received Barometer data")

    def on_streaming_client_failure(self, reason: aria.ErrorCode, message: str) -> None:
        logger.error(f"Streaming Client Failure: {reason}: {message}")