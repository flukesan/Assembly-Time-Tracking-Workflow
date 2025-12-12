# Phase 2: Single Camera + Detection

## 📋 Overview

Phase 2 implements **YOLOv8-based person detection** with camera management and zone-based tracking.

### ✨ Features Implemented

- 📷 **Camera Management**: RTSP stream capture with multi-threading
- 🤖 **YOLOv8 Detection**: Real-time person detection (CPU/GPU)
- 🏗️ **Zone Management**: Polygon-based zone definitions with point-in-polygon detection
- 🌐 **REST API**: Camera, Detection, and Zone endpoints
- 📡 **WebSocket**: Real-time detection results streaming
- 🎯 **Frame Buffer**: Thread-safe circular buffer for camera frames

---

## 🚀 Quick Start

### 1. Download YOLOv8 Models

```bash
# On host machine (recommended)
chmod +x scripts/download_models_local.sh
./scripts/download_models_local.sh

# Or inside Docker container
docker compose -f docker-compose.cpu.yml exec app bash
bash scripts/download_models.sh
```

This downloads:
- `yolov8n.pt` (6 MB) - Nano model, fastest (~30 FPS on CPU)
- `yolov8s.pt` (22 MB) - Small model, balanced (~15 FPS on CPU)

### 2. Start Services

```bash
# Start all services (PostgreSQL, Qdrant, Redis, Ollama, App)
docker compose -f docker-compose.cpu.yml up -d

# Check logs
docker compose -f docker-compose.cpu.yml logs -f app
```

### 3. Verify API

```bash
# Check if API is running
curl http://localhost:8000/

# Expected output:
{
  "message": "Assembly Time-Tracking System",
  "version": "2.0.0",
  "phase": "Phase 2 - Single Camera + Detection"
}

# Access API documentation
open http://localhost:8000/docs
```

---

## 📖 API Documentation

### 🎥 Camera API (`/api/v1/cameras`)

#### List All Cameras
```bash
curl http://localhost:8000/api/v1/cameras/
```

#### Create Camera (Test with Video File)
```bash
curl -X POST http://localhost:8000/api/v1/cameras/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Camera 1",
    "rtsp_url": "/path/to/test_video.mp4",
    "location": "Assembly Line 1",
    "fps": 30,
    "resolution_width": 1920,
    "resolution_height": 1080
  }'
```

#### Create Camera (RTSP Stream)
```bash
curl -X POST http://localhost:8000/api/v1/cameras/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "RTSP Camera 1",
    "rtsp_url": "rtsp://admin:password@192.168.1.100:554/stream1",
    "location": "Assembly Line 1",
    "fps": 30
  }'
```

#### Get Camera Status
```bash
curl http://localhost:8000/api/v1/cameras/1
```

#### Stop Camera
```bash
curl -X POST http://localhost:8000/api/v1/cameras/1/stop
```

#### Delete Camera
```bash
curl -X DELETE http://localhost:8000/api/v1/cameras/1
```

---

### 🏗️ Zone API (`/api/v1/zones`)

#### Create Zone (Work Area)
```bash
curl -X POST http://localhost:8000/api/v1/zones/ \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": 1,
    "name": "Assembly Zone A",
    "zone_type": "work",
    "polygon_coords": [[100, 100], [500, 100], [500, 400], [100, 400]],
    "color": "#00FF00",
    "active": true
  }'
```

#### List All Zones
```bash
curl http://localhost:8000/api/v1/zones/
```

#### Get Zones for Camera
```bash
curl http://localhost:8000/api/v1/zones/camera/1
```

#### Update Zone
```bash
curl -X PUT http://localhost:8000/api/v1/zones/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Zone Name",
    "active": false
  }'
```

#### Delete Zone
```bash
curl -X DELETE http://localhost:8000/api/v1/zones/1
```

---

### 🤖 Detection API (`/api/v1/detection`)

#### Start Detection
```bash
curl -X POST http://localhost:8000/api/v1/detection/start \
  -H "Content-Type: application/json" \
  -d '{
    "camera_ids": [1]
  }'
```

#### Stop Detection
```bash
curl -X POST http://localhost:8000/api/v1/detection/stop
```

#### Get Detection Status
```bash
curl http://localhost:8000/api/v1/detection/status
```

#### Get Detection Statistics
```bash
curl http://localhost:8000/api/v1/detection/stats

# Expected output:
{
  "model_name": "yolov8n.pt",
  "device": "cpu",
  "frames_processed": 1250,
  "total_detections": 342,
  "avg_inference_time_ms": 45.2,
  "avg_fps": 22.1
}
```

