"""
WebSocket API Endpoints
Real-time data streaming via WebSocket.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
from loguru import logger
from datetime import datetime

from analytics.realtime_analytics import RealtimeAnalytics, EventType

router = APIRouter(prefix="/ws", tags=["websocket"])

# Global real-time analytics instance (will be injected)
realtime_analytics: Optional[RealtimeAnalytics] = None


def set_realtime_analytics(analytics: RealtimeAnalytics):
    """Inject real-time analytics instance"""
    global realtime_analytics
    realtime_analytics = analytics


@router.websocket("/analytics")
async def websocket_analytics(
    websocket: WebSocket,
    event_types: Optional[str] = Query(None, description="Comma-separated event types to subscribe")
):
    """
    WebSocket endpoint for real-time analytics

    Streams real-time analytics events to connected clients.

    Event Types:
    - worker_status: Worker status changes
    - productivity_update: Productivity updates
    - zone_transition: Zone transition events
    - alert: Alert notifications
    - system_status: System status updates
    - metrics_snapshot: Metrics snapshots

    Example:
        ws://localhost:8000/ws/analytics
        ws://localhost:8000/ws/analytics?event_types=alert,worker_status
    """
    await websocket.accept()

    if not realtime_analytics:
        await websocket.send_json({
            "error": "Real-time analytics not initialized"
        })
        await websocket.close()
        return

    # Parse event type filter
    event_filter = None
    if event_types:
        try:
            event_filter = set(event_types.split(","))
        except Exception as e:
            logger.warning(f"Invalid event_types parameter: {e}")

    # Register connection
    await realtime_analytics.connect(websocket)

    try:
        # Send welcome message
        await websocket.send_json({
            "event_type": "connection",
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to real-time analytics stream",
            "connection_id": id(websocket),
            "total_connections": realtime_analytics.get_connection_count(),
            "event_filter": list(event_filter) if event_filter else None
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive message from client (for ping/pong or commands)
                data = await websocket.receive_text()

                # Handle client commands
                if data == "ping":
                    await websocket.send_json({
                        "event_type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                elif data == "get_metrics":
                    metrics = await realtime_analytics.get_metrics_snapshot()
                    await websocket.send_json({
                        "event_type": "metrics_snapshot",
                        "timestamp": datetime.now().isoformat(),
                        "data": metrics
                    })
                elif data.startswith("get_history"):
                    # get_history:alert:10
                    parts = data.split(":")
                    event_type = parts[1] if len(parts) > 1 else None
                    limit = int(parts[2]) if len(parts) > 2 else 50

                    history = await realtime_analytics.get_event_history(
                        event_type=EventType(event_type) if event_type else None,
                        limit=limit
                    )
                    await websocket.send_json({
                        "event_type": "history",
                        "timestamp": datetime.now().isoformat(),
                        "data": history
                    })
                elif data == "get_stats":
                    stats = realtime_analytics.get_stats()
                    await websocket.send_json({
                        "event_type": "stats",
                        "timestamp": datetime.now().isoformat(),
                        "data": stats
                    })

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket.send_json({
                    "event_type": "error",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                })

    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Unregister connection
        await realtime_analytics.disconnect(websocket)


@router.websocket("/live-metrics")
async def websocket_live_metrics(websocket: WebSocket):
    """
    WebSocket endpoint for live metrics only

    Streams simplified metrics updates at regular intervals.
    Lighter weight than full analytics stream.

    Example:
        ws://localhost:8000/ws/live-metrics
    """
    await websocket.accept()

    if not realtime_analytics:
        await websocket.send_json({
            "error": "Real-time analytics not initialized"
        })
        await websocket.close()
        return

    await realtime_analytics.connect(websocket)

    try:
        import asyncio

        while True:
            # Send metrics every 2 seconds
            await asyncio.sleep(2)

            metrics = await realtime_analytics.get_metrics_snapshot()
            await websocket.send_json({
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics
            })

    except WebSocketDisconnect:
        logger.info("Live metrics client disconnected")
    except Exception as e:
        logger.error(f"Live metrics error: {e}")
    finally:
        await realtime_analytics.disconnect(websocket)
