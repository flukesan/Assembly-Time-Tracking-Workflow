"""
Worker API
Endpoints for worker management, face enrollment, and productivity tracking
"""

from fastapi import APIRouter, HTTPException, status, Query, UploadFile, File
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel
import numpy as np
import cv2
import logging

from workers.worker_models import Worker, WorkerSession, ProductivityIndex, Shift, SkillLevel
from workers.worker_manager import WorkerManager

router = APIRouter(prefix="/api/v1/workers", tags=["workers"])
logger = logging.getLogger(__name__)

# Global instances (will be injected during startup)
worker_manager: Optional[WorkerManager] = None
time_tracker = None
face_recognizer = None
badge_ocr = None


def set_worker_manager(manager):
    """Set global worker manager instance"""
    global worker_manager
    worker_manager = manager


def set_time_tracker(tracker):
    """Set global time tracker instance"""
    global time_tracker
    time_tracker = tracker


def set_face_recognizer(recognizer):
    """Set global face recognizer instance"""
    global face_recognizer
    face_recognizer = recognizer


def set_badge_ocr(ocr):
    """Set global badge OCR instance"""
    global badge_ocr
    badge_ocr = ocr


# Request/Response Models
class WorkerCreate(BaseModel):
    worker_id: str
    name: str
    badge_id: Optional[str] = None
    shift: Shift = Shift.FLEXIBLE
    skill_level: SkillLevel = SkillLevel.JUNIOR
    station_assignments: Optional[List[str]] = None


class WorkerUpdate(BaseModel):
    name: Optional[str] = None
    badge_id: Optional[str] = None
    shift: Optional[Shift] = None
    skill_level: Optional[SkillLevel] = None
    station_assignments: Optional[List[str]] = None
    active: Optional[bool] = None


class FaceEnrollResponse(BaseModel):
    worker_id: str
    success: bool
    message: str
    embedding_shape: Optional[tuple] = None


class ProductivityResponse(BaseModel):
    worker_id: str
    indices: Optional[ProductivityIndex] = None
    recommendations: List[str]


# Worker CRUD Endpoints

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_worker(worker_data: WorkerCreate):
    """Create a new worker"""
    if worker_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Worker manager not initialized"
        )

    # Check if worker already exists
    existing = worker_manager.get_worker(worker_data.worker_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Worker {worker_data.worker_id} already exists"
        )

    # Create worker
    worker = Worker(
        worker_id=worker_data.worker_id,
        name=worker_data.name,
        badge_id=worker_data.badge_id,
        shift=worker_data.shift,
        skill_level=worker_data.skill_level,
        station_assignments=worker_data.station_assignments or [],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    success = worker_manager.add_worker(worker)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create worker"
        )

    return {
        "message": f"Worker {worker.name} created successfully",
        "worker": worker.dict()
    }


@router.get("/")
async def list_workers(
    active_only: bool = Query(True),
    shift: Optional[Shift] = Query(None)
):
    """List all workers"""
    if worker_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Worker manager not initialized"
        )

    if shift:
        workers = worker_manager.get_workers_by_shift(shift)
    elif active_only:
        workers = worker_manager.get_active_workers()
    else:
        workers = worker_manager.get_all_workers()

    return {
        "count": len(workers),
        "workers": [w.dict() for w in workers]
    }


@router.get("/{worker_id}")
async def get_worker(worker_id: str):
    """Get worker by ID"""
    if worker_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Worker manager not initialized"
        )

    worker = worker_manager.get_worker(worker_id)
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker {worker_id} not found"
        )

    return worker.dict()


@router.put("/{worker_id}")
async def update_worker(worker_id: str, updates: WorkerUpdate):
    """Update worker information"""
    if worker_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Worker manager not initialized"
        )

    # Get existing worker
    worker = worker_manager.get_worker(worker_id)
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker {worker_id} not found"
        )

    # Apply updates
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(worker, field, value)

    worker.updated_at = datetime.now()

    # Update in manager
    success = worker_manager.update_worker(worker)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update worker"
        )

    return {
        "message": f"Worker {worker_id} updated successfully",
        "worker": worker.dict()
    }


@router.delete("/{worker_id}")
async def delete_worker(worker_id: str):
    """Delete a worker"""
    if worker_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Worker manager not initialized"
        )

    success = worker_manager.remove_worker(worker_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker {worker_id} not found"
        )

    return {
        "message": f"Worker {worker_id} deleted successfully"
    }


# Face Recognition Endpoints

