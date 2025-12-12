# 🔧 GPU Error - Quick Fix Guide

## ❌ Error ที่พบ
```
nvidia-container-cli: initialization error: load library failed:
libnvidia-ml.so.1: cannot open shared object file: no such file or directory
```

## ✅ แก้ไขทันที - ใช้ CPU Mode แทน GPU

### Step 1: Stop services ที่รันอยู่

```bash
# Stop และลบ containers
docker compose down

# หรือถ้ายังไม่ได้ start ก็ข้ามไปได้
```

### Step 2: ใช้ docker-compose.cpu.yml แทน

```bash
# Start services ด้วย CPU mode
docker compose -f docker-compose.cpu.yml up -d --build

# ดู logs
docker compose -f docker-compose.cpu.yml logs -f
```

### Step 3: Verify

```bash
# Check containers
docker compose -f docker-compose.cpu.yml ps

# Test API
curl http://localhost:8000/

# Test health
curl http://localhost:8000/health
```

---

## 🎯 ความแตกต่างระหว่าง GPU mode vs CPU mode

### GPU Mode (docker-compose.yml)
- ✅ **Faster**: YOLO inference ~20ms
- ✅ **Better**: LLM inference ~2-3s
- ⚠️ **Requires**: NVIDIA GPU + Driver + NVIDIA Docker
- 💰 **Hardware**: RTX 4090, A5000 (แพง)

### CPU Mode (docker-compose.cpu.yml)
- ⚠️ **Slower**: YOLO inference ~200-500ms
- ⚠️ **Slower**: LLM inference ~10-30s
- ✅ **Works**: ทุกเครื่องที่มี Docker
- ✅ **Good for**: Development, Testing, Debugging
- 💰 **Hardware**: เครื่องปกติก็ใช้ได้

---

## 📊 สำหรับ Phase 1 (Foundation Testing)

**CPU mode เพียงพอแล้ว!** เพราะเรายังไม่ได้ใช้:
- ❌ ยังไม่มี Camera detection (Phase 2)
- ❌ ยังไม่มี YOLO inference (Phase 2)
- ❌ ยังไม่มี LLM queries (Phase 5)

**Phase 1 ทดสอบแค่:**
- ✅ Docker services start
- ✅ Database connection
- ✅ API responds
- ✅ Health checks

---

## 🔄 เปลี่ยนกลับไป GPU mode (เมื่อพร้อม)

### เมื่อติดตั้ง NVIDIA driver + NVIDIA Docker เรียบร้อยแล้ว:

```bash
# Stop CPU mode
docker compose -f docker-compose.cpu.yml down

# Start GPU mode
docker compose up -d --build

# Verify GPU
docker exec -it assembly_ollama nvidia-smi
```

---

## 🛠️ วิธีติดตั้ง NVIDIA Driver (ถ้าต้องการใช้ GPU ในอนาคต)

### Ubuntu 22.04

```bash
# 1. Check if you have NVIDIA GPU
lspci | grep -i nvidia

# 2. Install NVIDIA Driver
sudo apt update
sudo apt install -y nvidia-driver-535

# 3. Reboot
sudo reboot

# 4. Verify
nvidia-smi

# 5. Install NVIDIA Docker
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt update
sudo apt install -y nvidia-docker2
sudo systemctl restart docker

# 6. Test
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

---

## ✅ ตอนนี้ทำอย่างนี้

```bash
# 1. ใช้ CPU mode
docker compose -f docker-compose.cpu.yml up -d --build

# 2. ดู logs (รอ 30-60 วินาที)
docker compose -f docker-compose.cpu.yml logs -f

# 3. Test API
curl http://localhost:8000/

# 4. ถ้าทำงาน = Phase 1 สำเร็จ! 🎉
```

---

## 💡 คำแนะนำ

**สำหรับ Development/Testing:**
- ใช้ **CPU mode** (docker-compose.cpu.yml)
- เร็วพอสำหรับ debug และทดสอบ
- ไม่ต้องมี GPU ราคาแพง

**สำหรับ Production:**
- ใช้ **GPU mode** (docker-compose.yml)
- จำเป็นต้องมี NVIDIA GPU
- ประมวลผลเร็วกว่า 10-20 เท่า

---

## 📞 Need Help?

ถ้ายังมีปัญหา:

```bash
# 1. Check Docker version
docker --version

# 2. Check system
uname -a

# 3. Check GPU (if any)
lspci | grep -i nvidia

# 4. Share error logs
docker compose -f docker-compose.cpu.yml logs > error.log
```

แล้วส่ง error.log มาดูครับ
