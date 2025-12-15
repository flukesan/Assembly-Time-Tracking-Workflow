import axios from 'axios'
import type { Worker, TimeTracking, MetricsSnapshot, HealthStatus, Forecast, TrendAnalysis, ChartData } from '@/types/api'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Error interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// Worker API
export const workerAPI = {
  list: async (): Promise<Worker[]> => {
    const { data } = await api.get('/api/v1/workers')
    return data
  },

  get: async (workerId: string): Promise<Worker> => {
    const { data } = await api.get(`/api/v1/workers/${workerId}`)
    return data
  },

  create: async (worker: Partial<Worker>): Promise<Worker> => {
    const { data } = await api.post('/api/v1/workers', worker)
    return data
  },

  update: async (workerId: string, worker: Partial<Worker>): Promise<Worker> => {
    const { data } = await api.put(`/api/v1/workers/${workerId}`, worker)
    return data
  },

  delete: async (workerId: string): Promise<void> => {
    await api.delete(`/api/v1/workers/${workerId}`)
  },

  getTimeTracking: async (workerId: string): Promise<TimeTracking> => {
    const { data } = await api.get(`/api/v1/workers/${workerId}/time-tracking`)
    return data
  },
}

// Analytics API
export const analyticsAPI = {
  getMetrics: async (): Promise<MetricsSnapshot> => {
    const { data } = await api.get('/api/v1/analytics/metrics')
    return data
  },

  predictProductivity: async (historicalData: number[], forecastDays: number = 7): Promise<Forecast[]> => {
    const { data } = await api.post('/api/v1/analytics/predict/productivity', null, {
      params: { historical_data: historicalData, forecast_days: forecastDays }
    })
    return data.forecasts
  },

  analyzeTrend: async (timeSeriesData: number[], dataType: string = 'productivity'): Promise<TrendAnalysis> => {
    const { data } = await api.post('/api/v1/analytics/analyze/trend', null, {
      params: { time_series_data: timeSeriesData, data_type: dataType }
    })
    return data
  },

  generateHeatmap: async (chartData: any[], xAxis: string, yAxis: string, valueField: string): Promise<ChartData> => {
    const { data } = await api.post('/api/v1/analytics/visualize/heatmap', chartData, {
      params: { x_axis: xAxis, y_axis: yAxis, value_field: valueField }
    })
    return data
  },

  generateTimeSeries: async (chartData: any[], interval: string = 'hour'): Promise<ChartData> => {
    const { data } = await api.post('/api/v1/analytics/visualize/time-series', chartData, {
      params: { interval }
    })
    return data
  },

  exportJSON: async (exportData: any): Promise<{ filename: string; content: string }> => {
    const { data } = await api.post('/api/v1/analytics/export/json', exportData)
    return data
  },

  exportCSV: async (exportData: any[], columns?: string[]): Promise<{ filename: string; content: string }> => {
    const { data } = await api.post('/api/v1/analytics/export/csv', exportData, {
      params: { columns }
    })
    return data
  },
}

// AI Query API
export const aiAPI = {
  query: async (question: string, showReasoning: boolean = false): Promise<{ answer: string; reasoning?: string }> => {
    const { data } = await api.post('/api/v1/ai/query', {
      question,
      show_reasoning: showReasoning,
    })
    return data
  },

  analyzeWorker: async (workerId: string): Promise<any> => {
    const { data } = await api.post('/api/v1/ai/analyze/worker', {
      worker_id: workerId,
      include_recommendations: true,
    })
    return data
  },
}

// System API
export const systemAPI = {
  health: async (): Promise<HealthStatus> => {
    const { data } = await api.get('/health')
    return data
  },

  root: async (): Promise<any> => {
    const { data } = await api.get('/')
    return data
  },
}

export default api
