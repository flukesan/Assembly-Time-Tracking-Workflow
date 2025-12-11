# Testing Strategy

## 🎯 Overview

Comprehensive testing strategy covering unit, integration, performance, and end-to-end testing.

### Testing Goals
- **Code Coverage**: ≥80% for core components
- **Performance**: Meet all performance targets
- **Reliability**: Zero critical bugs in production
- **Compatibility**: Works on Ubuntu 22.04 LTS with specified hardware

---

## 📋 Test Levels

### 1. Unit Testing

**Scope**: Individual functions and methods

**Tools**:
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking

**Coverage Target**: ≥80%

```python
# Example: tests/unit/test_zone_manager.py

import pytest
from src.core.zone_manager import ZoneManager

def test_point_in_polygon():
    """Test point-in-polygon detection"""
    zone = ZoneManager()
    polygon = [[100, 200], [500, 200], [500, 800], [100, 800]]

    # Point inside
    assert zone.is_point_in_polygon((300, 500), polygon) == True

    # Point outside
    assert zone.is_point_in_polygon((50, 50), polygon) == False

    # Point on edge
    assert zone.is_point_in_polygon((100, 200), polygon) == True

def test_zone_validation():
    """Test zone polygon validation"""
    zone = ZoneManager()

    # Valid polygon (minimum 3 points)
    valid = [[100, 200], [500, 200], [300, 800]]
    assert zone.validate_polygon(valid) == True

    # Invalid polygon (only 2 points)
    invalid = [[100, 200], [500, 200]]
    assert zone.validate_polygon(invalid) == False
```

**Run Unit Tests**:
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

### 2. Integration Testing

**Scope**: Component interactions (Database, API, RAG pipeline)

**Tools**:
- `pytest` - Test framework
- `pytest-asyncio` - Async testing
- `testcontainers` - Docker containers for tests

```python
# Example: tests/integration/test_rag_pipeline.py

import pytest
from src.rag.rag_engine import RAGEngine

@pytest.mark.asyncio
async def test_rag_pipeline_end_to_end():
    """Test complete RAG pipeline"""
    rag = RAGEngine()

    query = "ทำไม zone Z01 วันนี้ช้ากว่าปกติ"
    result = await rag.query(query, stream=False)

    # Assert response structure
    assert 'reasoning' in result
    assert 'answer' in result
    assert 'sources' in result
    assert len(result['sources']) > 0

    # Assert content quality
    assert len(result['answer']) > 50  # Meaningful answer
    assert 'Z01' in result['answer'] or 'โซน' in result['answer']

@pytest.mark.asyncio
async def test_database_operations():
    """Test PostgreSQL operations"""
    from src.data.postgres_manager import PostgresManager

    db = PostgresManager()

    # Test worker creation
    worker = await db.create_worker({
        'worker_id': 'TEST001',
        'name': 'Test Worker',
        'badge_id': 'BADGE-TEST001',
        'shift': 'morning'
    })
    assert worker['worker_id'] == 'TEST001'

    # Test retrieval
    retrieved = await db.get_worker('TEST001')
    assert retrieved['name'] == 'Test Worker'

    # Cleanup
    await db.delete_worker('TEST001')
```

**Run Integration Tests**:
```bash
# Start test containers
docker compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/ -v

# Stop test containers
docker compose -f docker-compose.test.yml down
```

---

### 3. Performance Testing

**Scope**: System performance under load

**Tools**:
- `locust` - Load testing
- `pytest-benchmark` - Micro-benchmarking

**Targets**:
- Camera capture: 30 FPS
- Detection: 15 FPS (batch 4)
- YOLO inference: <50ms/batch
- RAG query: <3s
- API response: <200ms

```python
# Example: tests/performance/test_inference_speed.py

import pytest
from src.ai.yolo_detector import YOLODetector
import cv2
import time

def test_yolo_inference_speed(benchmark):
    """Test YOLO inference speed"""
    detector = YOLODetector(model='yolov8n.pt')
    frame = cv2.imread('tests/fixtures/test_frame.jpg')

    # Benchmark single inference
    result = benchmark(detector.detect, frame)

    # Assert inference time <50ms
    assert benchmark.stats['mean'] < 0.050  # 50ms

def test_yolo_batch_inference():
    """Test batch inference (4 frames)"""
    detector = YOLODetector(model='yolov8n.pt')
    frames = [cv2.imread(f'tests/fixtures/frame_{i}.jpg') for i in range(4)]

    start = time.time()
    results = detector.detect_batch(frames)
    duration = time.time() - start

    # Assert batch inference <50ms
    assert duration < 0.050
    assert len(results) == 4
```

**Load Testing (API)**:
```python
# tests/performance/locustfile.py

from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_metrics(self):
        self.client.get("/api/v1/metrics/today",
                       headers={"Authorization": "Bearer token"})

    @task(1)
    def query_rag(self):
        self.client.post("/api/v1/query",
                        json={"query": "สรุปประสิทธิภาพวันนี้"},
                        headers={"Authorization": "Bearer token"})
```

**Run Performance Tests**:
```bash
# Benchmark tests
pytest tests/performance/test_inference_speed.py --benchmark-only

# Load testing
locust -f tests/performance/locustfile.py --host=http://localhost:8000
# Open: http://localhost:8089
```

---

### 4. End-to-End (E2E) Testing

**Scope**: Complete user workflows

**Tools**:
- `pytest` - Test orchestration
- `selenium` - UI automation (for web interface)

