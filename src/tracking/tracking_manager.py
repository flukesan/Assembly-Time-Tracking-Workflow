"""
Tracking Manager - Coordinates multi-camera tracking
"""

import threading
import time
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict
import logging

from tracking.bytetrack import ByteTracker, Track
from tracking.tracking_models import TrackedObject, ZoneTransition, TrackStatus
from ai.detection_models import Detection
from core.zones.zone_manager import ZoneManager
from core.zones.zone_detector import ZoneDetector

logger = logging.getLogger(__name__)


class TrackingManager:
    """Manages multi-camera object tracking with ByteTrack"""

    def __init__(
        self,
        zone_manager: ZoneManager,
        track_thresh: float = 0.5,
        track_buffer: int = 30,
        match_thresh: float = 0.8,
        frame_rate: int = 30
    ):
        """
        Initialize tracking manager

        Args:
            zone_manager: Zone manager instance
            track_thresh: Detection confidence threshold
            track_buffer: Frames to keep lost tracks
            match_thresh: IoU matching threshold
            frame_rate: Video frame rate
        """
        self.zone_manager = zone_manager

        # One tracker per camera
        self.trackers: Dict[int, ByteTracker] = {}

        # Tracker config
        self.track_thresh = track_thresh
        self.track_buffer = track_buffer
        self.match_thresh = match_thresh
        self.frame_rate = frame_rate

        # Track zone history (for transition detection)
        self.track_zones: Dict[int, Dict[int, Optional[int]]] = defaultdict(dict)  # camera_id -> track_id -> zone_id
        self.track_zone_times: Dict[int, Dict[int, datetime]] = defaultdict(dict)  # camera_id -> track_id -> entry_time

        # Callbacks
        self.tracking_callbacks = []
        self.transition_callbacks = []

        self._lock = threading.Lock()

        logger.info(f"TrackingManager initialized (thresh={track_thresh}, buffer={track_buffer})")

    def add_camera(self, camera_id: int):
        """
        Add tracker for a camera

        Args:
            camera_id: Camera ID
        """
        with self._lock:
            if camera_id in self.trackers:
                logger.warning(f"Tracker for camera {camera_id} already exists")
                return

            self.trackers[camera_id] = ByteTracker(
                track_thresh=self.track_thresh,
                track_buffer=self.track_buffer,
                match_thresh=self.match_thresh,
                frame_rate=self.frame_rate
            )

            logger.info(f"Added tracker for camera {camera_id}")

    def remove_camera(self, camera_id: int):
        """Remove tracker for a camera"""
        with self._lock:
            if camera_id in self.trackers:
                del self.trackers[camera_id]
                logger.info(f"Removed tracker for camera {camera_id}")

    def update(
        self,
        camera_id: int,
        detections: List[Detection],
        timestamp: datetime
    ) -> List[TrackedObject]:
        """
        Update tracker with new detections

        Args:
            camera_id: Camera ID
            detections: List of Detection objects
            timestamp: Frame timestamp

        Returns:
            List of TrackedObject instances
        """
        # Get or create tracker
        with self._lock:
            if camera_id not in self.trackers:
                self.add_camera(camera_id)

            tracker = self.trackers[camera_id]

        # Update tracker
        tracks = tracker.update(detections)

        # Convert to TrackedObject and detect zones
        tracked_objects = []
        zones = self.zone_manager.get_zones_by_camera(camera_id)

        for track in tracks:
            # Get zone for this track
            center_x = (track.bbox[0] + track.bbox[2]) / 2
            center_y = (track.bbox[1] + track.bbox[3]) / 2

            current_zone = None
            for zone in zones:
                if ZoneDetector.point_in_polygon_cv2((center_x, center_y), zone.polygon_coords):
                    current_zone = zone
                    break

            # Check for zone transition
            prev_zone_id = self.track_zones[camera_id].get(track.track_id)
            current_zone_id = current_zone.zone_id if current_zone else None

            if prev_zone_id != current_zone_id:
                # Zone transition detected
                transition = self._create_transition(
                    camera_id=camera_id,
                    track_id=track.track_id,
                    from_zone_id=prev_zone_id,
                    to_zone_id=current_zone_id,
                    timestamp=timestamp
                )

                # Call transition callbacks
                for callback in self.transition_callbacks:
                    try:
                        callback(transition)
                    except Exception as e:
                        logger.error(f"Transition callback error: {e}")

                # Update zone history
                self.track_zones[camera_id][track.track_id] = current_zone_id
                self.track_zone_times[camera_id][track.track_id] = timestamp

            # Create TrackedObject
            tracked_obj = TrackedObject(
                track_id=track.track_id,
                camera_id=camera_id,
                class_id=track.class_id,
                class_name="person",  # Assuming person detection
                bbox=[float(track.bbox[0]), float(track.bbox[1]), float(track.bbox[2]), float(track.bbox[3])],
                confidence=float(track.score),
                status=self._get_track_status(track),
                frame_id=tracker.frame_id,
                age=track.tracklet_len,
                center_x=center_x,
                center_y=center_y,
                zone_id=current_zone.zone_id if current_zone else None,
                zone_name=current_zone.name if current_zone else None,
                first_seen=timestamp,  # Approximation
                last_seen=timestamp
            )

            tracked_objects.append(tracked_obj)

            # Call tracking callbacks
            for callback in self.tracking_callbacks:
                try:
                    callback(tracked_obj)
                except Exception as e:
                    logger.error(f"Tracking callback error: {e}")

        return tracked_objects

    def _create_transition(
        self,
        camera_id: int,
        track_id: int,
        from_zone_id: Optional[int],
        to_zone_id: Optional[int],
        timestamp: datetime
    ) -> ZoneTransition:
        """Create zone transition event"""
        # Calculate duration in previous zone
        duration = None
        if from_zone_id is not None and track_id in self.track_zone_times[camera_id]:
            entry_time = self.track_zone_times[camera_id][track_id]
            duration = (timestamp - entry_time).total_seconds()

        # Get zone names
        from_zone_name = None
        to_zone_name = None

        if from_zone_id is not None:
            from_zone = self.zone_manager.get_zone(from_zone_id)
            if from_zone:
                from_zone_name = from_zone.name

        if to_zone_id is not None:
            to_zone = self.zone_manager.get_zone(to_zone_id)
            if to_zone:
                to_zone_name = to_zone.name

        return ZoneTransition(
            track_id=track_id,
            camera_id=camera_id,
            from_zone_id=from_zone_id,
            from_zone_name=from_zone_name,
            to_zone_id=to_zone_id,
            to_zone_name=to_zone_name,
            transition_time=timestamp,
            duration_in_prev_zone=duration
        )

    def _get_track_status(self, track: Track) -> TrackStatus:
        """Convert ByteTrack status to TrackStatus"""
        if track.state == 1:  # TrackState.Tracked
            return TrackStatus.ACTIVE
        elif track.state == 2:  # TrackState.Lost
            return TrackStatus.LOST
        else:
            return TrackStatus.FINISHED

    def add_tracking_callback(self, callback):
        """Add callback for tracking events"""
        self.tracking_callbacks.append(callback)

    def add_transition_callback(self, callback):
        """Add callback for zone transition events"""
        self.transition_callbacks.append(callback)

    def reset_camera(self, camera_id: int):
        """Reset tracker for a camera"""
        with self._lock:
            if camera_id in self.trackers:
                self.trackers[camera_id].reset()
                self.track_zones[camera_id].clear()
                self.track_zone_times[camera_id].clear()
                logger.info(f"Reset tracker for camera {camera_id}")

    def reset_all(self):
        """Reset all trackers"""
        with self._lock:
            for camera_id in self.trackers:
                self.trackers[camera_id].reset()

            self.track_zones.clear()
            self.track_zone_times.clear()
            logger.info("Reset all trackers")

    def get_active_tracks(self, camera_id: Optional[int] = None) -> Dict[int, int]:
        """
        Get active track counts

        Args:
            camera_id: Filter by camera ID (None = all cameras)

        Returns:
            Dictionary of camera_id -> active_track_count
        """
        with self._lock:
            if camera_id is not None:
                if camera_id in self.trackers:
                    return {camera_id: len(self.trackers[camera_id].tracked_tracks)}
                else:
                    return {camera_id: 0}
            else:
                return {
                    cid: len(tracker.tracked_tracks)
                    for cid, tracker in self.trackers.items()
                }

    def get_stats(self) -> Dict:
        """Get tracking statistics"""
        with self._lock:
            stats = {
                'total_cameras': len(self.trackers),
                'cameras': {}
            }

            for camera_id, tracker in self.trackers.items():
                stats['cameras'][camera_id] = {
                    'active_tracks': len(tracker.tracked_tracks),
                    'lost_tracks': len(tracker.lost_tracks),
                    'frame_id': tracker.frame_id
                }

            return stats
