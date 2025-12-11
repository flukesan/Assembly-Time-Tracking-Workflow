# API Design - REST Endpoints & WebSocket

## 🔍 Overview

FastAPI-based REST API with WebSocket support for real-time updates.

### Base Configuration
- **Framework**: FastAPI 0.109+
- **Base URL**: `http://localhost:8000` (development), `https://api.your-domain.com` (production)
- **API Version**: v1 (`/api/v1/`)
- **Documentation**: Auto-generated Swagger UI at `/docs`
- **Authentication**: API Key (M2M) + OAuth2 (Users)
- **Rate Limiting**: 100 requests/minute per IP

---

## 🔐 Authentication

### 1. API Key Authentication (Machine-to-Machine)

**Usage**: For external systems, scripts, integrations

```http
GET /api/v1/metrics/today
Authorization: Bearer sk_your_api_key_here
```

**Generate API Key**:
```http
POST /api/v1/auth/api-keys
Content-Type: application/json
Authorization: Bearer <admin_jwt_token>

{
  "name": "External Dashboard",
  "permissions": ["metrics:read", "zones:read"],
  "expires_at": "2025-12-31T23:59:59Z"
}

Response 201:
{
  "api_key": "sk_live_abc123def456...",
  "name": "External Dashboard",
  "created_at": "2025-01-15T10:00:00Z",
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**Revoke API Key**:
```http
DELETE /api/v1/auth/api-keys/{key_id}
Authorization: Bearer <admin_jwt_token>

Response 204: No Content
```

---

### 2. OAuth2 + JWT (User Authentication)

**Login Flow**:
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "supervisor_001",
  "password": "secure_password_here"
}

Response 200:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "user_id": "supervisor_001",
    "name": "สมชาย ใจดี",
    "role": "supervisor",
    "permissions": ["read", "write", "acknowledge_alerts"]
  }
}
```

**Refresh Token**:
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

Response 200:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Logout**:
```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>

Response 200:
{
  "message": "Successfully logged out"
}
```

---

### 3. Role-Based Access Control (RBAC)

| Role | Permissions | Description |
|------|-------------|-------------|
| **admin** | `*` (all) | Full system access |
| **supervisor** | `read`, `write`, `acknowledge_alerts`, `view_reports` | Manage operations |
| **viewer** | `read`, `view_reports` | Read-only access |
| **api_client** | `metrics:read`, `zones:read` | External integrations |

---

## 📋 REST API Endpoints

### Health & System

#### `GET /health`
**Description**: System health check
**Authentication**: None (public)
**Rate Limit**: Unlimited

```http
GET /health

Response 200:
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "version": "1.0.0",
  "components": {
    "postgresql": "healthy",
    "qdrant": "healthy",
    "redis": "healthy",
    "ollama": "healthy",
    "cameras": {
      "CAM01": "active",
      "CAM02": "active",
      "CAM03": "active",
      "CAM04": "active"
    },
    "gpu": {
      "utilization": 85,
      "memory_used": 18432,
      "memory_total": 24576,
      "temperature": 72
    }
  },
  "uptime_seconds": 3600
}
```

---

### Workers

#### `GET /api/v1/workers`
**Description**: List all workers
**Authentication**: Required
**Permissions**: `read`

```http
GET /api/v1/workers?active=true&shift=morning&limit=50&offset=0
Authorization: Bearer <token>

Response 200:
{
  "total": 25,
  "limit": 50,
  "offset": 0,
  "workers": [
    {
      "worker_id": "W001",
      "name": "สมชาย ใจดี",
      "badge_id": "BADGE-001",
      "shift": "morning",
      "skill_level": "expert",
      "active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2025-01-15T08:00:00Z"
    },
    ...
  ]
}
```

#### `GET /api/v1/workers/{worker_id}`
**Description**: Get worker details
**Authentication**: Required
**Permissions**: `read`

```http
GET /api/v1/workers/W001
Authorization: Bearer <token>

Response 200:
{
  "worker_id": "W001",
  "name": "สมชาย ใจดี",
  "badge_id": "BADGE-001",
  "shift": "morning",
  "skill_level": "expert",
  "station_assignments": {
    "preferred": ["Z01"],
    "certified": ["Z01", "Z02", "Z03"]
  },
  "active": true,
  "statistics": {
    "total_sessions": 120,
    "total_active_hours": 480,
    "total_idle_hours": 20,
    "productivity_score": 0.96,
    "attendance_rate": 0.98
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2025-01-15T08:00:00Z"
}
```

