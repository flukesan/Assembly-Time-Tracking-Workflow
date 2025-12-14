# Phase 4B: RAG + DeepSeek-R1 Integration

## 📋 Overview

Phase 4B extends the Assembly Time-Tracking System with AI-powered insights using **Retrieval-Augmented Generation (RAG)** and **DeepSeek-R1** local LLM via Ollama.

### Key Features

- 🧠 **Natural Language Queries** - Ask questions in Thai or English
- 📊 **Automated Insights** - Daily productivity analysis
- 🔍 **Anomaly Detection** - Statistical pattern detection
- 🎯 **Smart Recommendations** - AI-powered actionable advice
- 📄 **Automated Reports** - Daily, weekly, and worker-specific reports
- 🗄️ **Knowledge Base** - Qdrant vector database with semantic search
- 🌐 **Bilingual Support** - Full Thai + English interface

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│                                                               │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Worker Mgmt   │  │ Time Track   │  │ AI Query API    │  │
│  │ (Face+Badge)  │  │ (Productivity)│  │ (NL Queries)    │  │
│  └───────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                    │                     │
         ▼                    ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────────┐
│ PostgreSQL   │    │   Qdrant     │    │     Ollama       │
│ (TimescaleDB)│    │ (Vector DB)  │    │ (DeepSeek-R1)    │
│              │    │              │    │                  │
│ - Workers    │    │ - Embeddings │    │ - LLM 14B        │
│ - Sessions   │    │ - Semantic   │    │ - Reasoning      │
│ - Tracking   │    │   Search     │    │ - Thai/English   │
└──────────────┘    └──────────────┘    └──────────────────┘
```

### RAG Pipeline

```
User Query (Thai/English)
    │
    ▼
┌─────────────────────┐
│ Embedding Generator │ (sentence-transformers)
└─────────────────────┘
    │ (768-dim vector)
    ▼
┌─────────────────────┐
│ Qdrant Search       │ (cosine similarity)
└─────────────────────┘
    │ (top-k results)
    ▼
┌─────────────────────┐
│ Prompt Builder      │ (context + query)
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ DeepSeek-R1 (LLM)   │ (generate response)
└─────────────────────┘
    │
    ▼
Response (with reasoning)
```

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Docker and Docker Compose installed
docker --version
docker compose version
```

### 2. Download DeepSeek-R1 Model

```bash
# Start Ollama service first
docker compose -f docker-compose.cpu.yml up ollama -d

# Pull the model (this will take some time, ~8GB download)
docker exec -it assembly_ollama ollama pull deepseek-r1:14b

# Verify model is available
docker exec -it assembly_ollama ollama list
```

### 3. Start All Services

```bash
# Start all services
docker compose -f docker-compose.cpu.yml up -d

# Check logs
docker compose -f docker-compose.cpu.yml logs -f app

# Wait for "Phase 4B RAG + DeepSeek-R1 system started successfully!"
```

### 4. Verify Services

```bash
# Check health endpoint
curl http://localhost:8000/health | jq

# Expected output:
{
  "status": "healthy",
  "phase": "Phase 4B - RAG + DeepSeek-R1",
  "components": {
    "api": "healthy",
    "postgresql": "connected",
    "qdrant": "connected",
    "redis": "available",
    "ollama": "connected"
  },
  "ai_services": {
    "knowledge_base": "ready",
    "insight_generator": "ready",
    "anomaly_detector": "ready",
    "recommendation_engine": "ready",
    "report_generator": "ready"
  }
}
```

---

## 📡 API Endpoints

### AI Query API (`/api/v1/ai`)

#### 1. Natural Language Query

**POST** `/api/v1/ai/query`

Ask questions in natural language (Thai or English).

**Request:**
```json
{
  "question": "พนักงาน W001 ทำงานอย่างไรบ้างวันนี้?",
  "show_reasoning": true,
  "max_context_items": 5
}
```

**Response:**
```json
{
  "question": "พนักงาน W001 ทำงานอย่างไรบ้างวันนี้?",
  "answer": "พนักงาน W001 (นายสมชาย ใจดี) ทำงานได้ดีมาก...",
  "reasoning": "<think>วิเคราะห์ข้อมูลจาก knowledge base...</think>",
  "context_used": {
    "workers": 1,
    "productivity": 3,
    "sessions": 2
  },
  "model": "deepseek-r1:14b",
  "duration_ms": 1250
}
```

