"""
Detection API
Endpoints for YOLOv8 detection control and monitoring
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from typing import Dict, List
from pydantic import BaseModel
import asyncio
import json
from datetime import datetime

router = APIRouter(prefix="/api/v1/detection", tags=["detection"])

# Global detection manager (will be injected during startup)
detection_manager = None


def set_detection_manager(manager):
    """Set global detection manager instance"""
    global detection_manager
    detection_manager = manager


class DetectionStartRequest(BaseModel):
    """Request to start detection on cameras"""
    camera_ids: List[int]


class DetectionStatsResponse(BaseModel):
    """Detection statistics response"""
    running: bool
    cameras_active: int
    total_detections: int
    avg_inference_time_ms: float
    avg_fps: float


@router.post("/start")
async def start_detection(request: DetectionStartRequest):
    """Start detection on specified cameras"""
    if detection_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Detection manager not initialized"
        )

    try:
        detection_manager.start(camera_ids=request.camera_ids)
        return {
            "message": "Detection started",
            "camera_ids": request.camera_ids
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start detection: {str(e)}"
        )


@router.post("/stop")
async def stop_detection():
    """Stop all detection"""
    if detection_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Detection manager not initialized"
        )

    try:
        detection_manager.stop()
        return {"message": "Detection stopped"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop detection: {str(e)}"
        )


@router.get("/status")
async def get_detection_status():
    """Get detection system status"""
    if detection_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Detection manager not initialized"
        )

    return detection_manager.get_status()


@router.get("/stats")
async def get_detection_stats():
    """Get detection statistics"""
    if detection_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Detection manager not initialized"
        )

    return detection_manager.get_stats()


# WebSocket connections storage
active_connections: List[WebSocket] = []


@router.websocket("/ws")
async def detection_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time detection results

    Client receives JSON messages with detection results:
    {
        "camera_id": 1,
        "timestamp": "2025-12-12T10:30:00",
        "detections": [
            {
                "class_name": "person",
                "confidence": 0.95,
                "bbox": [100, 200, 300, 400]
            }
        ],
        "inference_time_ms": 45.2
    }
    """
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()

            # Echo back (can be used for client commands)
            await websocket.send_text(f"Received: {data}")

    except WebSocketDisconnect:
        active_connections.remove(websocket)


async def broadcast_detection(detection_result: dict):
    """
    Broadcast detection result to all connected WebSocket clients

    Args:
        detection_result: Detection result dictionary
    """
    if len(active_connections) == 0:
        return

    message = json.dumps(detection_result, default=str)

    # Send to all connected clients
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except Exception:
            disconnected.append(connection)

    # Remove disconnected clients
    for connection in disconnected:
        active_connections.remove(connection)
