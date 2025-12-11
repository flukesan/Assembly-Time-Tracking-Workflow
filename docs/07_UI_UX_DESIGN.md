# UI/UX Design - PyQt6 Desktop Application

## 🎨 Overview

Desktop application built with PyQt6 for real-time monitoring and control.

### Design Principles
- **Minimal Clicks**: Common tasks accessible in ≤2 clicks
- **Real-time Updates**: 10 FPS UI refresh, instant alerts
- **Bilingual**: Thai + English UI (switchable)
- **Dark/Light Theme**: Support both modes
- **Responsive**: Adapts to different screen sizes (1920x1080 minimum)

---

## 🖼️ Main Window Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Assembly Time Tracking System               [−][□][×]    [👤 Admin ▾] │
├─────────────────────────────────────────────────────────────────────────┤
│  [File] [Camera] [Zone] [Schedule] [Analytics] [Settings] [Help]       │
├──────────────────────────────────────┬──────────────────────────────────┤
│                                      │  ┌─── Right Sidebar (320px) ───┐ │
│   ┌─── Status Bar ────────────────┐ │  │  📊 Live Statistics         │ │
│   │ Index: 5/11 │Workers: 20/25 │ │  │                              │ │
│   │ GPU: 85%    │Alerts: 3 🔴   │ │  │  Zone Z01: 2 workers (92%)  │ │
│   └──────────────────────────────── │  │  Zone Z02: 1 worker  (85%)  │ │
│                                      │  │  Zone Z03: 3 workers (95%)  │ │
│   ┌─── Camera Grid (2x2) ────────┐  │  │  Zone Z04: 0 workers ⚠️     │ │
│   │                              │  │  │                              │ │
│   │  ┌─────────┬─────────┐       │  │  ├─────────────────────────────┤ │
│   │  │ CAM01   │ CAM02   │       │  │  │  🚨 Active Alerts (3)       │ │
│   │  │ Zone Z01│ Zone Z02│       │  │  │                              │ │
│   │  │ 👤👤    │ 👤      │       │  │  │  [🔴] Z04 Empty (5 min)    │ │
│   │  │ [92%]   │ [85%]   │       │  │  │  [🟡] W005 Idle (90s)      │ │
│   │  ├─────────┼─────────┤       │  │  │  [🟡] Z02 Low (1 worker)   │ │
│   │  │ CAM03   │ CAM04   │       │  │  │                              │ │
│   │  │ Zone Z03│ Zone Z04│       │  │  │  [Acknowledge All]           │ │
│   │  │ 👤👤👤  │ (empty) │       │  │  │                              │ │
│   │  │ [95%]   │ ⚠️      │       │  │  ├─────────────────────────────┤ │
│   │  └─────────┴─────────┘       │  │  │  ⏱️ Index Progress          │ │
│   │                              │  │  │                              │ │
│   │  ● REC                       │  │  │  Index 5/11                  │ │
│   └──────────────────────────────┘  │  │  [█████████░░░░░] 65%       │ │
│                                      │  │  Time left: 20:15            │ │
│   ┌─── Chat Interface (RAG) ────┐  │  │  Next: Break 1 (10:00)       │ │
│   │  User: ทำไม Z01 ช้า?        │  │  │                              │ │
│   │  Claude: กำลังวิเคราะห์... │  │  │  [Start] [Pause] [Skip]      │ │
│   │  [Thinking...]              │  │  │                              │ │
│   │  [Send]                     │  │  └──────────────────────────────┘ │
│   └──────────────────────────────┘  │                                  │
└──────────────────────────────────────┴──────────────────────────────────┘
```

**Dimensions**:
- Main Window: 1920x1080 (minimum)
- Camera Grid: 1600x900 (resizable)
- Right Sidebar: 320px (fixed)
- Status Bar: 40px (top)

---

## 📐 Screen Layouts

### 1. Monitoring View (Default)
- **Camera Grid**: 2x2 layout with live feeds
- **Zone Overlays**: Colored polygons on each camera
- **Worker Indicators**: Icons/names on detected persons
- **Metrics**: Real-time productivity percentages
- **Right Sidebar**: Statistics, alerts, index progress

### 2. Zone Editor View
```
┌─────────────────────────────────────────────────────────────────┐
│  Zone Configuration - CAM01                        [Save] [Cancel]│
├─────────────────────────────────────────────────────────────────┤
│  ┌─── Camera Feed (Static) ──────────────────┐  ┌─ Properties ─┐│
│  │                                            │  │ Zone ID:     ││
│  │   [Camera frame with drawing canvas]      │  │ Z01          ││
│  │                                            │  │              ││
│  │   [Drawn polygon with draggable points]   │  │ Name:        ││
│  │                                            │  │ Station 1    ││
│  │                                            │  │              ││
│  │                                            │  │ Color:       ││
│  │                                            │  │ [🟢] Green   ││
│  │                                            │  │              ││
│  │   Tools: [✏️ Draw] [🗑️ Delete] [↶ Undo]   │  │ Type:        ││
│  │         [📐 Snap] [📋 Template]           │  │ work_area ▾  ││
│  │                                            │  │              ││
│  └────────────────────────────────────────────┘  │ Min Workers: ││
│                                                   │ [1]          ││
│  Existing Zones:                                 │ Max Workers: ││
│  ☑ Z01: Assembly Station 1 (🟢)                 │ [3]          ││
│  ☑ Z02: Assembly Station 2 (🔵)                 │              ││
│  ☐ Z03: Inspection Area (🔴)                    │ [Apply]      ││
│                                                   └──────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 3. Analytics Dashboard
```
┌─────────────────────────────────────────────────────────────────┐
│  Analytics Dashboard                         [Today ▾] [Export]  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─ Overview ──────────────────────────────────────────────────┐│
│  │ Total Active Time: 200h    Productivity: 89%   Indices: 11  ││
│  │ Total Idle Time: 25h       Workers: 25          Alerts: 12  ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌─ Productivity Chart (Line) ─────────┐ ┌─ Zone Comparison ───┐│
│  │ 100%│                   ╱─╲          │ │ Z01 ████████ 92%   ││
│  │  90%│         ╱─╲      ╱   ╲         │ │ Z02 ██████░░ 85%   ││
│  │  80%│   ╱─╲  ╱   ╲────╯     ╲╱─╲     │ │ Z03 █████████ 95%  ││
│  │  70%│  ╱   ╲╱                    ╲    │ │ Z04 ████░░░░ 78%   ││
│  │     └───────────────────────────────  │ └─────────────────────┘│
│  │     8AM  10AM  12PM  2PM  4PM         │                        │
│  └───────────────────────────────────────┘ ┌─ Top Performers ───┐│
│                                             │ 1. W001 (96%)      ││
│  ┌─ Anomalies Timeline ──────────────────┐ │ 2. W003 (94%)      ││
│  │ 10:15 [🔴] Z02: High idle              │ │ 3. W007 (93%)      ││
│  │ 11:30 [🟡] Z04: Empty zone             │ │ 4. W012 (92%)      ││
│  │ 14:20 [🟡] W005: Idle >60s             │ │ 5. W015 (91%)      ││
│  └─────────────────────────────────────────┘ └─────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 4. Schedule Configuration
```
┌─────────────────────────────────────────────────────────────────┐
│  Work Schedule Configuration                      [Save] [Cancel]│
├─────────────────────────────────────────────────────────────────┤
│  Date: [2025-01-15] ▾              Total Indices: [11]           │
│                                                                   │
│  Work Hours:                       Break Times:                  │
│  Start: [08:00] ▾                  Break 1: [10:00] ▾ [15] min   │
│  End:   [17:00] ▾                  Break 2: [15:00] ▾ [15] min   │
│                                                                   │
│  ┌─ Index Timeline Preview ───────────────────────────────────┐ │
│  │ Index 1:  08:00 - 08:57 (57 min)                           │ │
│  │ Index 2:  08:57 - 09:54 (57 min)                           │ │
│  │ Index 3:  09:54 - 10:00 (6 min) → BREAK 1 (10:00-10:15)   │ │
│  │          10:15 - 10:36 (21 min) ← Resume                   │ │
│  │ Index 4:  10:36 - 11:33 (57 min)                           │ │
│  │ ...                                                         │ │
│  │ Index 11: 16:03 - 17:00 (57 min)                           │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  [Auto-calculate] [Load Template] [Save as Template]             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Component Library

