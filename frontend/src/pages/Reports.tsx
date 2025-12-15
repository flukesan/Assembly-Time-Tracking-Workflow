import { useState } from 'react'
import { FileText, Download, History } from 'lucide-react'
import ReportGenerator, { ReportConfig } from '@/components/ReportGenerator'
import ReportViewer from '@/components/ReportViewer'
import { analyticsAPI, workerAPI } from '@/services/api'

interface GeneratedReport {
  id: string
  config: ReportConfig
  data: any
  generatedAt: string
}

export default function Reports() {
  const [currentReport, setCurrentReport] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [reportHistory, setReportHistory] = useState<GeneratedReport[]>([])

  const generateReport = async (config: ReportConfig) => {
    try {
      setLoading(true)

      // Generate report based on type
      let reportData: any

      switch (config.reportType) {
        case 'summary':
          reportData = await generateSummaryReport(config)
          break
        case 'worker':
          reportData = await generateWorkerReport(config)
          break
        case 'productivity':
          reportData = await generateProductivityReport(config)
          break
        case 'zone':
          reportData = await generateZoneReport(config)
          break
        default:
          throw new Error('Unknown report type')
      }

      // Add to history
      const newReport: GeneratedReport = {
        id: Date.now().toString(),
        config,
        data: reportData,
        generatedAt: new Date().toISOString(),
      }
      setReportHistory([newReport, ...reportHistory.slice(0, 9)]) // Keep last 10 reports

      // Set as current report
      setCurrentReport(reportData)

      // Export the report
      exportReport(reportData, config.format)
    } catch (err) {
      console.error('Error generating report:', err)
      alert('Failed to generate report. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const exportReport = (data: any, format: 'json' | 'csv') => {
    if (format === 'json') {
      // Export as JSON
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `report-${data.metadata.reportType}-${new Date().toISOString().split('T')[0]}.json`
      a.click()
      URL.revokeObjectURL(url)
    } else {
      // Export as CSV
      const csv = convertToCSV(data)
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `report-${data.metadata.reportType}-${new Date().toISOString().split('T')[0]}.csv`
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  const convertToCSV = (data: any): string => {
    const lines: string[] = []

    // Add metadata
    lines.push(`Report Type,${data.metadata.reportType}`)
    lines.push(`Generated At,${data.metadata.generatedAt}`)
    lines.push(`Date Range,${data.metadata.dateRange.start} to ${data.metadata.dateRange.end}`)
    lines.push('') // Empty line

    // Add summary if available
    if (data.summary) {
      lines.push('SUMMARY')
      lines.push(`Total Workers,${data.summary.totalWorkers}`)
      lines.push(`Total Sessions,${data.summary.totalSessions}`)
      lines.push(`Total Work Hours,${data.summary.totalWorkHours}`)
      lines.push(`Avg Productivity,${data.summary.avgProductivity}`)
      lines.push(`Avg Quality,${data.summary.avgQuality}`)
      lines.push(`Avg Efficiency,${data.summary.avgEfficiency}`)
      lines.push('') // Empty line
    }

    // Add workers data if available
    if (data.workers && data.workers.length > 0) {
      lines.push('WORKER PERFORMANCE')
      lines.push('Worker ID,Name,Total Sessions,Total Work Hours,Avg Productivity,Avg Quality')
      data.workers.forEach((worker: any) => {
        lines.push(
          `${worker.worker_id},${worker.name},${worker.total_sessions},${worker.total_work_hours},${worker.avg_productivity},${worker.avg_quality}`
        )
      })
      lines.push('') // Empty line
    }

    // Add productivity data if available
    if (data.productivity && data.productivity.length > 0) {
      lines.push('PRODUCTIVITY TREND')
      lines.push('Date,Productivity,Quality,Efficiency')
      data.productivity.forEach((entry: any) => {
        lines.push(`${entry.date},${entry.productivity},${entry.quality},${entry.efficiency}`)
      })
      lines.push('') // Empty line
    }

    // Add zone data if available
    if (data.zones && data.zones.length > 0) {
      lines.push('ZONE ACTIVITY')
      lines.push('Zone,Total Activities,Avg Duration (min),Peak Hour')
      data.zones.forEach((zone: any) => {
        lines.push(
          `${zone.zone},${zone.total_activities},${zone.avg_duration_minutes},${zone.peak_hour}`
        )
      })
    }

    return lines.join('\n')
  }

  const loadReportFromHistory = (report: GeneratedReport) => {
    setCurrentReport(report.data)
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reports & Export</h1>
          <p className="text-gray-600 mt-1">Generate and export custom reports</p>
        </div>

        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <FileText size={16} />
          <span>{reportHistory.length} reports in history</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Report Generator */}
        <div className="lg:col-span-1">
          <ReportGenerator onGenerate={generateReport} loading={loading} />

          {/* Report History */}
          {reportHistory.length > 0 && (
            <div className="card mt-6">
              <div className="flex items-center space-x-2 mb-4">
                <History size={20} className="text-gray-600" />
                <h3 className="text-lg font-semibold text-gray-900">Recent Reports</h3>
              </div>

              <div className="space-y-2 max-h-96 overflow-y-auto">
                {reportHistory.map((report) => (
                  <button
                    key={report.id}
                    onClick={() => loadReportFromHistory(report)}
                    className="w-full text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900 text-sm capitalize">
                          {report.config.reportType.replace(/_/g, ' ')}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">
                          {new Date(report.generatedAt).toLocaleString('th-TH')}
                        </p>
                      </div>
                      <Download size={14} className="text-gray-400" />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Report Preview */}
        <div className="lg:col-span-2">
          <ReportViewer data={currentReport} loading={loading} />
        </div>
      </div>
    </div>
  )
}

// Report generation functions (mock implementations - replace with real API calls)
async function generateSummaryReport(config: ReportConfig) {
  // Fetch workers for summary
  const workers = await workerAPI.list()

  const reportData = {
    metadata: {
      reportType: config.reportType,
      generatedAt: new Date().toISOString(),
      dateRange: {
        start: config.startDate,
        end: config.endDate,
      },
      filters: config.filters,
    },
    summary: {
      totalWorkers: workers.length,
      totalSessions: workers.reduce((sum, w) => sum + w.total_sessions, 0),
      totalWorkHours: workers.reduce((sum, w) => sum + w.total_work_hours, 0),
      avgProductivity: 75 + Math.random() * 20, // Mock
      avgQuality: 70 + Math.random() * 25, // Mock
      avgEfficiency: 65 + Math.random() * 30, // Mock
    },
  }

  return reportData
}

async function generateWorkerReport(config: ReportConfig) {
  const workers = await workerAPI.list()

  // Filter workers based on config
  let filteredWorkers = workers

  if (config.filters.workerIds && config.filters.workerIds.length > 0) {
    filteredWorkers = filteredWorkers.filter((w) =>
      config.filters.workerIds!.includes(w.worker_id)
    )
  }

  if (config.filters.shifts && config.filters.shifts.length > 0) {
    filteredWorkers = filteredWorkers.filter((w) => config.filters.shifts!.includes(w.shift))
  }

  const reportData = {
    metadata: {
      reportType: config.reportType,
      generatedAt: new Date().toISOString(),
      dateRange: {
        start: config.startDate,
        end: config.endDate,
      },
      filters: config.filters,
    },
    summary: {
      totalWorkers: filteredWorkers.length,
      totalSessions: filteredWorkers.reduce((sum, w) => sum + w.total_sessions, 0),
      totalWorkHours: filteredWorkers.reduce((sum, w) => sum + w.total_work_hours, 0),
      avgProductivity: 75 + Math.random() * 20,
      avgQuality: 70 + Math.random() * 25,
      avgEfficiency: 65 + Math.random() * 30,
    },
    workers: filteredWorkers.map((w) => ({
      worker_id: w.worker_id,
      name: w.name,
      total_sessions: w.total_sessions,
      total_work_hours: w.total_work_hours,
      avg_productivity: 70 + Math.random() * 25,
      avg_quality: 65 + Math.random() * 30,
    })),
  }

  return reportData
}

async function generateProductivityReport(config: ReportConfig) {
  // Generate productivity trend data
  const days = Math.ceil(
    (new Date(config.endDate).getTime() - new Date(config.startDate).getTime()) /
      (1000 * 60 * 60 * 24)
  )

  const productivity = []
  for (let i = 0; i < days; i++) {
    const date = new Date(config.startDate)
    date.setDate(date.getDate() + i)
    productivity.push({
      date: date.toISOString().split('T')[0],
      productivity: 70 + Math.random() * 25,
      quality: 65 + Math.random() * 30,
      efficiency: 60 + Math.random() * 35,
    })
  }

  const reportData = {
    metadata: {
      reportType: config.reportType,
      generatedAt: new Date().toISOString(),
      dateRange: {
        start: config.startDate,
        end: config.endDate,
      },
      filters: config.filters,
    },
    summary: {
      totalWorkers: 10,
      totalSessions: 100,
      totalWorkHours: 800,
      avgProductivity: productivity.reduce((sum, p) => sum + p.productivity, 0) / productivity.length,
      avgQuality: productivity.reduce((sum, p) => sum + p.quality, 0) / productivity.length,
      avgEfficiency: productivity.reduce((sum, p) => sum + p.efficiency, 0) / productivity.length,
    },
    productivity,
  }

  return reportData
}

async function generateZoneReport(config: ReportConfig) {
  const zones = ['Zone A', 'Zone B', 'Zone C', 'Zone D']

  const reportData = {
    metadata: {
      reportType: config.reportType,
      generatedAt: new Date().toISOString(),
      dateRange: {
        start: config.startDate,
        end: config.endDate,
      },
      filters: config.filters,
    },
    zones: zones.map((zone) => ({
      zone,
      total_activities: Math.floor(Math.random() * 500) + 100,
      avg_duration_minutes: 5 + Math.random() * 20,
      peak_hour: Math.floor(Math.random() * 9) + 8, // 8-17
    })),
  }

  return reportData
}
