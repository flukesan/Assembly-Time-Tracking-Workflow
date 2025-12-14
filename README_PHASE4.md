# Phase 4: Worker Identification + Time Tracking

## 📋 Overview

Phase 4 adds **worker identification** (face recognition + badge OCR) and **comprehensive time tracking** with 11 productivity indices.

### ✨ New Features

- 😊 **Face Recognition**: MTCNN detection + FaceNet embeddings for worker identification
- 🎫 **Badge OCR**: EasyOCR with Thai + English support for badge ID reading
- 👤 **Worker Management**: Full CRUD operations for worker data
- ⏱️ **Time Tracking**: Entry/exit detection, zone time tracking, session management
- 📊 **11 Productivity Indices**: Comprehensive worker performance metrics
- 🎯 **Real-time Tracking Integration**: Links tracking IDs to worker identities
- 💾 **Worker Database**: PostgreSQL storage for worker profiles and sessions

---

## 🚀 Quick Start

### 1. Rebuild with Phase 4 Dependencies

```bash
# Stop existing containers
docker compose -f docker-compose.cpu.yml down

# Rebuild with new dependencies (facenet-pytorch, updated requirements)
docker compose -f docker-compose.cpu.yml up -d --build

# Check logs
docker compose -f docker-compose.cpu.yml logs -f app
```

### 2. Verify Phase 4 Startup

Expected output:
```
assembly_app  | Phase: 4 - Worker Identification + Time Tracking
assembly_app  | 💾 Initializing PostgreSQL connection...
assembly_app  | 📷 Initializing Camera Manager...
assembly_app  | 🏗️  Initializing Zone Manager...
assembly_app  | 🎯 Initializing Tracking Manager...
assembly_app  | 👤 Initializing Worker Manager...
assembly_app  | 😊 Initializing Face Recognizer...
assembly_app  | 🎫 Initializing Badge OCR...
assembly_app  | ⏱️  Initializing Time Tracker...
assembly_app  | 🤖 Initializing YOLOv8 Detection...
assembly_app  | ✅ Phase 4 Worker Identification system started successfully!
assembly_app  | 😊 Face Recognition: Initialized
assembly_app  | 🎫 Badge OCR: Initialized (Thai + English)
assembly_app  | ⏱️  Time Tracking: Active
```

### 3. Test Worker API

```bash
# Check version
curl http://localhost:8000/

# Expected: {"version": "4.0.0", "phase": "Phase 4 - Worker Identification + Time Tracking"}

# Check API docs
open http://localhost:8000/docs
```

---

## 📖 New API Endpoints

### 👤 Worker Management API (`/api/v1/workers`)

#### Create Worker
```bash
curl -X POST http://localhost:8000/api/v1/workers/ \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "W001",
    "name": "สมชาย ใจดี",
    "badge_id": "BADGE001",
    "shift": "morning",
    "skill_level": "intermediate",
    "station_assignments": ["Assembly Line A", "Quality Check"]
  }'

# Response:
{
  "message": "Worker สมชาย ใจดี created successfully",
  "worker": {
    "worker_id": "W001",
    "name": "สมชาย ใจดี",
    "badge_id": "BADGE001",
    "shift": "morning",
    "skill_level": "intermediate",
    "active": true,
    "face_embedding": null
  }
}
```

#### List Workers
```bash
# All active workers
curl http://localhost:8000/api/v1/workers/

# All workers (including inactive)
curl "http://localhost:8000/api/v1/workers/?active_only=false"

# Workers by shift
curl "http://localhost:8000/api/v1/workers/?shift=morning"

# Response:
{
  "count": 10,
  "workers": [
    {
      "worker_id": "W001",
      "name": "สมชาย ใจดี",
      "badge_id": "BADGE001",
      "shift": "morning",
      "active": true
    }
  ]
}
```

