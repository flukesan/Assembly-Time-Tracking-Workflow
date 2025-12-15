import { FileText, Calendar, TrendingUp, Users, Activity, Zap } from 'lucide-react'
import { formatDuration, formatPercentage } from '@/utils/format'

interface ReportData {
  metadata: {
    reportType: string
    generatedAt: string
    dateRange: {
      start: string
      end: string
    }
    filters?: Record<string, any>
  }
  summary?: {
    totalWorkers: number
    totalSessions: number
    totalWorkHours: number
    avgProductivity: number
    avgQuality: number
    avgEfficiency: number
  }
  workers?: Array<{
    worker_id: string
    name: string
    total_sessions: number
    total_work_hours: number
    avg_productivity: number
    avg_quality: number
  }>
  productivity?: Array<{
    date: string
    productivity: number
    quality: number
    efficiency: number
  }>
  zones?: Array<{
    zone: string
    total_activities: number
    avg_duration_minutes: number
    peak_hour: number
  }>
}

interface ReportViewerProps {
  data: ReportData | null
  loading?: boolean
}

export default function ReportViewer({ data, loading = false }: ReportViewerProps) {
  if (loading) {
    return (
      <div className="card">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="card text-center py-12">
        <FileText className="mx-auto mb-4 text-gray-400" size={48} />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Report Generated</h3>
        <p className="text-gray-600">Configure and generate a report to preview it here</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 print:space-y-4">
      {/* Report Header */}
      <div className="card print:border-0">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 capitalize">
              {data.metadata.reportType.replace(/_/g, ' ')} Report
            </h2>
            <div className="mt-2 space-y-1 text-sm text-gray-600">
              <div className="flex items-center space-x-2">
                <Calendar size={14} />
                <span>
                  {new Date(data.metadata.dateRange.start).toLocaleDateString('th-TH')} -{' '}
                  {new Date(data.metadata.dateRange.end).toLocaleDateString('th-TH')}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <FileText size={14} />
                <span>Generated: {new Date(data.metadata.generatedAt).toLocaleString('th-TH')}</span>
              </div>
            </div>
          </div>

          <div className="print:hidden">
            <span className="px-3 py-1 bg-green-100 text-green-700 text-sm font-medium rounded-full">
              Ready
            </span>
          </div>
        </div>

        {/* Active Filters */}
        {data.metadata.filters && Object.keys(data.metadata.filters).length > 0 && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <h4 className="text-sm font-medium text-blue-900 mb-2">Active Filters:</h4>
            <div className="flex flex-wrap gap-2">
              {Object.entries(data.metadata.filters).map(([key, value]) => (
                <span key={key} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                  {key}: {Array.isArray(value) ? value.join(', ') : value}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Summary Section */}
      {data.summary && (
        <div className="card print:border-0">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Users className="text-blue-600" size={20} />
                <span className="text-sm font-medium text-blue-900">Total Workers</span>
              </div>
              <p className="text-2xl font-bold text-blue-900">{data.summary.totalWorkers}</p>
            </div>

            <div className="p-4 bg-green-50 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Activity className="text-green-600" size={20} />
                <span className="text-sm font-medium text-green-900">Total Sessions</span>
              </div>
              <p className="text-2xl font-bold text-green-900">{data.summary.totalSessions}</p>
            </div>

            <div className="p-4 bg-purple-50 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Zap className="text-purple-600" size={20} />
                <span className="text-sm font-medium text-purple-900">Work Hours</span>
              </div>
              <p className="text-2xl font-bold text-purple-900">
                {data.summary.totalWorkHours.toFixed(1)}
              </p>
            </div>

            <div className="p-4 bg-yellow-50 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <TrendingUp className="text-yellow-600" size={20} />
                <span className="text-sm font-medium text-yellow-900">Avg Productivity</span>
              </div>
              <p className="text-2xl font-bold text-yellow-900">
                {formatPercentage(data.summary.avgProductivity, 1)}
              </p>
            </div>

            <div className="p-4 bg-pink-50 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <TrendingUp className="text-pink-600" size={20} />
                <span className="text-sm font-medium text-pink-900">Avg Quality</span>
              </div>
              <p className="text-2xl font-bold text-pink-900">
                {formatPercentage(data.summary.avgQuality, 1)}
              </p>
            </div>

            <div className="p-4 bg-indigo-50 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <TrendingUp className="text-indigo-600" size={20} />
                <span className="text-sm font-medium text-indigo-900">Avg Efficiency</span>
              </div>
              <p className="text-2xl font-bold text-indigo-900">
                {formatPercentage(data.summary.avgEfficiency, 1)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Worker Data Table */}
      {data.workers && data.workers.length > 0 && (
        <div className="card print:border-0">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Worker Performance</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Worker
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sessions
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Work Hours
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Productivity
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quality
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.workers.map((worker) => (
                  <tr key={worker.worker_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div>
                        <div className="font-medium text-gray-900">{worker.name}</div>
                        <div className="text-sm text-gray-500">{worker.worker_id}</div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right text-sm text-gray-900">
                      {worker.total_sessions}
                    </td>
                    <td className="px-4 py-3 text-right text-sm text-gray-900">
                      {worker.total_work_hours.toFixed(1)}
                    </td>
                    <td className="px-4 py-3 text-right text-sm">
                      <span className="font-medium text-primary-600">
                        {formatPercentage(worker.avg_productivity, 1)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-sm">
                      <span className="font-medium text-green-600">
                        {formatPercentage(worker.avg_quality, 1)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Productivity Trend Table */}
      {data.productivity && data.productivity.length > 0 && (
        <div className="card print:border-0">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Productivity Trend</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Productivity
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quality
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Efficiency
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.productivity.map((entry) => (
                  <tr key={entry.date} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {new Date(entry.date).toLocaleDateString('th-TH')}
                    </td>
                    <td className="px-4 py-3 text-right text-sm font-medium text-primary-600">
                      {formatPercentage(entry.productivity, 1)}
                    </td>
                    <td className="px-4 py-3 text-right text-sm font-medium text-green-600">
                      {formatPercentage(entry.quality, 1)}
                    </td>
                    <td className="px-4 py-3 text-right text-sm font-medium text-yellow-600">
                      {formatPercentage(entry.efficiency, 1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Zone Activity Table */}
      {data.zones && data.zones.length > 0 && (
        <div className="card print:border-0">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Zone Activity</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Zone
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Activities
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Duration
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Peak Hour
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.zones.map((zone) => (
                  <tr key={zone.zone} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{zone.zone}</td>
                    <td className="px-4 py-3 text-right text-sm text-gray-900">
                      {zone.total_activities}
                    </td>
                    <td className="px-4 py-3 text-right text-sm text-gray-900">
                      {zone.avg_duration_minutes.toFixed(1)} min
                    </td>
                    <td className="px-4 py-3 text-right text-sm text-gray-900">
                      {zone.peak_hour.toString().padStart(2, '0')}:00
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
