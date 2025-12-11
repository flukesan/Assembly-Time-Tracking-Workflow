# Qdrant Vector Database Schema Design

## 🔍 Overview

**Qdrant** is used for semantic search in the RAG (Retrieval-Augmented Generation) system.

### Configuration
- **Qdrant Version**: 1.7+
- **Storage**: Persistent (mapped to `/qdrant/storage`)
- **API Port**: 6333 (HTTP), 6334 (gRPC)
- **Vector Model**: `paraphrase-multilingual-mpnet-base-v2` (768 dimensions)
- **Distance Metric**: Cosine similarity
- **Language Support**: Thai + English (bilingual)

---

## 📊 Collection Architecture

```
Qdrant Instance
    │
    ├── work_sequences          (Process patterns & workflows)
    ├── anomaly_patterns        (Historical issues & fixes)
    ├── knowledge_base          (SOPs, manuals, instructions)
    ├── worker_behaviors        (Performance patterns & insights)
    └── incident_reports        (Past incidents & resolutions)
```

---

## 📋 Collection Definitions

### 1. `work_sequences` - Process Patterns & Workflows

**Purpose**: Store standard work sequences, process flows, and assembly patterns for comparison and anomaly detection.

```python
# Collection configuration
COLLECTION_NAME = "work_sequences"
VECTOR_SIZE = 768
DISTANCE_METRIC = "Cosine"

# Sample document structure
{
    "id": "seq_001",
    "vector": [0.123, -0.456, ...],  # 768-dim embedding
    "payload": {
        "sequence_name": "Standard Assembly Process - Model A",
        "sequence_steps": [
            "Pick component from bin",
            "Align with fixture",
            "Install fasteners",
            "Tighten bolts (torque: 15 Nm)",
            "Visual inspection",
            "Quality check"
        ],
        "zone_id": "Z01",
        "product_type": "Model A",
        "avg_duration_seconds": 420,
        "worker_skill_level": "intermediate",
        "success_rate": 0.98,
        "deviation_threshold": 30,  # seconds
        "language": "th",  # or "en"
        "created_at": "2025-01-15T08:00:00+07:00",
        "updated_at": "2025-01-15T08:00:00+07:00",
        "metadata": {
            "tools_required": ["wrench", "screwdriver"],
            "quality_criteria": ["no gaps", "flush alignment"],
            "safety_notes": "Wear safety glasses"
        }
    }
}
```

**Indexing Strategy**:
```python
# HNSW index for fast approximate nearest neighbor search
collection_config = {
    "vectors": {
        "size": 768,
        "distance": "Cosine"
    },
    "hnsw_config": {
        "m": 16,                    # Max connections per layer
        "ef_construct": 100,        # Construction time/quality trade-off
        "full_scan_threshold": 10000
    },
    "optimizers_config": {
        "indexing_threshold": 20000
    }
}

# Payload indexes for filtering
payload_indexes = [
    ("zone_id", "keyword"),
    ("product_type", "keyword"),
    ("worker_skill_level", "keyword"),
    ("language", "keyword"),
    ("created_at", "datetime")
]
```

**Sample Queries**:
```python
# Query 1: Find similar work sequences
query_vector = embedding_model.encode("การประกอบชิ้นส่วน A กับ B")
results = qdrant_client.search(
    collection_name="work_sequences",
    query_vector=query_vector,
    limit=5,
    query_filter={
        "must": [
            {"key": "zone_id", "match": {"value": "Z01"}},
            {"key": "language", "match": {"value": "th"}}
        ]
    }
)

# Query 2: Find sequences by duration
results = qdrant_client.search(
    collection_name="work_sequences",
    query_vector=query_vector,
    limit=10,
    query_filter={
        "must": [
            {"key": "avg_duration_seconds", "range": {"gte": 300, "lte": 600}}
        ]
    }
)
```

---

### 2. `anomaly_patterns` - Historical Issues & Fixes

**Purpose**: Store past anomalies, their root causes, and resolutions for future reference and automated diagnosis.

