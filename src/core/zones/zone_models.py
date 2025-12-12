"""
Zone Data Models
"""

from pydantic import BaseModel, Field
from typing import List, Tuple, Optional, Literal
from datetime import datetime
from enum import Enum


class ZoneType(str, Enum):
    """Zone type enumeration"""
    WORK = "work"
    BREAK = "break"
    RESTRICTED = "restricted"
    ENTRY = "entry"
    EXIT = "exit"


class Zone(BaseModel):
    """Zone definition"""

    zone_id: int
    camera_id: int
    name: str
    zone_type: ZoneType
    polygon_coords: List[Tuple[int, int]] = Field(
        description="List of (x, y) coordinates defining the polygon"
    )
    color: Optional[str] = Field(default="#00FF00", description="Hex color for visualization")
    active: bool = Field(default=True)

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def num_vertices(self) -> int:
        """Number of polygon vertices"""
        return len(self.polygon_coords)

    class Config:
        from_attributes = True
        use_enum_values = True


class ZoneOccupancy(BaseModel):
    """Real-time zone occupancy data"""

    zone_id: int
    zone_name: str
    camera_id: int
    person_count: int
    worker_ids: List[int] = Field(default_factory=list)
    timestamp: datetime

    class Config:
        from_attributes = True