@router.post("/{worker_id}/enroll_face")
async def enroll_worker_face(
    worker_id: str,
    image: UploadFile = File(...)
):
    """Enroll worker's face from uploaded image"""
    if worker_manager is None or face_recognizer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Worker manager or face recognizer not initialized"
        )

    # Check if worker exists
    worker = worker_manager.get_worker(worker_id)
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker {worker_id} not found"
        )

    # Read image
    try:
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise ValueError("Failed to decode image")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file: {str(e)}"
        )

    # Enroll face
    try:
        embedding = face_recognizer.enroll_face(frame)

        if embedding is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No face detected in image"
            )

        # Store embedding in worker
        success = worker_manager.enroll_face(worker_id, embedding)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to enroll face"
            )

        return {
            "worker_id": worker_id,
            "success": True,
            "message": f"Face enrolled successfully for {worker.name}",
            "embedding_shape": embedding.shape
        }

    except Exception as e:
        logger.error(f"Face enrollment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Face enrollment failed: {str(e)}"
        )


@router.get("/{worker_id}/has_face")
async def check_face_enrollment(worker_id: str):
    """Check if worker has enrolled face"""
    if worker_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Worker manager not initialized"
        )

    worker = worker_manager.get_worker(worker_id)
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker {worker_id} not found"
        )

    has_face = worker.get_face_embedding() is not None

    return {
        "worker_id": worker_id,
        "has_face_enrolled": has_face
    }


# Session and Time Tracking Endpoints

@router.get("/{worker_id}/session")
async def get_worker_session(worker_id: str):
    """Get active session for a worker"""
    if time_tracker is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Time tracker not initialized"
        )

    session = time_tracker.get_session(worker_id)

    if not session:
        return {
            "worker_id": worker_id,
            "has_active_session": False,
            "session": None
        }

    return {
        "worker_id": worker_id,
        "has_active_session": True,
        "session": session.dict()
    }


@router.get("/{worker_id}/zone_times")
async def get_worker_zone_times(worker_id: str):
    """Get time spent in each zone for a worker"""
    if time_tracker is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Time tracker not initialized"
        )

    zone_times = time_tracker.get_zone_times(worker_id)

    if zone_times is None:
        return {
            "worker_id": worker_id,
            "has_active_session": False,
            "zone_times": {}
        }

    return {
        "worker_id": worker_id,
        "has_active_session": True,
        "zone_times": zone_times
    }


@router.post("/{worker_id}/end_session")
async def end_worker_session(worker_id: str):
    """Manually end a worker's session"""
    if time_tracker is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Time tracker not initialized"
        )

    session = time_tracker.end_worker_session(worker_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active session for worker {worker_id}"
        )

    return {
        "message": f"Session ended for worker {worker_id}",
        "session": session.dict()
    }


# Productivity Endpoints

@router.get("/{worker_id}/productivity")
async def get_worker_productivity(worker_id: str):
    """Get productivity indices for a worker"""
    if time_tracker is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Time tracker not initialized"
        )

    indices = time_tracker.calculate_productivity(worker_id)

    if not indices:
        return {
            "worker_id": worker_id,
            "has_active_session": False,
            "indices": None,
            "recommendations": ["No active session"]
        }

    recommendations = time_tracker.get_recommendations(worker_id)

    return {
        "worker_id": worker_id,
        "has_active_session": True,
        "indices": indices.dict(),
        "recommendations": recommendations
    }


@router.post("/{worker_id}/task_completed")
async def record_task_completion(
    worker_id: str,
    quality_score: Optional[float] = Query(None, ge=0, le=100)
):
    """Record a completed task for a worker"""
    if time_tracker is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Time tracker not initialized"
        )

    time_tracker.record_task_completed(worker_id, quality_score)

    return {
        "message": f"Task recorded for worker {worker_id}",
        "worker_id": worker_id,
        "quality_score": quality_score
    }


# Statistics Endpoints

@router.get("/stats/summary")
async def get_worker_statistics():
    """Get overall worker statistics"""
    if worker_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Worker manager not initialized"
        )

    stats = worker_manager.get_stats()

    # Add time tracker stats if available
    if time_tracker:
        stats['time_tracking'] = time_tracker.get_stats()

    return stats


@router.get("/sessions/active")
async def get_active_sessions():
    """Get all active worker sessions"""
    if time_tracker is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Time tracker not initialized"
        )

    sessions = time_tracker.get_all_sessions()

    return {
        "count": len(sessions),
        "sessions": [s.dict() for s in sessions]
    }


@router.post("/sessions/cleanup")
async def cleanup_idle_sessions(
    max_idle_minutes: int = Query(60, ge=1, le=1440)
):
    """Cleanup sessions that have been idle too long"""
    if time_tracker is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Time tracker not initialized"
        )

    ended_sessions = time_tracker.cleanup_idle_sessions(max_idle_minutes)

    return {
        "message": f"Cleaned up {len(ended_sessions)} idle sessions",
        "count": len(ended_sessions),
        "sessions": [s.dict() for s in ended_sessions]
    }
