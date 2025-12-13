"""
Detection Writer - Async batch writing to PostgreSQL
Writes detection results and tracking data to database
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from collections import deque
import logging

from .database import DatabaseManager
from ai.detection_models import DetectionResult
from tracking.tracking_models import TrackedObject, ZoneTransition

logger = logging.getLogger(__name__)


class DetectionWriter:
    """Asynchronous detection writer with batch processing"""

    def __init__(
        self,
        db_manager: DatabaseManager,
        batch_size: int = 100,
        flush_interval: float = 5.0
    ):
        """
        Initialize detection writer

        Args:
            db_manager: Database manager instance
            batch_size: Number of detections to batch before writing
            flush_interval: Seconds between automatic flushes
        """
        self.db_manager = db_manager
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        # Buffers
        self.detection_buffer: deque = deque(maxlen=10000)
        self.tracking_buffer: deque = deque(maxlen=10000)
        self.transition_buffer: deque = deque(maxlen=1000)

        # Stats
        self.total_detections_written = 0
        self.total_tracks_written = 0
        self.total_transitions_written = 0

        # Background task
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info(f"DetectionWriter initialized (batch={batch_size}, interval={flush_interval}s)")

    async def start(self):
        """Start background flush task"""
        if self._running:
            logger.warning("DetectionWriter already running")
            return

        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info("DetectionWriter started")

    async def stop(self):
        """Stop background task and flush remaining data"""
        if not self._running:
            return

        self._running = False

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self.flush()
        logger.info("DetectionWriter stopped")

    async def _flush_loop(self):
        """Background flush loop"""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self.flush()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in flush loop: {e}")

    def add_detection(
        self,
        camera_id: int,
        timestamp: datetime,
        class_name: str,
        confidence: float,
        bbox: List[float],
        zone_id: Optional[int] = None,
        track_id: Optional[int] = None
    ):
        """
        Add detection to buffer

        Args:
            camera_id: Camera ID
            timestamp: Detection timestamp
            class_name: Detected class name
            confidence: Confidence score
            bbox: Bounding box [x1, y1, x2, y2]
            zone_id: Zone ID (if in zone)
            track_id: Track ID (if tracked)
        """
        self.detection_buffer.append({
            'camera_id': camera_id,
            'timestamp': timestamp,
            'class_name': class_name,
            'confidence': confidence,
            'bbox_x1': bbox[0],
            'bbox_y1': bbox[1],
            'bbox_x2': bbox[2],
            'bbox_y2': bbox[3],
            'zone_id': zone_id,
            'track_id': track_id
        })

        # Auto-flush if buffer full
        if len(self.detection_buffer) >= self.batch_size:
            asyncio.create_task(self.flush_detections())

    def add_tracked_object(self, tracked_obj: TrackedObject):
        """
        Add tracked object to buffer

        Args:
            tracked_obj: TrackedObject instance
        """
        self.tracking_buffer.append({
            'track_id': tracked_obj.track_id,
            'camera_id': tracked_obj.camera_id,
            'class_name': tracked_obj.class_name,
            'confidence': tracked_obj.confidence,
            'bbox_x1': tracked_obj.bbox[0],
            'bbox_y1': tracked_obj.bbox[1],
            'bbox_x2': tracked_obj.bbox[2],
            'bbox_y2': tracked_obj.bbox[3],
            'zone_id': tracked_obj.zone_id,
            'status': tracked_obj.status.value,
            'age': tracked_obj.age,
            'last_seen': tracked_obj.last_seen
        })

        # Auto-flush if buffer full
        if len(self.tracking_buffer) >= self.batch_size:
            asyncio.create_task(self.flush_tracks())

    def add_zone_transition(self, transition: ZoneTransition):
        """
        Add zone transition event to buffer

        Args:
            transition: ZoneTransition instance
        """
        self.transition_buffer.append({
            'track_id': transition.track_id,
            'camera_id': transition.camera_id,
            'from_zone_id': transition.from_zone_id,
            'to_zone_id': transition.to_zone_id,
            'transition_time': transition.transition_time,
            'duration_in_prev_zone': transition.duration_in_prev_zone
        })

        # Auto-flush if buffer full
        if len(self.transition_buffer) >= self.batch_size:
            asyncio.create_task(self.flush_transitions())

    async def flush(self):
        """Flush all buffers"""
        await asyncio.gather(
            self.flush_detections(),
            self.flush_tracks(),
            self.flush_transitions()
        )

    async def flush_detections(self):
        """Flush detection buffer to database"""
        if len(self.detection_buffer) == 0:
            return

        # Get all items from buffer
        items = []
        while len(self.detection_buffer) > 0:
            items.append(self.detection_buffer.popleft())

        if len(items) == 0:
            return

        try:
            # Batch insert
            query = """
                INSERT INTO detections (
                    camera_id, timestamp, class_name, confidence,
                    bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                    zone_id, track_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """

            args_list = [
                (
                    item['camera_id'],
                    item['timestamp'],
                    item['class_name'],
                    item['confidence'],
                    item['bbox_x1'],
                    item['bbox_y1'],
                    item['bbox_x2'],
                    item['bbox_y2'],
                    item['zone_id'],
                    item['track_id']
                )
                for item in items
            ]

            await self.db_manager.executemany(query, args_list)

            self.total_detections_written += len(items)
            logger.debug(f"Wrote {len(items)} detections to database")

        except Exception as e:
            logger.error(f"Error writing detections: {e}")
            # Put items back in buffer
            for item in reversed(items):
                self.detection_buffer.appendleft(item)

    async def flush_tracks(self):
        """Flush tracking buffer to database"""
        if len(self.tracking_buffer) == 0:
            return

        items = []
        while len(self.tracking_buffer) > 0:
            items.append(self.tracking_buffer.popleft())

        if len(items) == 0:
            return

        try:
            # Batch insert/update tracking data
            query = """
                INSERT INTO tracked_objects (
                    track_id, camera_id, class_name, confidence,
                    bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                    zone_id, status, age, last_seen
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (track_id, camera_id) DO UPDATE SET
                    confidence = EXCLUDED.confidence,
                    bbox_x1 = EXCLUDED.bbox_x1,
                    bbox_y1 = EXCLUDED.bbox_y1,
                    bbox_x2 = EXCLUDED.bbox_x2,
                    bbox_y2 = EXCLUDED.bbox_y2,
                    zone_id = EXCLUDED.zone_id,
                    status = EXCLUDED.status,
                    age = EXCLUDED.age,
                    last_seen = EXCLUDED.last_seen
            """

            args_list = [
                (
                    item['track_id'],
                    item['camera_id'],
                    item['class_name'],
                    item['confidence'],
                    item['bbox_x1'],
                    item['bbox_y1'],
                    item['bbox_x2'],
                    item['bbox_y2'],
                    item['zone_id'],
                    item['status'],
                    item['age'],
                    item['last_seen']
                )
                for item in items
            ]

            await self.db_manager.executemany(query, args_list)

            self.total_tracks_written += len(items)
            logger.debug(f"Wrote {len(items)} tracks to database")

        except Exception as e:
            logger.error(f"Error writing tracks: {e}")
            for item in reversed(items):
                self.tracking_buffer.appendleft(item)

    async def flush_transitions(self):
        """Flush zone transition buffer to database"""
        if len(self.transition_buffer) == 0:
            return

        items = []
        while len(self.transition_buffer) > 0:
            items.append(self.transition_buffer.popleft())

        if len(items) == 0:
            return

        try:
            query = """
                INSERT INTO zone_transitions (
                    track_id, camera_id, from_zone_id, to_zone_id,
                    transition_time, duration_in_prev_zone
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """

            args_list = [
                (
                    item['track_id'],
                    item['camera_id'],
                    item['from_zone_id'],
                    item['to_zone_id'],
                    item['transition_time'],
                    item['duration_in_prev_zone']
                )
                for item in items
            ]

            await self.db_manager.executemany(query, args_list)

            self.total_transitions_written += len(items)
            logger.debug(f"Wrote {len(items)} zone transitions to database")

        except Exception as e:
            logger.error(f"Error writing transitions: {e}")
            for item in reversed(items):
                self.transition_buffer.appendleft(item)

    def get_stats(self) -> Dict:
        """Get writer statistics"""
        return {
            'total_detections_written': self.total_detections_written,
            'total_tracks_written': self.total_tracks_written,
            'total_transitions_written': self.total_transitions_written,
            'detection_buffer_size': len(self.detection_buffer),
            'tracking_buffer_size': len(self.tracking_buffer),
            'transition_buffer_size': len(self.transition_buffer)
        }
