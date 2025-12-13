"""
Assembly Time-Tracking System - Main Entry Point
Phase 3: Multi-Camera + Object Tracking
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
from tracking.tracking_manager import TrackingManager
from data.database import DatabaseManager
from data.detection_writer import DetectionWriter
from data.tracking_writer import TrackingWriter

# Import API routers
from api.v1 import cameras, detection, zones, tracking

# Global managers
camera_manager = None
zone_manager = None
tracking_manager = None
detection_manager = None
db_manager = None
detection_writer = None
tracking_writer = None

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
        "version": "3.0.0",
        "status": "running",
        "phase": "Phase 3 - Multi-Camera + Tracking"
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
    global camera_manager, zone_manager, tracking_manager, detection_manager
    global db_manager, detection_writer, tracking_writer

    logger.info("=" * 60)
    logger.info("Assembly Time-Tracking System - Starting Up")
    logger.info("=" * 60)
    logger.info("Phase: 3 - Multi-Camera + Tracking")
    logger.info("Status: Development Mode")
    logger.info("-" * 60)

    # Initialize database
    logger.info("💾 Initializing PostgreSQL connection...")
    db_manager = DatabaseManager()
    await db_manager.connect()

    # Initialize data writers
    logger.info("📝 Initializing data writers...")
    detection_writer = DetectionWriter(db_manager, batch_size=100, flush_interval=5.0)
    tracking_writer = TrackingWriter(db_manager)
    await detection_writer.start()

    # Initialize managers
    logger.info("📷 Initializing Camera Manager...")
    camera_manager = CameraManager()

    logger.info("🏗️  Initializing Zone Manager...")
    zone_manager = ZoneManager()

    logger.info("🎯 Initializing Tracking Manager...")
    tracking_manager = TrackingManager(
        zone_manager=zone_manager,
        track_thresh=0.5,
        track_buffer=30,
        match_thresh=0.8,
        frame_rate=30
    )

    # Add tracking callbacks for database writing
    def on_tracked_object(tracked_obj):
        """Callback when object is tracked"""
        detection_writer.add_tracked_object(tracked_obj)

    def on_zone_transition(transition):
        """Callback when zone transition occurs"""
        detection_writer.add_zone_transition(transition)

    tracking_manager.add_tracking_callback(on_tracked_object)
    tracking_manager.add_transition_callback(on_zone_transition)

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
        detection_config=detection_config,
        tracking_manager=tracking_manager  # Phase 3: Enable tracking
    )

    # Inject managers into API routers
    cameras.set_camera_manager(camera_manager)
    zones.set_zone_manager(zone_manager)
    detection.set_detection_manager(detection_manager)
    tracking.set_tracking_manager(tracking_manager)
    tracking.set_tracking_writer(tracking_writer)

    # Register API routers
    app.include_router(cameras.router)
    app.include_router(zones.router)
    app.include_router(detection.router)
    app.include_router(tracking.router)

    logger.info("-" * 60)
    logger.info("✅ Phase 3 Tracking system started successfully!")
    logger.info("🌐 API running on http://0.0.0.0:8000")
    logger.info("📚 API docs at http://0.0.0.0:8000/docs")
    logger.info("🎥 Camera API: http://0.0.0.0:8000/api/v1/cameras")
    logger.info("🤖 Detection API: http://0.0.0.0:8000/api/v1/detection")
    logger.info("🏗️  Zone API: http://0.0.0.0:8000/api/v1/zones")
    logger.info("🎯 Tracking API: http://0.0.0.0:8000/api/v1/tracking")
    logger.info("💾 PostgreSQL: Connected")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    global camera_manager, detection_manager, detection_writer, db_manager

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

    # Stop data writers
    if detection_writer:
        logger.info("Flushing detection writer...")
        await detection_writer.stop()

    # Close database
    if db_manager:
        logger.info("Closing database connection...")
        await db_manager.close()

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
