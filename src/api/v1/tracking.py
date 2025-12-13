"""
Tracking API
Endpoints for multi-object tracking and analytics
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/tracking", tags=["tracking"])

# Global tracking manager and database (will be injected during startup)
tracking_manager = None
tracking_writer = None


def set_tracking_manager(manager):
    """Set global tracking manager instance"""
    global tracking_manager
    tracking_manager = manager


def set_tracking_writer(writer):
    """Set global tracking writer instance"""
    global tracking_writer
    tracking_writer = writer


@router.get("/active")
async def get_active_tracks(camera_id: Optional[int] = Query(None)):
    """Get currently active tracks"""
    if tracking_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tracking manager not initialized"
        )

    active_tracks = tracking_manager.get_active_tracks(camera_id)

    return {
        "camera_tracks": active_tracks,
        "total_active": sum(active_tracks.values())
    }


@router.get("/stats")
async def get_tracking_stats(camera_id: Optional[int] = Query(None)):
    """Get tracking statistics"""
    if tracking_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tracking manager not initialized"
        )

    stats = tracking_manager.get_stats()

    # Add database stats if available
    if tracking_writer:
        try:
            db_stats = await tracking_writer.get_track_statistics(camera_id=camera_id)
            stats['database'] = db_stats
        except Exception as e:
            stats['database_error'] = str(e)

    return stats


@router.get("/history/{track_id}")
async def get_track_history(
    track_id: int,
    camera_id: int,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None)
):
    """Get full history for a specific track"""
    if tracking_writer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tracking writer not initialized"
        )

    try:
        history = await tracking_writer.get_track_history(
            track_id=track_id,
            camera_id=camera_id,
            start_time=start_time,
            end_time=end_time
        )

        return {
            "track_id": track_id,
            "camera_id": camera_id,
            "total_detections": len(history),
            "history": history
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get track history: {str(e)}"
        )


@router.get("/transitions")
async def get_zone_transitions(
    track_id: Optional[int] = Query(None),
    camera_id: Optional[int] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get zone transition events"""
    if tracking_writer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tracking writer not initialized"
        )

    try:
        transitions = await tracking_writer.get_zone_transitions(
            track_id=track_id,
            camera_id=camera_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

        return {
            "total": len(transitions),
            "transitions": transitions
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transitions: {str(e)}"
        )


@router.post("/reset/{camera_id}")
async def reset_camera_tracking(camera_id: int):
    """Reset tracking for a specific camera"""
    if tracking_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tracking manager not initialized"
        )

    tracking_manager.reset_camera(camera_id)

    return {
        "message": f"Tracking reset for camera {camera_id}",
        "camera_id": camera_id
    }


@router.post("/reset")
async def reset_all_tracking():
    """Reset tracking for all cameras"""
    if tracking_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tracking manager not initialized"
        )

    tracking_manager.reset_all()

    return {
        "message": "All tracking reset"
    }


@router.get("/detections/count")
async def get_detections_count(
    camera_id: Optional[int] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None)
):
    """Get total detection count"""
    if tracking_writer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tracking writer not initialized"
        )

    try:
        count = await tracking_writer.get_detections_count(
            camera_id=camera_id,
            start_time=start_time,
            end_time=end_time
        )

        return {
            "camera_id": camera_id,
            "start_time": start_time,
            "end_time": end_time,
            "count": count
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get detection count: {str(e)}"
        )