#### `POST /api/v1/workers`
**Description**: Create new worker
**Authentication**: Required
**Permissions**: `write`

```http
POST /api/v1/workers
Authorization: Bearer <token>
Content-Type: application/json

{
  "worker_id": "W025",
  "name": "สมหญิง รักงาน",
  "badge_id": "BADGE-025",
  "shift": "afternoon",
  "skill_level": "intermediate"
}

Response 201:
{
  "worker_id": "W025",
  "name": "สมหญิง รักงาน",
  "badge_id": "BADGE-025",
  "shift": "afternoon",
  "skill_level": "intermediate",
  "active": true,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

#### `PUT /api/v1/workers/{worker_id}`
**Description**: Update worker
**Authentication**: Required
**Permissions**: `write`

```http
PUT /api/v1/workers/W025
Authorization: Bearer <token>
Content-Type: application/json

{
  "skill_level": "expert",
  "station_assignments": {
    "preferred": ["Z01", "Z02"],
    "certified": ["Z01", "Z02", "Z03", "Z04"]
  }
}

Response 200:
{
  "worker_id": "W025",
  "name": "สมหญิง รักงาน",
  "badge_id": "BADGE-025",
  "shift": "afternoon",
  "skill_level": "expert",
  "station_assignments": {
    "preferred": ["Z01", "Z02"],
    "certified": ["Z01", "Z02", "Z03", "Z04"]
  },
  "active": true,
  "updated_at": "2025-01-15T10:35:00Z"
}
```

#### `DELETE /api/v1/workers/{worker_id}`
**Description**: Deactivate worker (soft delete)
**Authentication**: Required
**Permissions**: `delete`

```http
DELETE /api/v1/workers/W025
Authorization: Bearer <token>

Response 204: No Content
```

---

### Zones

#### `GET /api/v1/zones`
**Description**: List all zones
**Authentication**: Required
**Permissions**: `read`

```http
GET /api/v1/zones?camera_id=CAM01&active=true
Authorization: Bearer <token>

Response 200:
{
  "total": 4,
  "zones": [
    {
      "zone_id": "Z01",
      "camera_id": "CAM01",
      "name": "Assembly Station 1",
      "zone_type": "work_area",
      "color": "#00FF00",
      "polygon_coords": [[100, 200], [500, 200], [500, 800], [100, 800]],
      "min_workers": 1,
      "max_workers": 3,
      "active": true,
      "current_occupancy": 2,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2025-01-15T08:00:00Z"
    },
    ...
  ]
}
```

#### `POST /api/v1/zones`
**Description**: Create new zone
**Authentication**: Required
**Permissions**: `write`

```http
POST /api/v1/zones
Authorization: Bearer <token>
Content-Type: application/json

{
  "zone_id": "Z05",
  "camera_id": "CAM02",
  "name": "Inspection Area A",
  "zone_type": "inspection",
  "color": "#FF0000",
  "polygon_coords": [[150, 300], [600, 300], [600, 700], [150, 700]],
  "min_workers": 1,
  "max_workers": 2
}

Response 201:
{
  "zone_id": "Z05",
  "camera_id": "CAM02",
  "name": "Inspection Area A",
  "zone_type": "inspection",
  "color": "#FF0000",
  "polygon_coords": [[150, 300], [600, 300], [600, 700], [150, 700]],
  "min_workers": 1,
  "max_workers": 2,
  "active": true,
  "created_at": "2025-01-15T10:40:00Z",
  "updated_at": "2025-01-15T10:40:00Z"
}
```

#### `GET /api/v1/zones/{zone_id}/occupancy`
**Description**: Get current zone occupancy (real-time)
**Authentication**: Required
**Permissions**: `read`

```http
GET /api/v1/zones/Z01/occupancy
Authorization: Bearer <token>