```python
# Sample document structure
{
    "id": "anom_20250115_001",
    "vector": [0.789, -0.234, ...],  # 768-dim embedding
    "payload": {
        "anomaly_type": "excessive_idle",
        "severity": "medium",
        "description": "Worker idle for 5 minutes in assembly station",
        "root_cause": "Waiting for parts delivery from warehouse",
        "resolution": "Implemented buffer stock system",
        "zone_id": "Z01",
        "worker_id": "W001",
        "timestamp": "2025-01-15T10:15:00+07:00",
        "index_number": 3,
        "impact": {
            "productivity_loss": 0.08,  # 8% loss
            "time_lost_seconds": 300,
            "workers_affected": 1
        },
        "prevention_tips": [
            "Ensure buffer stock of common parts",
            "Set up automatic reorder points",
            "Improve warehouse communication"
        ],
        "similar_incidents_count": 5,  # How many times this has happened
        "language": "th",
        "tags": ["logistics", "inventory", "waiting_time"],
        "metadata": {
            "supervisor_notes": "Discussed with warehouse team",
            "follow_up_actions": ["Install buffer bins", "Train warehouse staff"]
        }
    }
}
```

**Indexing Strategy**:
```python
payload_indexes = [
    ("anomaly_type", "keyword"),
    ("severity", "keyword"),
    ("zone_id", "keyword"),
    ("worker_id", "keyword"),
    ("timestamp", "datetime"),
    ("index_number", "integer"),
    ("language", "keyword"),
    ("tags", "keyword")  # Array field
]
```

**Sample Queries**:
```python
# Query: Find similar anomalies
query = "พนักงานในสถานีประกอบหยุดทำงานนานเกินไป"
query_vector = embedding_model.encode(query)
results = qdrant_client.search(
    collection_name="anomaly_patterns",
    query_vector=query_vector,
    limit=5,
    query_filter={
        "must": [
            {"key": "severity", "match": {"any": ["medium", "high"]}},
            {"key": "language", "match": {"value": "th"}}
        ]
    }
)
```

---

### 3. `knowledge_base` - SOPs, Manuals & Instructions

**Purpose**: Store company documentation, SOPs, work instructions, and best practices for RAG retrieval.

```python
# Sample document structure
{
    "id": "kb_sop_001",
    "vector": [0.456, -0.789, ...],  # 768-dim embedding
    "payload": {
        "title": "Standard Operating Procedure - Assembly Line A",
        "document_type": "SOP",
        "content": """
        # ขั้นตอนการทำงานมาตรฐาน - สายการผลิต A

        ## 1. การเตรียมสถานีงาน
        - ตรวจสอบอุปกรณ์ครบถ้วน
        - ทดสอบเครื่องมือก่อนใช้งาน
        - จัดเตรียมชิ้นส่วนในปริมาณเพียงพอ

        ## 2. กระบวนการประกอบ
        - ยึดชิ้นงานด้วย jig
        - ติดตั้งชิ้นส่วนตามลำดับ 1-5
        - ใช้ torque wrench ที่ 15 Nm

        ## 3. การตรวจสอบคุณภาพ
        - ตรวจสอบความแน่นของสกรู
        - ตรวจสอบความตรงของชิ้นงาน
        - บันทึกผลการตรวจสอบ
        """,
        "section": "Assembly",
        "zone_applicable": ["Z01", "Z02"],
        "version": "2.1",
        "effective_date": "2025-01-01",
        "language": "th",
        "author": "Quality Team",
        "tags": ["assembly", "quality", "procedure"],
        "chunk_index": 0,  # If document is chunked
        "total_chunks": 1,
        "metadata": {
            "file_path": "/docs/SOP-Assembly-LineA-v2.1.pdf",
            "page_number": 1,
            "word_count": 250
        }
    }
}
```

**Chunking Strategy** (for long documents):
```python
# Split long documents into chunks (max 512 tokens per chunk)
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    separators=["\n\n", "\n", " ", ""]
)

chunks = splitter.split_text(long_document)
for i, chunk in enumerate(chunks):
    vector = embedding_model.encode(chunk)
    qdrant_client.upsert(
        collection_name="knowledge_base",
        points=[{
            "id": f"kb_doc001_chunk{i}",
            "vector": vector.tolist(),
            "payload": {
                "content": chunk,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "document_id": "doc001"
            }
        }]
    )
```

**Indexing Strategy**:
```python
payload_indexes = [
    ("document_type", "keyword"),
    ("section", "keyword"),
    ("zone_applicable", "keyword"),  # Array
    ("language", "keyword"),
    ("effective_date", "datetime"),
    ("tags", "keyword")  # Array
]
```

---

### 4. `worker_behaviors` - Performance Patterns & Insights

**Purpose**: Store aggregated worker performance patterns for personalized recommendations and benchmarking.