```python
# Example: tests/e2e/test_monitoring_workflow.py

def test_complete_monitoring_workflow():
    """Test: Start monitoring → Detect person → Track session → Generate report"""

    # 1. Start system
    system = AssemblyTrackingSystem()
    system.start()

    # 2. Inject test video
    system.camera_manager.load_test_video('tests/fixtures/test_video.mp4')

    # 3. Wait for detection
    time.sleep(5)

    # 4. Verify session created
    sessions = system.redis_manager.get_active_sessions()
    assert len(sessions) > 0

    # 5. Verify database logging
    time_logs = system.postgres_manager.get_recent_time_logs(limit=10)
    assert len(time_logs) > 0

    # 6. Generate report
    report = system.generate_daily_report(date='2025-01-15')
    assert report['total_workers'] > 0

    # 7. Stop system
    system.stop()
```

**Run E2E Tests**:
```bash
pytest tests/e2e/ -v -s
```

---

## 🧪 Test Categories

### Functional Tests
- ✅ Person detection accuracy
- ✅ Tracking ID persistence
- ✅ Zone matching correctness
- ✅ Active/idle state detection
- ✅ Index transitions
- ✅ Break time handling
- ✅ Worker identification (face/badge)
- ✅ RAG query accuracy

### Non-Functional Tests
- ✅ Performance (FPS, latency, throughput)
- ✅ Scalability (4 cameras, 10+ workers)
- ✅ Reliability (uptime, error recovery)
- ✅ Security (authentication, authorization)
- ✅ Usability (UI responsiveness)
- ✅ Compatibility (Ubuntu 22.04, GPU)

---

## 📊 Test Data

### Fixtures

```bash
tests/fixtures/
├── images/
│   ├── test_frame_empty.jpg       # Empty zone
│   ├── test_frame_1_person.jpg    # 1 person
│   ├── test_frame_3_persons.jpg   # 3 persons
│   └── test_frame_occlusion.jpg   # Person partially hidden
├── videos/
│   ├── test_video_normal.mp4      # Normal workflow
│   ├── test_video_idle.mp4        # Person idle for 90s
│   └── test_video_zone_exit.mp4   # Person exits zone
├── database/
│   ├── seed_workers.sql           # Sample workers
│   ├── seed_zones.sql             # Sample zones
│   └── seed_schedules.sql         # Sample schedules
└── embeddings/
    └── sample_embeddings.pkl      # Pre-computed embeddings
```

### Mock Data

```python
# tests/mocks/mock_data.py

MOCK_WORKERS = [
    {
        'worker_id': 'W001',
        'name': 'สมชาย ใจดี',
        'badge_id': 'BADGE-001',
        'shift': 'morning',
        'skill_level': 'expert'
    },
    # ... more workers
]

MOCK_ZONES = [
    {
        'zone_id': 'Z01',
        'camera_id': 'CAM01',
        'name': 'Assembly Station 1',
        'polygon_coords': [[100, 200], [500, 200], [500, 800], [100, 800]],
        'zone_type': 'work_area'
    },
    # ... more zones
]
```

---

## 🤖 Continuous Integration (CI)

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml

name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-22.04

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run unit tests
      run: |
        pytest tests/unit/ --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml

    - name: Run integration tests
      run: |
        docker compose -f docker-compose.test.yml up -d
        pytest tests/integration/
        docker compose -f docker-compose.test.yml down
```

---

## 📝 Test Documentation

### Test Reports

**Generate HTML Report**:
```bash
pytest --html=report.html --self-contained-html
```

**Generate Coverage Report**:
```bash
pytest --cov=src --cov-report=html
```

### Test Metrics

Track these metrics:
- **Code Coverage**: % of code exercised by tests
- **Test Pass Rate**: % of tests passing
- **Mean Time to Repair (MTTR)**: Time to fix failing tests
- **Flaky Test Rate**: % of tests with inconsistent results

---

## ✅ Acceptance Criteria

### System Must Pass:

1. **Functional**:
   - ✅ Person detection confidence >90%
   - ✅ Tracking ID persistence across occlusion
   - ✅ Zone matching accuracy >95%
   - ✅ RAG query relevance >80%

2. **Performance**:
   - ✅ Camera capture: 30 FPS (all 4 cameras)
   - ✅ Detection: 15 FPS (batch 4)
   - ✅ YOLO inference: <50ms/batch
   - ✅ End-to-end latency: <200ms
   - ✅ RAG query: <3s

3. **Reliability**:
   - ✅ Uptime: >99.9%
   - ✅ Camera reconnection: <5s
   - ✅ Database failover: <10s
   - ✅ Zero data loss (PostgreSQL WAL)

4. **Security**:
   - ✅ Authentication required for all endpoints
   - ✅ HTTPS enabled (production)
   - ✅ No SQL injection vulnerabilities
   - ✅ No XSS vulnerabilities

---

## 🚀 Pre-Production Checklist

Before deploying to production:

- [ ] All unit tests passing (≥80% coverage)
- [ ] All integration tests passing
- [ ] Performance benchmarks met
- [ ] E2E workflows validated
- [ ] Load testing completed (100 concurrent users)
- [ ] Security audit passed
- [ ] Documentation complete
- [ ] User acceptance testing (UAT) passed
- [ ] Backup & recovery tested
- [ ] Monitoring & alerting configured

---

## ✅ Testing Strategy Complete

### Summary
- ✅ **4 Test Levels**: Unit, Integration, Performance, E2E
- ✅ **Coverage Target**: ≥80%
- ✅ **Tools**: pytest, locust, selenium
- ✅ **CI/CD**: GitHub Actions
- ✅ **Fixtures**: Images, videos, mock data
- ✅ **Acceptance Criteria**: Functional, Performance, Reliability, Security

All design documentation complete! Ready to commit and push.
