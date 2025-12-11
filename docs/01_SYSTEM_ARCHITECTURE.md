# System Architecture - Assembly Time-Tracking System

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │   PyQt6 Desktop  │  │   Web Dashboard  │  │  Mobile Monitor  │ │
│  │   (Main UI)      │  │   (Analytics)    │  │  (Alerts)        │ │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘ │
└───────────┼──────────────────────┼──────────────────────┼───────────┘
            │                      │                      │
            └──────────────────────┴──────────────────────┘
                                   │
                         ┌─────────▼─────────┐
                         │   API Gateway     │
                         │  (FastAPI)        │
                         └─────────┬─────────┘
                                   │
┌─────────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │              CORE PROCESSING ENGINE                           │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │ │
│  │  │   Camera     │  │   Detection  │  │   Tracking   │       │ │
│  │  │   Manager    │→ │   Engine     │→ │   Engine     │       │ │
│  │  │  (4 threads) │  │  (YOLOv8)    │  │  (DeepSORT)  │       │ │
│  │  └──────────────┘  └──────────────┘  └──────┬───────┘       │ │
│  │                                              │                │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────▼───────┐       │ │
│  │  │   Zone       │  │   Time       │  │   Worker ID  │       │ │
│  │  │   Manager    │← │   Tracker    │← │   Service    │       │ │
│  │  └──────────────┘  └──────┬───────┘  └──────────────┘       │ │
│  └─────────────────────────────┼──────────────────────────────────┘ │
│                                │                                     │
│  ┌────────────────────────────▼─────────────────────────────────┐  │
│  │              INDEX & SCHEDULE MANAGER                        │  │
│  │  • 11 indices timeline calculation                           │  │
│  │  • Break time handling                                       │  │
│  │  • Index transition events                                   │  │
│  └──────────────────────────────┬───────────────────────────────┘  │
│                                  │                                   │
│  ┌─────────────────────────────▼────────────────────────────────┐  │
│  │         RAG + DeepSeek-R1 ANALYSIS ENGINE                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │  │
│  │  │  Query   │→ │ Vector   │→ │ Context  │→ │DeepSeek  │    │  │
│  │  │  Router  │  │ Search   │  │ Assembly │  │  R1:14B  │    │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              BACKGROUND SERVICES                             │  │
│  │  • ETL Pipeline (PostgreSQL → Qdrant)                       │  │
│  │  • Watchdog System (health monitoring)                      │  │
│  │  • Alert Manager (notifications)                            │  │
│  │  • Report Generator (scheduled)                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                    │
├─────────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │
│  │  PostgreSQL    │  │    Qdrant      │  │     Redis      │       │
│  │  (TimescaleDB) │  │  Vector DB     │  │    Cache       │       │
│  │                │  │                │  │                │       │
│  │ • time_logs    │  │ • work_seq     │  │ • sessions     │       │
│  │ • sessions     │  │ • anomalies    │  │ • zone_config  │       │
│  │ • workers      │  │ • knowledge    │  │ • worker_map   │       │
│  │ • zones        │  │ • behaviors    │  │ • index_state  │       │
│  └────────────────┘  └────────────────┘  └────────────────┘       │
│                                                                      │
│  ┌────────────────┐                                                 │
│  │  Ollama        │                                                 │
│  │  Server        │                                                 │
│  │                │                                                 │
│  │ • deepseek-r1  │                                                 │
│  │   :14b         │                                                 │
│  └────────────────┘                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                   │
┌─────────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │
│  │  RTSP Cameras  │  │  USB Cameras   │  │  Network       │       │
│  │  (IP Cameras)  │  │  (Local Cams)  │  │  Storage       │       │
│  └────────────────┘  └────────────────┘  └────────────────┘       │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Docker Compose Orchestration                              │    │
│  │  • GPU passthrough (NVIDIA Docker)                         │    │
│  │  • Network bridge                                          │    │
│  │  • Volume management                                       │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Architecture