**Example Queries:**
- Thai: `"พนักงานคนไหนมี productivity สูงสุดในกะเช้า?"`
- English: `"Who has the highest productivity in the morning shift?"`
- Thai: `"แนะนำการปรับปรุงสำหรับพนักงานที่มี efficiency ต่ำกว่า 70%"`
- English: `"Recommend improvements for workers with efficiency below 70%"`

#### 2. Worker Analysis

**POST** `/api/v1/ai/analyze/worker`

Analyze a specific worker's performance.

**Request:**
```json
{
  "worker_id": "W001",
  "include_recommendations": true
}
```

**Response:**
```json
{
  "worker_id": "W001",
  "worker_name": "นายสมชาย ใจดี",
  "analysis": "การวิเคราะห์ผลการทำงาน...",
  "reasoning": "<think>...</think>",
  "productivity_data": {
    "index_11_overall_productivity": 85.5,
    "index_5_work_efficiency": 78.2,
    "index_9_output_per_hour": 12.3,
    "index_10_quality_score": 92.0
  },
  "model": "deepseek-r1:14b"
}
```

#### 3. Compare Workers

**POST** `/api/v1/ai/compare/workers`

Compare multiple workers' performance.

**Request:**
```json
{
  "worker_ids": ["W001", "W002", "W003"],
  "criteria": "overall_productivity"
}
```

**Response:**
```json
{
  "workers_compared": 3,
  "comparison": "การเปรียบเทียบพนักงาน 3 คน...",
  "reasoning": "<think>...</think>",
  "workers_data": [...],
  "model": "deepseek-r1:14b"
}
```

#### 4. Shift Summary

**POST** `/api/v1/ai/summary/shift`

Generate shift performance summary.

**Request:**
```json
{
  "shift": "morning",
  "date": "2025-12-14"
}
```

**Response:**
```json
{
  "shift": "morning",
  "date": "2025-12-14",
  "summary": "กะเช้า วันที่ 14 ธันวาคม 2025...",
  "reasoning": "<think>...</think>",
  "statistics": {
    "total_workers": 15,
    "avg_productivity": 78.5,
    "total_output": 1250,
    "issues_count": 2
  },
  "model": "deepseek-r1:14b"
}
```

#### 5. Health Check

**GET** `/api/v1/ai/health`

Check AI services health.

**Response:**
```json
{
  "ollama_client": {
    "initialized": true,
    "connected": true,
    "stats": {
      "total_requests": 42,
      "total_errors": 0,
      "avg_response_time_ms": 1150
    }
  },
  "knowledge_base": {
    "initialized": true,
    "stats": {
      "total_indexed": 250,
      "collections": 4
    }
  }
}
```

#### 6. List Models

**GET** `/api/v1/ai/models`

List available LLM models.

**Response:**
```json
{
  "models": [
    {
      "name": "deepseek-r1:14b",
      "size": "8.5GB",
      "modified": "2025-12-14T10:30:00Z"
    }
  ],
  "current_model": "deepseek-r1:14b"
}
```

---

## 🧪 Testing Workflow

### Step 1: Register a Worker

```bash
curl -X POST http://localhost:8000/api/v1/workers \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "W001",
    "name": "นายสมชาย ใจดี",
    "shift": "morning",
    "role": "assembler",
    "department": "assembly_line_1"
  }'
```

### Step 2: Index Worker in Knowledge Base

The worker is automatically indexed when registered. Verify:

```bash
curl -X POST http://localhost:8000/api/v1/ai/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "มีพนักงานชื่อสมชายไหม?",
    "show_reasoning": false
  }'
```

### Step 3: Simulate Productivity Data

```bash
# Start a work session
curl -X POST http://localhost:8000/api/v1/workers/W001/sessions/start

# Complete some tasks (simulate work)
curl -X POST http://localhost:8000/api/v1/workers/W001/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_type": "assembly", "quantity": 10}'

# End session
curl -X POST http://localhost:8000/api/v1/workers/W001/sessions/end
```

### Step 4: Query Worker Performance

```bash
curl -X POST http://localhost:8000/api/v1/ai/analyze/worker \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "W001",
    "include_recommendations": true
  }' | jq
```

### Step 5: Generate Daily Report

```bash
curl -X POST http://localhost:8000/api/v1/ai/summary/shift \
  -H "Content-Type: application/json" \
  -d '{
    "shift": "morning",
    "date": "2025-12-14"
  }' | jq
```

### Step 6: Natural Language Query

