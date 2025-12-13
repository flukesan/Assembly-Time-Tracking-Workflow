# Phase 3: Multi-Camera + Object Tracking

## 📋 Overview

Phase 3 adds **ByteTrack-based multi-object tracking** with PostgreSQL database integration for persistent storage.

### ✨ New Features

- 🎯 **ByteTrack Multi-Object Tracking**: Fast, accurate person tracking across frames
- 📹 **Multi-Camera Support**: Track up to 4 cameras simultaneously
- 🔢 **Unique Track IDs**: Each person gets a persistent ID across frames
- 🏗️ **Zone Transitions**: Automatic detection when person moves between zones
- 💾 **PostgreSQL Integration**: Save detections, tracks, and transitions to database
- 📊 **Tracking Analytics**: Query track history, statistics, and zone transitions
- ⚡ **Async Batch Writing**: Efficient database writes with 5-second flush intervals

---

## 🚀 Quick Start

### 1. Rebuild with New Dependencies

```bash
# Stop existing containers
docker compose -f docker-compose.cpu.yml down

# Rebuild with new dependencies (lap, asyncpg)
docker compose -f docker-compose.cpu.yml up -d --build

# Check logs
docker compose -f docker-compose.cpu.yml logs -f app
```

### 2. Verify Phase 3 Startup

Expected output:
```
assembly_app  | Phase: 3 - Multi-Camera + Tracking
assembly_app  | 💾 Initializing PostgreSQL connection...
assembly_app  | 📝 Initializing data writers...
assembly_app  | 📷 Initializing Camera Manager...
assembly_app  | 🏗️  Initializing Zone Manager...
assembly_app  | 🎯 Initializing Tracking Manager...
assembly_app  | 🤖 Initializing YOLOv8 Detection...
assembly_app  | ✅ Phase 3 Tracking system started successfully!
assembly_app  | 💾 PostgreSQL: Connected
```

### 3. Test API

```bash
# Check version
curl http://localhost:8000/

# Expected: {"version": "3.0.0", "phase": "Phase 3 - Multi-Camera + Tracking"}

# Check API docs
open http://localhost:8000/docs
```

---

## 📖 New API Endpoints

### 🎯 Tracking API (`/api/v1/tracking`)

#### Get Active Tracks
```bash
# All cameras
curl http://localhost:8000/api/v1/tracking/active

# Specific camera
curl http://localhost:8000/api/v1/tracking/active?camera_id=1

# Response:
{
  "camera_tracks": {
    "1": 3,  # 3 active tracks on camera 1
    "2": 2
  },
  "total_active": 5
}
```

#### Get Tracking Statistics
```bash
curl http://localhost:8000/api/v1/tracking/stats

# Response:
{
  "total_cameras": 2,
  "cameras": {
    "1": {
      "active_tracks": 3,
      "lost_tracks": 1,
      "frame_id": 1250
    }
  },
  "database": {
    "total_tracks": 15,
    "active_tracks": 3,
    "lost_tracks": 2,
    "finished_tracks": 10,
    "avg_confidence": 0.87
  }
}
```

#### Get Track History
```bash
# Get full history for track_id=1 on camera_id=1
curl "http://localhost:8000/api/v1/tracking/history/1?camera_id=1"

# With time filter
curl "http://localhost:8000/api/v1/tracking/history/1?camera_id=1&start_time=2025-12-13T10:00:00&end_time=2025-12-13T11:00:00"

# Response:
{
  "track_id": 1,
  "camera_id": 1,
  "total_detections": 450,
  "history": [
    {
      "detection_id": 1,
      "timestamp": "2025-12-13T10:30:00",
      "bbox_x1": 100.5,
      "bbox_y1": 200.3,
      "bbox_x2": 300.8,
      "bbox_y2": 500.2,
      "zone_id": 1,
      "confidence": 0.95
    }
  ]
}
```

