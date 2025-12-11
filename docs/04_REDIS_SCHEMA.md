# Redis Caching Strategy Design

## 🔍 Overview

**Redis** is used as a high-performance in-memory cache for real-time tracking data, reducing PostgreSQL load and enabling sub-millisecond response times.

### Configuration
- **Redis Version**: 7.x Alpine
- **Persistence**: RDB snapshots + AOF (Append-Only File)
- **Memory**: 4GB allocated
- **Eviction Policy**: `allkeys-lru` (Least Recently Used)
- **Max Connections**: 10000
- **Default TTL**: Varies by data type (see below)

---

## 📊 Data Structure Architecture

```
Redis Instance (Memory: 4GB)
    │
    ├── Active Sessions (Hash)           - TTL: 8 hours
    ├── Zone Configurations (Hash)       - TTL: 24 hours
    ├── Worker-Track Mapping (Hash)      - TTL: 4 hours
    ├── Index State (String + Hash)      - TTL: 24 hours
    ├── Zone Occupancy (Set + Sorted Set)- TTL: 1 hour
    ├── Camera Status (Hash)             - TTL: 10 minutes
    ├── Recent Embeddings (String)       - TTL: 1 hour
    ├── Alert Queue (List)               - No TTL (FIFO)
    └── Rate Limiting (String)           - TTL: 60 seconds
```

---

## 📋 Key Naming Convention

```
Pattern: {namespace}:{entity}:{id}:{field}

Examples:
- session:active:W001_Z01_123456789
- zone:config:Z01
- worker:track:1
- index:current
- occupancy:zone:Z01
- camera:status:CAM01
- embedding:cache:abc123...
- alert:queue
- ratelimit:api:192.168.1.100
```

---

## 📋 Data Structure Definitions

### 1. Active Sessions (Hash)

**Purpose**: Store real-time tracking sessions (worker in zone)

**Key Pattern**: `session:active:{session_id}`

**TTL**: 8 hours (auto-expire after work shift)

```python
# Structure
session_id = "W001_Z01_20250115_083542"
key = f"session:active:{session_id}"

data = {
    "session_id": "W001_Z01_20250115_083542",
    "worker_id": "W001",
    "zone_id": "Z01",
    "track_id": "1",
    "entry_time": "2025-01-15T08:35:42+07:00",
    "exit_time": None,                      # NULL if still active
    "total_active_seconds": "2400",         # String for Redis
    "total_idle_seconds": "180",
    "index_number": "3",
    "state": "active",                      # "active", "idle", "exited"
    "last_motion_time": "2025-01-15T09:15:22+07:00",
    "motion_score": "0.85",
    "bbox": '{"x": 100, "y": 200, "w": 80, "h": 180}',  # JSON string
    "updated_at": "2025-01-15T09:15:30+07:00"
}

# Redis commands
redis.hset(f"session:active:{session_id}", mapping=data)
redis.expire(f"session:active:{session_id}", 28800)  # 8 hours

# Retrieve
session = redis.hgetall(f"session:active:{session_id}")

# Update specific field
redis.hset(f"session:active:{session_id}", "total_active_seconds", "2460")
redis.hset(f"session:active:{session_id}", "updated_at", current_timestamp)

# Delete on exit
redis.delete(f"session:active:{session_id}")
```

**Indexes** (using additional keys):
```python
# Track all active sessions globally
redis.sadd("sessions:active:all", session_id)

# Track sessions by worker
redis.sadd(f"sessions:active:worker:{worker_id}", session_id)

# Track sessions by zone
redis.sadd(f"sessions:active:zone:{zone_id}", session_id)

# Get all active sessions
all_sessions = redis.smembers("sessions:active:all")

# Get sessions for specific worker
worker_sessions = redis.smembers(f"sessions:active:worker:{worker_id}")
```

---

### 2. Zone Configurations (Hash)

**Purpose**: Cache zone polygon coordinates and properties for fast point-in-polygon checks

**Key Pattern**: `zone:config:{zone_id}`

**TTL**: 24 hours (or until config changes)