```bash
# Thai query
curl -X POST http://localhost:8000/api/v1/ai/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "พนักงานคนไหนทำงานได้ดีที่สุดวันนี้?",
    "show_reasoning": true
  }' | jq

# English query
curl -X POST http://localhost:8000/api/v1/ai/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Who are the top 3 performers today?",
    "show_reasoning": false
  }' | jq
```

---

## 📊 Knowledge Base Collections

### 1. Workers Collection

**Purpose:** Store worker profiles and metadata

**Indexed Fields:**
- Worker ID, name, shift, role, department
- Registration date, status
- Total sessions, total work hours

**Example Search:**
```python
results = knowledge_base.search_workers(
    query="morning shift assemblers",
    limit=10
)
```

### 2. Productivity Collection

**Purpose:** Store productivity indices and performance data

**Indexed Fields:**
- All 11 productivity indices
- Worker ID, shift, date
- Overall productivity score
- Quality score, output per hour

**Example Search:**
```python
results = knowledge_base.search_productivity(
    query="high productivity workers",
    limit=5,
    score_threshold=0.7
)
```

### 3. Sessions Collection

**Purpose:** Store work session details

**Indexed Fields:**
- Session ID, worker ID
- Start time, end time, duration
- Zone transitions, tasks completed
- Break time, idle time

**Example Search:**
```python
results = knowledge_base.search_sessions(
    query="long work sessions",
    limit=10
)
```

### 4. Insights Collection

**Purpose:** Store generated insights and summaries

**Indexed Fields:**
- Insight type (daily_summary, worker_analysis, etc.)
- Generated content
- Metadata (date, workers analyzed, etc.)

**Example Search:**
```python
results = knowledge_base.search_insights(
    query="low productivity alerts",
    limit=5
)
```

---

## 🔍 Anomaly Detection

### Statistical Methods

**1. Productivity Anomalies**
- Z-score calculation: `(current - mean) / std`
- Threshold: 2.0 standard deviations
- Types: `unusually_high`, `unusually_low`

**2. Efficiency Drop Detection**
- Compare current vs recent average
- Default threshold: 15% drop
- Severity: `critical` (>25%), `warning` (>15%)

**3. Quality Issues**
- Track recent quality scores
- Threshold: 80/100
- Alert if >50% of scores below threshold

**4. Idle Time Spikes**
- Compare to historical average
- Spike multiplier: 2.0x
- Severity: `warning`

**5. Output Decline**
- Compare current output vs average
- Threshold: 20% decline
- Severity: `critical` (>35%), `warning` (>20%)

### Example Usage

```python
from insights.anomaly_detector import AnomalyDetector

detector = AnomalyDetector(std_threshold=2.0)

result = detector.detect_productivity_anomalies(
    current_value=55.0,
    historical_values=[75, 78, 80, 77, 76]
)

# result:
{
  "is_anomaly": True,
  "anomaly_type": "unusually_low",
  "z_score": -2.5,
  "severity": "critical",
  "deviation_percent": -27.6
}
```

---

## 🎯 Recommendation Engine

### Priority Levels

- **High:** Critical issues requiring immediate action
- **Medium:** Important improvements for better performance
- **Low:** Optional optimizations
- **Info:** Informational feedback

### Recommendation Categories

1. **Productivity Improvement**
   - Low overall productivity (<60)
   - Declining productivity trend

2. **Efficiency Enhancement**
   - Low work efficiency (<70%)
   - Excessive idle time (>2 hours)

3. **Quality Control**
   - Quality score below 80
   - Consistent quality issues

4. **Output Optimization**
   - Output below target
   - Declining output trend

5. **Time Management**
   - Excessive break time
   - Poor time utilization

### Example Output

```json
{
  "recommendations": [
    {
      "priority": "high",
      "category": "productivity",
      "message": "Overall productivity is 55/100 (below target of 60). Immediate action needed.",
      "actionable_steps": [
        "Review work processes",
        "Provide additional training",
        "Check for equipment issues"
      ]
    },
    {
      "priority": "medium",
      "category": "efficiency",
      "message": "Work efficiency is 68% (target: 70%). Consider workflow optimization.",
      "actionable_steps": [
        "Analyze workflow bottlenecks",
        "Optimize task sequencing"
      ]
    }
  ]
}
```

---

## 📄 Report Generation

### Daily Report

```python
from reports.report_generator import ReportGenerator

report = await report_generator.generate_daily_report(
    date=datetime(2025, 12, 14),
    language="th"  # or "en"
)

print(report_generator.format_daily_report(report))
```

