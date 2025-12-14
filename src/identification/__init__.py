"""
Worker Identification Module
Handles face recognition and badge OCR for worker identification
"""

from .face_recognition import FaceRecognizer
from .badge_ocr import BadgeOCR

__all__ = ["FaceRecognizer", "BadgeOCR"]
