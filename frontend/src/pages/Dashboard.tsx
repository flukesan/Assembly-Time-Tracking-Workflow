import { useEffect, useState } from 'react'
import { Users, Activity, TrendingUp, Package, RefreshCw } from 'lucide-react'
import MetricCard from '@/components/MetricCard'
import WorkerStatusCard from '@/components/WorkerStatusCard'
import EventFeed from '@/components/EventFeed'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useStore } from '@/utils/store'
import { workerAPI, analyticsAPI } from '@/services/api'
import type { RealtimeEvent } from '@/types/api'

export default function Dashboard() {
  const { metrics, setMetrics, workers, setWorkers, realtimeEvents, addRealtimeEvent } = useStore()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // WebSocket connection for real-time updates
  const { isConnected, lastEvent } = useWebSocket('/ws/analytics', {
    onMessage: (event: RealtimeEvent) => {
      addRealtimeEvent(event)

      // Update metrics if we receive a metrics_snapshot
      if (event.event_type === 'metrics_snapshot') {
        setMetrics(event.data as any)
      }

      // Update worker status if we receive worker_status update
      if (event.event_type === 'worker_status' && event.data.worker_id) {
        const workerUpdate = {
          worker_id: event.data.worker_id,
          status: event.data.status,
        }
        useStore.getState().updateWorker(event.data.worker_id, workerUpdate)
      }
    },
    onConnect: () => {
      console.log('Dashboard WebSocket connected')
    },
    onDisconnect: () => {
      console.log('Dashboard WebSocket disconnected')
    },
  })

  // Fetch initial data
  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch metrics and workers in parallel
      const [metricsData, workersData] = await Promise.all([
        analyticsAPI.getMetrics(),
        workerAPI.list(),
      ])

      setMetrics(metricsData)
      setWorkers(workersData)
    } catch (err) {
      console.error('Error fetching dashboard data:', err)
      setError('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <RefreshCw className="animate-spin mx-auto mb-4 text-primary-600" size={48} />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="text-red-600 mb-4">⚠️</div>
          <p className="text-gray-900 font-semibold mb-2">Error</p>
          <p className="text-gray-600">{error}</p>
          <button
            onClick={fetchData}
            className="mt-4 btn btn-primary"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  // Calculate active workers
  const activeWorkers = workers.filter(w => w.status === 'active').length

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Real-time monitoring and analytics</p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 px-3 py-2 bg-white rounded-lg border border-gray-200">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-600">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          <button
            onClick={fetchData}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <RefreshCw size={16} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Workers"
          value={metrics?.total_workers || 0}
          icon={Users}
          color="blue"
        />

        <MetricCard
          title="Active Workers"
          value={activeWorkers}
          icon={Activity}
          color="green"
        />

        <MetricCard
          title="Average Productivity"
          value={`${metrics?.avg_productivity?.toFixed(1) || 0}%`}
          icon={TrendingUp}
          color="yellow"
          trend={{
            value: 5.2,
            direction: 'up',
          }}
        />

        <MetricCard
          title="Total Output"
          value={metrics?.total_output || 0}
          icon={Package}
          color="red"
        />
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Workers */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Active Workers</h3>
              <span className="text-sm text-gray-600">
                {activeWorkers} of {workers.length} workers
              </span>
            </div>

            <div className="space-y-3 max-h-96 overflow-y-auto">
              {workers.filter(w => w.status === 'active').length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Users className="mx-auto mb-2" size={32} />
                  <p>No active workers</p>
                </div>
              ) : (
                workers
                  .filter(w => w.status === 'active')
                  .map((worker) => (
                    <WorkerStatusCard
                      key={worker.worker_id}
                      worker={worker}
                      productivity={Math.random() * 40 + 60} // Mock data - replace with real data
                    />
                  ))
              )}
            </div>
          </div>
        </div>

        {/* Real-time Events */}
        <div className="lg:col-span-1">
          <EventFeed events={realtimeEvents} maxEvents={8} />
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
        <div className="space-y-2">
          {realtimeEvents.slice(0, 5).map((event, index) => (
            <div
              key={`activity-${index}`}
              className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
            >
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {event.event_type.replace(/_/g, ' ')}
                  </p>
                  {event.data.worker_name && (
                    <p className="text-xs text-gray-600">{event.data.worker_name}</p>
                  )}
                </div>
              </div>
              <span className="text-xs text-gray-500">
                {new Date(event.timestamp).toLocaleTimeString('th-TH')}
              </span>
            </div>
          ))}

          {realtimeEvents.length === 0 && (
            <div className="text-center py-4 text-gray-500">
              <p className="text-sm">No recent activity</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
