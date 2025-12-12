"""
YOLOv8 Detector Wrapper
Handles person detection using Ultralytics YOLOv8
"""

import cv2
import numpy as np
from typing import List, Optional
from datetime import datetime
import logging
import time

from .detection_models import Detection, DetectionResult, DetectionConfig

logger = logging.getLogger(__name__)


class YOLODetector:
    """YOLOv8-based object detector"""

    def __init__(self, config: DetectionConfig):
        """
        Initialize YOLOv8 detector

        Args:
            config: Detection configuration
        """
        self.config = config
        self.model = None
        self._frame_counter = 0

        # Statistics
        self.total_detections = 0
        self.total_inference_time = 0.0

        # COCO class names (YOLOv8 default)
        self.class_names = [
            "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
            "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
            "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
            "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
            "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
            "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
            "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
            "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
            "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
            "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
            "toothbrush"
        ]

        self._load_model()

    def _load_model(self):
        """Load YOLOv8 model"""
        try:
            from ultralytics import YOLO

            logger.info(f"Loading YOLOv8 model: {self.config.model_name}")
            self.model = YOLO(self.config.model_name)

            # Set device
            if self.config.device == "cuda":
                import torch
                if not torch.cuda.is_available():
                    logger.warning("CUDA not available, falling back to CPU")
                    self.config.device = "cpu"

            logger.info(f"YOLOv8 model loaded successfully on {self.config.device}")

        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model: {e}")
            raise

    def detect(self, frame: np.ndarray, camera_id: int, timestamp: Optional[datetime] = None) -> DetectionResult:
        """
        Run detection on a frame

        Args:
            frame: OpenCV image (BGR format)
            camera_id: Camera ID
            timestamp: Frame timestamp (defaults to now)

        Returns:
            DetectionResult object
        """
        if timestamp is None:
            timestamp = datetime.now()

        if self.model is None:
            raise RuntimeError("YOLOv8 model not loaded")

        self._frame_counter += 1
        frame_height, frame_width = frame.shape[:2]

        # Run inference
        start_time = time.time()

        results = self.model(
            frame,
            conf=self.config.confidence_threshold,
            iou=self.config.iou_threshold,
            classes=self.config.classes,
            max_det=self.config.max_detections,
            device=self.config.device,
            verbose=False
        )

        inference_time_ms = (time.time() - start_time) * 1000
        self.total_inference_time += inference_time_ms

        # Parse results
        detections = []

        if len(results) > 0:
            result = results[0]  # First image result

            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes.cpu().numpy()

                for box in boxes:
                    # Extract box data
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])

                    # Get class name
                    class_name = self.class_names[class_id] if class_id < len(self.class_names) else f"class_{class_id}"

                    # Create detection object
                    detection = Detection(
                        class_id=class_id,
                        class_name=class_name,
                        confidence=confidence,
                        bbox=[x1, y1, x2, y2],
                        bbox_normalized=[
                            x1 / frame_width,
                            y1 / frame_height,
                            x2 / frame_width,
                            y2 / frame_height
                        ]
                    )

                    detections.append(detection)

        self.total_detections += len(detections)

        return DetectionResult(
            camera_id=camera_id,
            timestamp=timestamp,
            frame_number=self._frame_counter,
            detections=detections,
            inference_time_ms=round(inference_time_ms, 2),
            frame_width=frame_width,
            frame_height=frame_height
        )

    def detect_batch(self, frames: List[np.ndarray], camera_id: int) -> List[DetectionResult]:
        """
        Run detection on multiple frames (batch processing)

        Args:
            frames: List of OpenCV images
            camera_id: Camera ID

        Returns:
            List of DetectionResult objects
        """
        results = []
        for frame in frames:
            result = self.detect(frame, camera_id)
            results.append(result)

        return results

    def get_stats(self) -> dict:
        """Get detector statistics"""
        avg_inference_time = 0.0
        if self._frame_counter > 0:
            avg_inference_time = self.total_inference_time / self._frame_counter

        avg_fps = 0.0
        if avg_inference_time > 0:
            avg_fps = 1000.0 / avg_inference_time

        return {
            "model_name": self.config.model_name,
            "device": self.config.device,
            "frames_processed": self._frame_counter,
            "total_detections": self.total_detections,
            "avg_inference_time_ms": round(avg_inference_time, 2),
            "avg_fps": round(avg_fps, 2)
        }

    def reset_stats(self):
        """Reset statistics"""
        self._frame_counter = 0
        self.total_detections = 0
        self.total_inference_time = 0.0

    def draw_detections(self, frame: np.ndarray, detections: List[Detection],
                       show_confidence: bool = True, color: tuple = (0, 255, 0)) -> np.ndarray:
        """
        Draw detection boxes on frame

        Args:
            frame: OpenCV image
            detections: List of Detection objects
            show_confidence: Show confidence score
            color: Box color (B, G, R)

        Returns:
            Frame with drawn boxes
        """
        frame_drawn = frame.copy()

        for det in detections:
            x1, y1, x2, y2 = [int(coord) for coord in det.bbox]

            # Draw bounding box
            cv2.rectangle(frame_drawn, (x1, y1), (x2, y2), color, 2)

            # Draw label
            label = det.class_name
            if show_confidence:
                label = f"{det.class_name} {det.confidence:.2f}"

            # Text background
            (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame_drawn, (x1, y1 - text_height - 10), (x1 + text_width, y1), color, -1)

            # Text
            cv2.putText(frame_drawn, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return frame_drawn
