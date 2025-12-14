"""
Face Recognition Module
Uses MTCNN for face detection and InceptionResnetV1 for face embeddings
"""

import logging
import numpy as np
import cv2
import torch
from typing import Optional, List, Tuple
from dataclasses import dataclass
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class FaceDetection:
    """Face detection result"""
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    landmarks: Optional[np.ndarray] = None  # 5 facial landmarks
    embedding: Optional[np.ndarray] = None


class FaceRecognizer:
    """
    Face Recognition System
    - Detection: MTCNN (Multi-task Cascaded Convolutional Networks)
    - Embedding: InceptionResnetV1 (FaceNet)
    """

    def __init__(
        self,
        device: str = "cpu",
        min_face_size: int = 40,
        detection_threshold: float = 0.9,
        keep_all: bool = True
    ):
        """
        Initialize face recognizer

        Args:
            device: "cpu" or "cuda"
            min_face_size: Minimum face size to detect (pixels)
            detection_threshold: Minimum confidence for face detection
            keep_all: Keep all detected faces (not just the largest)
        """
        self.device = torch.device(device)
        self.min_face_size = min_face_size
        self.detection_threshold = detection_threshold
        self.keep_all = keep_all

        # Lazy loading - models will be loaded on first use
        self.mtcnn = None
        self.facenet = None

        logger.info(
            f"FaceRecognizer initialized (device={device}, "
            f"min_face_size={min_face_size}, threshold={detection_threshold})"
        )

    def _load_models(self):
        """Load face detection and recognition models (lazy loading)"""
        if self.mtcnn is not None:
            return

        logger.info("Loading MTCNN face detector...")
        self.mtcnn = MTCNN(
            image_size=160,
            margin=0,
            min_face_size=self.min_face_size,
            thresholds=[0.6, 0.7, self.detection_threshold],
            factor=0.709,
            post_process=True,
            device=self.device,
            keep_all=self.keep_all,
            select_largest=False
        )

        logger.info("Loading InceptionResnetV1 (FaceNet) for embeddings...")
        self.facenet = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)

        logger.info("Face recognition models loaded successfully")

    def detect_faces(
        self,
        frame: np.ndarray,
        return_embeddings: bool = True
    ) -> List[FaceDetection]:
        """
        Detect faces in frame and optionally extract embeddings

        Args:
            frame: Input frame (BGR format from OpenCV)
            return_embeddings: Whether to compute face embeddings

        Returns:
            List of FaceDetection objects
        """
        # Lazy load models
        if self.mtcnn is None:
            self._load_models()

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)

        # Detect faces
        try:
            boxes, probs, landmarks = self.mtcnn.detect(pil_image, landmarks=True)
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return []

        if boxes is None:
            return []

        detections = []

        for i, (box, prob, landmark) in enumerate(zip(boxes, probs, landmarks)):
            if prob < self.detection_threshold:
                continue

            # Convert box to integers
            x1, y1, x2, y2 = [int(coord) for coord in box]

            # Ensure coordinates are within frame bounds
            h, w = frame.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            # Skip invalid boxes
            if x2 <= x1 or y2 <= y1:
                continue

            # Create detection
            detection = FaceDetection(
                bbox=(x1, y1, x2, y2),
                confidence=float(prob),
                landmarks=landmark
            )

            # Extract embedding if requested
            if return_embeddings:
                try:
                    embedding = self.extract_embedding(frame, (x1, y1, x2, y2))
                    detection.embedding = embedding
                except Exception as e:
                    logger.warning(f"Failed to extract embedding: {e}")

            detections.append(detection)

        logger.debug(f"Detected {len(detections)} faces in frame")
        return detections

    def extract_embedding(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        Extract face embedding from cropped face region

        Args:
            frame: Input frame (BGR format)
            bbox: Face bounding box (x1, y1, x2, y2)

        Returns:
            512-dimensional face embedding (normalized)
        """
        # Lazy load models
        if self.facenet is None:
            self._load_models()

        # Crop face region
        x1, y1, x2, y2 = bbox
        face_crop = frame[y1:y2, x1:x2]

        if face_crop.size == 0:
            raise ValueError("Empty face crop")

        # Convert BGR to RGB
        face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
        face_pil = Image.fromarray(face_rgb)

        # Resize to 160x160 (required by FaceNet)
        face_resized = face_pil.resize((160, 160), Image.BILINEAR)

        # Convert to tensor and normalize
        face_tensor = torch.from_numpy(np.array(face_resized)).float()
        face_tensor = face_tensor.permute(2, 0, 1).unsqueeze(0)  # (1, 3, 160, 160)
        face_tensor = (face_tensor - 127.5) / 128.0  # Normalize to [-1, 1]
        face_tensor = face_tensor.to(self.device)

        # Extract embedding
        with torch.no_grad():
            embedding = self.facenet(face_tensor)
            embedding = embedding.cpu().numpy().flatten()

        # Normalize embedding (L2 normalization)
        embedding = embedding / np.linalg.norm(embedding)

        return embedding.astype(np.float32)

    def enroll_face(
        self,
        frame: np.ndarray,
        bbox: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[np.ndarray]:
        """
        Enroll a face for a worker (extract and return embedding)

        Args:
            frame: Input frame (BGR format)
            bbox: Optional bounding box. If None, auto-detect largest face

        Returns:
            Face embedding or None if no face detected
        """
        if bbox is None:
            # Auto-detect face
            detections = self.detect_faces(frame, return_embeddings=True)

            if not detections:
                logger.warning("No face detected for enrollment")
                return None

            # Use the face with highest confidence
            best_detection = max(detections, key=lambda d: d.confidence)
            embedding = best_detection.embedding

        else:
            # Use provided bbox
            try:
                embedding = self.extract_embedding(frame, bbox)
            except Exception as e:
                logger.error(f"Failed to extract embedding: {e}")
                return None

        logger.info(f"Face enrolled successfully (embedding shape: {embedding.shape})")
        return embedding

    def compare_faces(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Compare two face embeddings using cosine similarity

        Args:
            embedding1: First face embedding
            embedding2: Second face embedding

        Returns:
            Similarity score (0-1, higher is more similar)
        """
        # Cosine similarity
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )

        return float(similarity)

    def identify_face(
        self,
        frame: np.ndarray,
        enrolled_embeddings: dict,
        threshold: float = 0.6,
        bbox: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[Tuple[str, float]]:
        """
        Identify a face against enrolled embeddings

        Args:
            frame: Input frame (BGR format)
            enrolled_embeddings: Dict of {worker_id: embedding}
            threshold: Minimum similarity threshold
            bbox: Optional bounding box. If None, auto-detect

        Returns:
            Tuple of (worker_id, similarity) or None
        """
        # Extract embedding from frame
        if bbox is None:
            detections = self.detect_faces(frame, return_embeddings=True)
            if not detections:
                return None
            embedding = detections[0].embedding
        else:
            try:
                embedding = self.extract_embedding(frame, bbox)
            except Exception as e:
                logger.error(f"Failed to extract embedding: {e}")
                return None

        # Compare against all enrolled embeddings
        best_match = None
        best_similarity = threshold

        for worker_id, enrolled_embedding in enrolled_embeddings.items():
            similarity = self.compare_faces(embedding, enrolled_embedding)

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = worker_id

        if best_match:
            logger.info(
                f"Face identified as {best_match} "
                f"(similarity: {best_similarity:.3f})"
            )
            return (best_match, best_similarity)

        return None

    def draw_faces(
        self,
        frame: np.ndarray,
        detections: List[FaceDetection],
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> np.ndarray:
        """
        Draw face bounding boxes and landmarks on frame

        Args:
            frame: Input frame (BGR format)
            detections: List of face detections
            color: Bounding box color (BGR)
            thickness: Line thickness

        Returns:
            Frame with drawn faces
        """
        output = frame.copy()

        for detection in detections:
            x1, y1, x2, y2 = detection.bbox

            # Draw bounding box
            cv2.rectangle(output, (x1, y1), (x2, y2), color, thickness)

            # Draw confidence
            conf_text = f"{detection.confidence:.2f}"
            cv2.putText(
                output, conf_text,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5, color, 1
            )

            # Draw landmarks if available
            if detection.landmarks is not None:
                for landmark in detection.landmarks:
                    x, y = int(landmark[0]), int(landmark[1])
                    cv2.circle(output, (x, y), 2, (255, 0, 0), -1)

        return output

    def get_stats(self) -> dict:
        """Get face recognizer statistics"""
        return {
            'device': str(self.device),
            'min_face_size': self.min_face_size,
            'detection_threshold': self.detection_threshold,
            'models_loaded': self.mtcnn is not None
        }