#### Get Worker
```bash
curl http://localhost:8000/api/v1/workers/W001

# Response:
{
  "worker_id": "W001",
  "name": "สมชาย ใจดี",
  "badge_id": "BADGE001",
  "shift": "morning",
  "skill_level": "intermediate",
  "active": true
}
```

#### Update Worker
```bash
curl -X PUT http://localhost:8000/api/v1/workers/W001 \
  -H "Content-Type: application/json" \
  -d '{
    "skill_level": "senior",
    "station_assignments": ["Assembly Line A", "Team Lead"]
  }'
```

#### Delete Worker
```bash
curl -X DELETE http://localhost:8000/api/v1/workers/W001
```

---

### 😊 Face Recognition API

#### Enroll Worker Face
```bash
# Upload face image for worker
curl -X POST http://localhost:8000/api/v1/workers/W001/enroll_face \
  -F "image=@worker_face.jpg"

# Response:
{
  "worker_id": "W001",
  "success": true,
  "message": "Face enrolled successfully for สมชาย ใจดี",
  "embedding_shape": [512]
}
```

#### Check Face Enrollment
```bash
curl http://localhost:8000/api/v1/workers/W001/has_face

# Response:
{
  "worker_id": "W001",
  "has_face_enrolled": true
}
```

---

### ⏱️ Time Tracking API

#### Get Active Session
```bash
curl http://localhost:8000/api/v1/workers/W001/session

# Response:
{
  "worker_id": "W001",
  "has_active_session": true,
  "session": {
    "session_id": null,
    "worker_id": "W001",
    "worker_name": "สมชาย ใจดี",
    "shift": "morning",
    "start_time": "2025-12-14T08:00:00",
    "end_time": null,
    "total_duration_seconds": null,
    "active_time_seconds": 7200.0,
    "idle_time_seconds": 300.0,
    "break_time_seconds": 600.0,
    "zones_visited": ["Assembly Line A", "Break Area"],
    "current_zone": "Assembly Line A",
    "is_active": true
  }
}
```

#### Get Zone Times
```bash
curl http://localhost:8000/api/v1/workers/W001/zone_times

# Response:
{
  "worker_id": "W001",
  "has_active_session": true,
  "zone_times": {
    "Assembly Line A": 6800.5,
    "Break Area": 650.2,
    "Quality Check": 1200.0
  }
}
```

#### End Session Manually
```bash
curl -X POST http://localhost:8000/api/v1/workers/W001/end_session

# Response:
{
  "message": "Session ended for worker W001",
  "session": {
    "worker_id": "W001",
    "start_time": "2025-12-14T08:00:00",
    "end_time": "2025-12-14T16:00:00",
    "total_duration_seconds": 28800.0
  }
}
```

---

### 📊 Productivity API

#### Get Productivity Indices
```bash
curl http://localhost:8000/api/v1/workers/W001/productivity

# Response:
{
  "worker_id": "W001",
  "has_active_session": true,
  "indices": {
    "session_id": 0,
    "worker_id": "W001",
    "shift": "morning",
    "timestamp": "2025-12-14T16:00:00",

    "index_1_active_time": 25200.0,
    "index_2_idle_time": 1800.0,
    "index_3_break_time": 1800.0,
    "index_4_total_time": 28800.0,

    "index_5_work_efficiency": 87.5,
    "index_6_zone_transitions": 12,
    "index_7_avg_time_per_zone": 2400.0,

    "index_8_tasks_completed": 85,
    "index_9_output_per_hour": 10.625,
    "index_10_quality_score": 95.0,

    "index_11_overall_productivity": 89.3
  },
  "recommendations": [
    "Excellent performance! Overall productivity: 89.3/100"
  ]
}
```

#### Record Task Completion
```bash
# Record task with quality score
curl -X POST "http://localhost:8000/api/v1/workers/W001/task_completed?quality_score=95"

# Response:
{
  "message": "Task recorded for worker W001",
  "worker_id": "W001",
  "quality_score": 95.0
}
```

---

### 📈 Statistics API