```python
# Structure
zone_id = "Z01"
key = f"zone:config:{zone_id}"

data = {
    "zone_id": "Z01",
    "camera_id": "CAM01",
    "name": "Assembly Station 1",
    "polygon_coords": "[[100,200],[500,200],[500,800],[100,800]]",  # JSON string
    "zone_type": "work_area",
    "color": "#00FF00",
    "min_workers": "1",
    "max_workers": "3",
    "alert_on_empty": "1",      # Boolean as string
    "alert_on_overflow": "1",
    "active": "1"
}

# Redis commands
redis.hset(f"zone:config:{zone_id}", mapping=data)
redis.expire(f"zone:config:{zone_id}", 86400)  # 24 hours

# Retrieve
zone_config = redis.hgetall(f"zone:config:{zone_id}")

# Get all zones for a camera
redis.keys("zone:config:*")  # Not recommended for production
# Better: Use a set to track zone IDs
redis.sadd(f"camera:zones:{camera_id}", zone_id)
camera_zones = redis.smembers(f"camera:zones:{camera_id}")
```

---

### 3. Worker-Track Mapping (Hash)

**Purpose**: Map tracker IDs to identified workers for re-identification

**Key Pattern**: `worker:track:{track_id}` or `track:worker:{worker_id}`

**TTL**: 4 hours (reset if worker leaves and re-enters)

```python
# Track ID → Worker ID mapping
track_id = 1
redis.hset(f"worker:track:{track_id}", mapping={
    "worker_id": "W001",
    "confidence": "0.95",       # Face recognition confidence
    "last_seen": "2025-01-15T09:20:00+07:00",
    "zone_id": "Z01",
    "camera_id": "CAM01"
})
redis.expire(f"worker:track:{track_id}", 14400)  # 4 hours

# Worker ID → Track ID mapping (reverse lookup)
redis.set(f"track:worker:W001", "1", ex=14400)

# Check if track is already mapped
mapped_worker = redis.hget(f"worker:track:{track_id}", "worker_id")
if not mapped_worker:
    # Perform face recognition
    worker_id = identify_worker(frame, bbox)
    redis.hset(f"worker:track:{track_id}", "worker_id", worker_id)
```

---

### 4. Index State (String + Hash)

**Purpose**: Track current index number and schedule

**Key Pattern**: `index:current`, `index:schedule:{date}`

**TTL**: 24 hours (reset at midnight)

```python
# Current index number (atomic operations)
redis.set("index:current", "3", ex=86400)
redis.incr("index:current")  # Atomically increment to 4
current_index = int(redis.get("index:current"))

# Index schedule for today
date = "2025-01-15"
schedule_data = {
    "date": "2025-01-15",
    "index_1_start": "08:00:00",
    "index_1_end": "08:57:00",
    "index_2_start": "08:57:00",
    "index_2_end": "09:54:00",
    "index_3_start": "09:54:00",
    "index_3_end": "10:36:00",  # Includes break
    "break1_start": "10:00:00",
    "break1_end": "10:15:00",
    # ... up to index_11
    "current_state": "active"  # "active", "break", "ended"
}
redis.hset(f"index:schedule:{date}", mapping=schedule_data)
redis.expire(f"index:schedule:{date}", 86400)

# Get current index schedule
schedule = redis.hgetall(f"index:schedule:{date}")
```

---

### 5. Zone Occupancy (Set + Sorted Set)

**Purpose**: Track which workers are currently in each zone (real-time)

**Key Pattern**: `occupancy:zone:{zone_id}`, `occupancy:zone:{zone_id}:sorted`

**TTL**: 1 hour (refreshed on every update)

```python
# Set: Simple list of worker IDs in zone
zone_id = "Z01"
redis.sadd(f"occupancy:zone:{zone_id}", "W001", "W003", "W007")
redis.expire(f"occupancy:zone:{zone_id}", 3600)

# Get count of workers in zone
worker_count = redis.scard(f"occupancy:zone:{zone_id}")

# Check if specific worker is in zone
is_present = redis.sismember(f"occupancy:zone:{zone_id}", "W001")

# Remove worker from zone (on exit)
redis.srem(f"occupancy:zone:{zone_id}", "W001")

# Sorted Set: Workers sorted by entry time (for analytics)
entry_time = time.time()
redis.zadd(f"occupancy:zone:{zone_id}:sorted", {
    "W001": entry_time,
    "W003": entry_time + 60,
    "W007": entry_time + 120
})

# Get workers sorted by entry time
workers = redis.zrange(f"occupancy:zone:{zone_id}:sorted", 0, -1, withscores=True)
# Returns: [('W001', 1705295742.0), ('W003', 1705295802.0), ...]
```

---

### 6. Camera Status (Hash)

**Purpose**: Monitor camera health (connection, FPS, last frame)

**Key Pattern**: `camera:status:{camera_id}`

**TTL**: 10 minutes (refreshed every frame)

