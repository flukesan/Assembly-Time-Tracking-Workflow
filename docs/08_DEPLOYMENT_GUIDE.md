# Deployment Guide - Step-by-Step Installation

## 🎯 Prerequisites

### Hardware Requirements
- **CPU**: 16+ cores (Intel Xeon / AMD EPYC)
- **RAM**: 64GB DDR4
- **GPU**: NVIDIA RTX 4090 or A5000 (24GB VRAM)
- **Storage**:
  - 500GB SSD (OS + Applications)
  - 2TB+ HDD (Video archives, backups)
  - 256GB NVMe (Qdrant index, PostgreSQL)
- **Network**: 10 Gbps Ethernet

### Software Requirements
- **OS**: Ubuntu 22.04 LTS (recommended) or Ubuntu 20.04 LTS
- **NVIDIA Driver**: 535.x or newer
- **CUDA**: 12.2 or newer
- **Docker**: 24.x or newer
- **Docker Compose**: v2.x or newer

---

## 📦 Step 1: System Preparation

### 1.1 Update System
```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y build-essential curl wget git vim htop
```

### 1.2 Install NVIDIA Driver + CUDA
```bash
# Check if NVIDIA GPU is detected
lspci | grep -i nvidia

# Install NVIDIA Driver
sudo apt install -y nvidia-driver-535

# Reboot
sudo reboot

# Verify installation
nvidia-smi

# Expected output:
# +---------------------------------------------------------------------------------------+
# | NVIDIA-SMI 535.xxx      Driver Version: 535.xxx      CUDA Version: 12.2             |
# |-----------------------------------------+----------------------+----------------------+
# | GPU  Name                   ...         | Bus-Id        ...    | GPU Temp  ...        |
# |=========================================+======================+======================|
# |   0  NVIDIA GeForce RTX 4090  ...       | 00:01:00.0    ...    |  45°C     ...        |
# +---------------------------------------------------------------------------------------+
```

### 1.3 Install Docker
```bash
# Uninstall old versions
sudo apt remove docker docker-engine docker.io containerd runc

# Install dependencies
sudo apt install -y ca-certificates gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify
docker --version
# Docker version 24.x.x

docker compose version
# Docker Compose version v2.x.x

# Add current user to docker group
sudo usermod -aG docker $USER

# Re-login to apply group changes
exit
# (login again)

# Test Docker
docker run hello-world
```

### 1.4 Install NVIDIA Container Toolkit
```bash
# Add NVIDIA package repositories
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-docker2
sudo apt update
sudo apt install -y nvidia-docker2

# Restart Docker daemon
sudo systemctl restart docker

# Test GPU access in Docker
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# Expected: nvidia-smi output inside container
```

---

## 📁 Step 2: Clone Repository

```bash
# Create project directory
mkdir -p ~/projects
cd ~/projects

# Clone repository
git clone https://github.com/your-org/Assembly-Time-Tracking-Workflow.git
cd Assembly-Time-Tracking-Workflow

# Check structure
ls -la
# Should see: docs/, src/, config/, docker-compose.yml, requirements.txt, README.md
```

---

## 🐳 Step 3: Docker Compose Setup

### 3.1 Create docker-compose.yml

```bash
cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  # PostgreSQL + TimescaleDB
  postgresql:
    image: timescale/timescaledb:latest-pg15
    container_name: assembly_postgres
    environment:
      POSTGRES_DB: assembly_tracking
      POSTGRES_USER: assembly_user
      POSTGRES_PASSWORD: change_me_in_production
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "5432:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./init-scripts/postgres:/docker-entrypoint-initdb.d
    networks:
      - app-network
    restart: unless-stopped

  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:latest
    container_name: assembly_qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./data/qdrant:/qdrant/storage
    environment:
      QDRANT__SERVICE__HTTP_PORT: 6333
      QDRANT__SERVICE__GRPC_PORT: 6334
    networks:
      - app-network
    restart: unless-stopped

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: assembly_redis
    command: redis-server --appendonly yes --requirepass change_me_redis_password
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    networks:
      - app-network
    restart: unless-stopped

  # Ollama (DeepSeek-R1:14B)
  ollama:
    image: ollama/ollama:latest
    container_name: assembly_ollama
    ports:
      - "11434:11434"
    volumes:
      - ./data/ollama:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - app-network
    restart: unless-stopped

  # Main Application (build from source)
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: assembly_app
    depends_on:
      - postgresql
      - qdrant
      - redis
      - ollama
    environment:
      # Database
      - POSTGRES_HOST=postgresql
      - POSTGRES_PORT=5432
      - POSTGRES_DB=assembly_tracking
      - POSTGRES_USER=assembly_user
      - POSTGRES_PASSWORD=change_me_in_production
      # Qdrant
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      # Redis
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=change_me_redis_password
      # Ollama
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=deepseek-r1:14b
      # Application
      - LOG_LEVEL=INFO
      - PYTHONUNBUFFERED=1
    ports:
      - "8000:8000"  # FastAPI
      - "8080:8080"  # PyQt6 VNC (optional)
    volumes:
      - ./src:/app/src
      - ./config:/app/config
      - ./logs:/app/logs
      - ./data/recordings:/app/data/recordings
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - app-network
    restart: unless-stopped

networks:
  app-network:
    driver: bridge
EOF
```

