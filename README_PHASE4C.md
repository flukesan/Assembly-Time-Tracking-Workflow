# Phase 4C: Advanced Analytics

## 📋 Overview

Phase 4C extends the Assembly Time-Tracking System with **Advanced Analytics** capabilities including real-time streaming, predictive forecasting, interactive visualizations, performance benchmarking, and data export.

### Version: 4.2.0

---

## 🎯 Key Features

1. **Real-time Analytics** - WebSocket streaming for live updates
2. **Predictive Analytics** - Time-series forecasting and trend analysis
3. **Advanced Visualizations** - Heatmaps, charts, and interactive data
4. **Performance Benchmarking** - Compare against standards and peers
5. **Data Export** - Export to JSON, CSV, and formatted reports

---

## 🏗️ Architecture

```
Phase 4C Components:

├─ Real-time Analytics (WebSocket)
│  ├─ Event broadcasting
│  ├─ Metrics streaming
│  └─ Connection management
│
├─ Predictive Analytics
│  ├─ Time-series forecasting
│  ├─ Trend analysis
│  └─ Anomaly prediction
│
├─ Visualization Data
│  ├─ Heatmap generators
│  ├─ Chart data formatters
│  ├─ Distribution analysis
│  └─ Correlation matrices
│
├─ Benchmarking
│  ├─ Standard comparisons
│  ├─ Historical analysis
│  ├─ Peer ranking
│  └─ Consistency analysis
│
└─ Export Manager
   ├─ JSON export
   ├─ CSV export
   └─ Text reports
```

---

## 📡 API Endpoints

### Real-time Analytics

**WebSocket Endpoints:**
```
ws://localhost:8000/ws/analytics
  - Full analytics stream with event filtering
  - Commands: ping, get_metrics, get_history, get_stats

ws://localhost:8000/ws/live-metrics
  - Simplified metrics updates (2-second intervals)
```

**REST Endpoints:**
```
GET  /api/v1/analytics/metrics
GET  /api/v1/analytics/stats
GET  /api/v1/analytics/history?event_type=alert&limit=50
GET  /api/v1/analytics/connections
POST /api/v1/analytics/test-event
```

### Predictive Analytics

```
POST /api/v1/analytics/predict/productivity
  - Forecast productivity trends (1-30 days)
  - Exponential smoothing with confidence intervals

POST /api/v1/analytics/predict/output
  - Forecast production output
  - Moving average with trend

POST /api/v1/analytics/analyze/trend
  - Linear regression trend analysis
  - R² goodness-of-fit
  - 7-day และ 30-day predictions

POST /api/v1/analytics/predict/anomaly
  - Anomaly probability detection
  - Z-score analysis

POST /api/v1/analytics/predict/worker-performance
  - Comprehensive performance forecast
  - Multi-metric predictions
```

### Visualization Data

```
POST /api/v1/analytics/visualize/heatmap
  - Productivity heatmaps (2D matrix)
  - Axes: hour/day/week vs worker/zone/shift

POST /api/v1/analytics/visualize/time-series
  - Multi-series time-series data
  - Aggregation: mean, sum, count, min, max

POST /api/v1/analytics/visualize/distribution
  - Histogram data with statistics
  - Configurable bins (5-50)

POST /api/v1/analytics/visualize/correlation
  - Correlation matrices
  - Pearson coefficients

POST /api/v1/analytics/visualize/comparison
  - Bar chart data
  - Group-by aggregation

GET  /api/v1/analytics/visualize/gauge
  - Gauge chart data
  - Threshold-based coloring
```

### Benchmarking

```
POST /api/v1/analytics/benchmark/compare
  - Compare to standard benchmarks
  - Performance levels: excellent/good/average/below_average/poor

POST /api/v1/analytics/benchmark/historical
  - Compare to historical data
  - Periods: all, recent_7days, recent_30days
```

### Export

```
POST /api/v1/analytics/export/json
  - Export data to JSON format
  - Pretty print option

POST /api/v1/analytics/export/csv
  - Export data to CSV format
  - Column selection
```

---

## 🚀 Quick Start

### 1. Start Services

```bash
docker compose -f docker-compose.cpu.yml up -d
```

### 2. Test WebSocket Connection

```javascript
// Browser JavaScript
const ws = new WebSocket('ws://localhost:8000/ws/analytics');

ws.onopen = () => {
  console.log('Connected to analytics stream');
  ws.send('get_metrics');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### 3. Forecast Productivity

```bash
curl -X POST http://localhost:8000/api/v1/analytics/predict/productivity \
  -H "Content-Type: application/json" \
  -d '{
    "historical_data": [75, 78, 80, 77, 82, 85, 83],
    "forecast_days": 7
  }'