```python
camera_id = "CAM01"
redis.hset(f"camera:status:{camera_id}", mapping={
    "camera_id": "CAM01",
    "status": "active",         # "active", "reconnecting", "error"
    "fps": "29.5",
    "resolution": "1920x1080",
    "last_frame_time": "2025-01-15T09:30:45.123+07:00",
    "frames_captured": "15420",
    "frames_dropped": "12",
    "reconnect_count": "0",
    "error_message": None
})
redis.expire(f"camera:status:{camera_id}", 600)  # 10 minutes

# Watchdog checks
for camera_id in ["CAM01", "CAM02", "CAM03", "CAM04"]:
    status = redis.hgetall(f"camera:status:{camera_id}")
    if not status:
        alert("Camera {camera_id} is offline (no heartbeat)")
    else:
        last_frame = datetime.fromisoformat(status['last_frame_time'])
        if (datetime.now() - last_frame).seconds > 30:
            alert("Camera {camera_id} frozen (no new frames)")
```

---

### 7. Recent Embeddings Cache (String)

**Purpose**: Cache recently generated text embeddings to avoid re-computation

**Key Pattern**: `embedding:cache:{text_hash}`

**TTL**: 1 hour

```python
import hashlib

# Generate hash of input text
query_text = "ทำไมสถานี Z01 ช้ากว่าปกติ"
text_hash = hashlib.md5(query_text.encode()).hexdigest()

# Check cache
cached_embedding = redis.get(f"embedding:cache:{text_hash}")
if cached_embedding:
    # Deserialize
    import pickle
    embedding = pickle.loads(cached_embedding)
else:
    # Generate new embedding
    embedding = embedding_model.encode(query_text)
    # Cache it
    redis.set(
        f"embedding:cache:{text_hash}",
        pickle.dumps(embedding),
        ex=3600  # 1 hour
    )
```

---

### 8. Alert Queue (List)

**Purpose**: FIFO queue for real-time alerts (consumed by notification service)

**Key Pattern**: `alert:queue`

**TTL**: None (persistent until consumed)

```python
# Push alert to queue (producer)
alert_data = {
    "timestamp": "2025-01-15T10:05:00+07:00",
    "alert_type": "idle_threshold",
    "severity": "warning",
    "zone_id": "Z01",
    "worker_id": "W001",
    "message": "Worker W001 idle for >60 seconds in Zone Z01"
}
import json
redis.rpush("alert:queue", json.dumps(alert_data))

# Consume alerts (consumer - notification service)
while True:
    # Blocking pop (waits up to 5 seconds for new alert)
    result = redis.blpop("alert:queue", timeout=5)
    if result:
        queue_name, alert_json = result
        alert = json.loads(alert_json)
        send_notification(alert)

# Check queue length
queue_length = redis.llen("alert:queue")
```

---

### 9. Rate Limiting (String)

**Purpose**: API rate limiting (prevent abuse)

**Key Pattern**: `ratelimit:api:{client_ip}` or `ratelimit:user:{user_id}`

**TTL**: 60 seconds (sliding window)

```python
# Fixed window rate limiting (100 requests per minute)
client_ip = "192.168.1.100"
key = f"ratelimit:api:{client_ip}"

# Increment request count
request_count = redis.incr(key)
if request_count == 1:
    redis.expire(key, 60)  # Set TTL on first request

# Check limit
if request_count > 100:
    return {"error": "Rate limit exceeded"}, 429

# Sliding window rate limiting (more accurate)
import time
key = f"ratelimit:api:{client_ip}:requests"
current_time = time.time()

# Add current request timestamp
redis.zadd(key, {str(current_time): current_time})

# Remove timestamps older than 60 seconds
redis.zremrangebyscore(key, 0, current_time - 60)

# Count requests in last 60 seconds
request_count = redis.zcard(key)
if request_count > 100:
    return {"error": "Rate limit exceeded"}, 429

# Set TTL
redis.expire(key, 60)
```

---

## 🔄 Cache Invalidation Strategies

### 1. Time-Based Expiration (TTL)
```python
# Automatically expire after set time
redis.setex("session:active:123", 28800, session_data)  # 8 hours
```

### 2. Event-Driven Invalidation
```python
# Invalidate cache when zone config changes
def update_zone_config(zone_id, new_config):
    # Update database
    db.update_zone(zone_id, new_config)

    # Invalidate Redis cache
    redis.delete(f"zone:config:{zone_id}")

    # Optionally pre-warm cache
    redis.hset(f"zone:config:{zone_id}", mapping=new_config)
    redis.expire(f"zone:config:{zone_id}", 86400)
```

