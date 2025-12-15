import { format, formatDistanceToNow } from 'date-fns'
import { th } from 'date-fns/locale'

export function formatDate(date: string | Date, formatStr: string = 'PPpp'): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return format(dateObj, formatStr, { locale: th })
}

export function formatRelativeTime(date: string | Date): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return formatDistanceToNow(dateObj, { addSuffix: true, locale: th })
}

export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`
}

export function formatPercentage(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`
}

export function formatNumber(value: number, decimals: number = 2): string {
  return value.toFixed(decimals)
}

export function getShiftLabel(shift: string): string {
  const labels: Record<string, string> = {
    morning: 'กะเช้า',
    afternoon: 'กะบ่าย',
    night: 'กะดึก',
  }
  return labels[shift] || shift
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    active: 'text-green-600 bg-green-100',
    inactive: 'text-gray-600 bg-gray-100',
    on_break: 'text-yellow-600 bg-yellow-100',
  }
  return colors[status] || 'text-gray-600 bg-gray-100'
}

export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    info: 'text-blue-600 bg-blue-100',
    warning: 'text-yellow-600 bg-yellow-100',
    critical: 'text-red-600 bg-red-100',
  }
  return colors[severity] || 'text-gray-600 bg-gray-100'
}