```
┌──────────┐
│ Camera 1 │───┐
└──────────┘   │
┌──────────┐   │
│ Camera 2 │───┼──→ Camera Manager ──→ Frame Queue (Buffer: 3)
└──────────┘   │                           │
┌──────────┐   │                           ▼
│ Camera 3 │───┤                    Detection Thread
└──────────┘   │                    (Batch 4 frames)
┌──────────┐   │                           │
│ Camera 4 │───┘                           │
└──────────┘                               ▼
                                    YOLOv8 Inference
                                    (GPU, FP16)
                                           │
                                           ▼
                                    [Person Detections]
                                           │
                     ┌─────────────────────┴─────────────────────┐
                     │                                           │
                     ▼                                           ▼
              Tracking Thread                              Face Recognition
              (DeepSORT/ByteTrack)                         (Optional)
                     │                                           │
                     └─────────────┬─────────────────────────────┘
                                   ▼
                          [Tracked Persons with IDs]
                                   │
                                   ▼
                          Zone Matching Engine
                          (Point-in-Polygon)
                                   │
                                   ▼
                     ┌─────────────┴─────────────┐
                     │                           │
                     ▼                           ▼
              Motion Detection            Worker Identification
              (Active/Idle)               (Face/Badge/ReID)
                     │                           │
                     └─────────────┬─────────────┘
                                   ▼
                          Time Tracking Engine
                          (Active/Idle counters)
                                   │
                     ┌─────────────┴─────────────┐
                     │                           │
                     ▼                           ▼
              Redis (Real-time)          PostgreSQL (Persistent)
              - Active sessions           - time_logs (TimescaleDB)
              - Zone states               - sessions
              - Worker mapping            - index_records
                     │                           │
                     └─────────────┬─────────────┘
                                   ▼
                          Index Manager
                          (11 indices timeline)
                                   │
                                   ▼
                          ETL Pipeline (Every 5min)
                                   │
                                   ▼
                          Qdrant Vector DB
                          (Embeddings + Metadata)
                                   │
                                   ▼
                          RAG Query Engine
                                   │
                                   ▼
                          DeepSeek-R1 (14B)
                          (Ollama Server)
                                   │
                                   ▼
                          [Insights + Recommendations]
                                   │
                     ┌─────────────┴─────────────┐
                     │                           │
                     ▼                           ▼
              PyQt6 UI                    FastAPI + WebSocket
              (Desktop)                   (Web/Mobile)
```

---

## 🧵 Multi-Threading Strategy

### Thread Pool Design

```python
# Thread allocation for optimal performance

CAMERA_THREADS = 4          # One per camera (30 FPS capture)
DETECTION_THREAD = 1        # GPU inference (batch 4 frames, 15 FPS)
TRACKING_THREAD = 1         # CPU tracking (15 FPS)
DB_WRITER_THREAD = 1        # Async batch writes (every 10s)
INDEX_MANAGER_THREAD = 1    # Schedule monitoring (1s interval)
ETL_THREAD = 1              # PostgreSQL → Qdrant (every 5min)
WATCHDOG_THREAD = 1         # Health monitoring (every 5s)
WEBSOCKET_THREAD = 1        # Real-time updates (push every 2s)
UI_THREAD = 1               # PyQt6 main thread (10 FPS refresh)

TOTAL_THREADS = 12
```

### Thread Communication

```
Camera Threads ──→ Queue(maxsize=3) ──→ Detection Thread
                                             │
                                             ▼
Detection Thread ──→ Queue(maxsize=5) ──→ Tracking Thread
                                             │
                                             ▼
Tracking Thread ──→ Redis + Queue ──→ Time Tracker + DB Writer
                                             │
                                             ▼
Time Tracker ──→ PostgreSQL (async batch insert)
                                             │
                                             ▼
ETL Thread ──→ Read PostgreSQL ──→ Qdrant (batch upsert)
```

### Synchronization Mechanisms