### 3. Lazy Loading Pattern
```python
def get_zone_config(zone_id):
    # Try cache first
    cached = redis.hgetall(f"zone:config:{zone_id}")
    if cached:
        return cached

    # Cache miss: Load from database
    zone_config = db.get_zone(zone_id)

    # Populate cache
    redis.hset(f"zone:config:{zone_id}", mapping=zone_config)
    redis.expire(f"zone:config:{zone_id}", 86400)

    return zone_config
```

---

## 📈 Performance Optimization

### 1. Pipelining (Batch Commands)
```python
# Inefficient: Multiple round-trips
for session_id in session_ids:
    redis.hgetall(f"session:active:{session_id}")

# Efficient: Single round-trip
pipe = redis.pipeline()
for session_id in session_ids:
    pipe.hgetall(f"session:active:{session_id}")
results = pipe.execute()
```

### 2. Connection Pooling
```python
import redis

# Create connection pool (reuse connections)
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,
    decode_responses=True
)
redis_client = redis.Redis(connection_pool=pool)
```

### 3. Pub/Sub for Real-time Updates
```python
# Publisher (time tracker)
def notify_zone_update(zone_id, worker_count):
    message = {"zone_id": zone_id, "worker_count": worker_count}
    redis.publish(f"zone:updates:{zone_id}", json.dumps(message))

# Subscriber (UI thread)
pubsub = redis.pubsub()
pubsub.subscribe("zone:updates:*")

for message in pubsub.listen():
    if message['type'] == 'message':
        data = json.loads(message['data'])
        update_ui(data['zone_id'], data['worker_count'])
```

---

## 🔐 Security

### 1. Password Protection
```bash
# In docker-compose.yml
environment:
  - REDIS_PASSWORD=your_secure_password_here

# In application
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    password='your_secure_password_here'
)
```

### 2. Disable Dangerous Commands
```bash
# In redis.conf
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG "CONFIG_abc123"  # Require secret suffix
```

---

## 🔄 Persistence Configuration

```bash
# redis.conf

# RDB Snapshots (point-in-time backups)
save 900 1      # Save if 1 key changed in 15 minutes
save 300 10     # Save if 10 keys changed in 5 minutes
save 60 10000   # Save if 10000 keys changed in 1 minute

# AOF (Append-Only File - more durable)
appendonly yes
appendfsync everysec  # Fsync every second (good balance)

# AOF rewrite (compact log file)
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
```

---

## 📊 Monitoring & Debugging

### 1. Memory Usage
```bash
# Check memory stats
redis-cli INFO memory

# Check key counts by pattern
redis-cli --scan --pattern 'session:active:*' | wc -l

# Find largest keys
redis-cli --bigkeys

# Get key size
redis-cli MEMORY USAGE "session:active:W001_Z01_123"
```

### 2. Slow Log
```bash
# Enable slow log (queries >10ms)
redis-cli CONFIG SET slowlog-log-slower-than 10000

# View slow queries
redis-cli SLOWLOG GET 10
```

### 3. Client Connections
```bash
# List connected clients
redis-cli CLIENT LIST

# Monitor real-time commands
redis-cli MONITOR
```

---

## 🔄 Backup & Recovery

```bash
# Manual backup (RDB snapshot)
redis-cli BGSAVE

# Copy snapshot file
cp /var/lib/redis/dump.rdb /backups/redis_backup_$(date +%Y%m%d).rdb

# Restore (stop Redis, replace dump.rdb, restart)
systemctl stop redis
cp /backups/redis_backup_20250115.rdb /var/lib/redis/dump.rdb
systemctl start redis

# Export all data (if migrating)
redis-cli --rdb /backups/dump.rdb
```

---

## 📋 Usage Examples in Python