#### Get Zone Transitions
```bash
# All transitions (last 100)
curl http://localhost:8000/api/v1/tracking/transitions

# Filter by track
curl "http://localhost:8000/api/v1/tracking/transitions?track_id=1"

# Filter by camera and time
curl "http://localhost:8000/api/v1/tracking/transitions?camera_id=1&start_time=2025-12-13T10:00:00&limit=50"

# Response:
{
  "total": 12,
  "transitions": [
    {
      "transition_id": 1,
      "track_id": 1,
      "camera_id": 1,
      "from_zone_id": 1,
      "from_zone_name": "Assembly Zone A",
      "to_zone_id": 2,
      "to_zone_name": "Break Area",
      "transition_time": "2025-12-13T10:35:22",
      "duration_in_prev_zone": 125.5
    }
  ]
}
```

#### Reset Tracking
```bash
# Reset specific camera
curl -X POST http://localhost:8000/api/v1/tracking/reset/1

# Reset all cameras
curl -X POST http://localhost:8000/api/v1/tracking/reset
```

#### Get Detection Count
```bash
# Total detections
curl http://localhost:8000/api/v1/tracking/detections/count

# Filter by camera and time
curl "http://localhost:8000/api/v1/tracking/detections/count?camera_id=1&start_time=2025-12-13T00:00:00"

# Response:
{
  "camera_id": 1,
  "start_time": "2025-12-13T00:00:00",
  "end_time": null,
  "count": 15420
}
```

---

## 🧪 Complete Testing Workflow

### Scenario: Multi-Camera Tracking with 4 Cameras

```bash
# 1. Create 4 cameras (video files or RTSP streams)
for i in {1..4}; do
  curl -X POST http://localhost:8000/api/v1/cameras/ \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"Camera $i\",
      \"rtsp_url\": \"/app/test_videos/camera$i.mp4\",
      \"location\": \"Assembly Line $i\",
      \"fps\": 30
    }"
done

# 2. Create zones for each camera
curl -X POST http://localhost:8000/api/v1/zones/ \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": 1,
    "name": "Work Zone",
    "zone_type": "work",
    "polygon_coords": [[200, 200], [800, 200], [800, 600], [200, 600]]
  }'

curl -X POST http://localhost:8000/api/v1/zones/ \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": 1,
    "name": "Break Zone",
    "zone_type": "break",
    "polygon_coords": [[850, 200], [1200, 200], [1200, 600], [850, 600]]
  }'

# 3. Start detection on all cameras
curl -X POST http://localhost:8000/api/v1/detection/start \
  -H "Content-Type: application/json" \
  -d '{"camera_ids": [1, 2, 3, 4]}'

# 4. Wait 30 seconds for tracking data

# 5. Check active tracks
curl http://localhost:8000/api/v1/tracking/active

# 6. Check tracking stats
curl http://localhost:8000/api/v1/tracking/stats

# 7. Check zone transitions
curl http://localhost:8000/api/v1/tracking/transitions?limit=20

# 8. Query database directly
docker compose -f docker-compose.cpu.yml exec postgresql psql -U assembly_user -d assembly_tracking -c "
SELECT
  track_id,
  camera_id,
  status,
  age,
  zone_id,
  last_seen
FROM tracked_objects
WHERE status = 'active'
ORDER BY last_seen DESC
LIMIT 10;
"

# 9. Stop detection
curl -X POST http://localhost:8000/api/v1/detection/stop
```

---

## 📊 Database Tables (Phase 3)

### New Tables Added

