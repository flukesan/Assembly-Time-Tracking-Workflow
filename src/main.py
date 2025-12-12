"""
Assembly Time-Tracking System - Main Entry Point
Phase 2: Single Camera + Detection
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from loguru import logger

# Import modules
from camera.camera_manager import CameraManager
from ai.detection_models import DetectionConfig
from core.zones.zone_manager import ZoneManager
from core.detection_manager import DetectionManager

# Import API routers
from api.v1 import cameras, detection, zones

# Global managers
camera_manager = None
zone_manager = None
detection_manager = None

# Application instance
app = FastAPI(
    title="Assembly Time-Tracking System",
    description="Real-time worker tracking and productivity analysis",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Assembly Time-Tracking System",
        "version": "2.0.0",
        "status": "running",
        "phase": "Phase 2 - Single Camera + Detection"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # TODO: Add actual health checks for databases
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "phase": "Phase 1 - Foundation",
                "components": {
                    "api": "healthy",
                    "postgresql": "not_yet_implemented",
                    "qdrant": "not_yet_implemented",
                    "redis": "not_yet_implemented",
                    "ollama": "not_yet_implemented"
                }
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    global camera_manager, zone_manager, detection_manager

    logger.info("=" * 60)
    logger.info("Assembly Time-Tracking System - Starting Up")
    logger.info("=" * 60)
    logger.info("Phase: 2 - Single Camera + Detection")
    logger.info("Status: Development Mode")
    logger.info("-" * 60)

    # Initialize managers
    logger.info("📷 Initializing Camera Manager...")
    camera_manager = CameraManager()

    logger.info("🏗️  Initializing Zone Manager...")
    zone_manager = ZoneManager()

    logger.info("🤖 Initializing YOLOv8 Detection...")
    detection_config = DetectionConfig(
        model_name="yolov8n.pt",
        confidence_threshold=0.5,
        device="cpu",  # Will be set to "cuda" if GPU available
        classes=[0]  # 0 = person
    )

    detection_manager = DetectionManager(
        camera_manager=camera_manager,
        zone_manager=zone_manager,
        detection_config=detection_config
    )

    # Inject managers into API routers
    cameras.set_camera_manager(camera_manager)
    zones.set_zone_manager(zone_manager)
    detection.set_detection_manager(detection_manager)

    # Register API routers
    app.include_router(cameras.router)
    app.include_router(zones.router)
    app.include_router(detection.router)

    logger.info("-" * 60)
    logger.info("✅ Phase 2 Detection system started successfully!")
    logger.info("🌐 API running on http://0.0.0.0:8000")
    logger.info("📚 API docs at http://0.0.0.0:8000/docs")
    logger.info("🎥 Camera API: http://0.0.0.0:8000/api/v1/cameras")
    logger.info("🤖 Detection API: http://0.0.0.0:8000/api/v1/detection")
    logger.info("🏗️  Zone API: http://0.0.0.0:8000/api/v1/zones")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    global camera_manager, detection_manager

    logger.info("=" * 60)
    logger.info("Assembly Time-Tracking System - Shutting Down")
    logger.info("=" * 60)

    # Stop detection
    if detection_manager:
        logger.info("Stopping detection...")
        detection_manager.stop()

    # Stop all cameras
    if camera_manager:
        logger.info("Stopping cameras...")
        camera_manager.stop_all()

    logger.info("✅ Cleanup complete")


def main():
    """Main entry point"""
    # Configure logging
    logger.add(
        "logs/app.log",
        rotation="1 day",
        retention="7 days",
        level="INFO"
    )

    # Run server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload for development
        log_level="info"
    )


if __name__ == "__main__":
    main()
