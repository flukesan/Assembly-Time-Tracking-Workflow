# Phase 1: Foundation Setup - Testing Guide

## ✅ สิ่งที่สร้างเสร็จแล้วใน Phase 1

### 1. Project Structure
```
assembly-time-tracking/
├── src/                    # Source code
│   ├── camera/
│   ├── ai/
│   ├── core/
│   ├── data/
│   ├── rag/
│   ├── api/
│   ├── ui/
│   └── main.py            # ✅ Entry point
├── config/
│   └── config.yaml         # ✅ Configuration
├── scripts/
│   └── init-db/
│       ├── 01_init_schema.sql   # ✅ Database schema
│       └── 02_seed_data.sql     # ✅ Sample data
├── docker-compose.yml      # ✅ Docker services
├── Dockerfile              # ✅ App container
├── requirements.txt        # ✅ Python dependencies
├── .env.example            # ✅ Environment template
└── .gitignore              # ✅ Git ignore rules
```

### 2. Docker Services
- ✅ PostgreSQL + TimescaleDB
- ✅ Qdrant Vector Database
- ✅ Redis Cache
- ✅ Ollama (DeepSeek-R1:14B)
- ✅ Application Container (FastAPI)

### 3. Database Schema
- ✅ 11 tables created
- ✅ TimescaleDB hypertable (time_logs)
- ✅ Indexes optimized
- ✅ Sample data seeded

---

## 🚀 การทดสอบ Phase 1

### ขั้นตอนที่ 1: Setup Environment

```bash
# 1. Clone repository (ถ้ายังไม่ได้ทำ)
git clone https://github.com/your-org/Assembly-Time-Tracking-Workflow.git
cd Assembly-Time-Tracking-Workflow

# 2. สร้าง .env file
cp .env.example .env

# 3. แก้ไข .env (optional - ใช้ค่า default ก็ได้)
nano .env
```

### ขั้นตอนที่ 2: Start All Services

**⚠️ สำคัญ: เลือก mode ที่เหมาะสม**

#### Option A: GPU Mode (ถ้ามี NVIDIA GPU + Driver)

```bash
# Start with GPU support
docker compose up -d --build

# ดู logs
docker compose logs -f
```

#### Option B: CPU Mode (แนะนำสำหรับ Testing/Development)

```bash
# Start with CPU only (ไม่ต้องมี GPU)
docker compose -f docker-compose.cpu.yml up -d --build

# ดู logs
docker compose -f docker-compose.cpu.yml logs -f
```

**💡 คำแนะนำ:**
- ถ้าเจอ error `libnvidia-ml.so.1: cannot open shared object file` → ใช้ **CPU Mode**
- Phase 1 ทดสอบได้ทั้ง GPU และ CPU mode
- CPU mode เพียงพอสำหรับ Phase 1-3 (Foundation + Detection + Zone)

**ดู logs แยก service:**
```bash
# สำหรับ CPU mode (เพิ่ม -f docker-compose.cpu.yml)
docker compose -f docker-compose.cpu.yml logs -f app
docker compose -f docker-compose.cpu.yml logs -f postgresql

# สำหรับ GPU mode (ปกติ)
docker compose logs -f app
docker compose logs -f postgresql
```

### ขั้นตอนที่ 3: Verify Services

#### ✅ 3.1 Check Container Status

```bash
docker compose ps

# Expected output:
# NAME                  STATUS          PORTS
# assembly_postgres     Up 30 seconds   0.0.0.0:5432->5432/tcp
# assembly_qdrant       Up 30 seconds   0.0.0.0:6333->6333/tcp
# assembly_redis        Up 30 seconds   0.0.0.0:6379->6379/tcp
# assembly_ollama       Up 30 seconds   0.0.0.0:11434->11434/tcp
# assembly_app          Up 15 seconds   0.0.0.0:8000->8000/tcp
```

#### ✅ 3.2 Test Application API

```bash
# Test root endpoint
curl http://localhost:8000/

# Expected:
# {
#   "message": "Assembly Time-Tracking System",
#   "version": "1.0.0",
#   "status": "running",
#   "phase": "Phase 1 - Foundation"
# }

# Test health check
curl http://localhost:8000/health

# Expected:
# {
#   "status": "healthy",
#   "phase": "Phase 1 - Foundation",
#   "components": {
#     "api": "healthy",
#     ...
#   }
# }
```

#### ✅ 3.3 Test PostgreSQL

