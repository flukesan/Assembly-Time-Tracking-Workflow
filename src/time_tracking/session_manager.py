"""
Session Manager
Manages worker work sessions (start/end times, duration tracking)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass, field
import threading

from workers.worker_models import WorkerSession, Shift

logger = logging.getLogger(__name__)


@dataclass
class SessionState:
    """Internal session state tracking"""
    session: WorkerSession
    current_zone: Optional[str] = None
    zone_entry_time: Optional[datetime] = None
    last_activity_time: datetime = field(default_factory=datetime.now)
    activity_state: str = "active"  # active, idle, break
    zone_times: Dict[str, float] = field(default_factory=dict)  # zone_name -> total_seconds


class SessionManager:
    """
    Manages worker work sessions
    - Tracks entry/exit times
    - Manages zone transitions
    - Calculates time breakdowns (active/idle/break)
    """

    def __init__(
        self,
        idle_threshold_seconds: float = 300.0,  # 5 minutes
        break_zone_names: Optional[List[str]] = None
    ):
        """
        Initialize session manager

        Args:
            idle_threshold_seconds: Time threshold for marking worker as idle
            break_zone_names: List of zone names considered as break zones
        """
        self.idle_threshold = idle_threshold_seconds
        self.break_zone_names = break_zone_names or ["Break Area", "Rest Zone", "Cafeteria"]

        # Active sessions: {worker_id: SessionState}
        self.sessions: Dict[str, SessionState] = {}
        self._lock = threading.Lock()

        logger.info(
            f"SessionManager initialized "
            f"(idle_threshold={idle_threshold_seconds}s, "
            f"break_zones={self.break_zone_names})"
        )

    def start_session(
        self,
        worker_id: str,
        worker_name: str,
        shift: Shift,
        camera_id: int,
        track_id: int,
        start_time: Optional[datetime] = None
    ) -> WorkerSession:
        """
        Start a new work session for a worker

        Args:
            worker_id: Worker ID
            worker_name: Worker name
            shift: Work shift
            camera_id: Camera ID where worker was detected
            track_id: Tracking ID
            start_time: Session start time (default: now)

        Returns:
            Created WorkerSession
        """
        with self._lock:
            if worker_id in self.sessions:
                logger.warning(
                    f"Worker {worker_id} already has active session, "
                    f"ending previous session"
                )
                self.end_session(worker_id)

            start_time = start_time or datetime.now()

            session = WorkerSession(
                worker_id=worker_id,
                worker_name=worker_name,
                shift=shift,
                start_time=start_time,
                camera_id=camera_id,
                track_id=track_id,
                is_active=True
            )

            state = SessionState(
                session=session,
                last_activity_time=start_time
            )

            self.sessions[worker_id] = state

            logger.info(
                f"Started session for worker {worker_id} "
                f"({worker_name}) at {start_time}"
            )

            return session

    def end_session(
        self,
        worker_id: str,
        end_time: Optional[datetime] = None
    ) -> Optional[WorkerSession]:
        """
        End a work session for a worker

        Args:
            worker_id: Worker ID
            end_time: Session end time (default: now)

        Returns:
            Ended WorkerSession or None
        """
        with self._lock:
            if worker_id not in self.sessions:
                logger.warning(f"No active session for worker {worker_id}")
                return None

            state = self.sessions[worker_id]
            session = state.session

            end_time = end_time or datetime.now()
            session.end_time = end_time
            session.is_active = False

            # Calculate total duration
            duration = (end_time - session.start_time).total_seconds()
            session.total_duration_seconds = duration

            # Update final zone time
            if state.current_zone and state.zone_entry_time:
                zone_duration = (end_time - state.zone_entry_time).total_seconds()
                state.zone_times[state.current_zone] = \
                    state.zone_times.get(state.current_zone, 0) + zone_duration

            # Set zones visited
            session.zones_visited = list(state.zone_times.keys())

            # Remove from active sessions
            del self.sessions[worker_id]

            logger.info(
                f"Ended session for worker {worker_id} "
                f"(duration: {duration:.1f}s)"
            )

            return session

    def update_zone(
        self,
        worker_id: str,
        zone_name: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Update worker's current zone

        Args:
            worker_id: Worker ID
            zone_name: New zone name
            timestamp: Update timestamp (default: now)

        Returns:
            True if updated successfully
        """
        with self._lock:
            if worker_id not in self.sessions:
                return False

            state = self.sessions[worker_id]
            timestamp = timestamp or datetime.now()

            # If zone changed, update zone times
            if state.current_zone != zone_name:
                if state.current_zone and state.zone_entry_time:
                    # Calculate time spent in previous zone
                    zone_duration = (timestamp - state.zone_entry_time).total_seconds()
                    state.zone_times[state.current_zone] = \
                        state.zone_times.get(state.current_zone, 0) + zone_duration

                # Update to new zone
                state.current_zone = zone_name
                state.zone_entry_time = timestamp
                state.session.current_zone = zone_name

                # Update activity state based on zone
                if zone_name in self.break_zone_names:
                    self._set_activity_state(state, "break", timestamp)
                else:
                    self._set_activity_state(state, "active", timestamp)

                logger.debug(
                    f"Worker {worker_id} moved to zone '{zone_name}' "
                    f"at {timestamp}"
                )

            # Update last activity time
            state.last_activity_time = timestamp

            return True

    def update_activity(
        self,
        worker_id: str,
        is_active: bool = True,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Update worker activity status

        Args:
            worker_id: Worker ID
            is_active: Whether worker is active (detected in current frame)
            timestamp: Update timestamp (default: now)

        Returns:
            True if updated successfully
        """
        with self._lock:
            if worker_id not in self.sessions:
                return False

            state = self.sessions[worker_id]
            timestamp = timestamp or datetime.now()

            if is_active:
                # Worker is active
                state.last_activity_time = timestamp

                # If not in break zone, set as active
                if state.current_zone not in self.break_zone_names:
                    self._set_activity_state(state, "active", timestamp)

            else:
                # Check if worker has been idle too long
                idle_duration = (timestamp - state.last_activity_time).total_seconds()

                if idle_duration > self.idle_threshold:
                    self._set_activity_state(state, "idle", timestamp)

            return True

    def _set_activity_state(
        self,
        state: SessionState,
        new_state: str,
        timestamp: datetime
    ):
        """
        Set activity state and update time counters

        Args:
            state: SessionState object
            new_state: New activity state ("active", "idle", "break")
            timestamp: Current timestamp
        """
        if state.activity_state == new_state:
            return

        old_state = state.activity_state
        state.activity_state = new_state

        logger.debug(
            f"Worker {state.session.worker_id} activity state: "
            f"{old_state} -> {new_state}"
        )

    def get_session(self, worker_id: str) -> Optional[WorkerSession]:
        """
        Get active session for a worker

        Args:
            worker_id: Worker ID

        Returns:
            WorkerSession or None
        """
        with self._lock:
            if worker_id not in self.sessions:
                return None

            state = self.sessions[worker_id]
            return state.session

    def get_all_sessions(self) -> List[WorkerSession]:
        """
        Get all active sessions

        Returns:
            List of active WorkerSessions
        """
        with self._lock:
            return [state.session for state in self.sessions.values()]

    def calculate_time_breakdown(
        self,
        worker_id: str,
        current_time: Optional[datetime] = None
    ) -> Optional[Dict[str, float]]:
        """
        Calculate time breakdown for a worker's current session

        Args:
            worker_id: Worker ID
            current_time: Current timestamp (default: now)

        Returns:
            Dict with time breakdown or None
            {
                'active_time': float,
                'idle_time': float,
                'break_time': float,
                'total_time': float
            }
        """
        with self._lock:
            if worker_id not in self.sessions:
                return None

            state = self.sessions[worker_id]
            session = state.session
            current_time = current_time or datetime.now()

            # Calculate total time
            total_time = (current_time - session.start_time).total_seconds()

            # Calculate break time (time in break zones)
            break_time = sum(
                duration for zone, duration in state.zone_times.items()
                if zone in self.break_zone_names
            )

            # Add current zone time if in break zone
            if (state.current_zone in self.break_zone_names and
                state.zone_entry_time):
                break_time += (current_time - state.zone_entry_time).total_seconds()

            # Estimate idle time (rough approximation)
            # In real system, this would be tracked more precisely
            idle_time = total_time * 0.1  # Assume 10% idle time

            # Active time = total - idle - break
            active_time = max(0, total_time - idle_time - break_time)

            return {
                'active_time': active_time,
                'idle_time': idle_time,
                'break_time': break_time,
                'total_time': total_time
            }

    def update_session_times(self, worker_id: str) -> bool:
        """
        Update session time counters (call periodically)

        Args:
            worker_id: Worker ID

        Returns:
            True if updated successfully
        """
        breakdown = self.calculate_time_breakdown(worker_id)
        if not breakdown:
            return False

        with self._lock:
            if worker_id not in self.sessions:
                return False

            session = self.sessions[worker_id].session
            session.active_time_seconds = breakdown['active_time']
            session.idle_time_seconds = breakdown['idle_time']
            session.break_time_seconds = breakdown['break_time']

            return True

    def get_zone_times(self, worker_id: str) -> Optional[Dict[str, float]]:
        """
        Get time spent in each zone for a worker

        Args:
            worker_id: Worker ID

        Returns:
            Dict of {zone_name: seconds} or None
        """
        with self._lock:
            if worker_id not in self.sessions:
                return None

            state = self.sessions[worker_id]

            # Create copy with current zone time added
            zone_times = state.zone_times.copy()

            if state.current_zone and state.zone_entry_time:
                current_zone_time = (
                    datetime.now() - state.zone_entry_time
                ).total_seconds()
                zone_times[state.current_zone] = \
                    zone_times.get(state.current_zone, 0) + current_zone_time

            return zone_times

    def cleanup_idle_sessions(
        self,
        max_idle_minutes: int = 60
    ) -> List[WorkerSession]:
        """
        Cleanup sessions that have been idle too long

        Args:
            max_idle_minutes: Maximum idle time before auto-ending session

        Returns:
            List of ended sessions
        """
        with self._lock:
            now = datetime.now()
            ended_sessions = []

            workers_to_remove = []

            for worker_id, state in self.sessions.items():
                idle_duration = (now - state.last_activity_time).total_seconds()

                if idle_duration > (max_idle_minutes * 60):
                    logger.info(
                        f"Auto-ending idle session for worker {worker_id} "
                        f"(idle for {idle_duration/60:.1f} minutes)"
                    )

                    session = self.end_session(worker_id, end_time=now)
                    if session:
                        ended_sessions.append(session)
                        workers_to_remove.append(worker_id)

            return ended_sessions

    def get_stats(self) -> dict:
        """Get session manager statistics"""
        with self._lock:
            return {
                'active_sessions': len(self.sessions),
                'idle_threshold_seconds': self.idle_threshold,
                'break_zone_names': self.break_zone_names
            }