```python
# src/data/redis_manager.py

import redis
import json
from datetime import datetime, timedelta

class RedisManager:
    def __init__(self):
        self.pool = redis.ConnectionPool(
            host='localhost',
            port=6379,
            max_connections=50,
            decode_responses=True
        )
        self.client = redis.Redis(connection_pool=self.pool)

    # ========== Active Sessions ==========
    def create_session(self, worker_id, zone_id, track_id):
        """Create new tracking session"""
        session_id = f"{worker_id}_{zone_id}_{int(datetime.now().timestamp())}"
        data = {
            "session_id": session_id,
            "worker_id": worker_id,
            "zone_id": zone_id,
            "track_id": str(track_id),
            "entry_time": datetime.now().isoformat(),
            "total_active_seconds": "0",
            "total_idle_seconds": "0",
            "index_number": str(self.get_current_index()),
            "state": "active",
            "updated_at": datetime.now().isoformat()
        }

        # Store session
        self.client.hset(f"session:active:{session_id}", mapping=data)
        self.client.expire(f"session:active:{session_id}", 28800)  # 8h TTL

        # Add to indexes
        self.client.sadd("sessions:active:all", session_id)
        self.client.sadd(f"sessions:active:worker:{worker_id}", session_id)
        self.client.sadd(f"sessions:active:zone:{zone_id}", session_id)

        # Update zone occupancy
        self.client.sadd(f"occupancy:zone:{zone_id}", worker_id)
        self.client.expire(f"occupancy:zone:{zone_id}", 3600)

        return session_id

    def update_session(self, session_id, active_seconds=None, idle_seconds=None, state=None):
        """Update session metrics"""
        updates = {"updated_at": datetime.now().isoformat()}
        if active_seconds is not None:
            updates["total_active_seconds"] = str(active_seconds)
        if idle_seconds is not None:
            updates["total_idle_seconds"] = str(idle_seconds)
        if state:
            updates["state"] = state

        self.client.hset(f"session:active:{session_id}", mapping=updates)

    def get_session(self, session_id):
        """Get session data"""
        return self.client.hgetall(f"session:active:{session_id}")

    def close_session(self, session_id):
        """Close session (worker exited zone)"""
        session = self.get_session(session_id)
        if not session:
            return

        # Update exit time
        self.client.hset(f"session:active:{session_id}", "exit_time", datetime.now().isoformat())
        self.client.hset(f"session:active:{session_id}", "state", "exited")

        # Remove from indexes
        self.client.srem("sessions:active:all", session_id)
        self.client.srem(f"sessions:active:worker:{session['worker_id']}", session_id)
        self.client.srem(f"sessions:active:zone:{session['zone_id']}", session_id)

        # Update zone occupancy
        self.client.srem(f"occupancy:zone:{session['zone_id']}", session['worker_id'])

        # Persist to PostgreSQL (async)
        # ... (delegate to DB writer thread)

    # ========== Zone Configuration ==========
    def get_zone_config(self, zone_id):
        """Get zone configuration (with cache)"""
        cached = self.client.hgetall(f"zone:config:{zone_id}")
        if cached:
            return cached

        # Cache miss: Load from database
        from data.postgres_manager import PostgresManager
        db = PostgresManager()
        zone = db.get_zone(zone_id)

        if zone:
            # Populate cache
            cache_data = {
                "zone_id": zone['zone_id'],
                "camera_id": zone['camera_id'],
                "name": zone['name'],
                "polygon_coords": json.dumps(zone['polygon_coords']),
                "zone_type": zone['zone_type'],
                "color": zone['color'],
                "min_workers": str(zone['min_workers']),
                "max_workers": str(zone['max_workers'])
            }
            self.client.hset(f"zone:config:{zone_id}", mapping=cache_data)
            self.client.expire(f"zone:config:{zone_id}", 86400)

        return zone

    # ========== Index Management ==========
    def get_current_index(self):
        """Get current index number"""
        index = self.client.get("index:current")
        return int(index) if index else 1

    def set_current_index(self, index_number):
        """Set current index number"""
        self.client.set("index:current", str(index_number), ex=86400)

    # ========== Zone Occupancy ==========
    def get_zone_occupancy(self, zone_id):
        """Get current workers in zone"""
        workers = self.client.smembers(f"occupancy:zone:{zone_id}")
        return len(workers), workers

    # ========== Alerts ==========
    def push_alert(self, alert_data):
        """Add alert to queue"""
        self.client.rpush("alert:queue", json.dumps(alert_data))

    def pop_alert(self, timeout=5):
        """Get next alert from queue (blocking)"""
        result = self.client.blpop("alert:queue", timeout=timeout)
        if result:
            _, alert_json = result
            return json.loads(alert_json)
        return None
```

---

## ✅ Redis Schema Design Complete

### Summary
- ✅ **9 Data Types**: sessions, zones, workers, index, occupancy, cameras, embeddings, alerts, rate-limiting
- ✅ **TTL Strategy**: Automatic expiration (8h sessions, 24h configs, 1h cache)
- ✅ **Indexing**: Sets for fast lookups, sorted sets for time-ordered data
- ✅ **Pub/Sub**: Real-time event notifications
- ✅ **Persistence**: RDB + AOF for durability
- ✅ **Performance**: Connection pooling, pipelining, lazy loading

Next: RAG + DeepSeek-R1 Integration Design →
