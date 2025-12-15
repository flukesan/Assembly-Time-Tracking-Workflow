import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts'
import { TrendingUp } from 'lucide-react'
import { useState } from 'react'

interface ComparisonData {
  name: string
  [key: string]: string | number
}

interface ComparisonChartProps {
  data: ComparisonData[]
  metrics: Array<{
    key: string
    label: string
    color: string
  }>
  title?: string
  height?: number
  chartType?: 'bar' | 'radar'
}

export default function ComparisonChart({
  data,
  metrics,
  title = 'Performance Comparison',
  height = 300,
  chartType: initialChartType = 'bar',
}: ComparisonChartProps) {
  const [chartType, setChartType] = useState<'bar' | 'radar'>(initialChartType)

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }} className="text-sm">
              {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}
              {typeof entry.value === 'number' && entry.value <= 100 ? '%' : ''}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  // Transform data for radar chart (limit to reasonable number of data points)
  const radarData = data.slice(0, 8)

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <TrendingUp size={16} />
            <span>{data.length} items</span>
          </div>
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setChartType('bar')}
              className={`px-3 py-1 text-sm rounded transition-colors ${
                chartType === 'bar'
                  ? 'bg-white text-primary-600 font-medium shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Bar
            </button>
            <button
              onClick={() => setChartType('radar')}
              className={`px-3 py-1 text-sm rounded transition-colors ${
                chartType === 'radar'
                  ? 'bg-white text-primary-600 font-medium shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Radar
            </button>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        {chartType === 'bar' ? (
          <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="name" stroke="#6b7280" fontSize={12} />
            <YAxis stroke="#6b7280" fontSize={12} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            {metrics.map((metric) => (
              <Bar
                key={metric.key}
                dataKey={metric.key}
                fill={metric.color}
                name={metric.label}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        ) : (
          <RadarChart data={radarData} margin={{ top: 20, right: 40, bottom: 20, left: 40 }}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis dataKey="name" stroke="#6b7280" fontSize={11} />
            <PolarRadiusAxis stroke="#6b7280" fontSize={10} domain={[0, 100]} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            {metrics.map((metric) => (
              <Radar
                key={metric.key}
                name={metric.label}
                dataKey={metric.key}
                stroke={metric.color}
                fill={metric.color}
                fillOpacity={0.3}
                strokeWidth={2}
              />
            ))}
          </RadarChart>
        )}
      </ResponsiveContainer>

      {/* Metrics Legend */}
      <div className="mt-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {metrics.map((metric) => {
          const values = data.map(d => Number(d[metric.key]) || 0)
          const avg = values.reduce((sum, v) => sum + v, 0) / values.length
          const max = Math.max(...values)
          const min = Math.min(...values)

          return (
            <div key={metric.key} className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-2 mb-1">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: metric.color }}></div>
                <span className="text-xs font-medium text-gray-900">{metric.label}</span>
              </div>
              <div className="text-xs text-gray-600 space-y-0.5">
                <div>Avg: {avg.toFixed(1)}</div>
                <div className="flex justify-between">
                  <span>Min: {min.toFixed(1)}</span>
                  <span>Max: {max.toFixed(1)}</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {chartType === 'radar' && data.length > 8 && (
        <div className="mt-3 text-center text-sm text-gray-600">
          Showing first 8 items. Switch to Bar chart to view all {data.length} items.
        </div>
      )}
    </div>
  )
}
