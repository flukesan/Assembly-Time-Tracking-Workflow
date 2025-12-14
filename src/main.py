"""
Assembly Time-Tracking System - Main Entry Point
Phase 4: Worker Identification + Time Tracking
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

# Phase 4: Worker identification and time tracking
from workers.worker_manager import WorkerManager
from identification.face_recognition import FaceRecognizer
from identification.badge_ocr import BadgeOCR
from time_tracking.time_tracker import TimeTracker

# Phase 4B: RAG + DeepSeek-R1 AI Services
from llm.ollama_client import OllamaClient
from rag.embeddings import EmbeddingGenerator
from rag.qdrant_manager import QdrantManager
from rag.knowledge_base import KnowledgeBase
from insights.insight_generator import InsightGenerator
from insights.anomaly_detector import AnomalyDetector
from insights.recommendation_engine import RecommendationEngine
from reports.report_generator import ReportGenerator

# Import API routers
from api.v1 import cameras, detection, zones, tracking, workers, ai_query

# Global managers
camera_manager = None
zone_manager = None
tracking_manager = None
detection_manager = None
db_manager = None
detection_writer = None
tracking_writer = None

# Phase 4: Worker and time tracking managers
worker_manager = None
face_recognizer = None
badge_ocr = None
time_tracker = None

# Phase 4B: RAG + AI managers
ollama_client = None
embedding_generator = None
qdrant_manager = None
knowledge_base = None
insight_generator = None
anomaly_detector = None
recommendation_engine = None
report_generator = None

# Application instance
app = FastAPI(
    title="Assembly Time-Tracking System",
    description="Real-time worker tracking with AI-powered insights via RAG + DeepSeek-R1. Features: Face/Badge recognition, time tracking, natural language queries (Thai/English), automated insights and reports.",
    version="4.1.0"
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
        "version": "4.1.0",
        "status": "running",
        "phase": "Phase 4B - RAG + DeepSeek-R1 Integration",
        "features": [
            "Worker Identification (Face + Badge)",
            "Time Tracking & Productivity",
            "RAG Knowledge Base (Qdrant)",
            "AI-Powered Insights (DeepSeek-R1)",
            "Natural Language Queries (Thai/English)",
            "Automated Reports"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        health_status = {
            "status": "healthy",
            "phase": "Phase 4B - RAG + DeepSeek-R1",
            "components": {
                "api": "healthy",
                "postgresql": "connected" if db_manager else "not_initialized",
                "qdrant": "connected" if qdrant_manager else "not_initialized",
                "redis": "available",
                "ollama": "connected" if ollama_client else "not_initialized"
            },
            "ai_services": {
                "knowledge_base": "ready" if knowledge_base else "not_initialized",
                "insight_generator": "ready" if insight_generator else "not_initialized",
                "anomaly_detector": "ready" if anomaly_detector else "not_initialized",
                "recommendation_engine": "ready" if recommendation_engine else "not_initialized",
                "report_generator": "ready" if report_generator else "not_initialized"
            },
            "worker_services": {
                "face_recognition": "ready" if face_recognizer else "not_initialized",
                "badge_ocr": "ready" if badge_ocr else "not_initialized",
                "time_tracking": "active" if time_tracker else "not_initialized"
            }
        }

        # Check if any component is not initialized
        all_healthy = all(
            v not in ["not_initialized", "unhealthy"]
            for services in [health_status["components"], health_status["ai_services"], health_status["worker_services"]]
            for v in services.values()
        )

        status_code = 200 if all_healthy else 503
        if not all_healthy:
            health_status["status"] = "degraded"

        return JSONResponse(
            status_code=status_code,
            content=health_status
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
    global worker_manager, face_recognizer, badge_ocr, time_tracker
    global ollama_client, embedding_generator, qdrant_manager, knowledge_base
    global insight_generator, anomaly_detector, recommendation_engine, report_generator

    logger.info("=" * 60)
    logger.info("Assembly Time-Tracking System - Starting Up")
    logger.info("=" * 60)
    logger.info("Phase: 4B - RAG + DeepSeek-R1 Integration")
    logger.info("Version: 4.1.0")
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

    # Phase 4: Initialize worker identification and time tracking
    logger.info("👤 Initializing Worker Manager...")
    worker_manager = WorkerManager()

    logger.info("😊 Initializing Face Recognizer...")
    face_recognizer = FaceRecognizer(
        device="cpu",  # Use CPU mode (can be changed to "cuda" for GPU)
        min_face_size=40,
        detection_threshold=0.9
    )

    logger.info("🎫 Initializing Badge OCR...")
    badge_ocr = BadgeOCR(
        languages=['th', 'en'],  # Thai + English support
        gpu=False,
        min_confidence=0.3
    )

    logger.info("⏱️  Initializing Time Tracker...")
    time_tracker = TimeTracker(
        idle_threshold_seconds=300,  # 5 minutes
        break_zone_names=["Break Area", "Rest Zone", "Cafeteria"],
        target_output_per_hour=10.0
    )

    # Phase 4B: Initialize RAG + AI services
    logger.info("🧠 Initializing Phase 4B: RAG + DeepSeek-R1...")
    logger.info("🔮 Initializing Ollama Client...")
    ollama_client = OllamaClient(
        base_url="http://ollama:11434",
        model="deepseek-r1:14b"
    )

    logger.info("📊 Initializing Embedding Generator...")
    embedding_generator = EmbeddingGenerator(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    )

    logger.info("🗄️  Initializing Qdrant Manager...")
    qdrant_manager = QdrantManager(
        host="qdrant",
        port=6333,
        embedding_dim=768
    )

    logger.info("📚 Initializing Knowledge Base...")
    knowledge_base = KnowledgeBase(
        qdrant_manager=qdrant_manager,
        embedding_generator=embedding_generator
    )

    logger.info("💡 Initializing Insight Generator...")
    insight_generator = InsightGenerator(
        ollama_client=ollama_client,
        knowledge_base=knowledge_base,
        min_productivity_threshold=60.0,
        min_efficiency_threshold=70.0
    )

    logger.info("🔍 Initializing Anomaly Detector...")
    anomaly_detector = AnomalyDetector(
        std_threshold=2.0,
        min_data_points=5
    )

    logger.info("🎯 Initializing Recommendation Engine...")
    recommendation_engine = RecommendationEngine(
        ollama_client=ollama_client,
        anomaly_detector=anomaly_detector
    )

    logger.info("📄 Initializing Report Generator...")
    report_generator = ReportGenerator(
        ollama_client=ollama_client,
        knowledge_base=knowledge_base,
        insight_generator=insight_generator
    )

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

    # Phase 4: Inject worker and time tracking managers
    workers.set_worker_manager(worker_manager)
    workers.set_time_tracker(time_tracker)
    workers.set_face_recognizer(face_recognizer)
    workers.set_badge_ocr(badge_ocr)

    # Phase 4B: Inject AI services into AI Query API
    ai_query.set_ollama_client(ollama_client)
    ai_query.set_knowledge_base(knowledge_base)

    # Register API routers
    app.include_router(cameras.router)
    app.include_router(zones.router)
    app.include_router(detection.router)
    app.include_router(tracking.router)
    app.include_router(workers.router)  # Phase 4: Worker API
    app.include_router(ai_query.router)  # Phase 4B: AI Query API

    logger.info("-" * 60)
    logger.info("✅ Phase 4B RAG + DeepSeek-R1 system started successfully!")
    logger.info("🌐 API running on http://0.0.0.0:8000")
    logger.info("📚 API docs at http://0.0.0.0:8000/docs")
    logger.info("")
    logger.info("📡 API Endpoints:")
    logger.info("  🎥 Camera API: http://0.0.0.0:8000/api/v1/cameras")
    logger.info("  🤖 Detection API: http://0.0.0.0:8000/api/v1/detection")
    logger.info("  🏗️  Zone API: http://0.0.0.0:8000/api/v1/zones")
    logger.info("  🎯 Tracking API: http://0.0.0.0:8000/api/v1/tracking")
    logger.info("  👤 Worker API: http://0.0.0.0:8000/api/v1/workers")
    logger.info("  🧠 AI Query API: http://0.0.0.0:8000/api/v1/ai")
    logger.info("")
    logger.info("💾 Services Status:")
    logger.info("  ✓ PostgreSQL: Connected")
    logger.info("  ✓ Qdrant: Connected")
    logger.info("  ✓ Ollama: Ready (DeepSeek-R1:14b)")
    logger.info("  ✓ Face Recognition: Initialized")
    logger.info("  ✓ Badge OCR: Initialized (Thai + English)")
    logger.info("  ✓ Time Tracking: Active")
    logger.info("  ✓ Knowledge Base: Ready (RAG)")
    logger.info("  ✓ AI Insights: Enabled")
    logger.info("  ✓ Reports: Enabled")
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
