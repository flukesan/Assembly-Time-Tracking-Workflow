"""
Detection Manager
Coordinates camera capture and YOLOv8 detection
"""

import threading
import time
from typing import Dict, List, Optional
from datetime import datetime
import logging

from camera.camera_manager import CameraManager
from ai.yolo_detector import YOLODetector
from ai.detection_models import DetectionConfig, DetectionResult
from core.zones.zone_manager import ZoneManager
from core.zones.zone_detector import ZoneDetector

logger = logging.getLogger(__name__)


class DetectionManager:
    """Manages detection pipeline: Camera → YOLOv8 → Zone matching"""

    def __init__(
        self,
        camera_manager: CameraManager,
        zone_manager: ZoneManager,
        detection_config: DetectionConfig
    ):
        """
        Initialize detection manager

        Args:
            camera_manager: Camera manager instance
            zone_manager: Zone manager instance
            detection_config: YOLOv8 detection configuration
        """
        self.camera_manager = camera_manager
        self.zone_manager = zone_manager
        self.detection_config = detection_config

        # Initialize detector
        self.detector = YOLODetector(detection_config)

        # Detection threads
        self.detection_threads: Dict[int, threading.Thread] = {}
        self.running_cameras: Dict[int, bool] = {}
        self._lock = threading.Lock()

        # Callbacks
        self.detection_callbacks = []

        logger.info("DetectionManager initialized")

    def add_detection_callback(self, callback):
        """
        Add callback function to be called on each detection result

        Args:
            callback: Function with signature: callback(detection_result: DetectionResult)
        """
        self.detection_callbacks.append(callback)

    def start(self, camera_ids: Optional[List[int]] = None):
        """
        Start detection on specified cameras

        Args:
            camera_ids: List of camera IDs to start detection on (None = all cameras)
        """
        cameras = self.camera_manager.get_all_cameras()

        if camera_ids is None:
            camera_ids = list(cameras.keys())

        for camera_id in camera_ids:
            if camera_id not in cameras:
                logger.warning(f"Camera {camera_id} not found, skipping")
                continue

            self._start_camera_detection(camera_id)

        logger.info(f"Started detection on {len(camera_ids)} cameras")

    def stop(self, camera_ids: Optional[List[int]] = None):
        """
        Stop detection on specified cameras

        Args:
            camera_ids: List of camera IDs to stop detection on (None = all cameras)
        """
        with self._lock:
            if camera_ids is None:
                camera_ids = list(self.running_cameras.keys())

            for camera_id in camera_ids:
                if camera_id in self.running_cameras:
                    self.running_cameras[camera_id] = False

                if camera_id in self.detection_threads:
                    thread = self.detection_threads[camera_id]
                    if thread.is_alive():
                        thread.join(timeout=5.0)

                    del self.detection_threads[camera_id]

        logger.info(f"Stopped detection on {len(camera_ids)} cameras")

    def _start_camera_detection(self, camera_id: int):
        """Start detection thread for a camera"""
        with self._lock:
            if camera_id in self.running_cameras and self.running_cameras[camera_id]:
                logger.warning(f"Detection already running for camera {camera_id}")
                return

            self.running_cameras[camera_id] = True

            thread = threading.Thread(
                target=self._detection_loop,
                args=(camera_id,),
                daemon=True
            )
            thread.start()

            self.detection_threads[camera_id] = thread
            logger.info(f"Started detection thread for camera {camera_id}")

    def _detection_loop(self, camera_id: int):
        """
        Detection loop for a single camera (runs in separate thread)

        Args:
            camera_id: Camera ID to run detection on
        """
        logger.info(f"Detection loop started for camera {camera_id}")

        camera = self.camera_manager.get_camera(camera_id)
        if camera is None:
            logger.error(f"Camera {camera_id} not found")
            return

        frame_skip = 1  # Process every frame (adjust for performance)
        frame_counter = 0

        while self.running_cameras.get(camera_id, False):
            try:
                # Get latest frame from camera buffer
                frame_data = camera.buffer.get_latest()

                if frame_data is None:
                    time.sleep(0.01)  # Wait for frames
                    continue

                frame, timestamp = frame_data

                # Frame skipping for performance
                frame_counter += 1
                if frame_counter % frame_skip != 0:
                    continue

                # Run detection
                detection_result = self.detector.detect(frame, camera_id, timestamp)

                # Match detections to zones
                zones = self.zone_manager.get_zones_by_camera(camera_id)
                zone_matches = ZoneDetector.match_detections_to_zones(
                    detection_result.detections,
                    zones
                )

                # Add zone information to result
                result_dict = detection_result.dict()
                result_dict['zone_matches'] = {
                    zone_id: [det.dict() for det in dets]
                    for zone_id, dets in zone_matches.items()
                }

                # Call callbacks
                for callback in self.detection_callbacks:
                    try:
                        callback(result_dict)
                    except Exception as e:
                        logger.error(f"Detection callback error: {e}")

                # Log detection stats (every 100 frames)
                if frame_counter % 100 == 0:
                    logger.info(
                        f"Camera {camera_id}: {detection_result.person_count} persons, "
                        f"{detection_result.inference_time_ms:.1f}ms"
                    )

            except Exception as e:
                logger.error(f"Detection error for camera {camera_id}: {e}")
                time.sleep(1.0)

        logger.info(f"Detection loop ended for camera {camera_id}")

    def get_status(self) -> dict:
        """Get detection system status"""
        with self._lock:
            return {
                "running": len(self.running_cameras) > 0,
                "active_cameras": list(self.running_cameras.keys()),
                "detector_stats": self.detector.get_stats()
            }

    def get_stats(self) -> dict:
        """Get detection statistics"""
        return self.detector.get_stats()