**Output:**
```
=== รายงานประจำวัน: 14 ธันวาคม 2025 ===

📊 สรุปภาพรวม:
  • พนักงานทั้งหมด: 45 คน
  • ผลผลิตเฉลี่ย: 76.5/100
  • ผลผลิตรวม: 2,450 ชิ้น
  • มีปัญหา: 3 คน

🌟 พนักงานยอดเยี่ยม (Top 5):
  1. นายสมชาย ใจดี (W001) - 95.2/100
  2. นางสาวมาลี รักงาน (W015) - 92.8/100
  ...

⚠️ พนักงานที่ต้องพัฒนา:
  • นายบุญมี ขยัน (W042) - 52.3/100
    → ปัญหา: efficiency ต่ำ, idle time สูง

📈 การวิเคราะห์ตามกะ:
  กะเช้า: ผลผลิตเฉลี่ย 78.2/100 (ดี)
  กะบ่าย: ผลผลิตเฉลี่ย 75.8/100 (พอใช้)
  กะดึก: ผลผลิตเฉลี่ย 74.1/100 (พอใช้)

🤖 AI Analysis:
วิเคราะห์โดย DeepSeek-R1...
[AI-generated summary]

📋 คำแนะนำ:
  1. พนักงาน 3 คนต้องการการพัฒนา
  2. กะดึกมีผลผลิตต่ำกว่าเป้าหมาย
  ...
```

### Weekly Report

```python
report = await report_generator.generate_weekly_report(
    start_date=datetime(2025, 12, 8)
)

print(report_generator.format_weekly_report(report))
```

### Worker Report

```python
report = await report_generator.generate_worker_report(
    worker_id="W001",
    days=30
)

print(report_generator.format_worker_report(report))
```

---

## 🛠️ Configuration

### Environment Variables

```env
# Ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=deepseek-r1:14b

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
EMBEDDING_DIM=768

# Thresholds
MIN_PRODUCTIVITY_THRESHOLD=60.0
MIN_EFFICIENCY_THRESHOLD=70.0
ANOMALY_STD_THRESHOLD=2.0
```

### Customizing Thresholds

Edit `src/main.py`:

```python
# Adjust insight generator thresholds
insight_generator = InsightGenerator(
    ollama_client=ollama_client,
    knowledge_base=knowledge_base,
    min_productivity_threshold=65.0,  # Increase from 60
    min_efficiency_threshold=75.0     # Increase from 70
)

# Adjust anomaly detector sensitivity
anomaly_detector = AnomalyDetector(
    std_threshold=1.5,     # More sensitive (default: 2.0)
    min_data_points=10     # Require more data (default: 5)
)
```

---

## 🐛 Troubleshooting

### 1. Ollama Connection Failed

**Symptom:** `Connection refused to ollama:11434`

**Solution:**
```bash
# Check if Ollama is running
docker compose ps ollama

# Restart Ollama
docker compose restart ollama

# Check logs
docker compose logs ollama
```

### 2. Model Not Found

**Symptom:** `Model 'deepseek-r1:14b' not found`

**Solution:**
```bash
# Pull the model
docker exec -it assembly_ollama ollama pull deepseek-r1:14b

# Verify
docker exec -it assembly_ollama ollama list
```

### 3. Slow Response Times

**Symptom:** AI queries take >10 seconds

**Solutions:**
- **CPU Mode:** DeepSeek-R1:14b is slow on CPU. Consider using GPU version.
- **Smaller Model:** Use `deepseek-r1:7b` or `llama3:8b` for faster responses.
- **Disable Reasoning:** Set `show_reasoning=false` in queries.

```bash
# Pull smaller model
docker exec -it assembly_ollama ollama pull llama3:8b

# Update environment variable
OLLAMA_MODEL=llama3:8b
```

### 4. Qdrant Connection Issues

**Symptom:** `Failed to connect to Qdrant`

**Solution:**
```bash
# Check Qdrant status
docker compose ps qdrant

# Restart Qdrant
docker compose restart qdrant

# Verify collections
curl http://localhost:6333/collections
```

### 5. Out of Memory

**Symptom:** `Ollama killed (OOM)`

**Solution:**
```yaml
# Edit docker-compose.cpu.yml
ollama:
  deploy:
    resources:
      limits:
        memory: 16G  # Increase from default
```

---

## 📈 Performance Optimization

### 1. Enable GPU Acceleration

