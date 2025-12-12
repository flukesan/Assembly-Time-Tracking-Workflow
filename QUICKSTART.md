# 🚀 Quick Start - Phase 1

## ⚡ เริ่มใช้งานภายใน 3 นาที!

### 1️⃣ Clone & Setup

```bash
cd Assembly-Time-Tracking-Workflow
cp .env.example .env
```

### 2️⃣ Start Services (CPU Mode)

```bash
# Clean start
docker compose -f docker-compose.cpu.yml down -v
docker compose -f docker-compose.cpu.yml up -d --build
```

### 3️⃣ Wait & Watch

```bash
# ดู logs (รอ 60-90 วินาที)
docker compose -f docker-compose.cpu.yml logs -f

# กด Ctrl+C เมื่อเห็น "started successfully"
```

### 4️⃣ Verify

```bash
# Test API (รอจนกว่า containers พร้อม)
curl http://localhost:8000/

# Expected: {"message": "Assembly Time-Tracking System", ...}
```

---

## ✅ Success Criteria

```bash
# All containers running
docker compose -f docker-compose.cpu.yml ps

# Expected: 5 containers (Up/healthy)
# assembly_postgres    Up (healthy)
# assembly_qdrant      Up (healthy)
# assembly_redis       Up (healthy)
# assembly_ollama      Up
# assembly_app         Up
```

---

## 🐛 Common Issues

### Issue 1: "Qdrant is unhealthy"

**Solution:** รอให้นานขึ้น (up to 90 seconds)

```bash
# Watch Qdrant logs
docker logs assembly_qdrant -f

# Wait until you see: "Qdrant gRPC listening on..."
```

### Issue 2: "Port already in use"

```bash
# Find process
sudo lsof -i :8000
sudo lsof -i :5432
sudo lsof -i :6333

# Kill if needed
sudo kill -9 <PID>

# Or use different ports
export APP_PORT=8001
export POSTGRES_PORT=5433
export QDRANT_HTTP_PORT=6334
```

### Issue 3: "Permission denied" on data folders

```bash
# Fix permissions
sudo chown -R $USER:$USER data/
chmod -R 755 data/
```

---

## 🔄 Fresh Restart

```bash
# Complete cleanup
docker compose -f docker-compose.cpu.yml down -v
sudo rm -rf data/postgres data/qdrant data/redis data/ollama

# Start fresh
docker compose -f docker-compose.cpu.yml up -d --build
```

---

## 📊 Check Individual Services

```bash
# PostgreSQL
docker exec -it assembly_postgres psql -U assembly_user -d assembly_tracking -c "SELECT COUNT(*) FROM workers;"

# Qdrant
curl http://localhost:6333/health

# Redis
docker exec -it assembly_redis redis-cli -a change_me_redis_password PING

# Ollama (optional)
curl http://localhost:11434/api/tags

# App
curl http://localhost:8000/health
```

---

## 🎯 What's Next?

เมื่อทุก service รันสำเร็จ:

✅ Phase 1 Complete! → Ready for Phase 2 (Camera + Detection)

---

## 💡 Tips

- **First time:** อาจใช้เวลา 2-3 นาที เพราะต้อง download images
- **Qdrant:** อาจใช้เวลา 40-60 วินาทีจึงจะ healthy
- **Ollama:** ไม่จำเป็นสำหรับ Phase 1 (ข้ามไปก่อนได้)
- **Logs:** ดูได้ด้วย `docker compose -f docker-compose.cpu.yml logs -f [service_name]`

---

## 📞 Still Having Issues?

```bash
# Get all logs
docker compose -f docker-compose.cpu.yml logs > debug.log

# Share debug.log for help
```

**Expected Timeline:**
- Pulling images: 1-2 min (first time only)
- Starting containers: 30 sec
- Health checks: 30-60 sec
- **Total: ~2-3 min** ⏱️