```python
# Sample document structure
{
    "id": "behavior_W001_2025W02",
    "vector": [0.321, -0.654, ...],  # 768-dim embedding
    "payload": {
        "worker_id": "W001",
        "worker_name": "สมชาย ใจดี",
        "time_period": "2025-W02",  # ISO week
        "zone_id": "Z01",
        "behavior_summary": """
        Worker W001 demonstrates consistent high productivity in Zone Z01 during
        morning shifts. Efficiency peaks between 09:00-11:00 (95% active time).
        Slight productivity drop after lunch (14:00-15:00, 85% active).
        Specializes in Model A assembly (avg 6.5 min/unit vs team avg 7.2 min).
        """,
        "metrics": {
            "total_active_seconds": 25200,  # 7 hours
            "total_idle_seconds": 3600,     # 1 hour
            "productivity_score": 0.875,
            "avg_task_duration": 390,       # seconds
            "tasks_completed": 72,
            "quality_score": 0.97,
            "attendance_rate": 1.0
        },
        "peak_hours": ["09:00-11:00", "16:00-17:00"],
        "low_hours": ["14:00-15:00"],
        "strengths": [
            "Fast assembly speed",
            "High quality output",
            "Consistent attendance"
        ],
        "improvement_areas": [
            "Post-lunch energy management",
            "Multi-model flexibility"
        ],
        "recommendations": [
            "Consider break schedule adjustment",
            "Cross-training on Model B"
        ],
        "language": "th",
        "metadata": {
            "skill_level": "expert",
            "years_experience": 5,
            "certifications": ["ISO 9001", "Safety Level 2"]
        }
    }
}
```

**Indexing Strategy**:
```python
payload_indexes = [
    ("worker_id", "keyword"),
    ("time_period", "keyword"),
    ("zone_id", "keyword"),
    ("language", "keyword"),
    ("metrics.productivity_score", "float"),
    ("metadata.skill_level", "keyword")
]
```

---

### 5. `incident_reports` - Past Incidents & Resolutions

**Purpose**: Store safety incidents, equipment failures, and critical events for learning and prevention.

```python
# Sample document structure
{
    "id": "incident_20250110_001",
    "vector": [0.987, -0.123, ...],  # 768-dim embedding
    "payload": {
        "incident_id": "INC-2025-001",
        "incident_type": "equipment_failure",
        "severity": "high",
        "title": "Conveyor Belt Malfunction",
        "description": """
        สายพานลำเลียงในสถานี Z02 หยุดทำงานกะทันหัน เวลา 14:35 น.
        ส่งผลให้กระบวนการผลิตหยุดชะงัก 45 นาที
        พบว่าสาเหตุมาจากมอเตอร์เกิดร้อนเกินไป เนื่องจากไม่ได้บำรุงรักษา
        """,
        "root_cause": "Lack of preventive maintenance",
        "resolution": """
        - ปิดสายพานและรอให้มอเตอร์เย็นลง
        - ทำความสะอาดและหล่อลื่นชิ้นส่วน
        - เปลี่ยนแบริ่งที่สึกหรอ
        - กลับมาใช้งานได้ภายใน 45 นาที
        """,
        "prevention_measures": [
            "ตั้งตารางบำรุงรักษาประจำสัปดาห์",
            "ติดตั้ง temperature sensor บนมอเตอร์",
            "อบรมช่างเทคนิคเรื่องการบำรุงรักษา"
        ],
        "timestamp": "2025-01-10T14:35:00+07:00",
        "zone_id": "Z02",
        "camera_id": "CAM02",
        "workers_affected": 4,
        "downtime_minutes": 45,
        "cost_estimate": 15000,  # THB
        "reported_by": "supervisor_002",
        "investigated_by": "maintenance_team",
        "status": "closed",
        "language": "th",
        "tags": ["equipment", "maintenance", "downtime"],
        "attachments": [
            "/incidents/2025/INC-2025-001/photo1.jpg",
            "/incidents/2025/INC-2025-001/report.pdf"
        ],
        "metadata": {
            "equipment_id": "CONV-002",
            "last_maintenance": "2024-12-01",
            "warranty_status": "expired"
        }
    }
}
```

**Indexing Strategy**:
```python
payload_indexes = [
    ("incident_type", "keyword"),
    ("severity", "keyword"),
    ("zone_id", "keyword"),
    ("timestamp", "datetime"),
    ("status", "keyword"),
    ("language", "keyword"),
    ("tags", "keyword")
]
```

---

## 🔄 ETL Pipeline: PostgreSQL → Qdrant

### Pipeline Flow

