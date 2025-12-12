"""
Zone Manager - Zone CRUD and Management
"""

import threading
from typing import Dict, List, Optional
import logging

from .zone_models import Zone, ZoneType, ZoneOccupancy

logger = logging.getLogger(__name__)


class ZoneManager:
    """Manages zone definitions and operations"""

    def __init__(self):
        """Initialize zone manager"""
        self.zones: Dict[int, Zone] = {}
        self._lock = threading.Lock()
        logger.info("ZoneManager initialized")

    def add_zone(self, zone: Zone) -> bool:
        """
        Add a zone

        Args:
            zone: Zone object

        Returns:
            True if zone added successfully
        """
        with self._lock:
            if zone.zone_id in self.zones:
                logger.warning(f"Zone {zone.zone_id} already exists")
                return False

            self.zones[zone.zone_id] = zone
            logger.info(f"Added zone {zone.zone_id}: {zone.name} ({zone.zone_type})")
            return True

    def update_zone(self, zone: Zone) -> bool:
        """
        Update an existing zone

        Args:
            zone: Zone object with updated data

        Returns:
            True if zone updated successfully
        """
        with self._lock:
            if zone.zone_id not in self.zones:
                logger.warning(f"Zone {zone.zone_id} not found")
                return False

            self.zones[zone.zone_id] = zone
            logger.info(f"Updated zone {zone.zone_id}: {zone.name}")
            return True

    def remove_zone(self, zone_id: int) -> bool:
        """
        Remove a zone

        Args:
            zone_id: Zone ID to remove

        Returns:
            True if zone removed successfully
        """
        with self._lock:
            if zone_id not in self.zones:
                logger.warning(f"Zone {zone_id} not found")
                return False

            zone = self.zones[zone_id]
            del self.zones[zone_id]
            logger.info(f"Removed zone {zone_id}: {zone.name}")
            return True

    def get_zone(self, zone_id: int) -> Optional[Zone]:
        """
        Get zone by ID

        Args:
            zone_id: Zone ID

        Returns:
            Zone object or None if not found
        """
        with self._lock:
            return self.zones.get(zone_id)

    def get_zones_by_camera(self, camera_id: int) -> List[Zone]:
        """
        Get all zones for a specific camera

        Args:
            camera_id: Camera ID

        Returns:
            List of zones for the camera
        """
        with self._lock:
            return [zone for zone in self.zones.values() if zone.camera_id == camera_id]

    def get_zones_by_type(self, zone_type: ZoneType) -> List[Zone]:
        """
        Get all zones of a specific type

        Args:
            zone_type: Zone type

        Returns:
            List of zones of the specified type
        """
        with self._lock:
            return [zone for zone in self.zones.values() if zone.zone_type == zone_type]

    def get_all_zones(self) -> List[Zone]:
        """
        Get all zones

        Returns:
            List of all zones
        """
        with self._lock:
            return list(self.zones.values())

    def get_active_zones(self) -> List[Zone]:
        """
        Get all active zones

        Returns:
            List of active zones
        """
        with self._lock:
            return [zone for zone in self.zones.values() if zone.active]

    def activate_zone(self, zone_id: int) -> bool:
        """Activate a zone"""
        with self._lock:
            if zone_id not in self.zones:
                return False

            self.zones[zone_id].active = True
            logger.info(f"Activated zone {zone_id}")
            return True

    def deactivate_zone(self, zone_id: int) -> bool:
        """Deactivate a zone"""
        with self._lock:
            if zone_id not in self.zones:
                return False

            self.zones[zone_id].active = False
            logger.info(f"Deactivated zone {zone_id}")
            return True

    def clear_zones(self):
        """Remove all zones"""
        with self._lock:
            self.zones.clear()
            logger.info("Cleared all zones")