---

### 📡 WebSocket (Real-time Detection Feed)

```javascript
// JavaScript example
const ws = new WebSocket('ws://localhost:8000/api/v1/detection/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Detection result:', data);

  // Example data structure:
  // {
  //   "camera_id": 1,
  //   "timestamp": "2025-12-12T10:30:00",
  //   "detections": [
  //     {
  //       "class_name": "person",
  //       "confidence": 0.95,
  //       "bbox": [100, 200, 300, 400]
  //     }
  //   ],
  //   "inference_time_ms": 45.2,
  //   "zone_matches": {
  //     "1": [...],  // Detections in zone 1
  //     "2": [...]   // Detections in zone 2
  //   }
  // }
};
```

```python
# Python example
import websockets
import asyncio
import json

async def listen_detections():
    uri = "ws://localhost:8000/api/v1/detection/ws"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Camera {data['camera_id']}: {len(data['detections'])} persons detected")

asyncio.run(listen_detections())
```

---

## 🧪 Testing Workflow

### Complete Test Scenario

```bash
# 1. Create a camera (replace with your video file or RTSP URL)
curl -X POST http://localhost:8000/api/v1/cameras/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Camera",
    "rtsp_url": "/path/to/test_video.mp4",
    "location": "Test Area",
    "fps": 30
  }'

# Response: {"camera_id": 1, ...}

# 2. Create a zone
curl -X POST http://localhost:8000/api/v1/zones/ \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": 1,
    "name": "Work Zone",
    "zone_type": "work",
    "polygon_coords": [[200, 200], [800, 200], [800, 600], [200, 600]],
    "color": "#00FF00"
  }'

# Response: {"zone_id": 1, ...}

# 3. Start detection
curl -X POST http://localhost:8000/api/v1/detection/start \
  -H "Content-Type: application/json" \
  -d '{"camera_ids": [1]}'

# 4. Check detection status (wait 10 seconds)
sleep 10
curl http://localhost:8000/api/v1/detection/stats

# 5. Stop detection
curl -X POST http://localhost:8000/api/v1/detection/stop

# 6. Cleanup
curl -X DELETE http://localhost:8000/api/v1/cameras/1
```

---

## 🎬 Testing with Sample Videos

### Download Sample Videos

```bash
# Create test videos directory
mkdir -p test_videos

# Download sample video (people walking)
wget -O test_videos/sample.mp4 \
  "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"

# Or use your own video
cp /path/to/your/video.mp4 test_videos/
```

### Mount Video in Docker

Update `docker-compose.cpu.yml`:

```yaml
services:
  app:
    volumes:
      - ./src:/app/src
      - ./config:/app/config
      - ./scripts:/app/scripts
      - ./models:/app/models      # YOLOv8 models
      - ./test_videos:/app/test_videos  # Add this line
```

Restart services:

```bash
docker compose -f docker-compose.cpu.yml down
docker compose -f docker-compose.cpu.yml up -d
```

Create camera with video file:

```bash
curl -X POST http://localhost:8000/api/v1/cameras/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Video",
    "rtsp_url": "/app/test_videos/sample.mp4",
    "location": "Test",
    "fps": 30
  }'
```

---

## 📊 Architecture

