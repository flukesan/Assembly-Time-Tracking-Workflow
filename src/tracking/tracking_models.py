"""
Tracking Data Models
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
from datetime import datetime
from enum import Enum


class TrackStatus(str, Enum):
    """Track status enumeration"""
    ACTIVE = "active"
    LOST = "lost"
    FINISHED = "finished"


class TrackedObject(BaseModel):
    """Single tracked object"""

    track_id: int
    camera_id: int
    class_id: int
    class_name: str
    bbox: List[float] = Field(description="[x1, y1, x2, y2]")
    confidence: float
    status: TrackStatus
    frame_id: int
    age: int = Field(description="Number of frames tracked")
    time_since_update: int = Field(description="Frames since last detection", default=0)

    # Position info
    center_x: float
    center_y: float

    # Zone info (if in any zone)
    zone_id: Optional[int] = None
    zone_name: Optional[str] = None

    # Timestamps
    first_seen: datetime
    last_seen: datetime

    class Config:
        from_attributes = True


class TrackingResult(BaseModel):
    """Tracking results for a single frame"""

    camera_id: int
    frame_id: int
    timestamp: datetime
    tracks: List[TrackedObject]
    active_track_count: int
    new_track_count: int = 0
    finished_track_count: int = 0

    class Config:
        from_attributes = True


class ZoneTransition(BaseModel):
    """Zone transition event"""

    transition_id: Optional[int] = None
    track_id: int
    camera_id: int
    from_zone_id: Optional[int]
    from_zone_name: Optional[str]
    to_zone_id: Optional[int]
    to_zone_name: Optional[str]
    transition_time: datetime
    duration_in_prev_zone: Optional[float] = Field(
        description="Seconds spent in previous zone", default=None
    )

    class Config:
        from_attributes = True


class TrackHistory(BaseModel):
    """Full track history"""

    track_id: int
    camera_id: int
    class_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration: Optional[float] = None  # seconds
    total_frames: int
    zones_visited: List[str] = Field(default_factory=list)
    zone_transitions: List[ZoneTransition] = Field(default_factory=list)
    avg_confidence: float
    status: TrackStatus

    class Config:
        from_attributes = True


class TrackStatistics(BaseModel):
    """Tracking statistics"""

    camera_id: int
    total_tracks: int
    active_tracks: int
    lost_tracks: int
    finished_tracks: int
    avg_track_duration: float  # seconds
    avg_confidence: float
    tracks_per_zone: dict = Field(default_factory=dict)  # zone_id -> count

    class Config:
        from_attributes = True