```
PostgreSQL Tables              ETL Process                 Qdrant Collections
─────────────────────────────────────────────────────────────────────────────
sessions                  ─┐
index_records              ├──→ Aggregate & Transform ──→ work_sequences
time_logs                 ─┘      (Process patterns)

anomalies                  ───→ Extract & Embed ────────→ anomaly_patterns
                                  (Root causes & fixes)

system_logs                ───→ Filter & Categorize ───→ incident_reports
                                  (Critical events)

(External docs)            ───→ Chunk & Embed ─────────→ knowledge_base
                                  (SOPs, manuals)

sessions (aggregated)      ───→ Analyze & Summarize ───→ worker_behaviors
workers (metadata)              (Performance patterns)
```

### ETL Implementation

```python
# src/data/etl_pipeline.py

import schedule
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class ETLPipeline:
    def __init__(self):
        self.qdrant = QdrantClient(host="localhost", port=6333)
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        self.postgres = PostgresManager()

    def run_periodic_etl(self):
        """Run every 5 minutes"""
        # 1. Work sequences (from completed sessions)
        self.sync_work_sequences()

        # 2. Anomaly patterns (from new anomalies)
        self.sync_anomaly_patterns()

        # 3. Worker behaviors (daily aggregation)
        self.sync_worker_behaviors()

    def sync_work_sequences(self):
        """Extract standard work sequences from sessions"""
        # Query sessions completed in last 5 minutes
        query = """
        SELECT
            s.session_id,
            s.zone_id,
            s.worker_id,
            s.total_active_seconds,
            s.total_idle_seconds,
            s.index_number,
            z.name as zone_name,
            w.skill_level
        FROM sessions s
        JOIN zones z ON s.zone_id = z.zone_id
        JOIN workers w ON s.worker_id = w.worker_id
        WHERE s.status = 'completed'
          AND s.updated_at > NOW() - INTERVAL '5 minutes'
        """
        sessions = self.postgres.execute(query)

        # Generate embeddings and upsert
        points = []
        for session in sessions:
            text = f"Zone {session['zone_name']} work session: {session['total_active_seconds']}s active, {session['total_idle_seconds']}s idle, skill level {session['skill_level']}"
            vector = self.embedding_model.encode(text)

            points.append({
                "id": session['session_id'],
                "vector": vector.tolist(),
                "payload": {
                    "zone_id": session['zone_id'],
                    "zone_name": session['zone_name'],
                    "avg_duration_seconds": session['total_active_seconds'],
                    "worker_skill_level": session['skill_level'],
                    "index_number": session['index_number'],
                    "language": "th",
                    "created_at": session['updated_at'].isoformat()
                }
            })

        if points:
            self.qdrant.upsert(
                collection_name="work_sequences",
                points=points
            )

    def sync_anomaly_patterns(self):
        """Extract anomalies detected in last 5 minutes"""
        query = """
        SELECT
            anomaly_id,
            anomaly_type,
            severity,
            description,
            root_cause,
            resolution,
            zone_id,
            worker_id,
            timestamp
        FROM anomalies
        WHERE created_at > NOW() - INTERVAL '5 minutes'
        """
        anomalies = self.postgres.execute(query)

        points = []
        for anom in anomalies:
            # Combine description + root_cause for better embedding
            text = f"{anom['description']} Root cause: {anom['root_cause']} Resolution: {anom['resolution']}"
            vector = self.embedding_model.encode(text)

            points.append({
                "id": f"anom_{anom['anomaly_id']}",
                "vector": vector.tolist(),
                "payload": {
                    "anomaly_type": anom['anomaly_type'],
                    "severity": anom['severity'],
                    "description": anom['description'],
                    "root_cause": anom['root_cause'],
                    "resolution": anom['resolution'],
                    "zone_id": anom['zone_id'],
                    "worker_id": anom['worker_id'],
                    "timestamp": anom['timestamp'].isoformat(),
                    "language": "th"
                }
            })

        if points:
            self.qdrant.upsert(
                collection_name="anomaly_patterns",
                points=points
            )

    def sync_worker_behaviors(self):
        """Daily aggregation of worker performance"""
        # Run daily at midnight
        query = """
        SELECT
            worker_id,
            DATE(timestamp) as date,
            SUM(active_duration_seconds) as total_active,
            SUM(idle_duration_seconds) as total_idle,
            AVG(motion_score) as avg_motion
        FROM time_logs
        WHERE DATE(timestamp) = CURRENT_DATE - INTERVAL '1 day'
        GROUP BY worker_id, DATE(timestamp)
        """
        behaviors = self.postgres.execute(query)

        # Generate summary and embed
        # ... (implementation details)

# Schedule ETL tasks
schedule.every(5).minutes.do(etl.run_periodic_etl)
schedule.every().day.at("00:05").do(etl.sync_worker_behaviors)
```

