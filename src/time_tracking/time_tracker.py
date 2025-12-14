"""
Time Tracker
Main interface for time tracking functionality
Integrates SessionManager and ProductivityCalculator
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict
import threading

from workers.worker_models import Worker, WorkerSession, ProductivityIndex, Shift
from .session_manager import SessionManager
from .productivity_calculator import ProductivityCalculator

logger = logging.getLogger(__name__)


class TimeTracker:
    """
    Main time tracking interface
    - Manages worker sessions
    - Tracks zone times
    - Calculates productivity indices
    """

    def __init__(
        self,
        idle_threshold_seconds: float = 300.0,
        break_zone_names: Optional[List[str]] = None,
        target_output_per_hour: float = 10.0
    ):
        """
        Initialize time tracker

        Args:
            idle_threshold_seconds: Time threshold for idle detection
            break_zone_names: List of break zone names
            target_output_per_hour: Target output for productivity calculation
        """
        self.session_manager = SessionManager(
            idle_threshold_seconds=idle_threshold_seconds,
            break_zone_names=break_zone_names
        )

        self.productivity_calculator = ProductivityCalculator(
            target_output_per_hour=target_output_per_hour
        )

        # Track worker productivity data
        # {worker_id: {'tasks_completed': int, 'quality_scores': [float], ...}}
        self.worker_data: Dict[str, Dict] = {}
        self._lock = threading.Lock()

        logger.info("TimeTracker initialized")

    def worker_detected(
        self,
        worker: Worker,
        camera_id: int,
        track_id: int,
        zone_name: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> WorkerSession:
        """
        Called when a worker is detected (start or update session)

        Args:
            worker: Worker object
            camera_id: Camera ID
            track_id: Tracking ID
            zone_name: Current zone name
            timestamp: Detection timestamp

        Returns:
            Current WorkerSession
        """
        timestamp = timestamp or datetime.now()

        # Check if session exists
        session = self.session_manager.get_session(worker.worker_id)

        if session is None:
            # Start new session
            session = self.session_manager.start_session(
                worker_id=worker.worker_id,
                worker_name=worker.name,
                shift=worker.shift,
                camera_id=camera_id,
                track_id=track_id,
                start_time=timestamp
            )

            logger.info(f"Started tracking for worker {worker.name}")

            # Initialize worker data
            with self._lock:
                if worker.worker_id not in self.worker_data:
                    self.worker_data[worker.worker_id] = {
                        'tasks_completed': 0,
                        'quality_scores': [],
                        'zone_transitions': []
                    }

        # Update zone if provided
        if zone_name:
            self.session_manager.update_zone(
                worker_id=worker.worker_id,
                zone_name=zone_name,
                timestamp=timestamp
            )

        # Update activity
        self.session_manager.update_activity(
            worker_id=worker.worker_id,
            is_active=True,
            timestamp=timestamp
        )

        return session

    def worker_lost(
        self,
        worker_id: str,
        timestamp: Optional[datetime] = None
    ) -> Optional[WorkerSession]:
        """
        Called when a worker is lost from tracking

        Args:
            worker_id: Worker ID
            timestamp: Timestamp when lost

        Returns:
            Ended WorkerSession or None
        """
        timestamp = timestamp or datetime.now()

        # Mark as inactive (but don't end session yet - they might return)
        self.session_manager.update_activity(
            worker_id=worker_id,
            is_active=False,
            timestamp=timestamp
        )

        logger.debug(f"Worker {worker_id} lost from tracking")
        return None

    def end_worker_session(
        self,
        worker_id: str,
        timestamp: Optional[datetime] = None
    ) -> Optional[WorkerSession]:
        """
        Explicitly end a worker's session

        Args:
            worker_id: Worker ID
            timestamp: End timestamp

        Returns:
            Ended WorkerSession or None
        """
        session = self.session_manager.end_session(worker_id, timestamp)

        if session:
            logger.info(
                f"Ended session for worker {worker_id} "
                f"(duration: {session.total_duration_seconds:.1f}s)"
            )

        return session

    def update_zone_transition(
        self,
        worker_id: str,
        from_zone: str,
        to_zone: str,
        duration_in_prev_zone: float,
        timestamp: Optional[datetime] = None
    ):
        """
        Record a zone transition

        Args:
            worker_id: Worker ID
            from_zone: Previous zone name
            to_zone: New zone name
            duration_in_prev_zone: Time spent in previous zone (seconds)
            timestamp: Transition timestamp
        """
        with self._lock:
            if worker_id in self.worker_data:
                self.worker_data[worker_id]['zone_transitions'].append({
                    'from_zone': from_zone,
                    'to_zone': to_zone,
                    'duration': duration_in_prev_zone,
                    'timestamp': timestamp or datetime.now()
                })

    def record_task_completed(
        self,
        worker_id: str,
        quality_score: Optional[float] = None
    ):
        """
        Record a completed task for a worker

        Args:
            worker_id: Worker ID
            quality_score: Optional quality score (0-100)
        """
        with self._lock:
            if worker_id not in self.worker_data:
                self.worker_data[worker_id] = {
                    'tasks_completed': 0,
                    'quality_scores': [],
                    'zone_transitions': []
                }

            self.worker_data[worker_id]['tasks_completed'] += 1

            if quality_score is not None:
                self.worker_data[worker_id]['quality_scores'].append(quality_score)

            logger.info(
                f"Task completed for worker {worker_id} "
                f"(total: {self.worker_data[worker_id]['tasks_completed']})"
            )

    def calculate_productivity(
        self,
        worker_id: str,
        current_time: Optional[datetime] = None
    ) -> Optional[ProductivityIndex]:
        """
        Calculate productivity indices for a worker

        Args:
            worker_id: Worker ID
            current_time: Current timestamp

        Returns:
            ProductivityIndex or None
        """
        # Update session times
        self.session_manager.update_session_times(worker_id)

        # Get session
        session = self.session_manager.get_session(worker_id)
        if not session:
            logger.warning(f"No active session for worker {worker_id}")
            return None

        # Get worker data
        with self._lock:
            worker_data = self.worker_data.get(worker_id, {
                'tasks_completed': 0,
                'quality_scores': [],
                'zone_transitions': []
            })

        # Calculate average quality score
        quality_scores = worker_data.get('quality_scores', [])
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 100.0

        # Calculate productivity indices
        indices = self.productivity_calculator.calculate_indices(
            session=session,
            zone_transitions=worker_data.get('zone_transitions', []),
            tasks_completed=worker_data.get('tasks_completed', 0),
            quality_score=avg_quality,
            current_time=current_time
        )

        return indices

    def get_session(self, worker_id: str) -> Optional[WorkerSession]:
        """
        Get active session for a worker

        Args:
            worker_id: Worker ID

        Returns:
            WorkerSession or None
        """
        return self.session_manager.get_session(worker_id)

    def get_all_sessions(self) -> List[WorkerSession]:
        """
        Get all active sessions

        Returns:
            List of active WorkerSessions
        """
        return self.session_manager.get_all_sessions()

    def get_zone_times(self, worker_id: str) -> Optional[Dict[str, float]]:
        """
        Get time spent in each zone for a worker

        Args:
            worker_id: Worker ID

        Returns:
            Dict of {zone_name: seconds} or None
        """
        return self.session_manager.get_zone_times(worker_id)

    def get_recommendations(
        self,
        worker_id: str
    ) -> List[str]:
        """
        Get productivity recommendations for a worker

        Args:
            worker_id: Worker ID

        Returns:
            List of recommendation strings
        """
        indices = self.calculate_productivity(worker_id)
        if not indices:
            return ["No active session for worker"]

        return self.productivity_calculator.get_recommendations(indices)

    def cleanup_idle_sessions(
        self,
        max_idle_minutes: int = 60
    ) -> List[WorkerSession]:
        """
        Auto-end sessions that have been idle too long

        Args:
            max_idle_minutes: Maximum idle time

        Returns:
            List of ended sessions
        """
        return self.session_manager.cleanup_idle_sessions(max_idle_minutes)

    def get_stats(self) -> dict:
        """Get time tracker statistics"""
        session_stats = self.session_manager.get_stats()
        calc_stats = self.productivity_calculator.get_stats()

        with self._lock:
            worker_count = len(self.worker_data)
            total_tasks = sum(
                data.get('tasks_completed', 0)
                for data in self.worker_data.values()
            )

        return {
            'session_manager': session_stats,
            'productivity_calculator': calc_stats,
            'tracked_workers': worker_count,
            'total_tasks_completed': total_tasks
        }
