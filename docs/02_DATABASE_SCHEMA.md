# Database Schema Design - PostgreSQL + TimescaleDB

## 🗄️ Overview

This system uses **PostgreSQL 15** with **TimescaleDB** extension for time-series data.

### Database Structure
- **Main Database**: `assembly_tracking`
- **Schema**: `public` (default)
- **TimescaleDB Extension**: Enabled for `time_logs` table
- **Encoding**: UTF-8 (supports Thai language)
- **Timezone**: Asia/Bangkok (UTC+7)

---

## 📊 Entity Relationship Diagram

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   workers    │         │    zones     │         │   cameras    │
│──────────────│         │──────────────│         │──────────────│
│ worker_id PK │         │ zone_id PK   │         │ camera_id PK │
│ name         │         │ camera_id FK │─────────│ name         │
│ badge_id     │         │ name         │         │ rtsp_url     │
│ face_embed   │         │ polygon      │         │ location     │
└──────┬───────┘         └──────┬───────┘         └──────────────┘
       │                        │
       │    ┌───────────────────┴───────────────────┐
       │    │                                       │
       ▼    ▼                                       ▼
┌──────────────────────┐                  ┌──────────────────┐
│    sessions          │                  │    time_logs     │
│──────────────────────│                  │──────────────────│
│ session_id PK        │                  │ log_id PK        │
│ worker_id FK         │                  │ timestamp        │
│ zone_id FK           │                  │ worker_id FK     │
│ track_id             │                  │ track_id         │
│ entry_time           │                  │ zone_id FK       │
│ exit_time            │                  │ camera_id FK     │
│ total_active_seconds │◄─────────────────│ state            │
│ total_idle_seconds   │                  │ active_duration  │
│ index_number         │                  │ idle_duration    │
└──────────────────────┘                  └──────────────────┘
       │                                           │
       └───────────────┬───────────────────────────┘
                       │
                       ▼
            ┌──────────────────┐
            │  index_records   │
            │──────────────────│
            │ index_id PK      │
            │ date             │
            │ index_number     │
            │ scheduled_start  │
            │ scheduled_end    │
            │ actual_start     │
            │ actual_end       │
            │ zone_metrics     │
            └──────────────────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│    anomalies     │        │      alerts      │
│──────────────────│        │──────────────────│
│ anomaly_id PK    │        │ alert_id PK      │
│ timestamp        │        │ timestamp        │
│ anomaly_type     │        │ alert_type       │
│ severity         │        │ severity         │
│ zone_id FK       │        │ zone_id FK       │
│ worker_id FK     │        │ worker_id FK     │
│ description      │        │ message          │
│ root_cause       │        │ acknowledged     │
│ resolution       │        │ acknowledged_by  │
└──────────────────┘        └──────────────────┘

┌──────────────────┐        ┌──────────────────┐
│    schedules     │        │  zone_templates  │
│──────────────────│        │──────────────────│
│ schedule_id PK   │        │ template_id PK   │
│ date             │        │ name             │
│ work_start_time  │        │ template_data    │
│ work_end_time    │        │ created_by       │
│ break1_start     │        │ created_at       │
│ break1_duration  │        └──────────────────┘
│ break2_start     │
│ break2_duration  │        ┌──────────────────┐
│ index_timeline   │        │  system_logs     │
│ active           │        │──────────────────│
└──────────────────┘        │ log_id PK        │
                            │ timestamp        │
                            │ level            │
                            │ component        │
                            │ message          │
                            │ stack_trace      │
                            └──────────────────┘
