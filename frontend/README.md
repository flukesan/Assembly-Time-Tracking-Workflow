# Assembly Time-Tracking Dashboard

React + TypeScript frontend for the Assembly Time-Tracking System.

## Features

- 📊 **Real-time Dashboard** - Live metrics and worker status updates via WebSocket
- 👥 **Worker Management** - View and manage workers
- 📈 **Analytics & Visualizations** - Interactive charts and forecasts
- 📄 **Reports** - Generate and export reports
- 🔄 **Real-time Updates** - WebSocket integration for live data
- 🌐 **Bilingual Support** - Thai/English interface

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Zustand** - State management
- **React Router** - Routing
- **Recharts** - Charts (planned)
- **Axios** - HTTP client
- **date-fns** - Date utilities
- **Lucide React** - Icons

## Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Backend API running on http://localhost:8000

## Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Edit .env if needed
# VITE_API_URL=http://localhost:8000
# VITE_WS_URL=ws://localhost:8000
```

## Development

```bash
# Start development server
npm run dev

# Open browser to http://localhost:3000
```

The dev server includes:
- Hot Module Replacement (HMR)
- Auto proxy to backend API (/api → http://localhost:8000)
- WebSocket proxy (/ws → ws://localhost:8000)

## Building

```bash
# Type check
npm run type-check

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   │   ├── Layout.tsx
│   │   ├── MetricCard.tsx
│   │   ├── WorkerStatusCard.tsx
│   │   └── EventFeed.tsx
│   ├── pages/          # Page components
│   │   └── Dashboard.tsx
│   ├── hooks/          # Custom React hooks
│   │   └── useWebSocket.ts
│   ├── services/       # API clients
│   │   └── api.ts
│   ├── types/          # TypeScript types
│   │   └── api.ts
│   ├── utils/          # Utilities
│   │   ├── store.ts    # Zustand store
│   │   └── format.ts   # Formatting functions
│   ├── App.tsx         # App component
│   ├── main.tsx        # Entry point
│   └── index.css       # Global styles
├── public/             # Static assets
├── index.html          # HTML template
├── vite.config.ts      # Vite configuration
├── tailwind.config.js  # Tailwind configuration
└── package.json
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_WS_URL` | WebSocket URL | `ws://localhost:8000` |
| `VITE_APP_ENV` | Environment | `development` |

## Features Overview

### Dashboard (Part 2 - Current)

- **Metrics Cards**: Total workers, active workers, productivity, output
- **Active Workers List**: Real-time worker status with productivity scores
- **Event Feed**: Live stream of system events via WebSocket
- **Recent Activity**: Timeline of recent events

### Worker Management (Part 3 - Planned)

- Worker list with search/filter
- Worker registration form
- Worker detail view
- Time tracking history

### Analytics (Part 4 - Planned)

- Interactive charts (Recharts)
- Productivity heatmaps
- Trend analysis
- Predictive forecasts

### Reports (Part 5 - Planned)

- Report generation
- Date range filtering
- Export to JSON/CSV
- Print functionality

## API Integration

The frontend connects to the backend API:

```typescript
// Worker API
workerAPI.list()              // GET /api/v1/workers
workerAPI.get(id)             // GET /api/v1/workers/:id
workerAPI.create(worker)      // POST /api/v1/workers
workerAPI.update(id, worker)  // PUT /api/v1/workers/:id

// Analytics API
analyticsAPI.getMetrics()     // GET /api/v1/analytics/metrics
analyticsAPI.predictProductivity(data, days)
analyticsAPI.generateHeatmap(data, x, y, field)

// AI API
aiAPI.query(question)         // POST /api/v1/ai/query
aiAPI.analyzeWorker(id)       // POST /api/v1/ai/analyze/worker
```

## WebSocket Integration

Real-time updates via WebSocket:

```typescript
// Connect to analytics stream
const ws = useWebSocket('/ws/analytics', {
  onMessage: (event) => {
    // Handle real-time events
    console.log(event.event_type, event.data)
  },
  eventTypes: ['alert', 'worker_status'], // Optional filter
})

// Connection status
ws.isConnected  // true/false

// Send commands
ws.sendMessage('get_metrics')
ws.sendMessage('ping')
```

## State Management

Global state with Zustand:

```typescript
import { useStore } from '@/utils/store'

function Component() {
  const { workers, metrics, realtimeEvents } = useStore()
  const { addWorker, setMetrics, addRealtimeEvent } = useStore()

  // Use state...
}
```

## Styling

TailwindCSS utility classes + custom components:

```tsx
// Using utility classes
<div className="card">
  <button className="btn btn-primary">Click</button>
</div>

// Custom classes defined in index.css
.card       // White card with shadow
.btn        // Base button
.btn-primary   // Primary button
.input      // Form input
```

## Development Tips

1. **API Proxy**: Development server proxies `/api` and `/ws` to backend
2. **Hot Reload**: Changes auto-reload in browser
3. **Type Safety**: TypeScript checks types at compile time
4. **State**: Use Zustand store for global state
5. **Formatting**: date-fns with Thai locale for dates

## Troubleshooting

**Port 3000 already in use:**
```bash
# Change port in vite.config.ts
server: { port: 3001 }
```

**API connection failed:**
- Check backend is running on port 8000
- Check VITE_API_URL in .env
- Check browser console for CORS errors

**WebSocket not connecting:**
- Check backend WebSocket endpoint is active
- Check VITE_WS_URL in .env
- Check browser console for connection errors

## License

Internal use only - Assembly Time-Tracking System
