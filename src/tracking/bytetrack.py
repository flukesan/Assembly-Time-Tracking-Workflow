"""
ByteTrack Tracker - Simple and Fast Multi-Object Tracking
Based on: https://github.com/ifzhang/ByteTrack
"""

import numpy as np
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict
import logging

from .kalman_filter import KalmanFilter
from ai.detection_models import Detection

logger = logging.getLogger(__name__)


@dataclass
class TrackState:
    """Track state enumeration"""
    New: int = 0
    Tracked: int = 1
    Lost: int = 2
    Removed: int = 3


@dataclass
class Track:
    """Single object track"""
    track_id: int
    bbox: np.ndarray  # [x1, y1, x2, y2]
    score: float
    class_id: int
    state: int = TrackState.Tracked
    is_activated: bool = False
    frame_id: int = 0
    tracklet_len: int = 0
    start_frame: int = 0

    # Kalman filter
    kalman_filter: Optional[KalmanFilter] = None
    mean: Optional[np.ndarray] = None
    covariance: Optional[np.ndarray] = None

    # History
    history: List[np.ndarray] = field(default_factory=list)

    def __post_init__(self):
        """Initialize Kalman filter"""
        if self.kalman_filter is None:
            self.kalman_filter = KalmanFilter()

    def activate(self, frame_id: int):
        """Activate new track"""
        self.track_id = self.next_id()
        self.tracklet_len = 0
        self.state = TrackState.Tracked
        self.is_activated = True
        self.frame_id = frame_id
        self.start_frame = frame_id

        # Initialize Kalman filter
        xyxy = self.bbox
        self.mean, self.covariance = self.kalman_filter.initiate(
            self._xyxy_to_xyah(xyxy)
        )

    def re_activate(self, new_track: 'Track', frame_id: int, new_id: bool = False):
        """Re-activate lost track"""
        self.mean, self.covariance = self.kalman_filter.update(
            self.mean, self.covariance, self._xyxy_to_xyah(new_track.bbox)
        )

        self.tracklet_len = 0
        self.state = TrackState.Tracked
        self.is_activated = True
        self.frame_id = frame_id

        if new_id:
            self.track_id = self.next_id()

        self.score = new_track.score

    def update(self, new_track: 'Track', frame_id: int):
        """Update track with new detection"""
        self.frame_id = frame_id
        self.tracklet_len += 1

        # Update Kalman filter
        self.mean, self.covariance = self.kalman_filter.update(
            self.mean, self.covariance, self._xyxy_to_xyah(new_track.bbox)
        )

        self.state = TrackState.Tracked
        self.is_activated = True

        self.score = new_track.score
        self.bbox = new_track.bbox

        # Add to history
        self.history.append(self.bbox.copy())

    def predict(self):
        """Predict next position using Kalman filter"""
        if self.state != TrackState.Tracked:
            self.mean[7] = 0  # Set velocity to 0

        self.mean, self.covariance = self.kalman_filter.predict(
            self.mean, self.covariance
        )

    def mark_lost(self):
        """Mark track as lost"""
        self.state = TrackState.Lost

    def mark_removed(self):
        """Mark track as removed"""
        self.state = TrackState.Removed

    @property
    def tlwh(self) -> np.ndarray:
        """Get bbox in (top left x, top left y, width, height) format"""
        if self.mean is None:
            ret = self.bbox.copy()
            ret[2:] = ret[2:] - ret[:2]  # Convert to width, height
            return ret

        ret = self.mean[:4].copy()
        ret[2] *= ret[3]
        ret[:2] -= ret[2:] / 2
        return ret

    @property
    def tlbr(self) -> np.ndarray:
        """Get bbox in (top left x, top left y, bottom right x, bottom right y) format"""
        ret = self.tlwh.copy()
        ret[2:] += ret[:2]
        return ret

    @staticmethod
    def _xyxy_to_xyah(bbox: np.ndarray) -> np.ndarray:
        """
        Convert bbox from (x1, y1, x2, y2) to (center_x, center_y, aspect_ratio, height)

        Args:
            bbox: [x1, y1, x2, y2]

        Returns:
            [center_x, center_y, aspect_ratio, height]
        """
        x1, y1, x2, y2 = bbox
        w = x2 - x1
        h = y2 - y1
        cx = x1 + w / 2
        cy = y1 + h / 2
        aspect_ratio = w / h if h > 0 else 1.0
        return np.array([cx, cy, aspect_ratio, h])

    @staticmethod
    def next_id():
        """Get next track ID (global counter)"""
        Track._count += 1
        return Track._count


# Global track ID counter
Track._count = 0


