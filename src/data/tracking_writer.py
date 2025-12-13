"""
Tracking Writer - Read tracking data from PostgreSQL
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging

from .database import DatabaseManager
from tracking.tracking_models import TrackedObject, ZoneTransition, TrackHistory, TrackStatistics

logger = logging.getLogger(__name__)


class TrackingWriter:
    """Read and query tracking data from PostgreSQL"""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize tracking writer

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        logger.info("TrackingWriter initialized")

    async def get_active_tracks(self, camera_id: Optional[int] = None) -> List[Dict]:
        """
        Get all currently active tracks

        Args:
            camera_id: Filter by camera ID (None = all cameras)

        Returns:
            List of active tracks
        """
        if camera_id is not None:
            query = """
                SELECT * FROM tracked_objects
                WHERE status = 'active' AND camera_id = $1
                ORDER BY last_seen DESC
            """
            rows = await self.db_manager.fetch(query, camera_id)
        else:
            query = """
                SELECT * FROM tracked_objects
                WHERE status = 'active'
                ORDER BY last_seen DESC
            """
            rows = await self.db_manager.fetch(query)

        return [dict(row) for row in rows]

    async def get_track_history(
        self,
        track_id: int,
        camera_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get full history for a specific track

        Args:
            track_id: Track ID
            camera_id: Camera ID
            start_time: Start time filter
            end_time: End time filter

        Returns:
            List of detection records
        """
        query = """
            SELECT * FROM detections
            WHERE track_id = $1 AND camera_id = $2
        """
        params = [track_id, camera_id]

        if start_time:
            query += " AND timestamp >= $3"
            params.append(start_time)

        if end_time:
            idx = len(params) + 1
            query += f" AND timestamp <= ${idx}"
            params.append(end_time)

        query += " ORDER BY timestamp ASC"

        rows = await self.db_manager.fetch(query, *params)
        return [dict(row) for row in rows]

    async def get_zone_transitions(
        self,
        track_id: Optional[int] = None,
        camera_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get zone transitions

        Args:
            track_id: Filter by track ID
            camera_id: Filter by camera ID
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of results

        Returns:
            List of zone transitions
        """
        query = "SELECT * FROM zone_transitions WHERE 1=1"
        params = []
        param_idx = 1

        if track_id is not None:
            query += f" AND track_id = ${param_idx}"
            params.append(track_id)
            param_idx += 1

        if camera_id is not None:
            query += f" AND camera_id = ${param_idx}"
            params.append(camera_id)
            param_idx += 1

        if start_time:
            query += f" AND transition_time >= ${param_idx}"
            params.append(start_time)
            param_idx += 1

        if end_time:
            query += f" AND transition_time <= ${param_idx}"
            params.append(end_time)
            param_idx += 1

        query += f" ORDER BY transition_time DESC LIMIT ${param_idx}"
        params.append(limit)

        rows = await self.db_manager.fetch(query, *params)
        return [dict(row) for row in rows]

    async def get_track_statistics(
        self,
        camera_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        """
        Get tracking statistics

        Args:
            camera_id: Filter by camera ID
            start_time: Start time filter
            end_time: End time filter

        Returns:
            Statistics dictionary
        """
        query = """
            SELECT
                camera_id,
                COUNT(*) as total_tracks,
                COUNT(*) FILTER (WHERE status = 'active') as active_tracks,
                COUNT(*) FILTER (WHERE status = 'lost') as lost_tracks,
                COUNT(*) FILTER (WHERE status = 'finished') as finished_tracks,
                AVG(confidence) as avg_confidence
            FROM tracked_objects
            WHERE 1=1
        """
        params = []
        param_idx = 1

        if camera_id is not None:
            query += f" AND camera_id = ${param_idx}"
            params.append(camera_id)
            param_idx += 1

        if start_time:
            query += f" AND last_seen >= ${param_idx}"
            params.append(start_time)
            param_idx += 1

        if end_time:
            query += f" AND last_seen <= ${param_idx}"
            params.append(end_time)
            param_idx += 1

        query += " GROUP BY camera_id"

        rows = await self.db_manager.fetch(query, *params)

        if len(rows) == 0:
            return {
                'camera_id': camera_id,
                'total_tracks': 0,
                'active_tracks': 0,
                'lost_tracks': 0,
                'finished_tracks': 0,
                'avg_confidence': 0.0
            }

        return dict(rows[0])

    async def get_detections_count(
        self,
        camera_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """
        Get total detection count

        Args:
            camera_id: Filter by camera ID
            start_time: Start time filter
            end_time: End time filter

        Returns:
            Number of detections
        """
        query = "SELECT COUNT(*) FROM detections WHERE 1=1"
        params = []
        param_idx = 1

        if camera_id is not None:
            query += f" AND camera_id = ${param_idx}"
            params.append(camera_id)
            param_idx += 1

        if start_time:
            query += f" AND timestamp >= ${param_idx}"
            params.append(start_time)
            param_idx += 1

        if end_time:
            query += f" AND timestamp <= ${param_idx}"
            params.append(end_time)
            param_idx += 1

        return await self.db_manager.fetchval(query, *params)

    async def cleanup_old_data(self, days: int = 90):
        """
        Clean up old tracking data

        Args:
            days: Delete data older than this many days
        """
        cutoff_time = datetime.now() - timedelta(days=days)

        # Delete old detections
        query = "DELETE FROM detections WHERE timestamp < $1"
        await self.db_manager.execute(query, cutoff_time)

        # Delete old zone transitions
        query = "DELETE FROM zone_transitions WHERE transition_time < $1"
        await self.db_manager.execute(query, cutoff_time)

        # Delete old finished tracks
        query = """
            DELETE FROM tracked_objects
            WHERE status = 'finished' AND last_seen < $1
        """
        await self.db_manager.execute(query, cutoff_time)

        logger.info(f"Cleaned up data older than {days} days")
