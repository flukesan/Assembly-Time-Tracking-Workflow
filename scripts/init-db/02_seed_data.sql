-- Seed Data for Development/Testing
-- Sample workers, cameras, zones, and schedules

-- ==========================================
-- Seed: Sample Workers
-- ==========================================
INSERT INTO workers (worker_id, name, badge_id, shift, skill_level, station_assignments, active)
VALUES
    ('W001', 'สมชาย ใจดี', 'BADGE-001', 'morning', 'expert', '{"preferred": ["Z01"], "certified": ["Z01", "Z02", "Z03"]}', TRUE),
    ('W002', 'สมหญิง ขยัน', 'BADGE-002', 'morning', 'intermediate', '{"preferred": ["Z02"], "certified": ["Z02", "Z03"]}', TRUE),
    ('W003', 'สมศรี รักงาน', 'BADGE-003', 'morning', 'expert', '{"preferred": ["Z01", "Z02"], "certified": ["Z01", "Z02", "Z03", "Z04"]}', TRUE),
    ('W004', 'สมปอง ใจเย็น', 'BADGE-004', 'afternoon', 'intermediate', '{"preferred": ["Z03"], "certified": ["Z03", "Z04"]}', TRUE),
    ('W005', 'สมใจ มั่นคง', 'BADGE-005', 'afternoon', 'beginner', '{"preferred": ["Z04"], "certified": ["Z04"]}', TRUE)
ON CONFLICT (worker_id) DO NOTHING;

-- ==========================================
-- Seed: Sample Cameras (for testing)
-- ==========================================
INSERT INTO cameras (camera_id, name, rtsp_url, location, status, resolution, fps)
VALUES
    ('CAM01', 'Station 1 Overhead', 'rtsp://192.168.1.100:554/stream1', 'Assembly Line A - North', 'inactive', '1920x1080', 30),
    ('CAM02', 'Station 2 Side View', 'rtsp://192.168.1.101:554/stream1', 'Assembly Line A - East', 'inactive', '1920x1080', 30),
    ('CAM03', 'Station 3 Overhead', 'rtsp://192.168.1.102:554/stream1', 'Assembly Line B - North', 'inactive', '1920x1080', 30),
    ('CAM04', 'Inspection Area', 'rtsp://192.168.1.103:554/stream1', 'Quality Control - Center', 'inactive', '1920x1080', 30)
ON CONFLICT (camera_id) DO NOTHING;

-- ==========================================
-- Seed: Sample Zones
-- ==========================================
INSERT INTO zones (zone_id, camera_id, name, polygon_coords, zone_type, color, min_workers, max_workers)
VALUES
    ('Z01', 'CAM01', 'Assembly Station 1', '[[100, 200], [500, 200], [500, 800], [100, 800]]', 'work_area', '#00FF00', 1, 2),
    ('Z02', 'CAM02', 'Assembly Station 2', '[[150, 250], [550, 250], [550, 750], [150, 750]]', 'work_area', '#0000FF', 1, 3),
    ('Z03', 'CAM03', 'Assembly Station 3', '[[100, 200], [500, 200], [500, 800], [100, 800]]', 'work_area', '#FF0000', 1, 3),
    ('Z04', 'CAM04', 'Inspection Area', '[[200, 300], [600, 300], [600, 700], [200, 700]]', 'inspection', '#FFFF00', 1, 2)
ON CONFLICT (zone_id) DO NOTHING;

-- ==========================================
-- Seed: Default Schedule (Today)
-- ==========================================
INSERT INTO schedules (
    date,
    work_start_time,
    work_end_time,
    break1_start,
    break1_duration,
    break2_start,
    break2_duration,
    index_timeline,
    total_indices,
    active
)
VALUES (
    CURRENT_DATE,
    '08:00:00',
    '17:00:00',
    '10:00:00',
    15,
    '15:00:00',
    15,
    '[
        {"index": 1, "start": "08:00", "end": "08:57"},
        {"index": 2, "start": "08:57", "end": "09:54"},
        {"index": 3, "start": "09:54", "end": "10:00", "break": "10:00-10:15", "resume": "10:15", "end_after_break": "10:36"},
        {"index": 4, "start": "10:36", "end": "11:33"},
        {"index": 5, "start": "11:33", "end": "12:30"},
        {"index": 6, "start": "12:30", "end": "13:27"},
        {"index": 7, "start": "13:27", "end": "14:24"},
        {"index": 8, "start": "14:24", "end": "15:00", "break": "15:00-15:15", "resume": "15:15", "end_after_break": "15:36"},
        {"index": 9, "start": "15:36", "end": "16:03"},
        {"index": 10, "start": "16:03", "end": "16:33"},
        {"index": 11, "start": "16:33", "end": "17:00"}
    ]'::jsonb,
    11,
    TRUE
)
ON CONFLICT (date) DO NOTHING;

-- ==========================================
-- Seed: Sample Zone Templates
-- ==========================================
INSERT INTO zone_templates (name, description, template_data, camera_type)
VALUES
    (
        'Standard 2x2 Grid',
        'Standard 4-zone layout for 2x2 grid arrangement',
        '[
            {"zone_name": "Station 1", "polygon": [[100, 200], [500, 200], [500, 800], [100, 800]], "color": "#00FF00"},
            {"zone_name": "Station 2", "polygon": [[550, 200], [950, 200], [950, 800], [550, 800]], "color": "#0000FF"},
            {"zone_name": "Station 3", "polygon": [[100, 850], [500, 850], [500, 1450], [100, 1450]], "color": "#FF0000"},
            {"zone_name": "Station 4", "polygon": [[550, 850], [950, 850], [950, 1450], [550, 1450]], "color": "#FFFF00"}
        ]'::jsonb,
        'overhead'
    ),
    (
        'Single Assembly Zone',
        'Single large zone for one assembly station',
        '[
            {"zone_name": "Main Assembly", "polygon": [[200, 300], [800, 300], [800, 900], [200, 900]], "color": "#00FF00"}
        ]'::jsonb,
        'overhead'
    )
ON CONFLICT (name) DO NOTHING;

-- ==========================================
-- Success Message
-- ==========================================
DO $$
BEGIN
    RAISE NOTICE 'Seed data inserted successfully!';
    RAISE NOTICE 'Workers: 5';
    RAISE NOTICE 'Cameras: 4';
    RAISE NOTICE 'Zones: 4';
    RAISE NOTICE 'Schedules: 1 (today)';
    RAISE NOTICE 'Templates: 2';
END $$;
