"""
Analytics REST API Endpoints
Advanced analytics queries and data retrieval.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from analytics.realtime_analytics import RealtimeAnalytics, EventType

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

# Global instances (will be injected)
realtime_analytics: Optional[RealtimeAnalytics] = None


def set_realtime_analytics(analytics: RealtimeAnalytics):
    """Inject real-time analytics instance"""
    global realtime_analytics
    realtime_analytics = analytics


# Pydantic models
class MetricsSnapshot(BaseModel):
    """Current metrics snapshot"""
    total_workers: int
    active_workers: int
    avg_productivity: float
    total_output: int
    alerts_count: int
    last_update: str


class AnalyticsStats(BaseModel):
    """Analytics system statistics"""
    active_connections: int
    event_queue_size: int
    event_history_size: int
    is_running: bool
    current_metrics: Dict[str, Any]


class EventHistoryRequest(BaseModel):
    """Event history query request"""
    event_type: Optional[str] = Field(None, description="Filter by event type")
    limit: int = Field(50, ge=1, le=500, description="Maximum events to return")


class EventHistoryResponse(BaseModel):
    """Event history response"""
    total_events: int
    events: List[Dict[str, Any]]


# Endpoints

@router.get("/metrics", response_model=MetricsSnapshot)
async def get_current_metrics():
    """
    Get current real-time metrics snapshot

    Returns:
        Current metrics including worker counts, productivity, output, etc.
    """
    if not realtime_analytics:
        raise HTTPException(status_code=503, detail="Real-time analytics not initialized")

    try:
        metrics = await realtime_analytics.get_metrics_snapshot()
        return MetricsSnapshot(**metrics)
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=AnalyticsStats)
async def get_analytics_stats():
    """
    Get analytics system statistics

    Returns:
        System statistics including connection count, queue sizes, etc.
    """
    if not realtime_analytics:
        raise HTTPException(status_code=503, detail="Real-time analytics not initialized")

    try:
        stats = realtime_analytics.get_stats()
        return AnalyticsStats(**stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=EventHistoryResponse)
async def get_event_history(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(50, ge=1, le=500, description="Maximum events to return")
):
    """
    Get event history

    Args:
        event_type: Optional event type filter (worker_status, productivity_update, etc.)
        limit: Maximum number of events to return (1-500)

    Returns:
        List of historical events
    """
    if not realtime_analytics:
        raise HTTPException(status_code=503, detail="Real-time analytics not initialized")

    try:
        # Validate event type
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = EventType(event_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid event type. Valid types: {[e.value for e in EventType]}"
                )

        events = await realtime_analytics.get_event_history(
            event_type=event_type_enum,
            limit=limit
        )

        return EventHistoryResponse(
            total_events=len(events),
            events=events
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections")
async def get_connection_info():
    """
    Get WebSocket connection information

    Returns:
        Information about active WebSocket connections
    """
    if not realtime_analytics:
        raise HTTPException(status_code=503, detail="Real-time analytics not initialized")

    try:
        return {
            "active_connections": realtime_analytics.get_connection_count(),
            "is_running": realtime_analytics.is_running,
            "websocket_endpoints": [
                "/ws/analytics",
                "/ws/live-metrics"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting connection info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-event")
async def test_event(
    event_type: str = Query(..., description="Event type to test"),
    message: str = Query("Test event", description="Test message")
):
    """
    Test event publishing (development only)

    Args:
        event_type: Type of event to publish
        message: Test message

    Returns:
        Success message
    """
    if not realtime_analytics:
        raise HTTPException(status_code=503, detail="Real-time analytics not initialized")

    try:
        # Validate event type
        try:
            EventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type. Valid types: {[e.value for e in EventType]}"
            )

        # Publish test event based on type
        if event_type == "worker_status":
            await realtime_analytics.update_worker_status(
                worker_id="TEST001",
                worker_name="Test Worker",
                status="active",
                current_zone="Test Zone",
                productivity=85.5
            )
        elif event_type == "productivity_update":
            await realtime_analytics.update_productivity(
                worker_id="TEST001",
                worker_name="Test Worker",
                indices={
                    "index_11_overall_productivity": 85.5,
                    "index_5_work_efficiency": 78.2
                },
                shift="morning"
            )
        elif event_type == "alert":
            await realtime_analytics.publish_alert(
                alert_type="test_alert",
                message=message,
                severity="warning",
                worker_id="TEST001",
                worker_name="Test Worker"
            )
        elif event_type == "system_status":
            await realtime_analytics.publish_system_status({
                "status": "healthy",
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
        else:
            raise HTTPException(status_code=400, detail="Event type not supported for testing")

        return {
            "success": True,
            "event_type": event_type,
            "message": "Test event published successfully",
            "active_connections": realtime_analytics.get_connection_count()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing test event: {e}")
        raise HTTPException(status_code=500, detail=str(e))
