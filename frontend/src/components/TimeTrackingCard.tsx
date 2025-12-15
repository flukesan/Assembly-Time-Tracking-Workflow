import { Clock, PlayCircle, StopCircle, Coffee, Zap, TrendingUp } from 'lucide-react'
import { formatDuration, formatPercentage } from '@/utils/format'
import type { TimeTracking } from '@/types/api'

interface TimeTrackingCardProps {
  timeTracking: TimeTracking | null
  loading?: boolean
}

export default function TimeTrackingCard({ timeTracking, loading }: TimeTrackingCardProps) {
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

  if (!timeTracking) {
    return (
      <div className="card text-center py-8 text-gray-500">
        <Clock className="mx-auto mb-2" size={32} />
        <p>No time tracking data available</p>
      </div>
    )
  }

  const { productivity_indices } = timeTracking

  return (
    <div className="space-y-4">
      {/* Time Overview */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Time Tracking</h3>

        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-start space-x-3">
            <div className="p-2 bg-green-100 text-green-600 rounded-lg">
              <PlayCircle size={20} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Clock In</p>
              <p className="font-semibold text-gray-900">
                {new Date(timeTracking.clock_in).toLocaleTimeString('th-TH')}
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <div className="p-2 bg-red-100 text-red-600 rounded-lg">
              <StopCircle size={20} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Clock Out</p>
              <p className="font-semibold text-gray-900">
                {timeTracking.clock_out
                  ? new Date(timeTracking.clock_out).toLocaleTimeString('th-TH')
                  : 'In Progress'
                }
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <div className="p-2 bg-blue-100 text-blue-600 rounded-lg">
              <Clock size={20} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Work Time</p>
              <p className="font-semibold text-gray-900">
                {formatDuration(timeTracking.work_duration_seconds)}
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <div className="p-2 bg-yellow-100 text-yellow-600 rounded-lg">
              <Coffee size={20} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Break Time</p>
              <p className="font-semibold text-gray-900">
                {formatDuration(timeTracking.break_duration_seconds)}
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <div className="p-2 bg-gray-100 text-gray-600 rounded-lg">
              <Zap size={20} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Idle Time</p>
              <p className="font-semibold text-gray-900">
                {formatDuration(timeTracking.idle_duration_seconds)}
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <div className="p-2 bg-purple-100 text-purple-600 rounded-lg">
              <TrendingUp size={20} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Zone Transitions</p>
              <p className="font-semibold text-gray-900">
                {timeTracking.zone_transitions}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Productivity Indices */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Productivity Indices</h3>

        <div className="space-y-3">
          {/* Overall Productivity */}
          <div className="p-4 bg-primary-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Overall Productivity</span>
              <span className="text-2xl font-bold text-primary-700">
                {formatPercentage(productivity_indices.index_11_overall_productivity, 0)}
              </span>
            </div>
            <div className="w-full bg-primary-200 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all"
                style={{ width: `${productivity_indices.index_11_overall_productivity}%` }}
              ></div>
            </div>
          </div>

          {/* Other Indices */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <IndexItem
              label="Work Efficiency"
              value={productivity_indices.index_5_work_efficiency}
              color="blue"
            />
            <IndexItem
              label="Quality Score"
              value={productivity_indices.index_10_quality_score}
              color="green"
            />
            <IndexItem
              label="Output per Hour"
              value={productivity_indices.index_9_output_per_hour}
              format="number"
              color="yellow"
            />
            <IndexItem
              label="Break Ratio"
              value={productivity_indices.index_6_break_ratio}
              color="orange"
            />
            <IndexItem
              label="Idle Ratio"
              value={productivity_indices.index_7_idle_ratio}
              color="red"
            />
            <IndexItem
              label="Work Time %"
              value={productivity_indices.index_2_work_time}
              color="purple"
            />
          </div>
        </div>
      </div>
    </div>
  )
}

interface IndexItemProps {
  label: string
  value: number
  color: string
  format?: 'percentage' | 'number'
}

function IndexItem({ label, value, color, format = 'percentage' }: IndexItemProps) {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    yellow: 'bg-yellow-50 text-yellow-700',
    orange: 'bg-orange-50 text-orange-700',
    red: 'bg-red-50 text-red-700',
    purple: 'bg-purple-50 text-purple-700',
  }

  return (
    <div className={`p-3 rounded-lg ${colorClasses[color] || 'bg-gray-50 text-gray-700'}`}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{label}</span>
        <span className="text-lg font-bold">
          {format === 'percentage' ? formatPercentage(value, 1) : value.toFixed(1)}
        </span>
      </div>
    </div>
  )
}
