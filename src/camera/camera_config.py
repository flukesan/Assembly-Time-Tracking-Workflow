"""
Camera Configuration Models
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class CameraConfig(BaseModel):
    """Camera configuration model"""

    camera_id: int
    name: str
    rtsp_url: str
    location: str
    status: Literal["active", "inactive", "error"] = "inactive"
    fps: int = Field(default=30, ge=1, le=60)
    resolution_width: int = Field(default=1920, ge=640)
    resolution_height: int = Field(default=1080, ge=480)
    rotation: int = Field(default=0, ge=0, le=360)

    # Advanced settings
    reconnect_delay: int = Field(default=5, description="Seconds to wait before reconnect")
    max_reconnect_attempts: int = Field(default=3, description="Max reconnect attempts")
    frame_buffer_size: int = Field(default=30, description="Frame buffer size")

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CameraStatus(BaseModel):
    """Camera runtime status"""

    camera_id: int
    name: str
    status: Literal["active", "inactive", "error", "reconnecting"]
    fps_actual: float = 0.0
    frames_captured: int = 0
    frames_dropped: int = 0
    last_frame_time: Optional[datetime] = None
    error_message: Optional[str] = None
    uptime_seconds: float = 0.0

    class Config:
        from_attributes = True