```

---

## 📋 Table Definitions

### 1. `workers` - Worker Registry

```sql
CREATE TABLE workers (
    worker_id VARCHAR(50) PRIMARY KEY,          -- Unique ID (e.g., "W001", "A023")
    name VARCHAR(255) NOT NULL,                 -- Full name (Thai/English)
    badge_id VARCHAR(50) UNIQUE,                -- Physical badge ID
    face_embedding BYTEA,                       -- Face recognition vector (encrypted)
    shift VARCHAR(20),                          -- "morning", "afternoon", "night"
    skill_level VARCHAR(50),                    -- "beginner", "intermediate", "expert"
    station_assignments JSONB,                  -- {"preferred": ["Z01"], "certified": ["Z01", "Z02"]}
    active BOOLEAN DEFAULT TRUE,                -- Currently active employee
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_workers_badge ON workers(badge_id);
CREATE INDEX idx_workers_shift ON workers(shift);
CREATE INDEX idx_workers_active ON workers(active);

-- Sample data
-- worker_id: "W001", "W002", "A023"
-- name: "สมชาย ใจดี", "John Smith"
-- badge_id: "BADGE-001", "BADGE-023"
-- face_embedding: Encrypted 512-dim vector from FaceNet/ArcFace
-- shift: "morning", "afternoon", "night"
-- skill_level: "beginner", "intermediate", "expert"
-- station_assignments: {"preferred": ["Z01"], "certified": ["Z01", "Z02", "Z03"]}
```

---

### 2. `cameras` - Camera Configuration

```sql
CREATE TABLE cameras (
    camera_id VARCHAR(50) PRIMARY KEY,          -- Unique ID (e.g., "CAM01", "CAM02")
    name VARCHAR(255) NOT NULL,                 -- Friendly name (e.g., "Station 1 Overhead")
    rtsp_url TEXT,                              -- RTSP stream URL (encrypted)
    usb_device VARCHAR(50),                     -- USB device path (e.g., "/dev/video0")
    location VARCHAR(255),                      -- Physical location (e.g., "Assembly Line A - North")
    status VARCHAR(20) DEFAULT 'active',        -- "active", "inactive", "error"
    calibration_params JSONB,                   -- Camera calibration data
    resolution VARCHAR(20) DEFAULT '1920x1080', -- Video resolution
    fps INTEGER DEFAULT 30,                     -- Frames per second
    last_seen_at TIMESTAMP WITH TIME ZONE,      -- Last successful frame capture
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_cameras_status ON cameras(status);
CREATE INDEX idx_cameras_last_seen ON cameras(last_seen_at);

-- Sample data
-- camera_id: "CAM01", "CAM02", "CAM03", "CAM04"
-- name: "Station 1 Overhead", "Station 2 Side View"
-- rtsp_url: "rtsp://192.168.1.100:554/stream1"
-- usb_device: "/dev/video0" (for USB cameras)
-- location: "Assembly Line A - North Corner"
-- status: "active", "inactive", "error"
-- calibration_params: {"fx": 1000, "fy": 1000, "cx": 960, "cy": 540, "distortion": []}
```

---

### 3. `zones` - Work Zone Definitions

```sql
CREATE TABLE zones (
    zone_id VARCHAR(50) PRIMARY KEY,            -- Unique ID (e.g., "Z01", "STATION_01")
    camera_id VARCHAR(50) NOT NULL,             -- Camera this zone belongs to
    name VARCHAR(255) NOT NULL,                 -- Zone name (e.g., "Assembly Station 1")
    polygon_coords JSONB NOT NULL,              -- Array of [x, y] points
    zone_type VARCHAR(50) DEFAULT 'work_area',  -- "work_area", "inspection", "break_area"
    color VARCHAR(20) DEFAULT '#00FF00',        -- Hex color for visualization
    min_workers INTEGER DEFAULT 1,              -- Minimum workers required
    max_workers INTEGER DEFAULT 3,              -- Maximum workers allowed
    alert_on_empty BOOLEAN DEFAULT FALSE,       -- Alert if no workers present
    alert_on_overflow BOOLEAN DEFAULT TRUE,     -- Alert if too many workers
    active BOOLEAN DEFAULT TRUE,                -- Zone is currently active
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_camera FOREIGN KEY (camera_id) REFERENCES cameras(camera_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_zones_camera ON zones(camera_id);
CREATE INDEX idx_zones_type ON zones(zone_type);
CREATE INDEX idx_zones_active ON zones(active);

-- Sample data
-- zone_id: "Z01", "Z02", "STATION_01", "INSPECTION_A"
-- camera_id: "CAM01"
-- name: "Assembly Station 1", "Inspection Area A"
-- polygon_coords: [[100, 200], [500, 200], [500, 800], [100, 800]]
-- zone_type: "work_area", "inspection", "break_area", "restricted"
-- color: "#00FF00", "#FF0000", "#0000FF"
-- min_workers: 1, max_workers: 3
```

---

### 4. `time_logs` - Real-time Time Tracking (TimescaleDB Hypertable)

```sql
CREATE TABLE time_logs (
    log_id BIGSERIAL,                           -- Auto-increment ID
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,-- Log timestamp (indexed for TimescaleDB)
    worker_id VARCHAR(50),                      -- Worker ID (nullable if unidentified)
    track_id INTEGER NOT NULL,                  -- Tracking ID from DeepSORT
    zone_id VARCHAR(50),                        -- Current zone (nullable if outside zones)
    camera_id VARCHAR(50) NOT NULL,             -- Source camera
    state VARCHAR(20) NOT NULL,                 -- "active", "idle", "unknown"
    active_duration_seconds INTEGER DEFAULT 0,  -- Seconds spent in active state
    idle_duration_seconds INTEGER DEFAULT 0,    -- Seconds spent in idle state
    index_number INTEGER,                       -- Current index (1-11)
    motion_score FLOAT,                         -- Motion intensity (0.0-1.0)
    bbox_coords JSONB,                          -- Bounding box [x, y, w, h]
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_worker FOREIGN KEY (worker_id) REFERENCES workers(worker_id) ON DELETE SET NULL,
    CONSTRAINT fk_zone FOREIGN KEY (zone_id) REFERENCES zones(zone_id) ON DELETE SET NULL,
    CONSTRAINT fk_camera FOREIGN KEY (camera_id) REFERENCES cameras(camera_id) ON DELETE CASCADE
);

-- Convert to TimescaleDB hypertable (CRITICAL for performance)
SELECT create_hypertable('time_logs', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Indexes (TimescaleDB optimized)
CREATE INDEX idx_time_logs_worker_time ON time_logs(worker_id, timestamp DESC);
CREATE INDEX idx_time_logs_zone_time ON time_logs(zone_id, timestamp DESC);
CREATE INDEX idx_time_logs_track ON time_logs(track_id, timestamp DESC);
CREATE INDEX idx_time_logs_index ON time_logs(index_number, timestamp DESC);
CREATE INDEX idx_time_logs_state ON time_logs(state);

-- Data retention policy (auto-delete after 90 days)
SELECT add_retention_policy('time_logs', INTERVAL '90 days');

-- Sample data
-- timestamp: 2025-01-15 08:35:42+07
-- worker_id: "W001" (or NULL if unidentified)
-- track_id: 1, 2, 3 (from tracker)
-- zone_id: "Z01" (or NULL if outside zones)
-- camera_id: "CAM01"
-- state: "active", "idle", "unknown"
-- active_duration_seconds: 120
-- idle_duration_seconds: 30
-- index_number: 3 (current index)
-- motion_score: 0.85 (high motion)
-- bbox_coords: {"x": 100, "y": 200, "w": 80, "h": 180}
```

---

### 5. `sessions` - Work Sessions (Entry to Exit)

```sql
CREATE TABLE sessions (
    session_id VARCHAR(100) PRIMARY KEY,        -- Unique session ID (UUID or composite)
    worker_id VARCHAR(50),                      -- Worker ID (nullable)
    zone_id VARCHAR(50) NOT NULL,               -- Zone where session occurred
    track_id INTEGER NOT NULL,                  -- Tracking ID
    entry_time TIMESTAMP WITH TIME ZONE NOT NULL, -- When entered zone
    exit_time TIMESTAMP WITH TIME ZONE,         -- When exited zone (NULL if active)
    total_active_seconds INTEGER DEFAULT 0,     -- Total active time in this session
    total_idle_seconds INTEGER DEFAULT 0,       -- Total idle time in this session
    index_number INTEGER NOT NULL,              -- Index during this session (1-11)
    status VARCHAR(20) DEFAULT 'active',        -- "active", "completed", "interrupted"
    entry_snapshot TEXT,                        -- Base64 image of person at entry
    exit_snapshot TEXT,                         -- Base64 image at exit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_session_worker FOREIGN KEY (worker_id) REFERENCES workers(worker_id) ON DELETE SET NULL,
    CONSTRAINT fk_session_zone FOREIGN KEY (zone_id) REFERENCES zones(zone_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_sessions_worker_index ON sessions(worker_id, index_number);
CREATE INDEX idx_sessions_zone_time ON sessions(zone_id, entry_time DESC);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_entry_time ON sessions(entry_time DESC);

-- Sample data
-- session_id: "W001_Z01_20250115_083542" or UUID
-- worker_id: "W001"
-- zone_id: "Z01"
-- track_id: 1
-- entry_time: 2025-01-15 08:35:42+07
-- exit_time: 2025-01-15 09:20:15+07 (or NULL if still active)
-- total_active_seconds: 2400 (40 minutes)
-- total_idle_seconds: 273 (4.5 minutes)
-- index_number: 3
-- status: "active", "completed", "interrupted"
```

---

### 6. `index_records` - Index Performance Tracking

```sql
CREATE TABLE index_records (
    index_id SERIAL PRIMARY KEY,                -- Auto-increment ID
    date DATE NOT NULL,                         -- Date of the index
    index_number INTEGER NOT NULL,              -- Index number (1-11)
    scheduled_start TIMESTAMP WITH TIME ZONE NOT NULL,   -- Planned start time
    scheduled_end TIMESTAMP WITH TIME ZONE NOT NULL,     -- Planned end time
    actual_start TIMESTAMP WITH TIME ZONE,      -- Actual start time (first activity)
    actual_end TIMESTAMP WITH TIME ZONE,        -- Actual end time
    zone_metrics JSONB,                         -- Per-zone statistics
    completion_status VARCHAR(50),              -- "on_time", "delayed", "incomplete"
    total_workers INTEGER,                      -- Number of workers during index
    total_active_seconds INTEGER,               -- Sum of all active time
    total_idle_seconds INTEGER,                 -- Sum of all idle time
    productivity_score FLOAT,                   -- active / (active + idle)
    anomalies_count INTEGER DEFAULT 0,          -- Number of anomalies detected
    notes TEXT,                                 -- Manual notes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_date_index UNIQUE (date, index_number)
);

-- Indexes
CREATE INDEX idx_index_records_date ON index_records(date DESC);
CREATE INDEX idx_index_records_index_number ON index_records(index_number);
CREATE INDEX idx_index_records_productivity ON index_records(productivity_score);

-- Sample data
-- date: 2025-01-15
-- index_number: 3
-- scheduled_start: 2025-01-15 09:54:00+07
-- scheduled_end: 2025-01-15 10:36:00+07
-- actual_start: 2025-01-15 09:55:30+07
-- actual_end: 2025-01-15 10:38:20+07
-- zone_metrics: {"Z01": {"workers": 2, "active": 2400, "idle": 240}, "Z02": {...}}
-- completion_status: "on_time", "delayed", "incomplete"
-- total_workers: 8
-- total_active_seconds: 19200
-- total_idle_seconds: 2400
-- productivity_score: 0.889 (88.9%)
-- anomalies_count: 2
```

---

### 7. `anomalies` - Anomaly Detection Log

```sql
CREATE TABLE anomalies (
    anomaly_id SERIAL PRIMARY KEY,              -- Auto-increment ID
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,-- When anomaly occurred
    anomaly_type VARCHAR(100) NOT NULL,         -- Type of anomaly
    severity VARCHAR(20) NOT NULL,              -- "low", "medium", "high", "critical"
    zone_id VARCHAR(50),                        -- Affected zone (nullable)
    worker_id VARCHAR(50),                      -- Affected worker (nullable)
    camera_id VARCHAR(50),                      -- Source camera
    index_number INTEGER,                       -- Index when detected
    description TEXT,                           -- Human-readable description
    root_cause TEXT,                            -- Identified root cause (from RAG)
    resolution TEXT,                            -- How it was resolved
    auto_detected BOOLEAN DEFAULT TRUE,         -- System detected vs manual
    resolved BOOLEAN DEFAULT FALSE,             -- Has been resolved
    resolved_at TIMESTAMP WITH TIME ZONE,       -- When resolved
    resolved_by VARCHAR(50),                    -- Who resolved it
    metadata JSONB,                             -- Additional data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_anomaly_zone FOREIGN KEY (zone_id) REFERENCES zones(zone_id) ON DELETE SET NULL,
    CONSTRAINT fk_anomaly_worker FOREIGN KEY (worker_id) REFERENCES workers(worker_id) ON DELETE SET NULL,
    CONSTRAINT fk_anomaly_camera FOREIGN KEY (camera_id) REFERENCES cameras(camera_id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_anomalies_timestamp ON anomalies(timestamp DESC);
CREATE INDEX idx_anomalies_type ON anomalies(anomaly_type);
CREATE INDEX idx_anomalies_severity ON anomalies(severity);
CREATE INDEX idx_anomalies_resolved ON anomalies(resolved);
CREATE INDEX idx_anomalies_zone_time ON anomalies(zone_id, timestamp DESC);

-- Sample data
-- anomaly_type: "excessive_idle", "zone_violation", "no_workers", "sequence_deviation"
-- severity: "low", "medium", "high", "critical"
-- zone_id: "Z01"
-- worker_id: "W001"
-- camera_id: "CAM01"
-- index_number: 3
-- description: "Worker W001 idle for 300 seconds in Zone Z01"
-- root_cause: "Waiting for parts delivery (from RAG analysis)"
-- resolution: "Parts delivered, worker resumed"
-- resolved: TRUE
-- resolved_at: 2025-01-15 10:15:00+07
-- resolved_by: "supervisor_001"
-- metadata: {"idle_duration": 300, "threshold": 180}
```

---

### 8. `alerts` - Real-time Alert System

```sql
CREATE TABLE alerts (
    alert_id SERIAL PRIMARY KEY,                -- Auto-increment ID
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,-- When alert triggered
    alert_type VARCHAR(100) NOT NULL,           -- Type of alert
    severity VARCHAR(20) NOT NULL,              -- "info", "warning", "error", "critical"
    zone_id VARCHAR(50),                        -- Related zone (nullable)
    worker_id VARCHAR(50),                      -- Related worker (nullable)
    camera_id VARCHAR(50),                      -- Source camera
    message TEXT NOT NULL,                      -- Alert message
    acknowledged BOOLEAN DEFAULT FALSE,         -- Has been acknowledged
    acknowledged_by VARCHAR(50),                -- Who acknowledged
    acknowledged_at TIMESTAMP WITH TIME ZONE,   -- When acknowledged
    action_taken TEXT,                          -- Action taken by user
    auto_resolved BOOLEAN DEFAULT FALSE,        -- System auto-resolved
    metadata JSONB,                             -- Additional data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_alert_zone FOREIGN KEY (zone_id) REFERENCES zones(zone_id) ON DELETE SET NULL,
    CONSTRAINT fk_alert_worker FOREIGN KEY (worker_id) REFERENCES workers(worker_id) ON DELETE SET NULL,
    CONSTRAINT fk_alert_camera FOREIGN KEY (camera_id) REFERENCES cameras(camera_id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp DESC);
CREATE INDEX idx_alerts_type ON alerts(alert_type);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_acknowledged ON alerts(acknowledged);
CREATE INDEX idx_alerts_zone ON alerts(zone_id);

-- Sample data
-- alert_type: "idle_threshold", "zone_empty", "zone_overflow", "productivity_drop"
-- severity: "info", "warning", "error", "critical"
-- zone_id: "Z01"
-- worker_id: "W001"
-- camera_id: "CAM01"
-- message: "Zone Z01: Worker W001 idle for >60 seconds"
-- acknowledged: TRUE
-- acknowledged_by: "supervisor_001"
-- acknowledged_at: 2025-01-15 10:10:00+07
-- action_taken: "Supervisor investigated - worker waiting for parts"
-- auto_resolved: FALSE
-- metadata: {"threshold": 60, "actual": 75}
```

---

### 9. `schedules` - Work Schedule Configuration

```sql
CREATE TABLE schedules (
    schedule_id SERIAL PRIMARY KEY,             -- Auto-increment ID
    date DATE NOT NULL UNIQUE,                  -- Schedule date
    work_start_time TIME NOT NULL,              -- Work start (e.g., 08:00)
    work_end_time TIME NOT NULL,                -- Work end (e.g., 17:00)
    break1_start TIME,                          -- First break start (e.g., 10:00)
    break1_duration INTEGER,                    -- First break duration (minutes)
    break2_start TIME,                          -- Second break start (e.g., 15:00)
    break2_duration INTEGER,                    -- Second break duration (minutes)
    index_timeline JSONB NOT NULL,              -- Pre-calculated index timeline
    total_indices INTEGER DEFAULT 11,           -- Number of indices (default 11)
    active BOOLEAN DEFAULT TRUE,                -- Schedule is active
    notes TEXT,                                 -- Manual notes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_schedules_date ON schedules(date DESC);
CREATE INDEX idx_schedules_active ON schedules(active);

-- Sample data
-- date: 2025-01-15
-- work_start_time: 08:00
-- work_end_time: 17:00
-- break1_start: 10:00
-- break1_duration: 15 (minutes)
-- break2_start: 15:00
-- break2_duration: 15 (minutes)
-- index_timeline: [
--   {"index": 1, "start": "08:00", "end": "08:57"},
--   {"index": 2, "start": "08:57", "end": "09:54"},
--   {"index": 3, "start": "09:54", "end": "10:00", "break": "10:00-10:15", "resume": "10:15", "end_after_break": "10:36"},
--   ...
--   {"index": 11, "start": "16:03", "end": "17:00"}
-- ]
-- total_indices: 11
-- active: TRUE
```

---

### 10. `system_logs` - Application Logging

```sql
CREATE TABLE system_logs (
    log_id BIGSERIAL PRIMARY KEY,               -- Auto-increment ID
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20) NOT NULL,                 -- "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    component VARCHAR(100) NOT NULL,            -- Component name (e.g., "camera_manager")
    message TEXT NOT NULL,                      -- Log message
    stack_trace TEXT,                           -- Error stack trace (if error)
    user_id VARCHAR(50),                        -- User who triggered (if applicable)
    metadata JSONB,                             -- Additional context
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_system_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX idx_system_logs_level ON system_logs(level);
CREATE INDEX idx_system_logs_component ON system_logs(component);

-- Data retention policy (auto-delete after 30 days)
-- NOTE: Implement via cron job or pg_cron extension
-- SELECT delete_old_logs(); -- Runs daily at midnight

-- Sample data
-- level: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
-- component: "camera_manager", "yolo_detector", "rag_engine", "db_writer"
-- message: "Camera CAM01 reconnected successfully"
-- stack_trace: NULL (or full Python traceback if error)
-- metadata: {"camera_id": "CAM01", "retry_count": 3}
```

---

### 11. `zone_templates` - Reusable Zone Configurations

```sql
CREATE TABLE zone_templates (
    template_id SERIAL PRIMARY KEY,             -- Auto-increment ID
    name VARCHAR(255) NOT NULL UNIQUE,          -- Template name
    description TEXT,                           -- Template description
    template_data JSONB NOT NULL,               -- Complete zone configuration
    camera_type VARCHAR(50),                    -- "overhead", "side_view", "front_view"
    created_by VARCHAR(50),                     -- User who created
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_zone_templates_name ON zone_templates(name);
CREATE INDEX idx_zone_templates_camera_type ON zone_templates(camera_type);

-- Sample data
-- name: "Assembly Line A - 4 Zones", "Inspection Area - 2 Zones"
-- description: "Standard 4-zone layout for assembly line with overhead camera"
-- template_data: [
--   {
--     "zone_name": "Station 1",
--     "polygon": [[100, 200], [500, 200], [500, 800], [100, 800]],
--     "color": "#00FF00",
--     "zone_type": "work_area",
--     "min_workers": 1,
--     "max_workers": 2
--   },
--   {...}
-- ]
-- camera_type: "overhead", "side_view", "front_view"
-- created_by: "admin_001"
```

---

## 🔐 Database Security

### 1. Row-Level Security (RLS)

```sql
-- Enable RLS on sensitive tables
ALTER TABLE workers ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see workers in their shift
CREATE POLICY workers_shift_policy ON workers
    FOR SELECT
    USING (shift = current_setting('app.current_shift', true));

-- Policy: Only admins can modify workers
CREATE POLICY workers_admin_policy ON workers
    FOR ALL
    USING (current_setting('app.user_role', true) = 'admin');
```

### 2. Encryption

```sql
-- Enable pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt sensitive data (e.g., face embeddings, RTSP URLs)
-- Example: Encrypting face_embedding
UPDATE workers
SET face_embedding = pgp_sym_encrypt(face_embedding, 'encryption_key');

-- Decrypt when needed
SELECT pgp_sym_decrypt(face_embedding, 'encryption_key') FROM workers;
```

### 3. Audit Logging

```sql
-- Create audit log table
CREATE TABLE audit_logs (
    audit_id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,             -- "INSERT", "UPDATE", "DELETE"
    old_data JSONB,
    new_data JSONB,
    user_id VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trigger function for audit logging
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_logs (table_name, operation, old_data, user_id)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), current_setting('app.user_id', true));
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_logs (table_name, operation, old_data, new_data, user_id)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), row_to_json(NEW), current_setting('app.user_id', true));
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_logs (table_name, operation, new_data, user_id)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(NEW), current_setting('app.user_id', true));
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to sensitive tables
CREATE TRIGGER workers_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON workers
FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
```

---

## 📈 Performance Optimization

### 1. Connection Pooling

```python
# Application-level connection pooling (PgBouncer or SQLAlchemy)
DATABASE_URL = "postgresql://user:pass@localhost:5432/assembly_tracking"
engine = create_engine(
    DATABASE_URL,
    pool_size=10,           # Max 10 connections
    max_overflow=5,         # Allow 5 extra connections
    pool_pre_ping=True,     # Test connections before use
    pool_recycle=3600       # Recycle after 1 hour
)
```

### 2. Materialized Views (for analytics)

```sql
-- Pre-computed daily statistics
CREATE MATERIALIZED VIEW daily_zone_stats AS
SELECT
    date_trunc('day', timestamp) AS day,
    zone_id,
    COUNT(DISTINCT worker_id) AS unique_workers,
    SUM(active_duration_seconds) AS total_active_seconds,
    SUM(idle_duration_seconds) AS total_idle_seconds,
    AVG(motion_score) AS avg_motion_score
FROM time_logs
GROUP BY date_trunc('day', timestamp), zone_id;

-- Create index on materialized view
CREATE INDEX idx_daily_zone_stats_day ON daily_zone_stats(day DESC);

-- Refresh daily at midnight (via cron job or pg_cron)
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_zone_stats;
```

### 3. Partitioning (Future scaling)

```sql
-- Partition time_logs by month (if data grows beyond 100M rows)
-- Already handled by TimescaleDB hypertable (chunks by day)

-- For sessions table (if needed)
CREATE TABLE sessions_2025_01 PARTITION OF sessions
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE sessions_2025_02 PARTITION OF sessions
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
```

---

## 🔄 Database Maintenance

### 1. Vacuum & Analyze (Automated)

```sql
-- Enable auto-vacuum (default in PostgreSQL 15)
ALTER TABLE time_logs SET (autovacuum_enabled = true);

-- Manual vacuum (if needed)
VACUUM ANALYZE time_logs;
```

### 2. Backup Strategy

```bash
# Full backup (daily at 2 AM via cron)
pg_dump -U postgres -F c assembly_tracking > /backups/assembly_tracking_$(date +%Y%m%d).dump

# Restore from backup
pg_restore -U postgres -d assembly_tracking /backups/assembly_tracking_20250115.dump

# Point-in-time recovery (PITR)
# Requires WAL archiving enabled in postgresql.conf
archive_mode = on
archive_command = 'cp %p /archive/%f'
```

### 3. Monitoring Queries

```sql
-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check slow queries (enable pg_stat_statements extension)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

SELECT
    mean_exec_time,
    calls,
    query
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check active connections
SELECT
    datname,
    usename,
    application_name,
    state,
    query
FROM pg_stat_activity
WHERE state = 'active';
```

---

## ✅ Database Schema Design Complete

### Summary
- ✅ **11 Core Tables**: workers, cameras, zones, time_logs, sessions, index_records, anomalies, alerts, schedules, zone_templates, system_logs
- ✅ **TimescaleDB**: Optimized for time-series data (time_logs)
- ✅ **Indexes**: Strategic indexes for fast queries
- ✅ **Security**: RLS, encryption, audit logging
- ✅ **Performance**: Connection pooling, materialized views, partitioning
- ✅ **Maintenance**: Backup, vacuum, monitoring

Next: Qdrant Vector Database Design →