```bash
# Use GPU docker-compose file (if available)
docker compose -f docker-compose.yml up -d

# Verify GPU usage
docker exec -it assembly_ollama nvidia-smi
```

### 2. Batch Processing

```python
# Process multiple workers in parallel
async def analyze_multiple_workers(worker_ids):
    tasks = [
        ai_query.analyze_worker(worker_id)
        for worker_id in worker_ids
    ]
    return await asyncio.gather(*tasks)
```

### 3. Cache Results

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def get_cached_analysis(worker_id: str, date: str):
    # Cache worker analysis for the day
    pass
```

### 4. Optimize Embedding Generation

```python
# Batch encode texts
texts = [worker1_text, worker2_text, ...]
embeddings = embedding_generator.encode(texts)  # Single batch call
```

---

## 🔐 Security Considerations

### 1. API Authentication

Add authentication middleware:

```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.middleware("http")
async def verify_token(request: Request, call_next):
    # Verify JWT token
    # ...
    response = await call_next(request)
    return response
```

### 2. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/ai/query")
@limiter.limit("10/minute")  # Max 10 queries per minute
async def natural_language_query(...):
    ...
```

### 3. Input Validation

```python
from pydantic import BaseModel, Field, validator

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)

    @validator('question')
    def sanitize_input(cls, v):
        # Prevent injection attacks
        return v.strip()
```

---

## 📚 Additional Resources

- **DeepSeek-R1 Documentation:** https://ollama.com/library/deepseek-r1
- **Qdrant Documentation:** https://qdrant.tech/documentation/
- **Sentence Transformers:** https://www.sbert.net/
- **FastAPI Documentation:** https://fastapi.tiangolo.com/

---

## 🎓 Example Use Cases

### Use Case 1: Daily Standup Report

**Goal:** Generate morning report for management

```bash
curl -X POST http://localhost:8000/api/v1/ai/summary/shift \
  -H "Content-Type: application/json" \
  -d '{"shift": "morning", "date": "2025-12-14"}' \
  | jq '.summary'
```

### Use Case 2: Worker Performance Review

**Goal:** Review worker performance for monthly evaluation

```bash
curl -X POST http://localhost:8000/api/v1/ai/analyze/worker \
  -H "Content-Type: application/json" \
  -d '{"worker_id": "W001", "include_recommendations": true}' \
  | jq
```

### Use Case 3: Identify Training Needs

**Goal:** Find workers who need additional training

```bash
curl -X POST http://localhost:8000/api/v1/ai/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "แสดงรายชื่อพนักงานที่มี quality score ต่ำกว่า 70 และแนะนำหลักสูตรที่เหมาะสม"
  }' | jq '.answer'
```

### Use Case 4: Compare Shift Performance

**Goal:** Compare productivity across shifts

```bash
curl -X POST http://localhost:8000/api/v1/ai/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "เปรียบเทียบผลผลิตของกะเช้า กะบ่าย และกะดึก แล้วแนะนำปรับปรุง"
  }' | jq '.answer'
```

---

## 📝 Changelog

### Version 4.1.0 (Phase 4B) - 2025-12-14

**Added:**
- ✨ RAG system with Qdrant vector database
- ✨ DeepSeek-R1 integration via Ollama
- ✨ Natural language query API (Thai/English)
- ✨ Automated insight generation
- ✨ Statistical anomaly detection
- ✨ AI-powered recommendation engine
- ✨ Automated report generation
- ✨ Knowledge base with 4 collections
- ✨ Bilingual prompt templates
- ✨ Comprehensive health check endpoint

**Changed:**
- 🔄 Updated main.py to initialize AI services
- 🔄 Enhanced health check with AI service status
- 🔄 Version bump: 4.0.0 → 4.1.0

**Technical:**
- 📦 LLM: DeepSeek-R1:14b (8.5GB)
- 📦 Embeddings: paraphrase-multilingual-mpnet-base-v2 (768-dim)
- 📦 Vector DB: Qdrant (cosine similarity)
- 📦 Framework: FastAPI + AsyncIO

---

## 🤝 Contributing

Phase 4B is complete. Future enhancements:

- [ ] Add caching layer (Redis)
- [ ] Implement user authentication
- [ ] Add Grafana dashboards
- [ ] Support more LLM models
- [ ] Add voice interface
- [ ] Mobile app integration

---

## 📄 License

Assembly Time-Tracking System - Internal Use Only

---

**Phase 4B Complete** ✅
**Next:** Phase 4C - Advanced Analytics (Optional)