### 1. Camera View Widget
```python
class CameraViewWidget(QWidget):
    """
    Single camera view with zone overlays

    Features:
    - Live video feed (30 FPS)
    - Zone polygon overlays (semi-transparent)
    - Worker bounding boxes
    - Worker ID labels
    - Productivity indicator
    - Recording indicator
    """
```

### 2. Zone Statistics Panel
```python
class ZoneStatsPanel(QWidget):
    """
    Real-time zone statistics

    Displays:
    - Zone name
    - Worker count (current/max)
    - Productivity percentage
    - Active/idle workers list
    - Status indicator (normal/warning/critical)
    """
```

### 3. Alert Widget
```python
class AlertWidget(QWidget):
    """
    Alert notification item

    Features:
    - Severity icon (🔴/🟡/🔵)
    - Alert message
    - Timestamp
    - Acknowledge button
    - Auto-dismiss (optional)
    """
```

### 4. RAG Chat Interface
```python
class RAGChatWidget(QWidget):
    """
    Chat interface for RAG queries

    Features:
    - Message history
    - Typing indicator
    - Reasoning chain (collapsible)
    - Source citations (clickable)
    - Copy response button
    - Language selector (TH/EN)
    """
```

---

## 🎨 Color Scheme

### Dark Theme (Default)
```python
COLORS = {
    'background': '#1E1E1E',
    'surface': '#2D2D2D',
    'primary': '#00A3E0',
    'secondary': '#6C757D',
    'success': '#28A745',
    'warning': '#FFC107',
    'danger': '#DC3545',
    'text_primary': '#FFFFFF',
    'text_secondary': '#B0B0B0',
    'border': '#404040'
}
```