---

## 🔍 Search & Retrieval Strategies

### 1. Hybrid Search (Vector + Filter)

```python
def hybrid_search(query_text, filters, top_k=5):
    """Combine semantic search with metadata filtering"""
    query_vector = embedding_model.encode(query_text)

    results = qdrant_client.search(
        collection_name="work_sequences",
        query_vector=query_vector,
        limit=top_k,
        query_filter={
            "must": [
                {"key": "zone_id", "match": {"value": filters['zone_id']}},
                {"key": "language", "match": {"value": "th"}}
            ],
            "should": [
                {"key": "worker_skill_level", "match": {"value": "expert"}}
            ]
        },
        score_threshold=0.7  # Only return results with similarity > 0.7
    )

    return results
```

### 2. Multi-Collection Search

```python
def multi_collection_search(query_text, collections, top_k=3):
    """Search across multiple collections"""
    query_vector = embedding_model.encode(query_text)
    all_results = []

    for collection in collections:
        results = qdrant_client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=top_k
        )
        all_results.extend(results)

    # Re-rank by score
    all_results.sort(key=lambda x: x.score, reverse=True)
    return all_results[:top_k]
```

### 3. Contextual Search (with time range)

```python
def contextual_search(query_text, time_range_hours=24):
    """Search with temporal context"""
    from datetime import datetime, timedelta

    query_vector = embedding_model.encode(query_text)
    cutoff_time = datetime.now() - timedelta(hours=time_range_hours)

    results = qdrant_client.search(
        collection_name="anomaly_patterns",
        query_vector=query_vector,
        limit=10,
        query_filter={
            "must": [
                {"key": "timestamp", "range": {"gte": cutoff_time.isoformat()}}
            ]
        }
    )

    return results
```

---

## 📈 Performance Optimization

### 1. Collection Configuration

```python
# Optimize for speed (lower accuracy)
qdrant_client.update_collection(
    collection_name="work_sequences",
    hnsw_config={
        "m": 16,
        "ef_construct": 100
    }
)

# Optimize for accuracy (slower)
qdrant_client.update_collection(
    collection_name="knowledge_base",
    hnsw_config={
        "m": 32,
        "ef_construct": 200
    }
)
```

### 2. Payload Indexing

```python
# Index frequently filtered fields
qdrant_client.create_payload_index(
    collection_name="anomaly_patterns",
    field_name="zone_id",
    field_schema="keyword"
)

qdrant_client.create_payload_index(
    collection_name="anomaly_patterns",
    field_name="timestamp",
    field_schema="datetime"
)
```

### 3. Batch Operations

```python
# Batch upsert for better performance
batch_size = 100
for i in range(0, len(points), batch_size):
    batch = points[i:i+batch_size]
    qdrant_client.upsert(
        collection_name="work_sequences",
        points=batch,
        wait=False  # Don't wait for indexing
    )
```

---

## 🔐 Security & Access Control

```python
# API Key authentication (if enabled)
from qdrant_client import QdrantClient

qdrant_client = QdrantClient(
    host="localhost",
    port=6333,
    api_key="your-secret-api-key"  # Set in docker-compose.yml
)
```

---

## 🔄 Backup & Recovery

```bash
# Snapshot creation (via API)
curl -X POST "http://localhost:6333/collections/work_sequences/snapshots"

# Download snapshot
curl -O "http://localhost:6333/collections/work_sequences/snapshots/snapshot-2025-01-15.snapshot"

# Restore from snapshot
curl -X PUT "http://localhost:6333/collections/work_sequences/snapshots/upload" \
  -F "snapshot=@snapshot-2025-01-15.snapshot"
```

---

## ✅ Qdrant Schema Design Complete

### Summary
- ✅ **5 Collections**: work_sequences, anomaly_patterns, knowledge_base, worker_behaviors, incident_reports
- ✅ **768-dim Vectors**: Multilingual embeddings (Thai + English)
- ✅ **HNSW Indexing**: Fast approximate nearest neighbor search
- ✅ **Payload Indexes**: Efficient filtering by metadata
- ✅ **ETL Pipeline**: Automated sync from PostgreSQL
- ✅ **Hybrid Search**: Vector + metadata filtering
- ✅ **Bilingual Support**: Thai and English content

Next: Redis Caching Strategy →
