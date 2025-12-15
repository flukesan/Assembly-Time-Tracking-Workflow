// API Response Types

export interface Worker {
  worker_id: string
  name: string
  shift: 'morning' | 'afternoon' | 'night'
  role: string
  department: string
  registered_at: string
  face_registered: boolean
  total_sessions: number
  total_work_hours: number
  status: 'active' | 'inactive' | 'on_break'
}

export interface ProductivityIndices {
  index_1_presence_time: number
  index_2_work_time: number
  index_3_break_time: number
  index_4_idle_time: number
  index_5_work_efficiency: number
  index_6_break_ratio: number
  index_7_idle_ratio: number
  index_8_zone_transitions: number
  index_9_output_per_hour: number
  index_10_quality_score: number
  index_11_overall_productivity: number
}

export interface TimeTracking {
  worker_id: string
  worker_name: string
  shift: string
  clock_in: string
  clock_out?: string
  total_duration_seconds: number
  work_duration_seconds: number
  break_duration_seconds: number
  idle_duration_seconds: number
  zone_transitions: number
  productivity_indices: ProductivityIndices
}

export interface RealtimeEvent {
  event_type: 'worker_status' | 'productivity_update' | 'zone_transition' | 'alert' | 'system_status' | 'metrics_snapshot'
  timestamp: string
  data: Record<string, any>
  severity: 'info' | 'warning' | 'critical'
}

export interface MetricsSnapshot {
  total_workers: number
  active_workers: number
  avg_productivity: number
  total_output: number
  alerts_count: number
  last_update: string
}

export interface Alert {
  alert_type: string
  message: string
  severity: 'info' | 'warning' | 'critical'
  worker_id?: string
  worker_name?: string
  timestamp: string
}

export interface Forecast {
  day: number
  date: string
  predicted_value: number
  confidence_lower: number
  confidence_upper: number
  model: string
}

export interface TrendAnalysis {
  trend: 'increasing' | 'decreasing' | 'stable'
  slope: number
  r_squared: number
  prediction_7days: number
  prediction_30days: number
}

export interface ChartData {
  timestamps?: string[]
  labels?: string[]
  values?: number[] | number[][]
  series?: Record<string, number[]>
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  phase: string
  components: Record<string, string>
  ai_services?: Record<string, string>
  worker_services?: Record<string, string>
}