```bash
# Connect to PostgreSQL
docker exec -it assembly_postgres psql -U assembly_user -d assembly_tracking

# Check tables
\dt

# Expected: List of 11 tables
# - workers
# - cameras
# - zones
# - time_logs
# - sessions
# - index_records
# - anomalies
# - alerts
# - schedules
# - zone_templates
# - system_logs

# Check sample data
SELECT COUNT(*) FROM workers;
# Expected: 5 rows

SELECT COUNT(*) FROM zones;
# Expected: 4 rows

# Exit
\q
```

#### ✅ 3.4 Test Qdrant

```bash
# Test Qdrant health
curl http://localhost:6333/health

# Expected: {"status": "ok"}

# List collections (should be empty for now)
curl http://localhost:6333/collections

# Expected: {"result": {"collections": []}}
```

#### ✅ 3.5 Test Redis

```bash
# Enter Redis CLI
docker exec -it assembly_redis redis-cli -a change_me_redis_password

# Test connection
PING
# Expected: PONG

# Test set/get
SET test_key "Hello from Redis"
GET test_key
# Expected: "Hello from Redis"

# Exit
EXIT
```

#### ✅ 3.6 Test Ollama (DeepSeek-R1)

```bash
# Enter Ollama container
docker exec -it assembly_ollama bash

# Pull DeepSeek-R1 model (ครั้งแรกอย่างเดียว)
ollama pull deepseek-r1:14b

# This will download ~8GB (อาจใช้เวลา 10-30 นาที)
# Expected: Download progress bar

# Verify model
ollama list

# Expected:
# NAME              ID              SIZE
# deepseek-r1:14b   abc123def456    8.2 GB

# Test inference (ภาษาไทย)
ollama run deepseek-r1:14b "สวัสดี วันนี้เป็นอย่างไรบ้าง"

# Expected: Thai response

# Exit
exit
```

---

## 🎯 Success Criteria สำหรับ Phase 1

### ทดสอบผ่านหมดทุกข้อแล้ว = Phase 1 สำเร็จ!

- [x] ✅ All 5 Docker containers running
- [x] ✅ FastAPI responds at http://localhost:8000
- [x] ✅ PostgreSQL has 11 tables + sample data
- [x] ✅ Qdrant is accessible (empty collections OK)
- [x] ✅ Redis is accessible
- [x] ✅ Ollama has deepseek-r1:14b model downloaded

---

## 🐛 Troubleshooting

### ปัญหา: Container ไม่สามารถ start ได้

```bash
# ดู error logs
docker compose logs [service_name]

# Restart service
docker compose restart [service_name]

# Rebuild and restart
docker compose up -d --build [service_name]
```

### ปัญหา: PostgreSQL connection failed

```bash
# Check PostgreSQL logs
docker compose logs postgresql

# Verify port is open
netstat -tuln | grep 5432

# Try manual connection
docker exec -it assembly_postgres pg_isready -U assembly_user
```

### ปัญหา: Ollama model download ช้า/ล้มเหลว

```bash
# Enter Ollama container
docker exec -it assembly_ollama bash

# Check storage space
df -h

# Retry download
ollama pull deepseek-r1:14b

# If failed, try smaller model for testing
ollama pull deepseek-r1:7b
```

### ปัญหา: GPU not detected

```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# If failed, reinstall nvidia-docker2
sudo apt install nvidia-docker2
sudo systemctl restart docker
```

---

## 🔄 Cleanup Commands

```bash
# Stop all services
docker compose down

# Stop and remove volumes (ลบข้อมูลทั้งหมด)
docker compose down -v

# Remove all images
docker compose down --rmi all

# Complete cleanup
docker compose down -v --rmi all
rm -rf data/postgres data/qdrant data/redis data/ollama
```

---

## ✅ ถ้าทดสอบผ่านหมดแล้ว

**Phase 1 เสร็จสมบูรณ์!** 🎉

**ขั้นตอนถัดไป:**
- Phase 2: Single Camera + Detection (YOLOv8)
- Phase 3: Zone Management
- Phase 4: Tracking
- และต่อไปเรื่อยๆ

---

## 📞 Need Help?

ถ้าพบปัญหา:
1. ดู logs: `docker compose logs -f`
2. Check health: `curl http://localhost:8000/health`
3. Verify containers: `docker compose ps`

ติดต่อ support หรือ open issue ใน GitHub repository
