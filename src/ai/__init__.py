"""
AI Detection Module
YOLOv8-based person detection and model management
"""

from .yolo_detector import YOLODetector
from .detection_models import Detection, DetectionResult

__all__ = ["YOLODetector", "Detection", "DetectionResult"]
