import { AlertCircle, Activity, TrendingUp, Navigation, Bell } from 'lucide-react'
import clsx from 'clsx'
import type { RealtimeEvent } from '@/types/api'
import { formatRelativeTime, getSeverityColor } from '@/utils/format'

interface EventFeedProps {
  events: RealtimeEvent[]
  maxEvents?: number
}

const eventIcons = {
  worker_status: Activity,
  productivity_update: TrendingUp,
  zone_transition: Navigation,
  alert: AlertCircle,
  system_status: Bell,
  metrics_snapshot: Activity,
}

export default function EventFeed({ events, maxEvents = 10 }: EventFeedProps) {
  const displayEvents = events.slice(0, maxEvents)

  if (displayEvents.length === 0) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Real-time Events</h3>
        <div className="text-center py-8 text-gray-500">
          <Activity className="mx-auto mb-2" size={32} />
          <p>Waiting for events...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Real-time Events</h3>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-600">Live</span>
        </div>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {displayEvents.map((event, index) => {
          const Icon = eventIcons[event.event_type] || Activity

          return (
            <div
              key={`${event.timestamp}-${index}`}
              className="flex items-start space-x-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
            >
              <div
                className={clsx(
                  'p-2 rounded-lg flex-shrink-0',
                  getSeverityColor(event.severity)
                )}
              >
                <Icon size={16} />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {event.event_type.replace(/_/g, ' ').toUpperCase()}
                  </p>
                  <span className="text-xs text-gray-500 ml-2 flex-shrink-0">
                    {formatRelativeTime(event.timestamp)}
                  </span>
                </div>

                <div className="mt-1 text-sm text-gray-600">
                  {event.event_type === 'worker_status' && (
                    <p>
                      {event.data.worker_name} - {event.data.status}
                      {event.data.current_zone && ` @ ${event.data.current_zone}`}
                    </p>
                  )}

                  {event.event_type === 'productivity_update' && (
                    <p>
                      {event.data.worker_name}: {event.data.overall_productivity?.toFixed(1)}%
                    </p>
                  )}

                  {event.event_type === 'zone_transition' && (
                    <p>
                      {event.data.worker_name}: {event.data.from_zone || 'Entry'} → {event.data.to_zone}
                    </p>
                  )}

                  {event.event_type === 'alert' && (
                    <p className="font-medium">{event.data.message}</p>
                  )}

                  {event.event_type === 'system_status' && (
                    <p>{event.data.message || 'System update'}</p>
                  )}

                  {event.event_type === 'metrics_snapshot' && (
                    <p>
                      Active: {event.data.active_workers}/{event.data.total_workers} workers
                    </p>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {events.length > maxEvents && (
        <div className="mt-3 text-center">
          <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
            View all {events.length} events
          </button>
        </div>
      )}
    </div>
  )
}