#### Worker Statistics
```bash
curl http://localhost:8000/api/v1/workers/stats/summary

# Response:
{
  "total_workers": 25,
  "active_workers": 18,
  "with_face_enrolled": 20,
  "with_badge": 25,
  "by_shift": {
    "morning": 8,
    "afternoon": 7,
    "night": 3,
    "flexible": 7
  },
  "time_tracking": {
    "session_manager": {
      "active_sessions": 12
    },
    "tracked_workers": 12,
    "total_tasks_completed": 1024
  }
}
```

#### Active Sessions
```bash
curl http://localhost:8000/api/v1/workers/sessions/active

# Response:
{
  "count": 12,
  "sessions": [
    {
      "worker_id": "W001",
      "worker_name": "สมชาย ใจดี",
      "shift": "morning",
      "start_time": "2025-12-14T08:00:00"
    }
  ]
}
```

#### Cleanup Idle Sessions
```bash
# End sessions idle for more than 60 minutes
curl -X POST "http://localhost:8000/api/v1/workers/sessions/cleanup?max_idle_minutes=60"

# Response:
{
  "message": "Cleaned up 3 idle sessions",
  "count": 3,
  "sessions": [...]
}
```

---

## 🧪 Complete Testing Workflow

### Scenario: Worker Identification and Time Tracking

```bash
# 1. Create a worker
curl -X POST http://localhost:8000/api/v1/workers/ \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "W001",
    "name": "สมชาย ใจดี",
    "badge_id": "BADGE001",
    "shift": "morning",
    "skill_level": "intermediate"
  }'

# 2. Enroll worker's face
curl -X POST http://localhost:8000/api/v1/workers/W001/enroll_face \
  -F "image=@test_images/worker001_face.jpg"

# 3. Create camera and zones (from Phase 3)
curl -X POST http://localhost:8000/api/v1/cameras/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Camera 1",
    "rtsp_url": "/app/test_videos/assembly_line.mp4",
    "location": "Assembly Line A",
    "fps": 30
  }'

curl -X POST http://localhost:8000/api/v1/zones/ \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": 1,
    "name": "Assembly Line A",
    "zone_type": "work",
    "polygon_coords": [[200, 200], [800, 200], [800, 600], [200, 600]]
  }'

# 4. Start detection (worker will be identified and tracked)
curl -X POST http://localhost:8000/api/v1/detection/start \
  -H "Content-Type: application/json" \
  -d '{"camera_ids": [1]}'

# 5. Wait 30 seconds for detection and tracking

# 6. Check worker's active session
curl http://localhost:8000/api/v1/workers/W001/session

# 7. Check zone times
curl http://localhost:8000/api/v1/workers/W001/zone_times

# 8. Record some completed tasks
for i in {1..10}; do
  curl -X POST "http://localhost:8000/api/v1/workers/W001/task_completed?quality_score=95"
  sleep 2
done

# 9. Check productivity indices
curl http://localhost:8000/api/v1/workers/W001/productivity

# 10. Check all active sessions
curl http://localhost:8000/api/v1/workers/sessions/active

# 11. Stop detection
curl -X POST http://localhost:8000/api/v1/detection/stop
```

---

## 📊 11 Productivity Indices

### Index Breakdown

**Time-based Indices (1-4):**
1. **Active Time**: Total time worker is actively working (seconds)
2. **Idle Time**: Total time worker is idle (seconds)
3. **Break Time**: Total time in break zones (seconds)
4. **Total Time**: Total session duration (seconds)

**Efficiency Indices (5-7):**
5. **Work Efficiency**: `(Active Time / Total Time) × 100` (%)
6. **Zone Transitions**: Number of times worker moved between zones
7. **Average Time Per Zone**: `Total Time / (Transitions + 1)` (seconds)

**Output Indices (8-10):**
8. **Tasks Completed**: Number of tasks/units completed
9. **Output Per Hour**: `Tasks Completed / (Total Time / 3600)` (tasks/hour)
10. **Quality Score**: Average quality rating (0-100)