### Components

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI Server                     │
│  ┌────────────┬────────────┬──────────────────────┐ │
│  │ Camera API │ Zone API   │ Detection API (WS)   │ │
│  └─────┬──────┴──────┬─────┴──────────┬───────────┘ │
│        │             │                │              │
│  ┌─────▼─────┐ ┌────▼────┐     ┌─────▼──────────┐  │
│  │  Camera   │ │  Zone   │     │   Detection    │  │
│  │  Manager  │ │ Manager │     │    Manager     │  │
│  └─────┬─────┘ └────┬────┘     └─────┬──────────┘  │
│        │             │                │              │
│  ┌─────▼─────────────▼────────────────▼──────────┐  │
│  │         Camera Capture Threads (x4)           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │  │
│  │  │ Camera 1 │  │ Camera 2 │  │ Camera N │   │  │
│  │  │  Buffer  │  │  Buffer  │  │  Buffer  │   │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘   │  │
│  └───────┼─────────────┼─────────────┼──────────┘  │
│          │             │             │              │
│  ┌───────▼─────────────▼─────────────▼──────────┐  │
│  │       YOLOv8 Detection Thread (x1)           │  │
│  │         ┌────────────────────┐                │  │
│  │         │  YOLOv8 Detector   │                │  │
│  │         └─────────┬──────────┘                │  │
│  │                   │                            │  │
│  │         ┌─────────▼──────────┐                │  │
│  │         │  Zone Detector     │                │  │
│  │         │ (Point-in-Polygon) │                │  │
│  │         └─────────┬──────────┘                │  │
│  └───────────────────┼──────────────────────────┘  │
│                      │                              │
│            ┌─────────▼──────────┐                   │
│            │  WebSocket Clients │                   │
│            └────────────────────┘                   │
└─────────────────────────────────────────────────────┘
```

### Data Flow

1. **Camera Capture** → RTSP/Video → Frame Buffer (thread-safe)
2. **Detection Thread** → Get frames → YOLOv8 inference → Detections
3. **Zone Matching** → Point-in-polygon → Assign detections to zones
4. **WebSocket Broadcast** → Real-time results to clients

---

## 🔧 Configuration

### Detection Settings

Edit `config/config.yaml`:

```yaml
detection:
  model_name: "yolov8n.pt"  # or yolov8s.pt, yolov8m.pt
  confidence_threshold: 0.5
  iou_threshold: 0.45
  device: "cpu"  # or "cuda" for GPU
  classes: [0]  # 0 = person (COCO dataset)
  img_size: 640
  max_detections: 100
```

### Camera Settings

```yaml
camera:
  default_fps: 30
  default_resolution_width: 1920
  default_resolution_height: 1080
  frame_buffer_size: 30  # Keep 30 frames (~1 second at 30fps)
  max_reconnect_attempts: 3
  reconnect_delay: 5  # seconds
```

---

## 🐛 Troubleshooting

### Issue: YOLOv8 Model Not Found

```bash
# Download models
./scripts/download_models_local.sh

# Verify models exist
ls -la models/

# Expected:
# yolov8n.pt
# yolov8s.pt
```

### Issue: Camera Connection Failed

```bash
# Check camera status
curl http://localhost:8000/api/v1/cameras/1

# Look for "error_message" field
# Common issues:
# - Invalid RTSP URL
# - Network firewall blocking RTSP
# - Video file not mounted in Docker
```

### Issue: Slow Detection (Low FPS)

```bash
# Check stats
curl http://localhost:8000/api/v1/detection/stats

# If avg_fps < 10:
# 1. Use smaller model (yolov8n.pt instead of yolov8m.pt)
# 2. Reduce resolution in camera config
# 3. Enable GPU (if available)
```

### Issue: No Detections

```bash
# Check confidence threshold (may be too high)
# Edit config/config.yaml:
detection:
  confidence_threshold: 0.3  # Lower = more detections (but more false positives)
```

---

## 📈 Performance

### CPU Performance (Expected)

| Model      | Size  | Inference Time | FPS (CPU) | Accuracy |
|------------|-------|----------------|-----------|----------|
| yolov8n.pt | 6 MB  | 30-50ms        | 20-30 FPS | Good     |
| yolov8s.pt | 22 MB | 60-80ms        | 12-15 FPS | Better   |
| yolov8m.pt | 52 MB | 150-200ms      | 5-7 FPS   | Best     |

### GPU Performance (Expected with CUDA)

| Model      | Inference Time | FPS (GPU) |
|------------|----------------|-----------|
| yolov8n.pt | 5-10ms         | 100+ FPS  |
| yolov8s.pt | 10-15ms        | 60+ FPS   |
| yolov8m.pt | 20-30ms        | 30+ FPS   |

---

## ✅ Phase 2 Completion Checklist

- [x] Camera Management (RTSP capture, frame buffering)
- [x] YOLOv8 Detection (person detection)
- [x] Zone Management (polygon definitions, point-in-polygon)
- [x] REST API (Camera, Detection, Zone endpoints)
- [x] WebSocket (Real-time detection streaming)
- [ ] PostgreSQL Integration (save detections to database)
- [ ] Performance Testing (FPS benchmarks, stress testing)

---

## 🎯 Next: Phase 3

Phase 3 will add:
- **Multi-Camera Support** (4 cameras simultaneously)
- **DeepSORT/ByteTrack** (Object tracking across frames)
- **Worker Identification** (Face recognition + badge matching)
- **Time Tracking** (Entry/exit timestamps, session management)

---

## 📞 Support

For issues, check:
1. API docs: http://localhost:8000/docs
2. Logs: `docker compose -f docker-compose.cpu.yml logs -f app`
3. Health check: `curl http://localhost:8000/health`

**Happy Testing! 🎉**