class ByteTracker:
    """
    ByteTrack: Simple, Online and Realtime Tracking

    Key features:
    - Fast: No deep feature extraction needed
    - Accurate: Two-stage association (high + low confidence)
    - Simple: Only uses IoU and Kalman filter
    """

    def __init__(
        self,
        track_thresh: float = 0.5,
        track_buffer: int = 30,
        match_thresh: float = 0.8,
        frame_rate: int = 30
    ):
        """
        Initialize ByteTrack

        Args:
            track_thresh: Detection confidence threshold for track initialization
            track_buffer: Number of frames to keep lost tracks
            match_thresh: IoU threshold for matching
            frame_rate: Video frame rate
        """
        self.track_thresh = track_thresh
        self.track_buffer = track_buffer
        self.match_thresh = match_thresh
        self.frame_rate = frame_rate

        # Track management
        self.tracked_tracks: List[Track] = []
        self.lost_tracks: List[Track] = []
        self.removed_tracks: List[Track] = []

        self.frame_id = 0
        self.max_time_lost = int(frame_rate / 30.0 * track_buffer)

        # Reset track ID counter
        Track._count = 0

        logger.info(f"ByteTracker initialized (thresh={track_thresh}, buffer={track_buffer})")

    def update(self, detections: List[Detection]) -> List[Track]:
        """
        Update tracker with new detections

        Args:
            detections: List of Detection objects

        Returns:
            List of active tracks
        """
        self.frame_id += 1

        # Convert detections to tracks
        if len(detections) > 0:
            det_scores = np.array([d.confidence for d in detections])
            det_bboxes = np.array([d.bbox for d in detections])
            det_classes = np.array([d.class_id for d in detections])

            # Split detections into high and low confidence
            remain_inds = det_scores > self.track_thresh
            inds_low = det_scores > 0.1
            inds_high = det_scores < self.track_thresh

            inds_second = np.logical_and(inds_low, inds_high)

            dets_second = det_bboxes[inds_second]
            dets = det_bboxes[remain_inds]
            scores_keep = det_scores[remain_inds]
            scores_second = det_scores[inds_second]
            classes_keep = det_classes[remain_inds]
            classes_second = det_classes[inds_second]

        else:
            dets = np.empty((0, 4))
            scores_keep = np.empty(0)
            classes_keep = np.empty(0)
            dets_second = np.empty((0, 4))
            scores_second = np.empty(0)
            classes_second = np.empty(0)

        # Add newly detected tracks
        if len(dets) > 0:
            detections_high = [
                Track(
                    track_id=0,
                    bbox=dets[i],
                    score=scores_keep[i],
                    class_id=int(classes_keep[i]),
                    frame_id=self.frame_id
                )
                for i in range(len(dets))
            ]
        else:
            detections_high = []

        # Add second stage detections (low confidence)
        if len(dets_second) > 0:
            detections_second = [
                Track(
                    track_id=0,
                    bbox=dets_second[i],
                    score=scores_second[i],
                    class_id=int(classes_second[i]),
                    frame_id=self.frame_id
                )
                for i in range(len(dets_second))
            ]
        else:
            detections_second = []

        # Combine tracked and lost tracks
        unconfirmed = []
        tracked_stracks = []

        for track in self.tracked_tracks:
            if not track.is_activated:
                unconfirmed.append(track)
            else:
                tracked_stracks.append(track)

        # Predict current locations with Kalman filter
        strack_pool = self._joint_tracks(tracked_stracks, self.lost_tracks)

        for track in strack_pool:
            track.predict()

        # First association (high confidence detections)
        matches, u_track, u_detection = self._matching(
            strack_pool, detections_high, self.match_thresh
        )

        # Update matched tracks
        for itracked, idet in matches:
            track = strack_pool[itracked]
            det = detections_high[idet]

            if track.state == TrackState.Tracked:
                track.update(det, self.frame_id)
            else:
                track.re_activate(det, self.frame_id, new_id=False)

        # Second association (low confidence detections with lost tracks)
        r_tracked_stracks = [strack_pool[i] for i in u_track if strack_pool[i].state == TrackState.Tracked]

        matches, u_track_second, u_detection_second = self._matching(
            r_tracked_stracks, detections_second, 0.5
        )

        for itracked, idet in matches:
            track = r_tracked_stracks[itracked]
            det = detections_second[idet]

            if track.state == TrackState.Tracked:
                track.update(det, self.frame_id)
            else:
                track.re_activate(det, self.frame_id, new_id=False)

        # Mark lost tracks
        for it in u_track_second:
            track = r_tracked_stracks[it]
            if track.state != TrackState.Lost:
                track.mark_lost()

        # Deal with unconfirmed tracks (usually tracks with only one detection)
        detections_high = [detections_high[i] for i in u_detection]

        matches, u_unconfirmed, u_detection = self._matching(
            unconfirmed, detections_high, 0.7
        )

        for itracked, idet in matches:
            unconfirmed[itracked].update(detections_high[idet], self.frame_id)

        # Init new tracks
        for inew in u_detection:
            track = detections_high[inew]
            if track.score < self.track_thresh:
                continue

            track.activate(self.frame_id)
            tracked_stracks.append(track)

        # Remove tracks
        for track in self.lost_tracks:
            if self.frame_id - track.frame_id > self.max_time_lost:
                track.mark_removed()
                self.removed_tracks.append(track)

        # Update track states
        self.tracked_tracks = [t for t in self.tracked_tracks if t.state == TrackState.Tracked]
        self.tracked_tracks = self._joint_tracks(self.tracked_tracks, tracked_stracks)
        self.tracked_tracks = self._joint_tracks(self.tracked_tracks, unconfirmed)
        self.lost_tracks = [t for t in self.lost_tracks if t.state == TrackState.Lost]
        self.lost_tracks = self._sub_tracks(self.lost_tracks, self.tracked_tracks)
        self.lost_tracks.extend([t for t in tracked_stracks if t.state == TrackState.Lost])
        self.lost_tracks = self._sub_tracks(self.lost_tracks, self.removed_tracks)

        # Get output tracks
        output_tracks = [track for track in self.tracked_tracks if track.is_activated]

        return output_tracks

    def _matching(
        self,
        tracks: List[Track],
        detections: List[Track],
        thresh: float
    ) -> Tuple[np.ndarray, List[int], List[int]]:
        """
        Match tracks to detections using IoU

        Returns:
            matches: Array of (track_idx, detection_idx) pairs
            unmatched_tracks: List of track indices
            unmatched_detections: List of detection indices
        """
        if len(tracks) == 0 or len(detections) == 0:
            return np.empty((0, 2), dtype=int), list(range(len(tracks))), list(range(len(detections)))

        # Compute IoU matrix
        iou_matrix = self._iou_distance(tracks, detections)

        # Linear assignment - try multiple methods
        try:
            # Method 1: Try lap package (optimal but requires compilation)
            import lap
            cost_matrix = 1 - iou_matrix
            _, x, y = lap.lapjv(cost_matrix, extend_cost=True, cost_limit=1 - thresh)
            matches = [[ix, mx] for ix, mx in enumerate(x) if mx >= 0]
        except ImportError:
            try:
                # Method 2: Use scipy.optimize (optimal, no compilation needed)
                from scipy.optimize import linear_sum_assignment
                cost_matrix = 1 - iou_matrix

                # Apply threshold by setting high cost for low IoU
                cost_matrix[iou_matrix < thresh] = 1.0

                row_ind, col_ind = linear_sum_assignment(cost_matrix)
                matches = [[i, j] for i, j in zip(row_ind, col_ind) if iou_matrix[i, j] >= thresh]
            except (ImportError, Exception):
                # Method 3: Fallback to greedy matching (suboptimal but always works)
                matches = []
                used_tracks = set()
                used_detections = set()

                # Sort by IoU (descending)
                ious = []
                for i in range(len(tracks)):
                    for j in range(len(detections)):
                        if iou_matrix[i, j] >= thresh:
                            ious.append((iou_matrix[i, j], i, j))

                ious.sort(reverse=True)

                for _, i, j in ious:
                    if i not in used_tracks and j not in used_detections:
                        matches.append([i, j])
                        used_tracks.add(i)
                        used_detections.add(j)

        matches = np.array(matches)

        unmatched_tracks = [i for i in range(len(tracks)) if i not in matches[:, 0]]
        unmatched_detections = [i for i in range(len(detections)) if i not in matches[:, 1]]

        return matches, unmatched_tracks, unmatched_detections

    @staticmethod
    def _iou_distance(tracks: List[Track], detections: List[Track]) -> np.ndarray:
        """
        Compute IoU distance matrix between tracks and detections

        Returns:
            IoU matrix [num_tracks x num_detections]
        """
        if len(tracks) == 0 or len(detections) == 0:
            return np.zeros((len(tracks), len(detections)))

        track_boxes = np.array([t.tlbr for t in tracks])
        det_boxes = np.array([d.bbox for d in detections])

        ious = np.zeros((len(tracks), len(detections)))

        for i, tbox in enumerate(track_boxes):
            for j, dbox in enumerate(det_boxes):
                ious[i, j] = ByteTracker._bbox_iou(tbox, dbox)

        return ious

    @staticmethod
    def _bbox_iou(box1: np.ndarray, box2: np.ndarray) -> float:
        """
        Compute IoU between two boxes

        Args:
            box1, box2: [x1, y1, x2, y2]

        Returns:
            IoU value
        """
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        inter_area = max(0, x2 - x1) * max(0, y2 - y1)

        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

        union_area = box1_area + box2_area - inter_area

        if union_area == 0:
            return 0.0

        return inter_area / union_area

    @staticmethod
    def _joint_tracks(tlista: List[Track], tlistb: List[Track]) -> List[Track]:
        """Join two track lists"""
        exists = {}
        res = []

        for t in tlista:
            exists[t.track_id] = 1
            res.append(t)

        for t in tlistb:
            tid = t.track_id
            if not exists.get(tid, 0):
                exists[tid] = 1
                res.append(t)

        return res

    @staticmethod
    def _sub_tracks(tlista: List[Track], tlistb: List[Track]) -> List[Track]:
        """Subtract tlistb from tlista"""
        track_ids_b = {t.track_id for t in tlistb}
        return [t for t in tlista if t.track_id not in track_ids_b]

    def reset(self):
        """Reset tracker state"""
        self.frame_id = 0
        self.tracked_tracks = []
        self.lost_tracks = []
        self.removed_tracks = []
        Track._count = 0
        logger.info("ByteTracker reset")