**Overall Index (11):**
11. **Overall Productivity**: Weighted average of all indices (0-100)
    - Efficiency (40%): indices 5-7
    - Output (40%): indices 8-10
    - Time Management (20%): indices 1-4

### Calculation Formula

```python
# Efficiency score (0-100)
efficiency_score = (
    work_efficiency * 0.6 +
    (100 - min(zone_transitions * 5, 100)) * 0.2 +
    (min(avg_time_per_zone / 60, 100)) * 0.2
)

# Output score (0-100)
output_score = (
    min(output_per_hour * 10, 100) * 0.6 +
    quality_score * 0.4
)

# Time management score (0-100)
time_score = (
    (active_time / total_time) * 100 * 0.7 +
    (1 - (idle_time / total_time)) * 100 * 0.3
)

# Overall productivity (0-100)
overall_productivity = (
    efficiency_score * 0.4 +
    output_score * 0.4 +
    time_score * 0.2
)
```

---

## 🏗️ Architecture (Phase 4)

```
┌───────────────────────────────────────────────────────────────┐
│                      FastAPI Server                           │
│  ┌────────┬────────┬──────────┬──────────┬──────────────┐    │
│  │Camera  │ Zone   │ Detection│ Tracking │ Worker (NEW) │    │
│  │  API   │  API   │   API    │   API    │     API      │    │
│  └────┬───┴────┬───┴─────┬────┴─────┬────┴──────┬───────┘    │
│       │        │         │          │            │             │
│  ┌────▼────────▼─────────▼──────────▼────────────▼────────┐  │
│  │              Detection Manager                          │  │
│  │    Camera → YOLOv8 → ByteTrack → Zone Detection        │  │
│  └──────────────────────┬──────────────────────────────────┘  │
│                         │                                      │
│       ┌─────────────────▼─────────────────┐                   │
│       │  Worker Identification (NEW)      │                   │
│       │  ┌──────────────┬──────────────┐  │                   │
│       │  │ Face Recog.  │  Badge OCR   │  │                   │
│       │  │  (MTCNN +    │  (EasyOCR    │  │                   │
│       │  │   FaceNet)   │  Thai+Eng)   │  │                   │
│       │  └──────────────┴──────────────┘  │                   │
│       └─────────────────┬─────────────────┘                   │
│                         │                                      │
│       ┌─────────────────▼─────────────────┐                   │
│       │   Time Tracking (NEW)             │                   │
│       │  - Session Management             │                   │
│       │  - Zone Time Tracking             │                   │
│       │  - Productivity Calculator        │                   │
│       │  - 11 Indices Computation         │                   │
│       └─────────────────┬─────────────────┘                   │
│                         │                                      │
│       ┌─────────────────▼─────────────────┐                   │
│       │   PostgreSQL Database             │                   │
│       │  - workers (NEW)                  │                   │
│       │  - worker_sessions (NEW)          │                   │
│       │  - productivity_indices (NEW)     │                   │
│       │  - detections                     │                   │
│       │  - tracked_objects                │                   │
│       │  - zone_transitions               │                   │
│       └───────────────────────────────────┘                   │
└───────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuration

### Face Recognition Settings

Edit `src/main.py`:

```python
face_recognizer = FaceRecognizer(
    device="cpu",              # "cpu" or "cuda"
    min_face_size=40,          # Minimum face size (pixels)
    detection_threshold=0.9    # Confidence threshold (0-1)
)
```

### Badge OCR Settings

```python
badge_ocr = BadgeOCR(
    languages=['th', 'en'],    # OCR languages
    gpu=False,                 # Use GPU for OCR
    min_confidence=0.3,        # Minimum confidence
    badge_pattern=r'^[A-Z]{2}\d{4}$'  # Badge ID pattern (optional)
)
```

### Time Tracking Settings

```python
time_tracker = TimeTracker(
    idle_threshold_seconds=300,  # 5 minutes idle threshold
    break_zone_names=[           # Zones considered as break areas
        "Break Area",
        "Rest Zone",
        "Cafeteria"
    ],
    target_output_per_hour=10.0  # Target output for productivity
)
```

---

## 🐛 Troubleshooting

### Issue: Face Recognition Fails

**Symptoms**: `No face detected in image`

**Solutions**:
1. Check image quality (good lighting, clear face)
2. Lower `detection_threshold`:
   ```python
   face_recognizer = FaceRecognizer(detection_threshold=0.7)
   ```
3. Ensure face is at least 40 pixels
4. Check image format (JPG/PNG supported)

### Issue: Badge OCR Not Reading

**Symptoms**: Badge ID not detected

**Solutions**:
1. Lower `min_confidence`:
   ```python
   badge_ocr = BadgeOCR(min_confidence=0.2)
   ```
2. Check badge is in upper chest region
3. Ensure good lighting and contrast
4. Set badge pattern if using specific format:
   ```python
   badge_ocr.set_badge_pattern(r'^\d{6}$')  # 6 digits
   ```

### Issue: Sessions Not Starting

**Symptoms**: Worker detected but no session created

**Solutions**:
1. Ensure worker is enrolled:
   ```bash
   curl http://localhost:8000/api/v1/workers/W001/has_face
   ```
2. Check time tracker initialization in logs
3. Verify worker identification is working:
   ```bash
   curl http://localhost:8000/api/v1/tracking/active
   ```

### Issue: Productivity Indices Are Zero

**Symptoms**: All indices return 0.0

**Solutions**:
1. Ensure session is active
2. Record some tasks:
   ```bash
   curl -X POST http://localhost:8000/api/v1/workers/W001/task_completed?quality_score=90
   ```
3. Check session times are updating:
   ```bash
   curl http://localhost:8000/api/v1/workers/W001/zone_times
   ```

---

## 📈 Performance

### Expected Performance (CPU Mode)

| Component | Model | Performance |
|-----------|-------|-------------|
| Face Detection | MTCNN | 15-20 FPS |
| Face Embedding | FaceNet | 30-40 FPS |
| Badge OCR | EasyOCR | 5-10 FPS |
| Overall Impact | - | -10% on detection FPS |

### Optimization Tips

1. **Use GPU for Face Recognition**:
   ```python
   face_recognizer = FaceRecognizer(device="cuda")
   badge_ocr = BadgeOCR(gpu=True)
   ```

2. **Reduce Face Detection Frequency**:
   - Only detect faces every 5th frame
   - Once identified, track by track_id

3. **Batch Badge OCR**:
   - Only run OCR when face match fails
   - Cache badge IDs for known track_ids

4. **Optimize Database Writes**:
   - Increase batch sizes
   - Use async writes

---

## ✅ Phase 4 Completion Checklist

- [x] Face recognition (MTCNN + FaceNet)
- [x] Badge OCR (EasyOCR with Thai + English)
- [x] Worker CRUD operations
- [x] Time tracking and session management
- [x] 11 productivity indices calculation
- [x] Worker API endpoints
- [x] Integration with tracking system
- [ ] Database schema for workers
- [ ] Real-time worker identification in video stream
- [ ] Productivity dashboard UI

---

## 🎯 Next: Phase 5 (RAG + DeepSeek-R1)

Planned features:
- **RAG System**: Vector database (Qdrant) for knowledge retrieval
- **DeepSeek-R1 Integration**: Local LLM via Ollama
- **Natural Language Queries**: Ask questions about worker productivity
- **Automated Insights**: LLM-generated recommendations
- **Report Generation**: Automated shift summaries and reports

---

## 📞 Support

For issues, check:
1. API docs: http://localhost:8000/docs
2. Logs: `docker compose -f docker-compose.cpu.yml logs -f app`
3. Database: `docker compose -f docker-compose.cpu.yml exec postgresql psql -U assembly_user -d assembly_tracking`

**Happy Tracking! 👤⏱️📊**