Response 200:
{
  "zone_id": "Z01",
  "zone_name": "Assembly Station 1",
  "current_count": 2,
  "min_workers": 1,
  "max_workers": 3,
  "status": "normal",
  "workers": [
    {
      "worker_id": "W001",
      "name": "สมชาย ใจดี",
      "entry_time": "2025-01-15T08:35:42Z",
      "duration_seconds": 3600,
      "state": "active"
    },
    {
      "worker_id": "W003",
      "name": "สมศรี ขยัน",
      "entry_time": "2025-01-15T08:40:15Z",
      "duration_seconds": 3300,
      "state": "idle"
    }
  ]
}
```

---

### Cameras

#### `GET /api/v1/cameras`
**Description**: List all cameras
**Authentication**: Required
**Permissions**: `read`

```http
GET /api/v1/cameras?status=active
Authorization: Bearer <token>

Response 200:
{
  "total": 4,
  "cameras": [
    {
      "camera_id": "CAM01",
      "name": "Station 1 Overhead",
      "rtsp_url": "rtsp://192.168.1.100:554/stream1",
      "location": "Assembly Line A - North",
      "status": "active",
      "resolution": "1920x1080",
      "fps": 30,
      "last_seen_at": "2025-01-15T10:45:30Z",
      "zones_count": 2
    },
    ...
  ]
}
```

#### `POST /api/v1/cameras`
**Description**: Add new camera
**Authentication**: Required
**Permissions**: `config`

```http
POST /api/v1/cameras
Authorization: Bearer <token>
Content-Type: application/json

{
  "camera_id": "CAM05",
  "name": "Station 3 Side View",
  "rtsp_url": "rtsp://192.168.1.105:554/stream1",
  "location": "Assembly Line B - East",
  "resolution": "1920x1080",
  "fps": 30
}

Response 201:
{
  "camera_id": "CAM05",
  "name": "Station 3 Side View",
  "rtsp_url": "rtsp://192.168.1.105:554/stream1",
  "location": "Assembly Line B - East",
  "status": "inactive",
  "resolution": "1920x1080",
  "fps": 30,
  "created_at": "2025-01-15T10:50:00Z"
}
```

---

### Sessions & Tracking

#### `GET /api/v1/sessions/active`
**Description**: Get all active tracking sessions
**Authentication**: Required
**Permissions**: `read`

```http
GET /api/v1/sessions/active?zone_id=Z01
Authorization: Bearer <token>

Response 200:
{
  "total": 8,
  "sessions": [
    {
      "session_id": "W001_Z01_20250115_083542",
      "worker_id": "W001",
      "worker_name": "สมชาย ใจดี",
      "zone_id": "Z01",
      "zone_name": "Assembly Station 1",
      "track_id": 1,
      "entry_time": "2025-01-15T08:35:42Z",
      "duration_seconds": 4200,
      "total_active_seconds": 3800,
      "total_idle_seconds": 400,
      "productivity": 0.905,
      "state": "active",
      "index_number": 5
    },
    ...
  ]
}
```

#### `GET /api/v1/sessions/{session_id}`
**Description**: Get session details
**Authentication**: Required
**Permissions**: `read`

```http
GET /api/v1/sessions/W001_Z01_20250115_083542
Authorization: Bearer <token>

Response 200:
{
  "session_id": "W001_Z01_20250115_083542",
  "worker_id": "W001",
  "worker_name": "สมชาย ใจดี",
  "zone_id": "Z01",
  "zone_name": "Assembly Station 1",
  "track_id": 1,
  "entry_time": "2025-01-15T08:35:42Z",
  "exit_time": null,
  "total_active_seconds": 3800,
  "total_idle_seconds": 400,
  "index_number": 5,
  "state": "active",
  "motion_score": 0.85,
  "timeline": [
    {
      "timestamp": "2025-01-15T08:35:42Z",
      "event": "entry",
      "state": "active"
    },
    {
      "timestamp": "2025-01-15T09:15:00Z",
      "event": "idle_start",
      "state": "idle",
      "duration": 120
    },
    {
      "timestamp": "2025-01-15T09:17:00Z",
      "event": "active_resume",
      "state": "active"
    }
  ]
}
```

---

### Metrics & Analytics

#### `GET /api/v1/metrics/today`
**Description**: Today's metrics summary
**Authentication**: Required
**Permissions**: `read`

```http
GET /api/v1/metrics/today
Authorization: Bearer <token>

