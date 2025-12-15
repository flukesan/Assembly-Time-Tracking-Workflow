import { useEffect, useState } from 'react'
import {
  BarChart3,
  RefreshCw,
  Calendar,
  Download,
  TrendingUp,
  Users,
  Activity,
} from 'lucide-react'
import ProductivityChart from '@/components/ProductivityChart'
import ZoneHeatmap from '@/components/ZoneHeatmap'
import ComparisonChart from '@/components/ComparisonChart'
import { analyticsAPI } from '@/services/api'
import type { Forecast } from '@/types/api'

interface ProductivityData {
  date: string
  productivity: number
  quality: number
  efficiency: number
}

interface ZoneActivityData {
  zone: string
  hour: number
  activity_count: number
  avg_duration_minutes: number
}

interface WorkerComparison {
  name: string
  productivity: number
  quality: number
  efficiency: number
  output: number
}

export default function Analytics() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Data states
  const [productivityData, setProductivityData] = useState<ProductivityData[]>([])
  const [zoneActivityData, setZoneActivityData] = useState<ZoneActivityData[]>([])
  const [workerComparison, setWorkerComparison] = useState<WorkerComparison[]>([])
  const [forecasts, setForecasts] = useState<Forecast[]>([])

  // UI states
  const [dateRange, setDateRange] = useState<'7d' | '30d' | '90d'>('30d')
  const [showForecast, setShowForecast] = useState(false)

  // Fetch analytics data
  const fetchAnalytics = async () => {
    try {
      setLoading(true)
      setError(null)

      // Calculate date range
      const days = dateRange === '7d' ? 7 : dateRange === '30d' ? 30 : 90
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - days)

      // Fetch all analytics in parallel
      const [trendData, zoneData, comparisonData] = await Promise.all([
        // Productivity trend data (mock for now - replace with real API)
        generateMockProductivityTrend(days),
        // Zone activity data (mock for now - replace with real API)
        generateMockZoneActivity(),
        // Worker comparison data (mock for now - replace with real API)
        generateMockWorkerComparison(),
      ])

      setProductivityData(trendData)
      setZoneActivityData(zoneData)
      setWorkerComparison(comparisonData)

      // Fetch forecast if enabled
      if (showForecast) {
        try {
          const historicalProductivity = trendData.map(d => d.productivity)
          const forecastData = await analyticsAPI.predictProductivity(historicalProductivity, 7)
          setForecasts(forecastData)
        } catch (err) {
          console.warn('Forecast not available:', err)
          setForecasts([])
        }
      }
    } catch (err) {
      console.error('Error fetching analytics:', err)
      setError('Failed to load analytics data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAnalytics()
  }, [dateRange, showForecast])

  const handleExport = () => {
    // Export analytics data to JSON
    const exportData = {
      date_range: dateRange,
      productivity_trend: productivityData,
      zone_activity: zoneActivityData,
      worker_comparison: workerComparison,
      forecasts: showForecast ? forecasts : null,
      exported_at: new Date().toISOString(),
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `analytics-${dateRange}-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <RefreshCw className="animate-spin mx-auto mb-4 text-primary-600" size={48} />
          <p className="text-gray-600">Loading analytics...</p>
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
          <button onClick={fetchAnalytics} className="mt-4 btn btn-primary">
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics & Insights</h1>
          <p className="text-gray-600 mt-1">Visualize trends and performance metrics</p>
        </div>

        <div className="flex items-center space-x-3">
          {/* Date Range Selector */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setDateRange('7d')}
              className={`px-3 py-1.5 text-sm rounded transition-colors ${
                dateRange === '7d'
                  ? 'bg-white text-primary-600 font-medium shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              7 Days
            </button>
            <button
              onClick={() => setDateRange('30d')}
              className={`px-3 py-1.5 text-sm rounded transition-colors ${
                dateRange === '30d'
                  ? 'bg-white text-primary-600 font-medium shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              30 Days
            </button>
            <button
              onClick={() => setDateRange('90d')}
              className={`px-3 py-1.5 text-sm rounded transition-colors ${
                dateRange === '90d'
                  ? 'bg-white text-primary-600 font-medium shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              90 Days
            </button>
          </div>

          {/* Forecast Toggle */}
          <button
            onClick={() => setShowForecast(!showForecast)}
            className={`btn flex items-center space-x-2 ${
              showForecast ? 'btn-primary' : 'btn-secondary'
            }`}
          >
            <TrendingUp size={16} />
            <span>{showForecast ? 'Hide' : 'Show'} Forecast</span>
          </button>

          <button onClick={fetchAnalytics} className="btn btn-secondary flex items-center space-x-2">
            <RefreshCw size={16} />
            <span>Refresh</span>
          </button>

          <button onClick={handleExport} className="btn btn-secondary flex items-center space-x-2">
            <Download size={16} />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Productivity</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {productivityData.length > 0
                  ? (productivityData.reduce((sum, d) => sum + d.productivity, 0) / productivityData.length).toFixed(1)
                  : 0}%
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <TrendingUp size={24} className="text-blue-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Quality</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {productivityData.length > 0
                  ? (productivityData.reduce((sum, d) => sum + d.quality, 0) / productivityData.length).toFixed(1)
                  : 0}%
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <BarChart3 size={24} className="text-green-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Efficiency</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {productivityData.length > 0
                  ? (productivityData.reduce((sum, d) => sum + d.efficiency, 0) / productivityData.length).toFixed(1)
                  : 0}%
              </p>
            </div>
            <div className="p-3 bg-yellow-100 rounded-lg">
              <Activity size={24} className="text-yellow-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Workers</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{workerComparison.length}</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <Users size={24} className="text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Productivity Trend Chart */}
      <ProductivityChart
        data={productivityData}
        forecasts={forecasts}
        title="Productivity Trends"
        height={350}
        showForecast={showForecast}
      />

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Worker Comparison */}
        <ComparisonChart
          data={workerComparison}
          metrics={[
            { key: 'productivity', label: 'Productivity', color: '#3b82f6' },
            { key: 'quality', label: 'Quality', color: '#10b981' },
            { key: 'efficiency', label: 'Efficiency', color: '#f59e0b' },
          ]}
          title="Worker Performance Comparison"
          height={300}
        />

        {/* Top Performers */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Performers</h3>
          <div className="space-y-3">
            {workerComparison
              .sort((a, b) => b.productivity - a.productivity)
              .slice(0, 5)
              .map((worker, index) => (
                <div
                  key={worker.name}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-bold text-sm">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{worker.name}</p>
                      <p className="text-xs text-gray-600">Output: {worker.output} units</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold text-primary-600">{worker.productivity.toFixed(1)}%</p>
                    <p className="text-xs text-gray-600">Quality: {worker.quality.toFixed(1)}%</p>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Zone Activity Heatmap */}
      <ZoneHeatmap data={zoneActivityData} title="Zone Activity Heatmap" height={400} />
    </div>
  )
}

// Mock data generators (replace with real API calls)
function generateMockProductivityTrend(days: number): ProductivityData[] {
  const data: ProductivityData[] = []
  const today = new Date()

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)

    data.push({
      date: date.toISOString().split('T')[0],
      productivity: 65 + Math.random() * 25,
      quality: 70 + Math.random() * 20,
      efficiency: 60 + Math.random() * 30,
    })
  }

  return data
}

function generateMockZoneActivity(): ZoneActivityData[] {
  const zones = ['Zone A', 'Zone B', 'Zone C', 'Zone D']
  const data: ZoneActivityData[] = []

  zones.forEach((zone) => {
    for (let hour = 0; hour < 24; hour++) {
      // Higher activity during work hours (8-17)
      const isWorkHour = hour >= 8 && hour <= 17
      const activityCount = isWorkHour
        ? Math.floor(Math.random() * 50) + 20
        : Math.floor(Math.random() * 10)

      data.push({
        zone,
        hour,
        activity_count: activityCount,
        avg_duration_minutes: 5 + Math.random() * 20,
      })
    }
  })

  return data
}

function generateMockWorkerComparison(): WorkerComparison[] {
  const workers = ['Worker A', 'Worker B', 'Worker C', 'Worker D', 'Worker E', 'Worker F']

  return workers.map((name) => ({
    name,
    productivity: 60 + Math.random() * 35,
    quality: 65 + Math.random() * 30,
    efficiency: 55 + Math.random() * 40,
    output: Math.floor(Math.random() * 100) + 50,
  }))
}
