"""
Thread-safe Frame Buffer for Camera Capture
Implements circular buffer with thread safety for multi-threaded access
"""

import threading
from collections import deque
from typing import Optional, Tuple
import numpy as np
from datetime import datetime


class FrameBuffer:
    """Thread-safe circular buffer for camera frames"""

    def __init__(self, maxsize: int = 30):
        """
        Initialize frame buffer

        Args:
            maxsize: Maximum number of frames to keep (default: 30 = ~1 second at 30fps)
        """
        self.maxsize = maxsize
        self._buffer = deque(maxlen=maxsize)
        self._lock = threading.Lock()
        self._dropped_frames = 0

    def put(self, frame: np.ndarray, timestamp: Optional[datetime] = None) -> bool:
        """
        Add frame to buffer

        Args:
            frame: OpenCV frame (numpy array)
            timestamp: Frame timestamp (defaults to now)

        Returns:
            True if frame added successfully
        """
        if timestamp is None:
            timestamp = datetime.now()

        with self._lock:
            if len(self._buffer) >= self.maxsize:
                self._dropped_frames += 1

            self._buffer.append({
                'frame': frame,
                'timestamp': timestamp
            })
            return True

    def get(self) -> Optional[Tuple[np.ndarray, datetime]]:
        """
        Get oldest frame from buffer (FIFO)

        Returns:
            Tuple of (frame, timestamp) or None if buffer empty
        """
        with self._lock:
            if len(self._buffer) == 0:
                return None

            item = self._buffer.popleft()
            return item['frame'], item['timestamp']

    def get_latest(self) -> Optional[Tuple[np.ndarray, datetime]]:
        """
        Get latest frame without removing it

        Returns:
            Tuple of (frame, timestamp) or None if buffer empty
        """
        with self._lock:
            if len(self._buffer) == 0:
                return None

            item = self._buffer[-1]
            return item['frame'].copy(), item['timestamp']

    def clear(self):
        """Clear all frames from buffer"""
        with self._lock:
            self._buffer.clear()

    def size(self) -> int:
        """Get current buffer size"""
        with self._lock:
            return len(self._buffer)

    def is_empty(self) -> bool:
        """Check if buffer is empty"""
        with self._lock:
            return len(self._buffer) == 0

    def get_dropped_frames(self) -> int:
        """Get number of dropped frames"""
        with self._lock:
            return self._dropped_frames

    def reset_stats(self):
        """Reset dropped frame counter"""
        with self._lock:
            self._dropped_frames = 0