Response 200:
{
  "date": "2025-01-15",
  "current_index": 5,
  "total_indices": 11,
  "total_workers": 25,
  "active_workers": 20,
  "total_active_seconds": 72000,
  "total_idle_seconds": 8000,
  "overall_productivity": 0.9,
  "zones": [
    {
      "zone_id": "Z01",
      "zone_name": "Assembly Station 1",
      "workers_count": 2,
      "productivity": 0.92,
      "status": "normal"
    },
    ...
  ],
  "anomalies_count": 3,
  "alerts_count": 5
}
```

#### `GET /api/v1/metrics/zone/{zone_id}`
**Description**: Zone-specific metrics
**Authentication**: Required
**Permissions**: `read`

```http
GET /api/v1/metrics/zone/Z01?period=today
Authorization: Bearer <token>

Response 200:
{
  "zone_id": "Z01",
  "zone_name": "Assembly Station 1",
  "period": "today",
  "start_time": "2025-01-15T08:00:00Z",
  "end_time": "2025-01-15T10:50:00Z",
  "total_workers": 4,
  "unique_workers": 4,
  "total_sessions": 12,
  "total_active_seconds": 38400,
  "total_idle_seconds": 3600,
  "productivity": 0.914,
  "avg_session_duration": 3600,
  "peak_occupancy": 3,
  "hourly_breakdown": [
    {
      "hour": "08:00",
      "workers": 2,
      "active_seconds": 7200,
      "idle_seconds": 800,
      "productivity": 0.9
    },
    ...
  ]
}
```

#### `GET /api/v1/metrics/worker/{worker_id}`
**Description**: Worker-specific metrics
**Authentication**: Required
**Permissions**: `read`

```http
GET /api/v1/metrics/worker/W001?period=week
Authorization: Bearer <token>

Response 200:
{
  "worker_id": "W001",
  "worker_name": "สมชาย ใจดี",
  "period": "week",
  "start_date": "2025-01-09",
  "end_date": "2025-01-15",
  "total_days_worked": 5,
  "total_sessions": 55,
  "total_active_hours": 40,
  "total_idle_hours": 5,
  "productivity": 0.889,
  "zones_worked": ["Z01", "Z02"],
  "daily_breakdown": [
    {
      "date": "2025-01-15",
      "sessions": 11,
      "active_hours": 8,
      "idle_hours": 1,
      "productivity": 0.889
    },
    ...
  ]
}
```

---

### Anomalies & Alerts

#### `GET /api/v1/anomalies`
**Description**: List anomalies
**Authentication**: Required
**Permissions**: `read`

```http
GET /api/v1/anomalies?severity=high&resolved=false&limit=20
Authorization: Bearer <token>

Response 200:
{
  "total": 15,
  "anomalies": [
    {
      "anomaly_id": 123,
      "timestamp": "2025-01-15T10:15:00Z",
      "anomaly_type": "excessive_idle",
      "severity": "high",
      "zone_id": "Z02",
      "worker_id": "W005",
      "description": "Worker idle for 300 seconds",
      "root_cause": "Waiting for parts delivery",
      "resolved": false
    },
    ...
  ]
}
```

#### `GET /api/v1/alerts`
**Description**: List alerts
**Authentication**: Required
**Permissions**: `read`

```http
GET /api/v1/alerts?acknowledged=false&severity=critical
Authorization: Bearer <token>

Response 200:
{
  "total": 2,
  "alerts": [
    {
      "alert_id": 456,
      "timestamp": "2025-01-15T10:20:00Z",
      "alert_type": "zone_empty",
      "severity": "critical",
      "zone_id": "Z03",
      "message": "Critical zone Z03 has no workers for 5 minutes",
      "acknowledged": false
    },
    ...
  ]
}
```

#### `POST /api/v1/alerts/{alert_id}/acknowledge`
**Description**: Acknowledge alert
**Authentication**: Required
**Permissions**: `acknowledge_alerts`

```http
POST /api/v1/alerts/456/acknowledge
Authorization: Bearer <token>
Content-Type: application/json

{
  "acknowledged_by": "supervisor_001",
  "action_taken": "Dispatched worker to Zone Z03"
}

