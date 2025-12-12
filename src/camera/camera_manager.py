"""
Camera Manager - RTSP Stream Management
Handles camera lifecycle, capture threads, and frame distribution
"""

import cv2
import threading
import time
from typing import Dict, Optional, Callable
from datetime import datetime
import logging

from .frame_buffer import FrameBuffer
from .camera_config import CameraConfig, CameraStatus

logger = logging.getLogger(__name__)


class CameraCapture:
    """Single camera capture thread"""

    def __init__(self, config: CameraConfig, frame_callback: Optional[Callable] = None):
        """
        Initialize camera capture

        Args:
            config: Camera configuration
            frame_callback: Optional callback function(camera_id, frame, timestamp)
        """
        self.config = config
        self.frame_callback = frame_callback

        self.buffer = FrameBuffer(maxsize=config.frame_buffer_size)
        self.cap: Optional[cv2.VideoCapture] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False

        # Statistics
        self.frames_captured = 0
        self.start_time: Optional[datetime] = None
        self.last_frame_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.reconnect_attempts = 0

    def start(self) -> bool:
        """Start camera capture thread"""
        if self.running:
            logger.warning(f"Camera {self.config.camera_id} already running")
            return False

        self.running = True
        self.start_time = datetime.now()
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

        logger.info(f"Started camera {self.config.camera_id}: {self.config.name}")
        return True

    def stop(self):
        """Stop camera capture thread"""
        self.running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)

        if self.cap:
            self.cap.release()
            self.cap = None

        logger.info(f"Stopped camera {self.config.camera_id}: {self.config.name}")

    def _connect(self) -> bool:
        """Connect to RTSP stream"""
        try:
            logger.info(f"Connecting to camera {self.config.camera_id}: {self.config.rtsp_url}")

            self.cap = cv2.VideoCapture(self.config.rtsp_url)

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.resolution_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.resolution_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)

            # Test connection
            if not self.cap.isOpened():
                raise Exception("Failed to open RTSP stream")

            ret, frame = self.cap.read()
            if not ret or frame is None:
                raise Exception("Failed to read first frame")

            logger.info(f"Camera {self.config.camera_id} connected successfully")
            self.error_message = None
            self.reconnect_attempts = 0
            return True

        except Exception as e:
            self.error_message = str(e)
            logger.error(f"Camera {self.config.camera_id} connection failed: {e}")

            if self.cap:
                self.cap.release()
                self.cap = None

            return False

    def _capture_loop(self):
        """Main capture loop (runs in separate thread)"""
        while self.running:
            # Connect if not connected
            if self.cap is None or not self.cap.isOpened():
                if not self._connect():
                    self.reconnect_attempts += 1

                    if self.reconnect_attempts >= self.config.max_reconnect_attempts:
                        logger.error(f"Camera {self.config.camera_id} max reconnect attempts reached")
                        break

                    logger.info(f"Camera {self.config.camera_id} reconnecting in {self.config.reconnect_delay}s...")
                    time.sleep(self.config.reconnect_delay)
                    continue

            # Read frame
            try:
                ret, frame = self.cap.read()

                if not ret or frame is None:
                    logger.warning(f"Camera {self.config.camera_id} failed to read frame")
                    self.cap.release()
                    self.cap = None
                    continue

                # Apply rotation if needed
                if self.config.rotation == 90:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                elif self.config.rotation == 180:
                    frame = cv2.rotate(frame, cv2.ROTATE_180)
                elif self.config.rotation == 270:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

                timestamp = datetime.now()

                # Store in buffer
                self.buffer.put(frame, timestamp)

                # Call callback if provided
                if self.frame_callback:
                    try:
                        self.frame_callback(self.config.camera_id, frame, timestamp)
                    except Exception as e:
                        logger.error(f"Frame callback error for camera {self.config.camera_id}: {e}")

                # Update statistics
                self.frames_captured += 1
                self.last_frame_time = timestamp

                # Frame rate limiting (if needed)
                time.sleep(1.0 / self.config.fps / 2)  # Sleep for half frame interval

            except Exception as e:
                logger.error(f"Camera {self.config.camera_id} capture error: {e}")
                self.error_message = str(e)
                time.sleep(1.0)

    def get_status(self) -> CameraStatus:
        """Get current camera status"""
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()

        fps_actual = 0.0
        if uptime > 0:
            fps_actual = self.frames_captured / uptime

        # Determine status
        if not self.running:
            status = "inactive"
        elif self.error_message:
            status = "error"
        elif self.reconnect_attempts > 0:
            status = "reconnecting"
        else:
            status = "active"

        return CameraStatus(
            camera_id=self.config.camera_id,
            name=self.config.name,
            status=status,
            fps_actual=round(fps_actual, 2),
            frames_captured=self.frames_captured,
            frames_dropped=self.buffer.get_dropped_frames(),
            last_frame_time=self.last_frame_time,
            error_message=self.error_message,
            uptime_seconds=round(uptime, 2)
        )


class CameraManager:
    """Manages multiple camera captures"""

    def __init__(self):
        self.cameras: Dict[int, CameraCapture] = {}
        self._lock = threading.Lock()
        logger.info("CameraManager initialized")

    def add_camera(self, config: CameraConfig, frame_callback: Optional[Callable] = None) -> bool:
        """
        Add and start a camera

        Args:
            config: Camera configuration
            frame_callback: Optional callback for each frame

        Returns:
            True if camera added successfully
        """
        with self._lock:
            if config.camera_id in self.cameras:
                logger.warning(f"Camera {config.camera_id} already exists")
                return False

            camera = CameraCapture(config, frame_callback)
            self.cameras[config.camera_id] = camera

            return camera.start()

    def remove_camera(self, camera_id: int) -> bool:
        """Remove and stop a camera"""
        with self._lock:
            if camera_id not in self.cameras:
                logger.warning(f"Camera {camera_id} not found")
                return False

            camera = self.cameras[camera_id]
            camera.stop()
            del self.cameras[camera_id]

            logger.info(f"Removed camera {camera_id}")
            return True

    def get_camera(self, camera_id: int) -> Optional[CameraCapture]:
        """Get camera by ID"""
        with self._lock:
            return self.cameras.get(camera_id)

    def get_all_cameras(self) -> Dict[int, CameraCapture]:
        """Get all cameras"""
        with self._lock:
            return self.cameras.copy()

    def get_status(self, camera_id: int) -> Optional[CameraStatus]:
        """Get camera status"""
        camera = self.get_camera(camera_id)
        if camera:
            return camera.get_status()
        return None

    def get_all_status(self) -> Dict[int, CameraStatus]:
        """Get status of all cameras"""
        with self._lock:
            return {
                camera_id: camera.get_status()
                for camera_id, camera in self.cameras.items()
            }

    def stop_all(self):
        """Stop all cameras"""
        with self._lock:
            for camera in self.cameras.values():
                camera.stop()

            self.cameras.clear()
            logger.info("Stopped all cameras")
