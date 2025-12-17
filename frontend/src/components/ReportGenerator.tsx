import { useState } from 'react'
import { FileText, Download, Calendar, Filter, Printer } from 'lucide-react'
import { format } from 'date-fns'

interface ReportGeneratorProps {
  onGenerate: (config: ReportConfig) => Promise<void>
  loading?: boolean
}

export interface ReportConfig {
  reportType: 'worker' | 'productivity' | 'zone' | 'summary'
  startDate: string
  endDate: string
  format: 'json' | 'csv'
  filters: {
    workerIds?: string[]
    zones?: string[]
    shifts?: string[]
    minProductivity?: number
  }
}

export default function ReportGenerator({ onGenerate, loading = false }: ReportGeneratorProps) {
  const [reportType, setReportType] = useState<ReportConfig['reportType']>('summary')
  const [startDate, setStartDate] = useState(() => {
    const date = new Date()
    date.setDate(date.getDate() - 30)
    return format(date, 'yyyy-MM-dd')
  })
  const [endDate, setEndDate] = useState(() => format(new Date(), 'yyyy-MM-dd'))
  const [exportFormat, setExportFormat] = useState<'json' | 'csv'>('json')

  // Advanced filters
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  const [workerFilter, setWorkerFilter] = useState('')
  const [zoneFilter, setZoneFilter] = useState('')
  const [shiftFilter, setShiftFilter] = useState<string>('all')
  const [minProductivity, setMinProductivity] = useState(0)

  const handleGenerate = async () => {
    const config: ReportConfig = {
      reportType,
      startDate,
      endDate,
      format: exportFormat,
      filters: {
        workerIds: workerFilter ? workerFilter.split(',').map(id => id.trim()) : undefined,
        zones: zoneFilter ? zoneFilter.split(',').map(z => z.trim()) : undefined,
        shifts: shiftFilter !== 'all' ? [shiftFilter] : undefined,
        minProductivity: minProductivity > 0 ? minProductivity : undefined,
      },
    }

    await onGenerate(config)
  }

  const reportTypes = [
    { value: 'summary', label: 'Summary Report', description: 'Overall metrics and statistics' },
    { value: 'worker', label: 'Worker Report', description: 'Individual worker performance' },
    { value: 'productivity', label: 'Productivity Report', description: 'Productivity trends and analysis' },
    { value: 'zone', label: 'Zone Activity Report', description: 'Zone-based activity breakdown' },
  ]

  return (
    <div className="card">
      <div className="flex items-center space-x-3 mb-6">
        <div className="p-3 bg-primary-100 rounded-lg">
          <FileText className="text-primary-600" size={24} />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Generate Report</h3>
          <p className="text-sm text-gray-600">Configure and export custom reports</p>
        </div>
      </div>

      <div className="space-y-6">
        {/* Report Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">Report Type</label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {reportTypes.map((type) => (
              <button
                key={type.value}
                onClick={() => setReportType(type.value as any)}
                className={`p-4 text-left border-2 rounded-lg transition-colors ${
                  reportType === type.value
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-medium text-gray-900">{type.label}</div>
                <div className="text-sm text-gray-600 mt-1">{type.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Date Range */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Calendar size={14} className="inline mr-1" />
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Calendar size={14} className="inline mr-1" />
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Export Format */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Export Format</label>
          <div className="flex space-x-3">
            <button
              onClick={() => setExportFormat('json')}
              className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                exportFormat === 'json'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              JSON
            </button>
            <button
              onClick={() => setExportFormat('csv')}
              className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                exportFormat === 'csv'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              CSV
            </button>
          </div>
        </div>

        {/* Advanced Filters Toggle */}
        <div>
          <button
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            className="flex items-center space-x-2 text-primary-600 hover:text-primary-700 font-medium"
          >
            <Filter size={16} />
            <span>{showAdvancedFilters ? 'Hide' : 'Show'} Advanced Filters</span>
          </button>
        </div>

        {/* Advanced Filters */}
        {showAdvancedFilters && (
          <div className="p-4 bg-gray-50 rounded-lg space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Worker IDs (comma-separated)
              </label>
              <input
                type="text"
                value={workerFilter}
                onChange={(e) => setWorkerFilter(e.target.value)}
                placeholder="e.g., W001, W002, W003"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Zones (comma-separated)
              </label>
              <input
                type="text"
                value={zoneFilter}
                onChange={(e) => setZoneFilter(e.target.value)}
                placeholder="e.g., Zone A, Zone B"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Shift</label>
              <select
                value={shiftFilter}
                onChange={(e) => setShiftFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="all">All Shifts</option>
                <option value="morning">Morning</option>
                <option value="afternoon">Afternoon</option>
                <option value="night">Night</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Productivity (%)
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={minProductivity}
                onChange={(e) => setMinProductivity(Number(e.target.value))}
                className="w-full"
              />
              <div className="text-sm text-gray-600 mt-1">{minProductivity}%</div>
            </div>
          </div>
        )}

        {/* Generate Button */}
        <div className="flex space-x-3">
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="flex-1 btn btn-primary flex items-center justify-center space-x-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                <span>Generating...</span>
              </>
            ) : (
              <>
                <Download size={16} />
                <span>Generate & Download</span>
              </>
            )}
          </button>

          <button
            onClick={() => window.print()}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <Printer size={16} />
            <span>Print</span>
          </button>
        </div>
      </div>
    </div>
  )
}