```python
# Critical sections protected by locks

camera_lock = threading.Lock()        # Camera frame access
redis_lock = threading.Lock()         # Redis write operations
postgres_lock = threading.Lock()      # PostgreSQL connection pool
qdrant_lock = threading.Lock()        # Qdrant client access

# Event-driven coordination

index_transition_event = threading.Event()  # Index change notification
break_start_event = threading.Event()       # Break time start
break_end_event = threading.Event()         # Break time end
shutdown_event = threading.Event()          # Graceful shutdown
```

---

## 🎯 Component Responsibilities

### 1. Camera Manager (`src/camera/camera_manager.py`)
- **Purpose**: Multi-camera stream management
- **Threads**: 4 (one per camera)
- **Responsibilities**:
  - RTSP/USB connection handling
  - Frame acquisition (30 FPS)
  - Auto-reconnection on failure
  - Frame buffering (queue size: 3)
  - Grid layout coordination

### 2. Detection Engine (`src/ai/yolo_detector.py`)
- **Purpose**: Person detection using YOLOv8
- **Threads**: 1 (GPU-bound)
- **Responsibilities**:
  - Batch inference (4 frames simultaneously)
  - FP16 optimization (half precision)
  - Confidence filtering (>0.6)
  - Bounding box validation
  - False positive filtering

### 3. Tracking Engine (`src/ai/tracker.py`)
- **Purpose**: Multi-object tracking (DeepSORT/ByteTrack)
- **Threads**: 1 (CPU-bound)
- **Responsibilities**:
  - Assign unique track IDs
  - Handle occlusion (Kalman filter)
  - Re-identification after disappearance
  - Track lifecycle management
  - Remove stale tracks (>30 frames)

### 4. Zone Manager (`src/core/zone_manager.py`)
- **Purpose**: Zone configuration and matching
- **Responsibilities**:
  - Polygon drawing UI
  - Point-in-polygon detection
  - Multi-camera zone mapping
  - Zone template management
  - Overlap handling

### 5. Time Tracker (`src/core/time_tracker.py`)
- **Purpose**: Active/Idle time tracking
- **Threads**: 1 (event-driven)
- **Responsibilities**:
  - Session initialization (entry detection)
  - Active time accumulation
  - Idle state detection (60s threshold)
  - Motion score calculation
  - Session finalization (exit detection)

### 6. Index Manager (`src/core/index_manager.py`)
- **Purpose**: 11-index timeline management
- **Threads**: 1 (timer-based)
- **Responsibilities**:
  - Schedule calculation (with breaks)
  - Index transition detection
  - Break time handling (pause tracking)
  - Index completion events
  - Daily reset at midnight

### 7. Worker Identification Service (`src/ai/reid_service.py`)
- **Purpose**: Worker identity management
- **Responsibilities**:
  - Face recognition (ArcFace/FaceNet)
  - Badge OCR (Tesseract/EasyOCR)
  - Re-identification (appearance matching)
  - Worker registry management
  - track_id → worker_id mapping

### 8. RAG Engine (`src/rag/rag_engine.py`)
- **Purpose**: Intelligent query answering
- **Components**:
  - **Query Router**: Determine query intent
  - **Retriever**: Vector search in Qdrant (top-k=5)
  - **SQL Executor**: Fetch real-time data
  - **Context Assembler**: Combine vector + SQL results
  - **Prompt Builder**: Structure prompt for DeepSeek-R1
  - **LLM Service**: Interface with Ollama (deepseek-r1:14b)

### 9. ETL Pipeline (`src/data/etl_pipeline.py`)
- **Purpose**: PostgreSQL → Qdrant data sync
- **Threads**: 1 (scheduled)
- **Trigger Conditions**:
  - Periodic: Every 5 minutes
  - Event-driven: Anomaly detection
  - Scheduled: Daily at midnight
- **Process**:
  1. Read new data from PostgreSQL
  2. Generate embeddings (sentence-transformers)
  3. Batch upsert to Qdrant (100 points/batch)
  4. Update sync status

### 10. Alert Manager (`src/core/alert_manager.py`)
- **Purpose**: Real-time alerting system
- **Channels**:
  - In-app (PyQt6 toast)
  - Email (SMTP)
  - LINE Notify (webhook)
  - WebSocket push
