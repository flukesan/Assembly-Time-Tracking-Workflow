import { useMemo } from 'react'
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { MapPin } from 'lucide-react'

interface ZoneActivity {
  zone: string
  hour: number
  activity_count: number
  avg_duration_minutes: number
}

interface ZoneHeatmapProps {
  data: ZoneActivity[]
  title?: string
  height?: number
}

const HOURS = Array.from({ length: 24 }, (_, i) => i)
const HOUR_LABELS = HOURS.map(h => `${h.toString().padStart(2, '0')}:00`)

export default function ZoneHeatmap({ data, title = 'Zone Activity Heatmap', height = 400 }: ZoneHeatmapProps) {
  // Get unique zones
  const zones = useMemo(() => {
    const uniqueZones = Array.from(new Set(data.map(d => d.zone))).sort()
    return uniqueZones
  }, [data])

  // Transform data for heatmap
  const heatmapData = useMemo(() => {
    const transformed: Array<{
      hour: number
      zone: number
      value: number
      zoneLabel: string
      hourLabel: string
    }> = []

    zones.forEach((zone, zoneIndex) => {
      HOURS.forEach((hour) => {
        const entry = data.find(d => d.zone === zone && d.hour === hour)
        transformed.push({
          hour,
          zone: zoneIndex,
          value: entry?.activity_count || 0,
          zoneLabel: zone,
          hourLabel: HOUR_LABELS[hour],
        })
      })
    })

    return transformed
  }, [data, zones])

  // Calculate max value for color scaling
  const maxValue = useMemo(() => {
    return Math.max(...data.map(d => d.activity_count), 1)
  }, [data])

  // Color interpolation
  const getColor = (value: number) => {
    if (value === 0) return '#f3f4f6' // gray-100

    const intensity = value / maxValue
    if (intensity < 0.25) return '#dbeafe' // blue-100
    if (intensity < 0.5) return '#93c5fd' // blue-300
    if (intensity < 0.75) return '#3b82f6' // blue-500
    return '#1e40af' // blue-800
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      const originalEntry = data.value > 0
        ? data.find((d: ZoneActivity) => d.zone === data.zoneLabel && d.hour === data.hour)
        : null

      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900">{data.zoneLabel}</p>
          <p className="text-sm text-gray-600">{data.hourLabel}</p>
          <div className="mt-2 space-y-1">
            <p className="text-sm">
              <span className="font-medium">Activity: </span>
              {data.value} events
            </p>
            {originalEntry && (
              <p className="text-sm">
                <span className="font-medium">Avg Duration: </span>
                {originalEntry.avg_duration_minutes.toFixed(1)} min
              </p>
            )}
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <MapPin size={16} />
          <span>{zones.length} zones</span>
        </div>
      </div>

      <div className="mb-4">
        <ResponsiveContainer width="100%" height={height}>
          <ScatterChart margin={{ top: 20, right: 20, bottom: 60, left: 80 }}>
            <XAxis
              type="number"
              dataKey="hour"
              domain={[0, 23]}
              ticks={HOURS}
              tickFormatter={(value) => HOUR_LABELS[value]}
              angle={-45}
              textAnchor="end"
              stroke="#6b7280"
              fontSize={10}
              label={{ value: 'Hour of Day', position: 'bottom', offset: 40 }}
            />
            <YAxis
              type="number"
              dataKey="zone"
              domain={[0, zones.length - 1]}
              ticks={zones.map((_, i) => i)}
              tickFormatter={(value) => zones[value] || ''}
              stroke="#6b7280"
              fontSize={11}
              width={70}
              label={{ value: 'Zone', angle: -90, position: 'left', offset: 10 }}
            />
            <ZAxis type="number" dataKey="value" range={[0, 400]} />
            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
            <Scatter data={heatmapData} shape="square">
              {heatmapData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getColor(entry.value)} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center space-x-4 text-sm">
        <span className="text-gray-600">Activity Level:</span>
        <div className="flex items-center space-x-2">
          <div className="w-8 h-4 bg-gray-100 border border-gray-300 rounded"></div>
          <span className="text-gray-600">Low</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-8 h-4 bg-blue-300 border border-gray-300 rounded"></div>
          <span className="text-gray-600">Medium</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-8 h-4 bg-blue-800 border border-gray-300 rounded"></div>
          <span className="text-gray-600">High</span>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-4 grid grid-cols-3 gap-4">
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <div className="text-2xl font-bold text-blue-900">
            {data.reduce((sum, d) => sum + d.activity_count, 0)}
          </div>
          <div className="text-xs text-blue-700 mt-1">Total Activities</div>
        </div>

        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-900">
            {zones.length}
          </div>
          <div className="text-xs text-green-700 mt-1">Active Zones</div>
        </div>

        <div className="text-center p-3 bg-purple-50 rounded-lg">
          <div className="text-2xl font-bold text-purple-900">
            {data.length > 0
              ? (data.reduce((sum, d) => sum + d.avg_duration_minutes, 0) / data.length).toFixed(1)
              : 0}
          </div>
          <div className="text-xs text-purple-700 mt-1">Avg Duration (min)</div>
        </div>
      </div>
    </div>
  )
}
