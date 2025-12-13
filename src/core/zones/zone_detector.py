"""
Zone Detector - Point-in-Polygon Detection
Checks if detection centers are inside defined zones
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict
import logging

from .zone_models import Zone
from ai.detection_models import Detection

logger = logging.getLogger(__name__)


class ZoneDetector:
    """Detects which zone(s) a detection belongs to"""

    @staticmethod
    def point_in_polygon(point: Tuple[float, float], polygon: List[Tuple[int, int]]) -> bool:
        """
        Check if a point is inside a polygon using ray-casting algorithm

        Args:
            point: (x, y) coordinates
            polygon: List of (x, y) polygon vertices

        Returns:
            True if point is inside polygon
        """
        x, y = point
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]

            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x

                        if p1x == p2x or x <= xinters:
                            inside = not inside

            p1x, p1y = p2x, p2y

        return inside

    @staticmethod
    def point_in_polygon_cv2(point: Tuple[float, float], polygon: List[Tuple[int, int]]) -> bool:
        """
        Check if point is inside polygon using OpenCV (faster for complex polygons)

        Args:
            point: (x, y) coordinates
            polygon: List of (x, y) polygon vertices

        Returns:
            True if point is inside polygon
        """
        polygon_array = np.array(polygon, dtype=np.int32)
        result = cv2.pointPolygonTest(polygon_array, point, False)
        return result >= 0  # >= 0 means inside or on edge

    @staticmethod
    def find_zones_for_detection(detection: Detection, zones: List[Zone]) -> List[Zone]:
        """
        Find all zones that contain the detection center point

        Args:
            detection: Detection object
            zones: List of Zone objects

        Returns:
            List of zones containing the detection
        """
        point = (detection.center_x, detection.center_y)
        matching_zones = []

        for zone in zones:
            if not zone.active:
                continue

            if ZoneDetector.point_in_polygon_cv2(point, zone.polygon_coords):
                matching_zones.append(zone)

        return matching_zones

    @staticmethod
    def match_detections_to_zones(detections: List[Detection],
                                  zones: List[Zone]) -> Dict[int, List[Detection]]:
        """
        Match all detections to their respective zones

        Args:
            detections: List of Detection objects
            zones: List of Zone objects

        Returns:
            Dictionary mapping zone_id to list of detections in that zone
        """
        zone_detections = {zone.zone_id: [] for zone in zones}

        for detection in detections:
            matching_zones = ZoneDetector.find_zones_for_detection(detection, zones)

            for zone in matching_zones:
                zone_detections[zone.zone_id].append(detection)

        return zone_detections

    @staticmethod
    def draw_zone(frame: np.ndarray, zone: Zone, thickness: int = 2,
                 show_label: bool = True) -> np.ndarray:
        """
        Draw zone polygon on frame

        Args:
            frame: OpenCV image
            zone: Zone object
            thickness: Line thickness
            show_label: Show zone name label

        Returns:
            Frame with drawn zone
        """
        frame_drawn = frame.copy()

        # Convert hex color to BGR
        color_hex = zone.color.lstrip('#') if zone.color else "00FF00"
        r = int(color_hex[0:2], 16)
        g = int(color_hex[2:4], 16)
        b = int(color_hex[4:6], 16)
        color = (b, g, r)

        # Draw polygon
        polygon_array = np.array(zone.polygon_coords, dtype=np.int32)
        cv2.polylines(frame_drawn, [polygon_array], isClosed=True, color=color, thickness=thickness)

        # Optional: Fill with transparent color
        overlay = frame_drawn.copy()
        cv2.fillPoly(overlay, [polygon_array], color)
        cv2.addWeighted(overlay, 0.2, frame_drawn, 0.8, 0, frame_drawn)

        # Draw label
        if show_label and len(zone.polygon_coords) > 0:
            # Calculate label position (centroid of polygon)
            centroid_x = int(np.mean([p[0] for p in zone.polygon_coords]))
            centroid_y = int(np.mean([p[1] for p in zone.polygon_coords]))

            label = f"{zone.name} ({zone.zone_type})"

            # Text background
            (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame_drawn,
                         (centroid_x - 5, centroid_y - text_height - 10),
                         (centroid_x + text_width + 5, centroid_y + 5),
                         color, -1)

            # Text
            cv2.putText(frame_drawn, label, (centroid_x, centroid_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return frame_drawn

    @staticmethod
    def draw_all_zones(frame: np.ndarray, zones: List[Zone]) -> np.ndarray:
        """
        Draw all zones on frame

        Args:
            frame: OpenCV image
            zones: List of Zone objects

        Returns:
            Frame with all zones drawn
        """
        frame_drawn = frame.copy()

        for zone in zones:
            if zone.active:
                frame_drawn = ZoneDetector.draw_zone(frame_drawn, zone)

        return frame_drawn