- **Alert Types**:
  - Idle threshold exceeded
  - Zone violation
  - No worker in critical zone
  - Productivity drop
  - System failures

### 11. Watchdog System (`src/monitoring/watchdog.py`)
- **Purpose**: System health monitoring
- **Threads**: 1 (5s interval)
- **Monitors**:
  - Thread heartbeats (detect frozen threads)
  - Camera connection status
  - Database health (ping + query test)
  - GPU utilization (nvidia-smi)
  - Memory usage (alert if >80%)
  - Disk space
- **Actions**:
  - Auto-restart dead threads
  - Send admin alerts
  - Log to system_logs table

---

## 🔐 Security Architecture

### Authentication & Authorization

```
API Layer:
├── Public Endpoints (no auth):
│   └── GET /health
│
├── API Key Auth (M2M):
│   ├── GET /api/v1/metrics/*
│   └── POST /api/v1/query
│
└── OAuth2 + JWT (Users):
    ├── Roles: admin, supervisor, viewer
    ├── Permissions: read, write, delete, config
    └── Token expiry: 24h (refresh: 7 days)
```

### Data Protection

- **In Transit**: TLS 1.3 (HTTPS/WSS)
- **At Rest**: PostgreSQL encryption (pgcrypto)
- **Secrets**: Environment variables (.env) + Docker secrets
- **Face Embeddings**: Hashed + encrypted in database
- **Logs**: PII redaction (no names in logs)

---

## 📊 Performance Targets

| Metric | Target | Hardware |
|--------|--------|----------|
| Camera capture FPS | 30 FPS/cam | 4 cameras |
| Detection processing | 15 FPS (batch 4) | RTX 4090 |
| YOLO inference time | <50ms/batch | GPU FP16 |
| Tracking latency | <30ms | CPU 16 cores |
| End-to-end latency | <200ms | Camera → UI |
| UI refresh rate | 10 FPS | PyQt6 |
| Database write | Batch every 10s | Async |
| RAG query time | <3s | DeepSeek-R1:14B |
| Memory usage | <50GB | 64GB RAM |
| GPU VRAM | <20GB | 24GB total |
| Disk writes | <100MB/min | SSD |

---

## 🔧 Scalability Considerations

### Horizontal Scaling (Future)

```
Load Balancer
     │
     ├──→ Processing Node 1 (Cameras 1-2)
     ├──→ Processing Node 2 (Cameras 3-4)
     └──→ Processing Node 3 (Cameras 5-6)
          │
          ├──→ Shared PostgreSQL (Primary-Replica)
          ├──→ Shared Qdrant (Cluster mode)
          └──→ Shared Redis (Sentinel)
```

### Vertical Scaling (Current)

- **GPU**: Single RTX 4090 handles 4 cameras
- **CPU**: 16 cores for tracking + background tasks
- **RAM**: 64GB for all in-memory operations
- **Storage**: NVMe for Qdrant index, HDD for archives

---

## 🚨 Fault Tolerance & Recovery

### Camera Failures
- **Detection**: RTSP timeout (30s ping)
- **Action**: Auto-reconnect with exponential backoff
- **Fallback**: Continue with remaining cameras
- **Alert**: Notify admin immediately

### Database Failures
- **PostgreSQL**: Connection pool retry (3 attempts, 5s delay)
- **Qdrant**: Queue writes in memory, retry when online
- **Redis**: Graceful degradation (fetch from PostgreSQL)

### GPU Failures
- **Detection**: Inference timeout or CUDA error
- **Action**: Restart YOLO model, fallback to CPU (slow)
- **Alert**: Critical alert to admin

### Thread Failures
- **Detection**: Watchdog checks heartbeat every 5s
- **Action**: Kill and restart thread
- **Alert**: Log to system_logs

### Power Loss
- **PostgreSQL**: WAL (Write-Ahead Logging) ensures durability
- **Qdrant**: Periodic snapshots (daily)
- **Redis**: RDB snapshots + AOF (Append-Only File)

---

## 📁 Deployment Architecture

### Docker Compose Stack

