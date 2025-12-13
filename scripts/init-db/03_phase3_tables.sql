-- Phase 3: Add Detection and Tracking Tables
-- Run after 01_init_schema.sql

-- ==========================================
-- Table: detections (for raw detection data)
-- ==========================================
CREATE TABLE IF NOT EXISTS detections (
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

CREATE INDEX idx_detections_camera ON detections(camera_id);
CREATE INDEX idx_detections_timestamp ON detections(timestamp DESC);
CREATE INDEX idx_detections_track ON detections(track_id);
CREATE INDEX idx_detections_zone ON detections(zone_id);

-- ==========================================
-- Table: tracked_objects (current track states)
-- ==========================================
CREATE TABLE IF NOT EXISTS tracked_objects (
    track_id INTEGER NOT NULL,
    camera_id INTEGER NOT NULL,
    class_name VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    bbox_x1 FLOAT NOT NULL,
    bbox_y1 FLOAT NOT NULL,
    bbox_x2 FLOAT NOT NULL,
    bbox_y2 FLOAT NOT NULL,
    zone_id INTEGER,
    status VARCHAR(20) NOT NULL,
    age INTEGER DEFAULT 0,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL,

    PRIMARY KEY (track_id, camera_id)
);

CREATE INDEX idx_tracked_status ON tracked_objects(status);
CREATE INDEX idx_tracked_camera ON tracked_objects(camera_id);
CREATE INDEX idx_tracked_zone ON tracked_objects(zone_id);
CREATE INDEX idx_tracked_last_seen ON tracked_objects(last_seen DESC);

-- ==========================================
-- Table: zone_transitions (zone change events)
-- ==========================================
CREATE TABLE IF NOT EXISTS zone_transitions (
    transition_id BIGSERIAL PRIMARY KEY,
    track_id INTEGER NOT NULL,
    camera_id INTEGER NOT NULL,
    from_zone_id INTEGER,
    to_zone_id INTEGER,
    transition_time TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_in_prev_zone FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transitions_track ON zone_transitions(track_id);
CREATE INDEX idx_transitions_camera ON zone_transitions(camera_id);
CREATE INDEX idx_transitions_time ON zone_transitions(transition_time DESC);
CREATE INDEX idx_transitions_from_zone ON zone_transitions(from_zone_id);
CREATE INDEX idx_transitions_to_zone ON zone_transitions(to_zone_id);

-- ==========================================
-- Grant Permissions
-- ==========================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO assembly_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO assembly_user;