Response 200:
{
  "alert_id": 456,
  "acknowledged": true,
  "acknowledged_by": "supervisor_001",
  "acknowledged_at": "2025-01-15T10:25:00Z",
  "action_taken": "Dispatched worker to Zone Z03"
}
```

---

### RAG Query (Intelligent Analysis)

#### `POST /api/v1/query`
**Description**: Ask natural language questions
**Authentication**: Required
**Permissions**: `read`

```http
POST /api/v1/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "ทำไม zone Z01 วันนี้ทำงานช้ากว่าปกติ",
  "language": "th",
  "stream": false
}

Response 200:
{
  "query": "ทำไม zone Z01 วันนี้ทำงานช้ากว่าปกติ",
  "language": "th",
  "reasoning": "จากการวิเคราะห์ข้อมูล...\n1. เปรียบเทียบประสิทธิภาพวันนี้กับค่าเฉลี่ย\n2. ตรวจสอบ idle time และสาเหตุ\n3. ค้นหาเหตุการณ์ที่คล้ายกันในอดีต",
  "answer": "Zone Z01 วันนี้มีประสิทธิภาพ 85% ต่ำกว่าค่าเฉลี่ย (92%) เนื่องจาก:\n\n1. **Idle time สูงกว่าปกติ**: พนักงานรอชิ้นส่วนจากคลัง 3 ครั้ง (รวม 15 นาที)\n2. **พนักงานน้อยกว่าปกติ**: มีพนักงาน 1 คน (ปกติ 2 คน)\n3. **เหตุการณ์คล้ายกัน**: เกิดขึ้นเมื่อ 2025-01-10 ด้วยสาเหตุเดียวกัน\n\n**คำแนะนำ**:\n- เพิ่ม buffer stock ของชิ้นส่วนที่ใช้บ่อย\n- จัดพนักงานเพิ่มเติมเข้า Zone Z01",
  "sources": [
    {
      "type": "sql",
      "query": "zone_stats",
      "data": {...}
    },
    {
      "type": "vector",
      "collection": "anomaly_patterns",
      "score": 0.89,
      "payload": {...}
    }
  ],
  "query_time_ms": 2340
}
```

#### `POST /api/v1/query/stream`
**Description**: Streaming RAG query
**Authentication**: Required
**Permissions**: `read`

```http
POST /api/v1/query/stream
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "วิเคราะห์ประสิทธิภาพของพนักงาน W001",
  "language": "th"
}

Response 200 (Server-Sent Events):
data: {"type": "chunk", "content": "จากการ"}
data: {"type": "chunk", "content": "วิเคราะห์"}
data: {"type": "chunk", "content": "ข้อมูล"}
...
data: {"type": "final", "reasoning": "...", "answer": "...", "sources": [...]}
```

---

### Reports

#### `GET /api/v1/reports/daily`
**Description**: Generate daily report
**Authentication**: Required
**Permissions**: `view_reports`

```http
GET /api/v1/reports/daily?date=2025-01-15&format=json
Authorization: Bearer <token>

Response 200:
{
  "report_type": "daily",
  "date": "2025-01-15",
  "generated_at": "2025-01-15T17:00:00Z",
  "summary": {
    "total_indices": 11,
    "completed_indices": 11,
    "total_workers": 25,
    "total_active_hours": 200,
    "total_idle_hours": 25,
    "overall_productivity": 0.889,
    "anomalies_count": 12,
    "alerts_count": 8
  },
  "zones": [...],
  "top_performers": [...],
  "issues": [...]
}
```

#### `GET /api/v1/reports/daily/export`
**Description**: Export daily report
**Authentication**: Required
**Permissions**: `view_reports`

```http
GET /api/v1/reports/daily/export?date=2025-01-15&format=pdf
Authorization: Bearer <token>

Response 200:
Content-Type: application/pdf
Content-Disposition: attachment; filename="daily_report_2025-01-15.pdf"

[Binary PDF data]
```

---

## 🔌 WebSocket API

### Connection

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/tracking?token=<jwt_token>');

ws.onopen = () => {
  console.log('Connected to tracking WebSocket');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleUpdate(data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket disconnected');
};
```

---

### Message Types

#### 1. **Zone Update**
```json
{
  "type": "zone_update",
  "timestamp": "2025-01-15T10:30:00Z",
  "zone_id": "Z01",
  "data": {
    "workers_count": 2,
    "productivity": 0.92,
    "active_sessions": [
      {
        "session_id": "W001_Z01_20250115_083542",
        "worker_id": "W001",
        "state": "active",
        "duration": 4200
      }
    ]
  }
}
```