```

### 4. Generate Heatmap Data

```bash
curl -X POST http://localhost:8000/api/v1/analytics/visualize/heatmap \
  -H "Content-Type: application/json" \
  -d '{
    "data": [...],
    "x_axis": "hour",
    "y_axis": "worker",
    "value_field": "productivity"
  }'
```

---

## 📊 Real-time Events

### Event Types

1. **worker_status** - Worker status changes
   ```json
   {
     "event_type": "worker_status",
     "timestamp": "2025-12-14T10:30:00Z",
     "data": {
       "worker_id": "W001",
       "worker_name": "นายสมชาย",
       "status": "active",
       "current_zone": "Assembly Line 1",
       "productivity": 85.5
     }
   }
   ```

2. **productivity_update** - Productivity updates
3. **zone_transition** - Zone changes
4. **alert** - System alerts
5. **system_status** - System health
6. **metrics_snapshot** - Metrics overview

### WebSocket Commands

```javascript
// Send commands to WebSocket
ws.send('ping');              // Ping-pong
ws.send('get_metrics');       // Current metrics
ws.send('get_history:alert:10');  // Last 10 alerts
ws.send('get_stats');         // Analytics statistics
```

---

## 📈 Predictive Models

### 1. Exponential Smoothing
- **Used for:** Productivity forecasting
- **Alpha:** 0.3 (smoothing parameter)
- **Output:** Forecast + trend + 95% confidence intervals

### 2. Moving Average with Trend
- **Used for:** Output forecasting
- **Window:** 7 days (configurable)
- **Output:** Predicted values + margins

### 3. Linear Regression
- **Used for:** Trend analysis
- **Output:** Slope, intercept, R²
- **Trend detection:** increasing/decreasing/stable

### 4. Z-Score Analysis
- **Used for:** Anomaly detection
- **Threshold:** 2.0 standard deviations
- **Output:** Probability, severity, deviation %

---

## 📊 Visualization Examples

### Heatmap Usage
```python
# Productivity by hour and worker
data = [
  {"timestamp": datetime(...), "worker": "W001", "productivity": 85},
  {"timestamp": datetime(...), "worker": "W002", "productivity": 78},
  ...
]

result = visualize_heatmap(
  data=data,
  x_axis="hour",      # 0-23
  y_axis="worker",    # W001, W002, ...
  value_field="productivity"
)
# Returns: {x_labels, y_labels, values (2D matrix)}
```

### Time-Series Usage
```python
# Multi-metric over time
result = visualize_time_series(
  data=productivity_records,
  time_field="timestamp",
  value_fields=["productivity", "efficiency", "output"],
  aggregation="mean",
  interval="hour"
)
# Returns: {timestamps, series: {productivity: [...], efficiency: [...], ...}}
```

---

## 🎯 Benchmarking Examples

### Compare to Standard
```python
result = benchmark.compare_to_benchmark(
  current_value=82.5,
  metric_name="productivity",
  benchmark_value=75.0  # Default if not specified
)
# Returns: {
#   current_value: 82.5,
#   benchmark_value: 75.0,
#   difference: +7.5,
#   difference_percent: +10.0,
#   performance_level: "good"
# }
```

### Compare to Peers
```python
result = benchmark.compare_to_peers(
  worker_value=85.0,
  peer_values=[78, 80, 72, 88, 82, 75],
  worker_name="นายสมชาย"
)
# Returns: {
#   rank: 2,
#   total_workers: 7,
#   percentile: 71.4,
#   category: "top_25_percent",
#   peer_mean: 79.2,
#   ...
# }
```

---

## 💾 Data Export

### JSON Export
```bash
curl -X POST http://localhost:8000/api/v1/analytics/export/json \
  -H "Content-Type: application/json" \
  -d '{"data": {...}, "pretty": true}'

# Returns:
{
  "filename": "export_20251214_103000.json",
  "content_type": "application/json",
  "content": "{...}",
  "size_bytes": 1234,
  "generated_at": "2025-12-14T10:30:00Z"
}
```

### CSV Export
```bash
curl -X POST http://localhost:8000/api/v1/analytics/export/csv \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"worker": "W001", "productivity": 85, "efficiency": 78},
      {"worker": "W002", "productivity": 80, "efficiency": 75}
    ],
    "columns": ["worker", "productivity", "efficiency"]
  }'
```

---

## 🛠️ Configuration

### Default Benchmarks
```python
# In src/analytics/benchmarking.py
default_benchmarks = {
    "productivity": 75.0,
    "efficiency": 70.0,
    "quality": 85.0,
    "output_per_hour": 10.0
}
```

### Real-time Analytics
```python
# Event history size
max_history = 100  # Keep last 100 events