### 3.2 Create Dockerfile

```bash
cat > Dockerfile <<'EOF'
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3-dev \
    build-essential \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Expose ports
EXPOSE 8000

# Start application
CMD ["python3", "src/main.py"]
EOF
```

### 3.3 Create requirements.txt

```bash
cat > requirements.txt <<'EOF'
# Core
python==3.11

# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
websockets==12.0

# Database
psycopg2-binary==2.9.9
sqlalchemy==2.0.25
asyncpg==0.29.0
redis==5.0.1

# AI/ML
torch==2.1.2
torchvision==0.16.2
ultralytics==8.1.0  # YOLOv8
opencv-python==4.9.0.80
sentence-transformers==2.3.1
qdrant-client==1.7.3

# OCR
easyocr==1.7.0
pytesseract==0.3.10

# LLM
requests==2.31.0
langdetect==1.0.9

# UI
PyQt6==6.6.1
PyQt6-WebEngine==6.6.0
pyqtgraph==0.13.3

# Utilities
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.5.3
python-dotenv==1.0.1
pyyaml==6.0.1
pillow==10.2.0
numpy==1.26.3
pandas==2.1.4

# Monitoring
prometheus-client==0.19.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
EOF
```

---

## 🚀 Step 4: Initialize Services

### 4.1 Create Data Directories

```bash
# Create directory structure
mkdir -p data/{postgres,qdrant,redis,ollama,recordings}
mkdir -p logs
mkdir -p init-scripts/postgres

# Set permissions
chmod -R 755 data/
chmod -R 755 logs/
```

### 4.2 Create PostgreSQL Init Script

```bash
cat > init-scripts/postgres/01_init_schema.sql <<'EOF'
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create tables (paste schema from 02_DATABASE_SCHEMA.md)
-- ... (full schema from previous design doc)

-- Create indexes
CREATE INDEX idx_time_logs_worker_time ON time_logs(worker_id, timestamp DESC);
CREATE INDEX idx_time_logs_zone_time ON time_logs(zone_id, timestamp DESC);
-- ... (all other indexes)

-- Convert to hypertable
SELECT create_hypertable('time_logs', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Add retention policy
SELECT add_retention_policy('time_logs', INTERVAL '90 days');
EOF
```

### 4.3 Start Services

```bash
# Build and start all services
docker compose up -d --build

# Check status
docker compose ps

# Expected output:
# NAME                  STATUS          PORTS
# assembly_postgres     Up 30 seconds   0.0.0.0:5432->5432/tcp
# assembly_qdrant       Up 30 seconds   0.0.0.0:6333->6333/tcp
# assembly_redis        Up 30 seconds   0.0.0.0:6379->6379/tcp
# assembly_ollama       Up 30 seconds   0.0.0.0:11434->11434/tcp
# assembly_app          Up 15 seconds   0.0.0.0:8000->8000/tcp

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

---

## 🤖 Step 5: Pull DeepSeek-R1 Model

```bash
# Enter Ollama container
docker exec -it assembly_ollama bash

# Pull model (inside container)
ollama pull deepseek-r1:14b

# This will download ~8GB
# Downloading 100% |████████████████| 8.2 GB/8.2 GB

# Verify
ollama list

# Expected:
# NAME              ID              SIZE     MODIFIED
# deepseek-r1:14b   abc123def456    8.2 GB   2 minutes ago

# Test
ollama run deepseek-r1:14b "สวัสดี ทดสอบภาษาไทย"

# Expected: Response in Thai