**1. detections**
```sql
CREATE TABLE detections (
    detection_id BIGSERIAL PRIMARY KEY,
    camera_id INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    class_name VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    bbox_x1 FLOAT NOT NULL,
    bbox_y1 FLOAT NOT NULL,
    bbox_x2 FLOAT NOT NULL,
    bbox_y2 FLOAT NOT NULL,
    zone_id INTEGER,
    track_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**2. tracked_objects**
```sql
CREATE TABLE tracked_objects (
    track_id INTEGER NOT NULL,
    camera_id INTEGER NOT NULL,
    class_name VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    bbox_x1 FLOAT NOT NULL,
    bbox_y1 FLOAT NOT NULL,
    bbox_x2 FLOAT NOT NULL,
    bbox_y2 FLOAT NOT NULL,
    zone_id INTEGER,
    status VARCHAR(20) NOT NULL,  -- active, lost, finished
    age INTEGER DEFAULT 0,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (track_id, camera_id)
);
```

**3. zone_transitions**
```sql
CREATE TABLE zone_transitions (
    transition_id BIGSERIAL PRIMARY KEY,
    track_id INTEGER NOT NULL,
    camera_id INTEGER NOT NULL,
    from_zone_id INTEGER,
    to_zone_id INTEGER,
    transition_time TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_in_prev_zone FLOAT,  -- seconds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Query Examples

```bash
# Connect to database
docker compose -f docker-compose.cpu.yml exec postgresql psql -U assembly_user -d assembly_tracking

# Count active tracks
SELECT camera_id, COUNT(*)
FROM tracked_objects
WHERE status = 'active'
GROUP BY camera_id;

# Zone transition summary
SELECT
  from_zone_id,
  to_zone_id,
  COUNT(*) as transition_count,
  AVG(duration_in_prev_zone) as avg_duration
FROM zone_transitions
WHERE transition_time >= NOW() - INTERVAL '1 hour'
GROUP BY from_zone_id, to_zone_id;

# Track with most detections
SELECT
  track_id,
  COUNT(*) as detection_count,
  AVG(confidence) as avg_confidence,
  MIN(timestamp) as first_seen,
  MAX(timestamp) as last_seen
FROM detections
GROUP BY track_id
ORDER BY detection_count DESC
LIMIT 10;
```

---

## 🏗️ Architecture (Phase 3)

```
┌───────────────────────────────────────────────────────────────┐
│                      FastAPI Server                           │
│  ┌────────┬────────┬──────────┬──────────────────────────┐   │
│  │Camera  │ Zone   │ Detection│ Tracking API (NEW)       │   │
│  │  API   │  API   │   API    │                          │   │
│  └────┬───┴────┬───┴─────┬────┴──────────┬───────────────┘   │
│       │        │         │                │                    │
│  ┌────▼────────▼─────────▼────────────────▼──────────────┐   │
│  │              Detection Manager                         │   │
│  │    Camera → YOLOv8 → ByteTrack → Zone Detection       │   │
│  └──────────────────────┬────────────────────────────────┘   │
│                         │                                     │
│       ┌─────────────────▼─────────────────┐                  │
│       │     Tracking Manager (NEW)        │                  │
│       │  ┌──────────────────────────┐    │                  │
│       │  │  ByteTracker (per camera)│    │                  │
│       │  │   - Kalman Filter         │    │                  │
│       │  │   - IoU Matching          │    │                  │
│       │  │   - Track ID Assignment   │    │                  │
│       │  └──────────────────────────┘    │                  │
│       └────────────┬──────────────────────┘                  │
│                    │                                          │
│       ┌────────────▼──────────────────┐                      │
│       │  Detection Writer (NEW)       │                      │
│       │  - Batch writing (100 items)  │                      │
│       │  - 5-second flush interval    │                      │
│       │  - Async PostgreSQL writes    │                      │
│       └────────────┬──────────────────┘                      │
│                    │                                          │
│       ┌────────────▼──────────────────┐                      │
│       │   PostgreSQL Database         │                      │
│       │  - detections                 │                      │
│       │  - tracked_objects            │                      │
│       │  - zone_transitions           │                      │
│       └───────────────────────────────┘                      │
└───────────────────────────────────────────────────────────────┘
```

---

## 🎯 ByteTrack Algorithm

**Key Features:**
- **Two-stage association**: High confidence + low confidence detections
- **Kalman filter**: Smooth trajectory prediction
- **IoU matching**: Fast, no deep features needed
- **Track buffer**: Keep lost tracks for 30 frames (re-identification)

**Performance:**
- ~30 FPS on CPU (yolov8n.pt)
- Handles occlusions and brief disappearances
- Minimal ID switches

---

## 🔧 Configuration

### Tracking Settings

Edit `src/main.py`:

```python
tracking_manager = TrackingManager(
    zone_manager=zone_manager,
    track_thresh=0.5,      # Min confidence for track initialization
    track_buffer=30,       # Frames to keep lost tracks
    match_thresh=0.8,      # IoU threshold for matching
    frame_rate=30          # Video frame rate
)
```

### Database Writer Settings

```python
detection_writer = DetectionWriter(
    db_manager=db_manager,
    batch_size=100,         # Detections per batch
    flush_interval=5.0      # Seconds between flushes
)
```

---

## 🐛 Troubleshooting

### Issue: Tracking IDs Change Too Often

**Solution**: Lower `match_thresh` or increase `track_buffer`

```python
tracking_manager = TrackingManager(
    track_thresh=0.5,
    track_buffer=60,       # Increase to 60 frames
    match_thresh=0.7,      # Lower threshold
    frame_rate=30
)
```

### Issue: Database Writes Too Slow

**Solution**: Increase `batch_size` or `flush_interval`

```python
detection_writer = DetectionWriter(
    db_manager=db_manager,
    batch_size=200,         # Increase batch size
    flush_interval=10.0     # Flush every 10 seconds
)
```

### Issue: PostgreSQL Connection Errors

```bash
# Check if PostgreSQL is running
docker compose -f docker-compose.cpu.yml ps postgresql

# Check logs
docker compose -f docker-compose.cpu.yml logs postgresql

# Restart PostgreSQL
docker compose -f docker-compose.cpu.yml restart postgresql

# Verify connection
docker compose -f docker-compose.cpu.yml exec postgresql psql -U assembly_user -d assembly_tracking -c "SELECT 1"
```

---

## 📈 Performance

### Expected Performance (CPU Mode)

| Cameras | FPS (Total) | FPS (Per Camera) | Database Writes/s |
|---------|-------------|------------------|-------------------|
| 1       | 25-30       | 25-30            | ~20               |
| 2       | 20-25       | 10-12            | ~40               |
| 4       | 15-20       | 4-5              | ~80               |

### Optimization Tips

1. **Use GPU**: 10x faster detection → 100+ total FPS
2. **Reduce frame rate**: Process every 2nd frame for 2x speedup
3. **Increase batch size**: Fewer database round trips
4. **Use smaller model**: yolov8n.pt vs yolov8s.pt

---

## ✅ Phase 3 Completion Checklist

- [x] ByteTrack multi-object tracking
- [x] Multi-camera support (4 cameras)
- [x] Unique track ID assignment
- [x] Zone transition detection
- [x] PostgreSQL database integration
- [x] Async batch writing (detections + tracks)
- [x] Tracking API endpoints
- [x] Track history queries
- [x] Zone transition queries
- [ ] Performance testing with 4 cameras
- [ ] Track ID persistence across long occlusions

---

## 🎯 Next: Phase 4 (Future)

Planned features:
- **Worker Identification**: Face recognition + badge matching
- **Time Tracking**: Entry/exit timestamps, duration in zones
- **Break Detection**: Automatic break time logging
- **Productivity Indices**: 11 indices per shift
- **RAG + DeepSeek-R1**: LLM-based analytics and insights

---

## 📞 Support

For issues, check:
1. API docs: http://localhost:8000/docs
2. Logs: `docker compose -f docker-compose.cpu.yml logs -f app`
3. Database: `docker compose -f docker-compose.cpu.yml exec postgresql psql -U assembly_user -d assembly_tracking`

**Happy Tracking! 🎯**
