"""
Camera Management API
Endpoints for camera CRUD operations and status monitoring
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict
from pydantic import BaseModel

from camera.camera_config import CameraConfig, CameraStatus

router = APIRouter(prefix="/api/v1/cameras", tags=["cameras"])

# Global camera manager (will be injected during startup)
camera_manager = None


def set_camera_manager(manager):
    """Set global camera manager instance"""
    global camera_manager
    camera_manager = manager


class CameraCreateRequest(BaseModel):
    """Request model for creating a camera"""
    name: str
    rtsp_url: str
    location: str
    fps: int = 30
    resolution_width: int = 1920
    resolution_height: int = 1080
    rotation: int = 0


class CameraUpdateRequest(BaseModel):
    """Request model for updating a camera"""
    name: str = None
    rtsp_url: str = None
    location: str = None
    fps: int = None
    resolution_width: int = None
    resolution_height: int = None
    rotation: int = None
    status: str = None


@router.get("/", response_model=Dict[int, CameraStatus])
async def list_cameras():
    """Get all cameras and their status"""
    if camera_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Camera manager not initialized"
        )

    return camera_manager.get_all_status()


@router.get("/{camera_id}", response_model=CameraStatus)
async def get_camera(camera_id: int):
    """Get camera status by ID"""
    if camera_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Camera manager not initialized"
        )

    camera_status = camera_manager.get_status(camera_id)
    if camera_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )

    return camera_status


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_camera(request: CameraCreateRequest):
    """Create and start a new camera"""
    if camera_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Camera manager not initialized"
        )

    # Generate new camera_id (simple increment for now)
    existing_cameras = camera_manager.get_all_cameras()
    new_camera_id = max(existing_cameras.keys(), default=0) + 1

    # Create camera config
    config = CameraConfig(
        camera_id=new_camera_id,
        name=request.name,
        rtsp_url=request.rtsp_url,
        location=request.location,
        fps=request.fps,
        resolution_width=request.resolution_width,
        resolution_height=request.resolution_height,
        rotation=request.rotation,
        status="active"
    )

    # Add camera
    success = camera_manager.add_camera(config)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create camera"
        )

    return {
        "message": "Camera created successfully",
        "camera_id": new_camera_id,
        "status": "active"
    }


@router.delete("/{camera_id}")
async def delete_camera(camera_id: int):
    """Stop and remove a camera"""
    if camera_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Camera manager not initialized"
        )

    success = camera_manager.remove_camera(camera_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )

    return {
        "message": "Camera deleted successfully",
        "camera_id": camera_id
    }


@router.post("/{camera_id}/start")
async def start_camera(camera_id: int):
    """Start a stopped camera"""
    if camera_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Camera manager not initialized"
        )

    camera = camera_manager.get_camera(camera_id)
    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )

    success = camera.start()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start camera"
        )

    return {
        "message": "Camera started successfully",
        "camera_id": camera_id
    }


@router.post("/{camera_id}/stop")
async def stop_camera(camera_id: int):
    """Stop a running camera"""
    if camera_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Camera manager not initialized"
        )

    camera = camera_manager.get_camera(camera_id)
    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )

    camera.stop()

    return {
        "message": "Camera stopped successfully",
        "camera_id": camera_id
    }