#### 2. **Alert**
```json
{
  "type": "alert",
  "timestamp": "2025-01-15T10:35:00Z",
  "alert": {
    "alert_id": 789,
    "alert_type": "idle_threshold",
    "severity": "warning",
    "zone_id": "Z02",
    "worker_id": "W005",
    "message": "Worker W005 idle for >60 seconds in Zone Z02"
  }
}
```

#### 3. **Index Transition**
```json
{
  "type": "index_transition",
  "timestamp": "2025-01-15T10:36:00Z",
  "old_index": 4,
  "new_index": 5,
  "data": {
    "scheduled_start": "2025-01-15T10:36:00Z",
    "scheduled_end": "2025-01-15T11:33:00Z",
    "indices_remaining": 7
  }
}
```

#### 4. **Session Update**
```json
{
  "type": "session_update",
  "timestamp": "2025-01-15T10:37:00Z",
  "event": "entry",
  "session": {
    "session_id": "W003_Z02_20250115_103700",
    "worker_id": "W003",
    "zone_id": "Z02",
    "entry_time": "2025-01-15T10:37:00Z",
    "state": "active"
  }
}
```

#### 5. **Metrics Update** (every 30 seconds)
```json
{
  "type": "metrics_update",
  "timestamp": "2025-01-15T10:40:00Z",
  "metrics": {
    "current_index": 5,
    "active_workers": 20,
    "overall_productivity": 0.9,
    "zones": [
      {
        "zone_id": "Z01",
        "workers_count": 2,
        "productivity": 0.92
      }
    ]
  }
}
```

---

## 🚨 Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Worker W999 not found",
    "details": {
      "worker_id": "W999"
    },
    "timestamp": "2025-01-15T10:45:00Z"
  }
}
```

### HTTP Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful GET/PUT/DELETE |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE with no response body |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | System maintenance or overload |

### Error Codes

| Code | Description |
|------|-------------|
| `AUTH_INVALID_TOKEN` | Invalid or expired token |
| `AUTH_INSUFFICIENT_PERMISSIONS` | User lacks required permissions |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `RESOURCE_ALREADY_EXISTS` | Resource with same ID already exists |
| `VALIDATION_ERROR` | Request validation failed |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `DATABASE_ERROR` | Database operation failed |
| `INFERENCE_ERROR` | LLM inference failed |
| `CAMERA_OFFLINE` | Camera is offline or unreachable |

---

## 📊 Rate Limiting

### Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/v1/*` | 100 requests | 1 minute |
| `/api/v1/query` | 20 requests | 1 minute |
| `/api/v1/metrics/*` | 200 requests | 1 minute |
| `/health` | Unlimited | - |

### Rate Limit Headers

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705310400
```

### Rate Limit Exceeded Response

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 30

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after 30 seconds.",
    "details": {
      "limit": 100,
      "window": "1 minute",
      "retry_after": 30
    }
  }
}
```

---

## 🔄 API Versioning

### Current Version: v1

All endpoints are prefixed with `/api/v1/`.

### Future Versions

When breaking changes are introduced:
- New version endpoint: `/api/v2/`
- v1 will be deprecated (12 months notice)
- Both versions will run concurrently during transition

---

## 📚 API Documentation

### Swagger UI

Available at: `http://localhost:8000/docs`

### ReDoc

Available at: `http://localhost:8000/redoc`

### OpenAPI Spec

Download: `http://localhost:8000/openapi.json`

---

## ✅ API Design Complete

### Summary
- ✅ **37+ REST Endpoints**: Workers, Zones, Cameras, Sessions, Metrics, Anomalies, Alerts, RAG Query, Reports
- ✅ **WebSocket Protocol**: Real-time updates (5 message types)
- ✅ **Authentication**: API Key + OAuth2/JWT + RBAC
- ✅ **Rate Limiting**: 100 req/min (configurable per endpoint)
- ✅ **Error Handling**: Standard error format with codes
- ✅ **Documentation**: Auto-generated Swagger UI
- ✅ **Versioning**: /api/v1/ (future-proof)

Next: UI/UX Design Documentation →
