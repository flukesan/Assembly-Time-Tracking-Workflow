"""
Detection Data Models
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Detection(BaseModel):
    """Single object detection"""

    class_id: int
    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: List[float] = Field(description="[x1, y1, x2, y2] in pixels")
    bbox_normalized: Optional[List[float]] = Field(
        default=None,
        description="[x1, y1, x2, y2] normalized to [0, 1]"
    )

    # Computed properties
    @property
    def center_x(self) -> float:
        """Get bounding box center X coordinate"""
        return (self.bbox[0] + self.bbox[2]) / 2

    @property
    def center_y(self) -> float:
        """Get bounding box center Y coordinate"""
        return (self.bbox[1] + self.bbox[3]) / 2

    @property
    def width(self) -> float:
        """Get bounding box width"""
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> float:
        """Get bounding box height"""
        return self.bbox[3] - self.bbox[1]

    @property
    def area(self) -> float:
        """Get bounding box area"""
        return self.width * self.height


class DetectionResult(BaseModel):
    """Detection results for a single frame"""

    camera_id: int
    timestamp: datetime
    frame_number: int
    detections: List[Detection]
    inference_time_ms: float = Field(description="Inference time in milliseconds")
    frame_width: int
    frame_height: int

    @property
    def person_count(self) -> int:
        """Count of person detections"""
        return len([d for d in self.detections if d.class_name == "person"])

    class Config:
        from_attributes = True


class DetectionConfig(BaseModel):
    """YOLOv8 detection configuration"""

    model_name: str = Field(default="yolov8n.pt", description="YOLOv8 model file")
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    iou_threshold: float = Field(default=0.45, ge=0.0, le=1.0)
    device: str = Field(default="cpu", description="cpu or cuda")
    max_detections: int = Field(default=100, ge=1)
    classes: Optional[List[int]] = Field(default=[0], description="Class IDs to detect (0=person)")
    img_size: int = Field(default=640, description="Input image size")

    class Config:
        from_attributes = True