# WebSocket timeout
timeout = 30.0  # seconds
```

### Predictive Analytics
```python
# Minimum data points for forecasting
min_data_points = 5

# Exponential smoothing alpha
alpha = 0.3

# Confidence level
confidence_level = 0.95  # 95%
```

---

## 📚 Use Cases

### 1. Live Dashboard
```javascript
// Real-time productivity dashboard
const ws = new WebSocket('ws://localhost:8000/ws/analytics');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.event_type === 'productivity_update') {
    updateDashboard(data.data);
  }
};
```

### 2. Performance Forecasting
```bash
# Predict next week's performance
curl -X POST /api/v1/analytics/predict/worker-performance \
  -d '{"worker_id": "W001", "worker_history": [...], "forecast_days": 7}'
```

### 3. Trend Detection
```bash
# Analyze productivity trend
curl -X POST /api/v1/analytics/analyze/trend \
  -d '{"time_series_data": [75, 78, 80, 82, 85, 87], "data_type": "productivity"}'
```

### 4. Alert System
```javascript
// Subscribe to alerts only
const ws = new WebSocket('ws://localhost:8000/ws/analytics?event_types=alert');
ws.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  if (alert.severity === 'critical') {
    notifyAdmin(alert);
  }
};
```

---

## 🔐 Best Practices

1. **WebSocket Connections**
   - Implement reconnection logic
   - Handle ping/pong for keep-alive
   - Filter events to reduce bandwidth

2. **Predictive Analytics**
   - Minimum 5-7 data points for reliable forecasts
   - Use appropriate aggregation methods
   - Consider seasonal patterns

3. **Visualization**
   - Limit data points for large datasets
   - Use appropriate time intervals
   - Cache generated chart data

4. **Benchmarking**
   - Update benchmarks quarterly
   - Use peer groups of similar size
   - Consider context (shift, season, etc.)

5. **Export**
   - Paginate large exports
   - Compress large files
   - Clean sensitive data before export

---

## 📝 Changelog

### Version 4.2.0 (Phase 4C) - 2025-12-14

**Added:**
- ✨ Real-time Analytics with WebSocket streaming
- ✨ Predictive Analytics (forecasting, trend analysis)
- ✨ Advanced Visualization Data generators
- ✨ Performance Benchmarking engine
- ✨ Data Export system (JSON/CSV)
- ✨ 6 chart types (heatmap, time-series, distribution, correlation, comparison, gauge)
- ✨ 4 forecasting methods
- ✨ 5 benchmark comparison types
- ✨ WebSocket event filtering and commands

**Technical:**
- 📦 Real-time: Event queue, broadcast loop, connection tracking
- 📦 Predictive: Exponential smoothing, moving average, linear regression, Z-score
- 📦 Visualization: Numpy-based calculations, multi-format support
- 📦 Benchmarking: Historical/peer/standard comparisons
- 📦 Export: JSON/CSV with metadata

---

## 🎓 Example Workflow

### Complete Analytics Pipeline

```bash
# 1. Start real-time monitoring
wscat -c ws://localhost:8000/ws/analytics

# 2. Get current metrics
curl http://localhost:8000/api/v1/analytics/metrics

# 3. Analyze trends
curl -X POST http://localhost:8000/api/v1/analytics/analyze/trend \
  -H "Content-Type: application/json" \
  -d '{"time_series_data": [70, 72, 75, 78, 80, 82, 85]}'

# 4. Forecast next week
curl -X POST http://localhost:8000/api/v1/analytics/predict/productivity \
  -H "Content-Type: application/json" \
  -d '{"historical_data": [70, 72, 75, 78, 80, 82, 85], "forecast_days": 7}'

# 5. Generate visualization
curl -X POST http://localhost:8000/api/v1/analytics/visualize/time-series \
  -H "Content-Type: application/json" \
  -d '{"data": [...], "interval": "day"}'

# 6. Compare performance
curl -X POST http://localhost:8000/api/v1/analytics/benchmark/compare \
  -H "Content-Type: application/json" \
  -d '{"current_value": 85, "metric_name": "productivity"}'

# 7. Export results
curl -X POST http://localhost:8000/api/v1/analytics/export/csv \
  -H "Content-Type: application/json" \
  -d '{"data": [...]}'
```

---

## 🤝 Integration

Phase 4C integrates with:
- **Phase 4**: Worker tracking data
- **Phase 4B**: AI insights and reports
- **Frontend Dashboards**: Real-time updates via WebSocket
- **External Analytics**: Export data for Tableau/PowerBI
- **Monitoring Systems**: Alert webhooks

---

**Phase 4C Complete** ✅
**Total Phases:** 4A ✅ + 4B ✅ + 4C ✅
**System Version:** 4.2.0