### Light Theme
```python
COLORS = {
    'background': '#FFFFFF',
    'surface': '#F5F5F5',
    'primary': '#0078D4',
    'secondary': '#6C757D',
    'success': '#28A745',
    'warning': '#FFC107',
    'danger': '#DC3545',
    'text_primary': '#000000',
    'text_secondary': '#6C757D',
    'border': '#CCCCCC'
}
```

### Zone Colors
```python
ZONE_COLORS = [
    '#00FF00',  # Green
    '#0000FF',  # Blue
    '#FF0000',  # Red
    '#FFFF00',  # Yellow
    '#FF00FF',  # Magenta
    '#00FFFF',  # Cyan
]
```

---

## 🔔 Notification System

### Toast Notifications
- **Position**: Bottom-right corner
- **Duration**: 5 seconds (dismissible)
- **Types**: Info, Success, Warning, Error

```python
# Example
show_toast(
    title="Zone Alert",
    message="Zone Z04 has been empty for 5 minutes",
    severity="warning",
    duration=5000
)
```

### Alert Panel
- **Position**: Right sidebar (top)
- **Features**:
  - List of active alerts
  - Color-coded by severity
  - Acknowledge button
  - Auto-refresh

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `F11` | Toggle fullscreen |
| `Ctrl+M` | Switch to monitoring view |
| `Ctrl+Z` | Switch to zone editor |
| `Ctrl+A` | Switch to analytics |
| `Ctrl+S` | Save configuration |
| `Ctrl+Q` | Quit application |
| `Ctrl+R` | Refresh data |
| `Ctrl+/` | Open RAG chat |
| `Space` | Pause/resume tracking |
| `Esc` | Cancel current operation |

---

## 📱 Responsive Design

### Screen Sizes
- **Minimum**: 1920x1080 (Full HD)
- **Recommended**: 2560x1440 (2K)
- **Maximum**: 3840x2160 (4K)

### Adaptive Layouts
- **≥1920px**: 2x2 camera grid
- **1600-1920px**: 2x1 camera grid
- **1280-1600px**: 1x1 camera grid (fullscreen single camera)

---

## 🎯 User Workflows

### Workflow 1: Start Monitoring
1. Launch application
2. System auto-loads cameras
3. Default monitoring view displayed
4. Real-time updates start

### Workflow 2: Configure Zone
1. Click `Zone` → `Edit Zones`
2. Select camera
3. Draw polygon on frame
4. Set zone properties
5. Save configuration
6. Zone immediately active

### Workflow 3: Acknowledge Alert
1. Alert appears in sidebar
2. Click on alert
3. View details
4. Enter action taken
5. Click "Acknowledge"
6. Alert marked as resolved

### Workflow 4: Query RAG
1. Open chat panel (Ctrl+/)
2. Type question in Thai/English
3. Send query
4. View reasoning chain (collapsible)
5. Read answer with sources
6. Copy/export response

---

## ✅ UI/UX Design Complete

### Summary
- ✅ **5 Main Views**: Monitoring, Zone Editor, Analytics, Schedule, Settings
- ✅ **8+ Custom Widgets**: Camera view, stats panel, alerts, chat, charts
- ✅ **Dark/Light Theme**: Full theme support
- ✅ **Bilingual**: Thai + English UI
- ✅ **Responsive**: 1920x1080 minimum
- ✅ **Real-time**: 10 FPS updates
- ✅ **Keyboard Shortcuts**: 10+ shortcuts

Next: Deployment Guide →
