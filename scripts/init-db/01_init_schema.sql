-- Assembly Time-Tracking System
-- Database Initialization Script
-- PostgreSQL + TimescaleDB

-- ==========================================
-- Enable Extensions
-- ==========================================
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ==========================================
-- Table: workers
-- ==========================================
CREATE TABLE IF NOT EXISTS workers (
    worker_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    badge_id VARCHAR(50) UNIQUE,
    face_embedding BYTEA,
    shift VARCHAR(20),
    skill_level VARCHAR(50),
    station_assignments JSONB,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workers_badge ON workers(badge_id);
CREATE INDEX idx_workers_shift ON workers(shift);
CREATE INDEX idx_workers_active ON workers(active);

-- ==========================================
-- Table: cameras
-- ==========================================
CREATE TABLE IF NOT EXISTS cameras (
    camera_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    rtsp_url TEXT,
    usb_device VARCHAR(50),
    location VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    calibration_params JSONB,
    resolution VARCHAR(20) DEFAULT '1920x1080',
    fps INTEGER DEFAULT 30,
    last_seen_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cameras_status ON cameras(status);
CREATE INDEX idx_cameras_last_seen ON cameras(last_seen_at);

-- ==========================================
-- Table: zones
-- ==========================================
CREATE TABLE IF NOT EXISTS zones (
    zone_id VARCHAR(50) PRIMARY KEY,
    camera_id VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    polygon_coords JSONB NOT NULL,
    zone_type VARCHAR(50) DEFAULT 'work_area',
    color VARCHAR(20) DEFAULT '#00FF00',
    min_workers INTEGER DEFAULT 1,
    max_workers INTEGER DEFAULT 3,
    alert_on_empty BOOLEAN DEFAULT FALSE,
    alert_on_overflow BOOLEAN DEFAULT TRUE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_camera FOREIGN KEY (camera_id)
        REFERENCES cameras(camera_id) ON DELETE CASCADE
);

CREATE INDEX idx_zones_camera ON zones(camera_id);
CREATE INDEX idx_zones_type ON zones(zone_type);
CREATE INDEX idx_zones_active ON zones(active);

-- ==========================================
-- Table: time_logs (TimescaleDB Hypertable)
-- ==========================================
CREATE TABLE IF NOT EXISTS time_logs (
    log_id BIGSERIAL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    worker_id VARCHAR(50),
    track_id INTEGER NOT NULL,
    zone_id VARCHAR(50),
    camera_id VARCHAR(50) NOT NULL,
    state VARCHAR(20) NOT NULL,
    active_duration_seconds INTEGER DEFAULT 0,
    idle_duration_seconds INTEGER DEFAULT 0,
    index_number INTEGER,
    motion_score FLOAT,
    bbox_coords JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_worker FOREIGN KEY (worker_id)
        REFERENCES workers(worker_id) ON DELETE SET NULL,
    CONSTRAINT fk_zone FOREIGN KEY (zone_id)
        REFERENCES zones(zone_id) ON DELETE SET NULL,
    CONSTRAINT fk_camera_log FOREIGN KEY (camera_id)
        REFERENCES cameras(camera_id) ON DELETE CASCADE
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('time_logs', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Indexes for time_logs
CREATE INDEX IF NOT EXISTS idx_time_logs_worker_time
    ON time_logs(worker_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_time_logs_zone_time
    ON time_logs(zone_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_time_logs_track
    ON time_logs(track_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_time_logs_index
    ON time_logs(index_number, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_time_logs_state
    ON time_logs(state);

-- Data retention policy (keep 90 days)
SELECT add_retention_policy('time_logs', INTERVAL '90 days', if_not_exists => TRUE);

-- ==========================================
-- Table: sessions
-- ==========================================
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    worker_id VARCHAR(50),
    zone_id VARCHAR(50) NOT NULL,
    track_id INTEGER NOT NULL,
    entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
    exit_time TIMESTAMP WITH TIME ZONE,
    total_active_seconds INTEGER DEFAULT 0,
    total_idle_seconds INTEGER DEFAULT 0,
    index_number INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    entry_snapshot TEXT,
    exit_snapshot TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_session_worker FOREIGN KEY (worker_id)
        REFERENCES workers(worker_id) ON DELETE SET NULL,
    CONSTRAINT fk_session_zone FOREIGN KEY (zone_id)
        REFERENCES zones(zone_id) ON DELETE CASCADE
);

CREATE INDEX idx_sessions_worker_index ON sessions(worker_id, index_number);
CREATE INDEX idx_sessions_zone_time ON sessions(zone_id, entry_time DESC);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_entry_time ON sessions(entry_time DESC);

-- ==========================================
-- Table: index_records
-- ==========================================
CREATE TABLE IF NOT EXISTS index_records (
    index_id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    index_number INTEGER NOT NULL,
    scheduled_start TIMESTAMP WITH TIME ZONE NOT NULL,
    scheduled_end TIMESTAMP WITH TIME ZONE NOT NULL,
    actual_start TIMESTAMP WITH TIME ZONE,
    actual_end TIMESTAMP WITH TIME ZONE,
    zone_metrics JSONB,
    completion_status VARCHAR(50),
    total_workers INTEGER,
    total_active_seconds INTEGER,
    total_idle_seconds INTEGER,
    productivity_score FLOAT,
    anomalies_count INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_date_index UNIQUE (date, index_number)
);

CREATE INDEX idx_index_records_date ON index_records(date DESC);
CREATE INDEX idx_index_records_index_number ON index_records(index_number);
CREATE INDEX idx_index_records_productivity ON index_records(productivity_score);

-- ==========================================
-- Table: anomalies
-- ==========================================
CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    anomaly_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    zone_id VARCHAR(50),
    worker_id VARCHAR(50),
    camera_id VARCHAR(50),
    index_number INTEGER,
    description TEXT,
    root_cause TEXT,
    resolution TEXT,
    auto_detected BOOLEAN DEFAULT TRUE,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_anomaly_zone FOREIGN KEY (zone_id)
        REFERENCES zones(zone_id) ON DELETE SET NULL,
    CONSTRAINT fk_anomaly_worker FOREIGN KEY (worker_id)
        REFERENCES workers(worker_id) ON DELETE SET NULL,
    CONSTRAINT fk_anomaly_camera FOREIGN KEY (camera_id)
        REFERENCES cameras(camera_id) ON DELETE SET NULL
);

CREATE INDEX idx_anomalies_timestamp ON anomalies(timestamp DESC);
CREATE INDEX idx_anomalies_type ON anomalies(anomaly_type);
CREATE INDEX idx_anomalies_severity ON anomalies(severity);
CREATE INDEX idx_anomalies_resolved ON anomalies(resolved);
CREATE INDEX idx_anomalies_zone_time ON anomalies(zone_id, timestamp DESC);

-- ==========================================
-- Table: alerts
-- ==========================================
CREATE TABLE IF NOT EXISTS alerts (
    alert_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    zone_id VARCHAR(50),
    worker_id VARCHAR(50),
    camera_id VARCHAR(50),
    message TEXT NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(50),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    action_taken TEXT,
    auto_resolved BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_alert_zone FOREIGN KEY (zone_id)
        REFERENCES zones(zone_id) ON DELETE SET NULL,
    CONSTRAINT fk_alert_worker FOREIGN KEY (worker_id)
        REFERENCES workers(worker_id) ON DELETE SET NULL,
    CONSTRAINT fk_alert_camera FOREIGN KEY (camera_id)
        REFERENCES cameras(camera_id) ON DELETE SET NULL
);

CREATE INDEX idx_alerts_timestamp ON alerts(timestamp DESC);
CREATE INDEX idx_alerts_type ON alerts(alert_type);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_acknowledged ON alerts(acknowledged);
CREATE INDEX idx_alerts_zone ON alerts(zone_id);

-- ==========================================
-- Table: schedules
-- ==========================================
CREATE TABLE IF NOT EXISTS schedules (
    schedule_id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    work_start_time TIME NOT NULL,
    work_end_time TIME NOT NULL,
    break1_start TIME,
    break1_duration INTEGER,
    break2_start TIME,
    break2_duration INTEGER,
    index_timeline JSONB NOT NULL,
    total_indices INTEGER DEFAULT 11,
    active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_schedules_date ON schedules(date DESC);
CREATE INDEX idx_schedules_active ON schedules(active);

-- ==========================================
-- Table: zone_templates
-- ==========================================
CREATE TABLE IF NOT EXISTS zone_templates (
    template_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    template_data JSONB NOT NULL,
    camera_type VARCHAR(50),
    created_by VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_zone_templates_name ON zone_templates(name);
CREATE INDEX idx_zone_templates_camera_type ON zone_templates(camera_type);

-- ==========================================
-- Table: system_logs
-- ==========================================
CREATE TABLE IF NOT EXISTS system_logs (
    log_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20) NOT NULL,
    component VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    stack_trace TEXT,
    user_id VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX idx_system_logs_level ON system_logs(level);
CREATE INDEX idx_system_logs_component ON system_logs(component);

-- ==========================================
-- Success Message
-- ==========================================
DO $$
BEGIN
    RAISE NOTICE 'Database schema initialized successfully!';
    RAISE NOTICE 'Tables created: 11';
    RAISE NOTICE 'TimescaleDB hypertable: time_logs';
    RAISE NOTICE 'Ready for Assembly Time-Tracking System';
END $$;