# Exit container
exit
```

---

## 🔧 Step 6: Configuration

### 6.1 Camera Configuration

```bash
cat > config/camera_config.yaml <<'EOF'
cameras:
  - camera_id: CAM01
    name: "Station 1 Overhead"
    type: rtsp
    rtsp_url: "rtsp://192.168.1.100:554/stream1"
    username: "admin"
    password: "camera_password"
    resolution: "1920x1080"
    fps: 30
    enabled: true

  - camera_id: CAM02
    name: "Station 2 Side View"
    type: rtsp
    rtsp_url: "rtsp://192.168.1.101:554/stream1"
    username: "admin"
    password: "camera_password"
    resolution: "1920x1080"
    fps: 30
    enabled: true

  - camera_id: CAM03
    name: "Station 3 Overhead"
    type: usb
    device: "/dev/video0"
    resolution: "1920x1080"
    fps: 30
    enabled: true

  - camera_id: CAM04
    name: "Inspection Area"
    type: rtsp
    rtsp_url: "rtsp://192.168.1.103:554/stream1"
    username: "admin"
    password: "camera_password"
    resolution: "1920x1080"
    fps: 30
    enabled: true
EOF
```

### 6.2 Schedule Configuration

```bash
cat > config/schedule_config.yaml <<'EOF'
default_schedule:
  work_start_time: "08:00"
  work_end_time: "17:00"
  break1_start: "10:00"
  break1_duration: 15  # minutes
  break2_start: "15:00"
  break2_duration: 15  # minutes
  total_indices: 11
  index_duration: 57  # minutes (auto-calculated)
EOF
```

---

## ✅ Step 7: Verification

### 7.1 Check All Services

```bash
# Health check endpoint
curl http://localhost:8000/health

# Expected:
# {
#   "status": "healthy",
#   "components": {
#     "postgresql": "healthy",
#     "qdrant": "healthy",
#     "redis": "healthy",
#     "ollama": "healthy"
#   }
# }
```

### 7.2 Test PostgreSQL

```bash
# Connect to PostgreSQL
docker exec -it assembly_postgres psql -U assembly_user -d assembly_tracking

# Run test query
SELECT COUNT(*) FROM workers;

# Exit
\q
```

### 7.3 Test Qdrant

```bash
# Check Qdrant health
curl http://localhost:6333/health

# Expected: {"status": "ok"}

# List collections
curl http://localhost:6333/collections

# Expected: {"result": {"collections": []}}
```

### 7.4 Test Ollama

```bash
# Test DeepSeek-R1 inference
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1:14b",
    "messages": [{"role": "user", "content": "สวัสดี"}],
    "stream": false
  }'

# Expected: JSON response with Thai text
```

---

## 🎯 Step 8: First Run

### 8.1 Start Application

```bash
# Start all services
docker compose up -d

# View application logs
docker compose logs -f app

# Expected logs:
# [INFO] Loading configuration...
# [INFO] Connecting to PostgreSQL...
# [INFO] Connecting to Qdrant...
# [INFO] Connecting to Redis...
# [INFO] Loading YOLOv8 model...
# [INFO] Starting camera threads...
# [INFO] Starting FastAPI server on 0.0.0.0:8000
# [INFO] System ready!
```

### 8.2 Access UI

```bash
# If running on local machine
# Open browser: http://localhost:8000

# If running on remote server
# Open browser: http://YOUR_SERVER_IP:8000

# Expected: PyQt6 application or web interface
```

---

## 🔒 Step 9: Production Hardening

### 9.1 Change Default Passwords

```bash
# Edit docker-compose.yml
# Change:
# - POSTGRES_PASSWORD
# - REDIS_PASSWORD
# - Camera passwords in config/camera_config.yaml

# Regenerate
docker compose down
docker compose up -d
```

### 9.2 Enable HTTPS

```bash
# Install certbot
sudo apt install certbot

# Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com

# Update docker-compose.yml to use SSL
# Add nginx reverse proxy (recommended)
```

### 9.3 Setup Firewall

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # Application
sudo ufw allow 443/tcp   # HTTPS (if using)
sudo ufw enable

# Check status
sudo ufw status
```

---

## 📊 Step 10: Monitoring Setup (Optional)

### 10.1 Install Prometheus + Grafana

```bash
# Add to docker-compose.yml
# (Prometheus + Grafana services)

# Access Grafana: http://localhost:3000
# Default: admin / admin
```

---

## 🔄 Maintenance Commands

```bash
# View logs
docker compose logs -f [service_name]

# Restart service
docker compose restart [service_name]

# Update application
git pull
docker compose up -d --build app

# Backup database
docker exec assembly_postgres pg_dump -U assembly_user assembly_tracking > backup_$(date +%Y%m%d).sql

# Restore database
docker exec -i assembly_postgres psql -U assembly_user assembly_tracking < backup_20250115.sql

# Clean up old data
docker system prune -a
```

---

## ✅ Deployment Complete!

System is now running and ready for use. Access at:
- **Main UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

Next: Testing Strategy →
