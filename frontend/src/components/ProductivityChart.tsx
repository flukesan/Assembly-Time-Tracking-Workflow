import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp } from 'lucide-react'
import type { Forecast } from '@/types/api'

interface ProductivityChartProps {
  data: Array<{
    date: string
    productivity: number
    quality?: number
    efficiency?: number
  }>
  forecasts?: Forecast[]
  title?: string
  height?: number
  showForecast?: boolean
}

export default function ProductivityChart({
  data,
  forecasts = [],
  title = 'Productivity Trends',
  height = 300,
  showForecast = false,
}: ProductivityChartProps) {
  // Combine historical data with forecasts
  const chartData = [...data]

  if (showForecast && forecasts.length > 0) {
    forecasts.forEach((forecast) => {
      chartData.push({
        date: forecast.date,
        productivity: undefined as any,
        forecast: forecast.predicted_value,
        upper_bound: forecast.upper_bound,
        lower_bound: forecast.lower_bound,
      })
    })
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }} className="text-sm">
              {entry.name}: {entry.value?.toFixed(2)}%
              {entry.name === 'Forecast' && entry.payload.upper_bound && (
                <span className="text-gray-600 text-xs ml-1">
                  (±{(entry.payload.upper_bound - entry.value).toFixed(1)})
                </span>
              )}
            </p>
          ))}
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
          <TrendingUp size={16} />
          <span>{data.length} data points</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        {showForecast ? (
          <AreaChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="date" stroke="#6b7280" fontSize={12} />
            <YAxis stroke="#6b7280" fontSize={12} domain={[0, 100]} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />

            {/* Historical data */}
            <Area
              type="monotone"
              dataKey="productivity"
              stroke="#3b82f6"
              fill="#93c5fd"
              strokeWidth={2}
              name="Productivity"
            />

            {/* Forecast data */}
            <Area
              type="monotone"
              dataKey="forecast"
              stroke="#8b5cf6"
              fill="#c4b5fd"
              strokeWidth={2}
              strokeDasharray="5 5"
              name="Forecast"
            />

            {/* Confidence interval */}
            <Area
              type="monotone"
              dataKey="upper_bound"
              stroke="none"
              fill="#e9d5ff"
              fillOpacity={0.3}
              name="Upper Bound"
            />
            <Area
              type="monotone"
              dataKey="lower_bound"
              stroke="none"
              fill="#e9d5ff"
              fillOpacity={0.3}
              name="Lower Bound"
            />
          </AreaChart>
        ) : (
          <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="date" stroke="#6b7280" fontSize={12} />
            <YAxis stroke="#6b7280" fontSize={12} domain={[0, 100]} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />

            <Line
              type="monotone"
              dataKey="productivity"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              name="Productivity"
            />

            {data.some(d => d.quality !== undefined) && (
              <Line
                type="monotone"
                dataKey="quality"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
                name="Quality"
              />
            )}

            {data.some(d => d.efficiency !== undefined) && (
              <Line
                type="monotone"
                dataKey="efficiency"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
                name="Efficiency"
              />
            )}
          </LineChart>
        )}
      </ResponsiveContainer>

      {showForecast && forecasts.length > 0 && (
        <div className="mt-4 p-3 bg-purple-50 rounded-lg">
          <div className="flex items-start space-x-2">
            <TrendingUp className="text-purple-600 mt-0.5" size={16} />
            <div className="text-sm text-purple-900">
              <p className="font-medium">Forecast Summary</p>
              <p className="text-purple-700 mt-1">
                Predicted average: {(forecasts.reduce((sum, f) => sum + f.predicted_value, 0) / forecasts.length).toFixed(1)}%
                {' '}over next {forecasts.length} days
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