```yaml
services:
  postgresql:
    image: timescale/timescaledb:latest-pg15
    deploy:
      resources:
        limits:
          memory: 8G

  qdrant:
    image: qdrant/qdrant:latest
    deploy:
      resources:
        limits:
          memory: 16G

  redis:
    image: redis:7-alpine
    deploy:
      resources:
        limits:
          memory: 4G

  ollama:
    image: ollama/ollama:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  app:
    build: .
    deploy:
      resources:
        limits:
          memory: 32G
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    depends_on:
      - postgresql
      - qdrant
      - redis
      - ollama
```

---

## 🌐 Network Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Camera Network (VLAN 10)                                │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐        │
│  │ Cam 1  │  │ Cam 2  │  │ Cam 3  │  │ Cam 4  │        │
│  │ (RTSP) │  │ (RTSP) │  │ (RTSP) │  │ (RTSP) │        │
│  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘        │
│      └───────────┴───────────┴───────────┘              │
│                          │                               │
└──────────────────────────┼───────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │   Switch    │
                    │  (10 Gbps)  │
                    └──────┬──────┘
                           │
┌──────────────────────────┼───────────────────────────────┐
│  Application Network (VLAN 20)                           │
│                    ┌─────▼─────┐                         │
│                    │ App Server│                         │
│                    │ (Docker)  │                         │
│                    └─────┬─────┘                         │
│                          │                               │
│      ┌───────────────────┼───────────────────┐          │
│      │                   │                   │          │
│ ┌────▼────┐      ┌───────▼────┐      ┌──────▼─────┐   │
│ │ PostgreSQL│      │   Qdrant   │      │   Redis    │   │
│ └─────────┘      └────────────┘      └────────────┘   │
│                                                         │
│ ┌───────────┐                                          │
│ │  Ollama   │                                          │
│ │ DeepSeek  │                                          │
│ └───────────┘                                          │
└──────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────┐
│  Client Network (VLAN 30)                                │
│                    ┌─────▼─────┐                         │
│                    │  Clients  │                         │
│                    │ PyQt6/Web │                         │
│                    └───────────┘                         │
└──────────────────────────────────────────────────────────┘
```

---

## 📝 Technology Stack Summary

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **OS** | Ubuntu | 22.04 LTS | Server OS |
| **Container** | Docker | 24.x | Containerization |
| **Orchestration** | Docker Compose | v2.x | Service orchestration |
| **GPU Runtime** | NVIDIA Docker | Latest | GPU passthrough |
| **Language** | Python | 3.11+ | Primary language |
| **UI** | PyQt6 | 6.6+ | Desktop interface |
| **API** | FastAPI | 0.109+ | REST + WebSocket |
| **Detection** | YOLOv8 | Ultralytics | Person detection |
| **Tracking** | DeepSORT | Custom | Multi-object tracking |
| **Face Rec** | FaceNet/ArcFace | Custom | Worker identification |
| **OCR** | EasyOCR | 1.7+ | Badge reading |
| **Database** | PostgreSQL | 15 | Relational data |
| **Time-series** | TimescaleDB | 2.13+ | Time-series extension |
| **Vector DB** | Qdrant | 1.7+ | Embeddings storage |
| **Cache** | Redis | 7.x | Session cache |
| **LLM** | DeepSeek-R1 | 14B | Analysis & insights |
| **LLM Server** | Ollama | Latest | LLM inference |
| **Embeddings** | Sentence-Transformers | Latest | Text embeddings |
| **Monitoring** | Prometheus + Grafana | Optional | System monitoring |

---

## ✅ Architecture Design Complete

This architecture is designed for:
- ✅ **High Performance**: GPU optimization, multi-threading
- ✅ **Reliability**: Fault tolerance, auto-recovery
- ✅ **Scalability**: Horizontal and vertical scaling paths
- ✅ **Security**: Authentication, encryption, access control
- ✅ **Maintainability**: Modular design, clear separation of concerns
- ✅ **Observability**: Logging, monitoring, health checks

Next: Database Schema Design →
