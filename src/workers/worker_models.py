"""
Worker Data Models
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import numpy as np


class Shift(str, Enum):
    """Work shift enumeration"""
    MORNING = "morning"      # 06:00 - 14:00
    AFTERNOON = "afternoon"  # 14:00 - 22:00
    NIGHT = "night"          # 22:00 - 06:00
    FLEXIBLE = "flexible"


class SkillLevel(str, Enum):
    """Worker skill level"""
    TRAINEE = "trainee"
    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    SENIOR = "senior"
    EXPERT = "expert"


class WorkerStatus(str, Enum):
    """Worker status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"


class Worker(BaseModel):
    """Worker data model"""

    worker_id: str
    name: str
    badge_id: Optional[str] = None
    face_embedding: Optional[bytes] = None  # Serialized numpy array
    shift: Shift = Shift.FLEXIBLE
    skill_level: SkillLevel = SkillLevel.JUNIOR
    station_assignments: Optional[List[str]] = Field(default_factory=list)
    active: bool = True

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        use_enum_values = True

    def set_face_embedding(self, embedding: np.ndarray):
        """
        Set face embedding from numpy array

        Args:
            embedding: Face embedding vector (numpy array)
        """
        self.face_embedding = embedding.tobytes()

    def get_face_embedding(self) -> Optional[np.ndarray]:
        """
        Get face embedding as numpy array

        Returns:
            Face embedding vector or None
        """
        if self.face_embedding is None:
            return None

        # Reconstruct numpy array (assuming 512-dim embedding)
        return np.frombuffer(self.face_embedding, dtype=np.float32)


class WorkerIdentification(BaseModel):
    """Worker identification result"""

    worker_id: str
    name: str
    confidence: float
    method: str  # "face", "badge", "manual"
    timestamp: datetime
    track_id: Optional[int] = None
    camera_id: Optional[int] = None

    class Config:
        from_attributes = True


class WorkerSession(BaseModel):
    """Worker work session"""

    session_id: Optional[int] = None
    worker_id: str
    worker_name: str
    shift: Shift
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None

    # Time breakdown
    active_time_seconds: float = 0.0
    idle_time_seconds: float = 0.0
    break_time_seconds: float = 0.0

    # Zone information
    zones_visited: List[str] = Field(default_factory=list)
    current_zone: Optional[str] = None

    # Tracking information
    track_id: Optional[int] = None
    camera_id: Optional[int] = None

    # Status
    is_active: bool = True

    class Config:
        from_attributes = True


class ProductivityIndex(BaseModel):
    """11 Productivity Indices per shift"""

    session_id: int
    worker_id: str
    shift: Shift
    timestamp: datetime

    # Time-based indices (1-4)
    index_1_active_time: float = 0.0          # Active work time (seconds)
    index_2_idle_time: float = 0.0            # Idle time (seconds)
    index_3_break_time: float = 0.0           # Break time (seconds)
    index_4_total_time: float = 0.0           # Total session time (seconds)

    # Efficiency indices (5-7)
    index_5_work_efficiency: float = 0.0      # Active time / Total time (%)
    index_6_zone_transitions: int = 0         # Number of zone changes
    index_7_avg_time_per_zone: float = 0.0    # Average time spent per zone (seconds)

    # Output indices (8-10)
    index_8_tasks_completed: int = 0          # Number of tasks/units completed
    index_9_output_per_hour: float = 0.0      # Tasks per hour
    index_10_quality_score: float = 0.0       # Quality rating (0-100)

    # Overall index (11)
    index_11_overall_productivity: float = 0.0  # Weighted average of all indices (0-100)

    class Config:
        from_attributes = True

    def calculate_overall_productivity(self):
        """Calculate overall productivity index (weighted average)"""
        # Weights for each index category
        weights = {
            'efficiency': 0.4,      # indices 5-7
            'output': 0.4,          # indices 8-10
            'time_management': 0.2  # indices 1-4
        }

        # Efficiency score (0-100)
        efficiency_score = (
            self.index_5_work_efficiency * 0.6 +  # Work efficiency is most important
            (100 - min(self.index_6_zone_transitions * 5, 100)) * 0.2 +  # Fewer transitions is better
            (min(self.index_7_avg_time_per_zone / 60, 100)) * 0.2  # Reasonable time per zone
        )

        # Output score (0-100)
        output_score = (
            min(self.index_9_output_per_hour * 10, 100) * 0.6 +  # Output rate
            self.index_10_quality_score * 0.4  # Quality
        )

        # Time management score (0-100)
        if self.index_4_total_time > 0:
            time_score = (
                (self.index_1_active_time / self.index_4_total_time) * 100 * 0.7 +
                (1 - (self.index_2_idle_time / self.index_4_total_time)) * 100 * 0.3
            )
        else:
            time_score = 0.0

        # Overall productivity
        self.index_11_overall_productivity = (
            efficiency_score * weights['efficiency'] +
            output_score * weights['output'] +
            time_score * weights['time_management']
        )

        return self.index_11_overall_productivity
