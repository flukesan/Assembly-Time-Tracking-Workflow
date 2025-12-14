"""
Real-time Analytics Manager
Provides real-time analytics updates via WebSocket connections.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from loguru import logger


class EventType(str, Enum):
    """Real-time event types"""
    WORKER_STATUS = "worker_status"
    PRODUCTIVITY_UPDATE = "productivity_update"
    ZONE_TRANSITION = "zone_transition"
    ALERT = "alert"
    SYSTEM_STATUS = "system_status"
    METRICS_SNAPSHOT = "metrics_snapshot"


@dataclass
class RealtimeEvent:
    """Real-time event data structure"""
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    severity: str = "info"  # info, warning, critical

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "severity": self.severity
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class RealtimeAnalytics:
    """
    Real-time Analytics Manager

    Manages WebSocket connections and broadcasts real-time analytics updates.
    """

    def __init__(self):
        """Initialize real-time analytics manager"""
        self.active_connections: Set[Any] = set()
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        self.broadcast_task: Optional[asyncio.Task] = None

        # Metrics cache
        self.current_metrics: Dict[str, Any] = {
            "total_workers": 0,
            "active_workers": 0,
            "avg_productivity": 0.0,
            "total_output": 0,
            "alerts_count": 0,
            "last_update": datetime.now().isoformat()
        }

        # Event history (keep last 100 events)
        self.event_history: List[RealtimeEvent] = []
        self.max_history = 100

        logger.info("Real-time Analytics Manager initialized")

    async def start(self):
        """Start the real-time analytics broadcast loop"""
        if self.is_running:
            logger.warning("Real-time analytics already running")
            return

        self.is_running = True
        self.broadcast_task = asyncio.create_task(self._broadcast_loop())
        logger.info("Real-time analytics started")

    async def stop(self):
        """Stop the real-time analytics broadcast loop"""
        self.is_running = False

        if self.broadcast_task:
            self.broadcast_task.cancel()
            try:
                await self.broadcast_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        for connection in self.active_connections.copy():
            await self.disconnect(connection)

        logger.info("Real-time analytics stopped")

    async def connect(self, websocket: Any):
        """
        Register a new WebSocket connection

        Args:
            websocket: WebSocket connection object
        """
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

        # Send current metrics immediately
        await self._send_to_client(
            websocket,
            RealtimeEvent(
                event_type=EventType.METRICS_SNAPSHOT,
                timestamp=datetime.now(),
                data=self.current_metrics,
                severity="info"
            )
        )

    async def disconnect(self, websocket: Any):
        """
        Unregister a WebSocket connection

        Args:
            websocket: WebSocket connection object
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def publish_event(self, event: RealtimeEvent):
        """
        Publish an event to all connected clients

        Args:
            event: RealtimeEvent to publish
        """
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        # Add to queue for broadcasting
        await self.event_queue.put(event)

    async def update_worker_status(
        self,
        worker_id: str,
        worker_name: str,
        status: str,
        current_zone: Optional[str] = None,
        productivity: Optional[float] = None
    ):
        """
        Publish worker status update

        Args:
            worker_id: Worker ID
            worker_name: Worker name
            status: Worker status (active, idle, break, offline)
            current_zone: Current zone name
            productivity: Current productivity index
        """
        event = RealtimeEvent(
            event_type=EventType.WORKER_STATUS,
            timestamp=datetime.now(),
            data={
                "worker_id": worker_id,
                "worker_name": worker_name,
                "status": status,
                "current_zone": current_zone,
                "productivity": productivity
            },
            severity="info"
        )
        await self.publish_event(event)

    async def update_productivity(
        self,
        worker_id: str,
        worker_name: str,
        indices: Dict[str, float],
        shift: str
    ):
        """
        Publish productivity update

        Args:
            worker_id: Worker ID
            worker_name: Worker name
            indices: Productivity indices dictionary
            shift: Worker shift
        """
        event = RealtimeEvent(
            event_type=EventType.PRODUCTIVITY_UPDATE,
            timestamp=datetime.now(),
            data={
                "worker_id": worker_id,
                "worker_name": worker_name,
                "shift": shift,
                "indices": indices,
                "overall_productivity": indices.get("index_11_overall_productivity", 0.0)
            },
            severity="info"
        )
        await self.publish_event(event)

        # Update global metrics
        await self._update_global_metrics()

    async def publish_zone_transition(
        self,
        worker_id: str,
        worker_name: str,
        from_zone: Optional[str],
        to_zone: str,
        duration_in_previous: Optional[float] = None
    ):
        """
        Publish zone transition event

        Args:
            worker_id: Worker ID
            worker_name: Worker name
            from_zone: Previous zone
            to_zone: New zone
            duration_in_previous: Duration in previous zone (seconds)
        """
        event = RealtimeEvent(
            event_type=EventType.ZONE_TRANSITION,
            timestamp=datetime.now(),
            data={
                "worker_id": worker_id,
                "worker_name": worker_name,
                "from_zone": from_zone,
                "to_zone": to_zone,
                "duration_in_previous": duration_in_previous
            },
            severity="info"
        )
        await self.publish_event(event)

    async def publish_alert(
        self,
        alert_type: str,
        message: str,
        severity: str,
        worker_id: Optional[str] = None,
        worker_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Publish alert event

        Args:
            alert_type: Type of alert (low_productivity, idle_time, quality_issue, etc.)
            message: Alert message
            severity: Alert severity (info, warning, critical)
            worker_id: Related worker ID
            worker_name: Related worker name
            details: Additional details
        """
        event = RealtimeEvent(
            event_type=EventType.ALERT,
            timestamp=datetime.now(),
            data={
                "alert_type": alert_type,
                "message": message,
                "worker_id": worker_id,
                "worker_name": worker_name,
                "details": details or {}
            },
            severity=severity
        )
        await self.publish_event(event)

        # Update alerts count
        self.current_metrics["alerts_count"] += 1

    async def publish_system_status(self, status: Dict[str, Any]):
        """
        Publish system status update

        Args:
            status: System status dictionary
        """
        event = RealtimeEvent(
            event_type=EventType.SYSTEM_STATUS,
            timestamp=datetime.now(),
            data=status,
            severity="info"
        )
        await self.publish_event(event)

    async def get_metrics_snapshot(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot

        Returns:
            Current metrics dictionary
        """
        return self.current_metrics.copy()

    async def get_event_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get event history

        Args:
            event_type: Filter by event type
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        events = self.event_history

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        # Get last N events
        events = events[-limit:]

        return [e.to_dict() for e in events]

    async def _broadcast_loop(self):
        """Background task to broadcast events to all clients"""
        try:
            while self.is_running:
                try:
                    # Get event from queue with timeout
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=1.0
                    )

                    # Broadcast to all connected clients
                    await self._broadcast_to_all(event)

                except asyncio.TimeoutError:
                    # No events in queue, continue
                    continue
                except Exception as e:
                    logger.error(f"Error in broadcast loop: {e}")
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("Broadcast loop cancelled")
        except Exception as e:
            logger.error(f"Fatal error in broadcast loop: {e}")

    async def _broadcast_to_all(self, event: RealtimeEvent):
        """
        Broadcast event to all connected clients

        Args:
            event: RealtimeEvent to broadcast
        """
        if not self.active_connections:
            return

        # Send to all clients
        disconnected = []
        for connection in self.active_connections:
            try:
                await self._send_to_client(connection, event)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            await self.disconnect(connection)

    async def _send_to_client(self, websocket: Any, event: RealtimeEvent):
        """
        Send event to a specific client

        Args:
            websocket: WebSocket connection
            event: RealtimeEvent to send
        """
        try:
            await websocket.send_text(event.to_json())
        except Exception as e:
            logger.error(f"Error sending to client: {e}")
            raise

    async def _update_global_metrics(self):
        """Update global metrics (called periodically)"""
        # This would query the database for current metrics
        # For now, we'll update the timestamp
        self.current_metrics["last_update"] = datetime.now().isoformat()

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get analytics statistics

        Returns:
            Statistics dictionary
        """
        return {
            "active_connections": len(self.active_connections),
            "event_queue_size": self.event_queue.qsize(),
            "event_history_size": len(self.event_history),
            "is_running": self.is_running,
            "current_metrics": self.current_metrics
        }
