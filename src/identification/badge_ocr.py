"""
Badge OCR Module
Uses EasyOCR for badge ID recognition (supports Thai + English)
"""

import logging
import numpy as np
import cv2
import re
from typing import Optional, List, Tuple
from dataclasses import dataclass
import easyocr

logger = logging.getLogger(__name__)


@dataclass
class BadgeDetection:
    """Badge detection result"""
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    badge_id: str
    confidence: float
    text_bbox: List[List[int]]  # OCR text bounding box


class BadgeOCR:
    """
    Badge OCR System
    - Supports Thai and English text
    - Extracts badge IDs from worker badges
    """

    def __init__(
        self,
        languages: List[str] = ['th', 'en'],
        gpu: bool = False,
        min_confidence: float = 0.3,
        badge_pattern: Optional[str] = None
    ):
        """
        Initialize Badge OCR

        Args:
            languages: List of languages to recognize ('th', 'en', etc.)
            gpu: Use GPU for OCR (faster but requires CUDA)
            min_confidence: Minimum confidence for text detection
            badge_pattern: Regex pattern for badge ID validation
                          (e.g., r'^[A-Z]{2}\d{4}$' for "AB1234" format)
        """
        self.languages = languages
        self.gpu = gpu
        self.min_confidence = min_confidence
        self.badge_pattern = badge_pattern

        # Lazy loading - reader will be loaded on first use
        self.reader = None

        logger.info(
            f"BadgeOCR initialized (languages={languages}, "
            f"gpu={gpu}, min_confidence={min_confidence})"
        )

    def _load_reader(self):
        """Load EasyOCR reader (lazy loading)"""
        if self.reader is not None:
            return

        logger.info(f"Loading EasyOCR reader for languages: {self.languages}...")
        self.reader = easyocr.Reader(
            self.languages,
            gpu=self.gpu,
            verbose=False
        )
        logger.info("EasyOCR reader loaded successfully")

    def detect_badge(
        self,
        frame: np.ndarray,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[BadgeDetection]:
        """
        Detect and read badge ID from frame

        Args:
            frame: Input frame (BGR format from OpenCV)
            region: Optional region of interest (x1, y1, x2, y2)
                   If None, search entire frame

        Returns:
            BadgeDetection object or None
        """
        # Lazy load reader
        if self.reader is None:
            self._load_reader()

        # Extract region if specified
        if region is not None:
            x1, y1, x2, y2 = region
            search_area = frame[y1:y2, x1:x2]
        else:
            search_area = frame
            x1, y1 = 0, 0

        # Preprocess image for better OCR
        preprocessed = self._preprocess_badge(search_area)

        # Perform OCR
        try:
            results = self.reader.readtext(
                preprocessed,
                detail=1,
                paragraph=False,
                min_size=10
            )
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return None

        if not results:
            return None

        # Find best badge ID candidate
        best_detection = self._find_best_badge(results, x1, y1)

        return best_detection

    def _preprocess_badge(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess badge image for better OCR

        Args:
            image: Input image (BGR)

        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10)

        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )

        return thresh

    def _find_best_badge(
        self,
        ocr_results: List,
        offset_x: int = 0,
        offset_y: int = 0
    ) -> Optional[BadgeDetection]:
        """
        Find best badge ID from OCR results

        Args:
            ocr_results: EasyOCR results [(bbox, text, confidence), ...]
            offset_x: X offset for bounding box adjustment
            offset_y: Y offset for bounding box adjustment

        Returns:
            Best badge detection or None
        """
        candidates = []

        for bbox, text, confidence in ocr_results:
            if confidence < self.min_confidence:
                continue

            # Clean text (remove spaces, special characters)
            cleaned_text = self._clean_badge_text(text)

            if not cleaned_text:
                continue

            # Validate against pattern if specified
            if self.badge_pattern:
                if not re.match(self.badge_pattern, cleaned_text):
                    continue

            # Calculate bounding box
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            x1 = int(min(x_coords)) + offset_x
            y1 = int(min(y_coords)) + offset_y
            x2 = int(max(x_coords)) + offset_x
            y2 = int(max(y_coords)) + offset_y

            candidates.append(BadgeDetection(
                bbox=(x1, y1, x2, y2),
                badge_id=cleaned_text,
                confidence=confidence,
                text_bbox=bbox
            ))

        if not candidates:
            return None

        # Return badge with highest confidence
        best = max(candidates, key=lambda d: d.confidence)
        logger.debug(
            f"Detected badge ID: {best.badge_id} "
            f"(confidence: {best.confidence:.3f})"
        )

        return best

    def _clean_badge_text(self, text: str) -> str:
        """
        Clean and normalize badge text

        Args:
            text: Raw OCR text

        Returns:
            Cleaned badge ID
        """
        # Remove spaces
        text = text.replace(' ', '')

        # Remove common OCR errors
        text = text.replace('O', '0')  # Letter O -> Zero
        text = text.replace('I', '1')  # Letter I -> One
        text = text.replace('l', '1')  # Lowercase L -> One

        # Keep only alphanumeric
        text = re.sub(r'[^A-Za-z0-9]', '', text)

        # Convert to uppercase
        text = text.upper()

        return text

    def read_badge_from_person(
        self,
        frame: np.ndarray,
        person_bbox: Tuple[int, int, int, int],
        badge_position: str = "upper_chest"
    ) -> Optional[BadgeDetection]:
        """
        Read badge from person's bounding box

        Args:
            frame: Input frame (BGR)
            person_bbox: Person bounding box (x1, y1, x2, y2)
            badge_position: Where to look for badge
                           "upper_chest" (default) or "full"

        Returns:
            BadgeDetection or None
        """
        x1, y1, x2, y2 = person_bbox

        # Calculate badge search region
        if badge_position == "upper_chest":
            # Search upper 40% of person's torso (typical badge location)
            person_height = y2 - y1
            person_width = x2 - x1

            # Upper chest region (20-60% from top)
            search_y1 = y1 + int(person_height * 0.2)
            search_y2 = y1 + int(person_height * 0.6)

            # Center 60% width
            search_x1 = x1 + int(person_width * 0.2)
            search_x2 = x2 - int(person_width * 0.2)

            region = (search_x1, search_y1, search_x2, search_y2)

        else:
            # Search full person bbox
            region = person_bbox

        # Detect badge in region
        return self.detect_badge(frame, region=region)

    def draw_badge(
        self,
        frame: np.ndarray,
        detection: BadgeDetection,
        color: Tuple[int, int, int] = (255, 0, 0),
        thickness: int = 2
    ) -> np.ndarray:
        """
        Draw badge detection on frame

        Args:
            frame: Input frame (BGR)
            detection: Badge detection
            color: Bounding box color (BGR)
            thickness: Line thickness

        Returns:
            Frame with drawn badge
        """
        output = frame.copy()

        x1, y1, x2, y2 = detection.bbox

        # Draw bounding box
        cv2.rectangle(output, (x1, y1), (x2, y2), color, thickness)

        # Draw badge ID and confidence
        label = f"{detection.badge_id} ({detection.confidence:.2f})"
        cv2.putText(
            output, label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6, color, 2
        )

        return output

    def set_badge_pattern(self, pattern: str):
        """
        Set regex pattern for badge ID validation

        Args:
            pattern: Regex pattern (e.g., r'^[A-Z]{2}\d{4}$')

        Examples:
            - r'^[A-Z]{2}\d{4}$' -> "AB1234"
            - r'^\d{6}$' -> "123456"
            - r'^EMP-\d{5}$' -> "EMP-12345"
        """
        self.badge_pattern = pattern
        logger.info(f"Badge pattern set to: {pattern}")

    def get_stats(self) -> dict:
        """Get badge OCR statistics"""
        return {
            'languages': self.languages,
            'gpu': self.gpu,
            'min_confidence': self.min_confidence,
            'badge_pattern': self.badge_pattern,
            'reader_loaded': self.reader is not None
        }
