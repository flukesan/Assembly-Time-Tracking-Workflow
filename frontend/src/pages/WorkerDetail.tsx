import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  User,
  Clock,
  Calendar,
  Briefcase,
  Building,
  TrendingUp,
  Activity,
  Edit,
  Trash2,
  RefreshCw,
} from 'lucide-react'
import TimeTrackingCard from '@/components/TimeTrackingCard'
import WorkerModal from '@/components/WorkerModal'
import { workerAPI, analyticsAPI } from '@/services/api'
import { getStatusColor, getShiftLabel } from '@/utils/format'
import clsx from 'clsx'
import type { Worker, TimeTracking } from '@/types/api'

export default function WorkerDetail() {
  const { workerId } = useParams<{ workerId: string }>()
  const navigate = useNavigate()

  const [worker, setWorker] = useState<Worker | null>(null)
  const [timeTracking, setTimeTracking] = useState<TimeTracking | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Modal state
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)

  // Fetch worker data
  const fetchWorkerData = async () => {
    if (!workerId) return

    try {
      setLoading(true)
      setError(null)

      // Fetch worker info and current time tracking
      const [workerData, trackingData] = await Promise.all([
        workerAPI.get(workerId),
        analyticsAPI.getWorkerTimeTracking(workerId).catch(() => null), // May not have tracking data
      ])

      setWorker(workerData)
      setTimeTracking(trackingData)
    } catch (err: any) {
      console.error('Error fetching worker data:', err)
      setError(err.response?.status === 404 ? 'Worker not found' : 'Failed to load worker data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWorkerData()
  }, [workerId])

  const handleEdit = () => {
    setIsEditModalOpen(true)
  }

  const handleDelete = async () => {
    if (!worker || !confirm(`Are you sure you want to delete ${worker.name}?`)) {
      return
    }

    try {
      await workerAPI.delete(worker.worker_id)
      navigate('/workers')
    } catch (err) {
      console.error('Error deleting worker:', err)
      alert('Failed to delete worker')
    }
  }

  const handleUpdateWorker = async (data: Partial<Worker>) => {
    if (!worker) return

    await workerAPI.update(worker.worker_id, data)
    await fetchWorkerData() // Refresh data
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <RefreshCw className="animate-spin mx-auto mb-4 text-primary-600" size={48} />
          <p className="text-gray-600">Loading worker details...</p>
        </div>
      </div>
    )
  }

  if (error || !worker) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="text-red-600 mb-4">⚠️</div>
          <p className="text-gray-900 font-semibold mb-2">Error</p>
          <p className="text-gray-600">{error || 'Worker not found'}</p>
          <button onClick={() => navigate('/workers')} className="mt-4 btn btn-primary">
            Back to Workers
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/workers')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft size={24} />
          </button>

          <div>
            <h1 className="text-2xl font-bold text-gray-900">{worker.name}</h1>
            <p className="text-gray-600 mt-1">{worker.worker_id}</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button onClick={fetchWorkerData} className="btn btn-secondary flex items-center space-x-2">
            <RefreshCw size={16} />
            <span>Refresh</span>
          </button>

          <button onClick={handleEdit} className="btn btn-secondary flex items-center space-x-2">
            <Edit size={16} />
            <span>Edit</span>
          </button>

          <button
            onClick={handleDelete}
            className="btn bg-red-600 hover:bg-red-700 text-white flex items-center space-x-2"
          >
            <Trash2 size={16} />
            <span>Delete</span>
          </button>
        </div>
      </div>

      {/* Worker Profile Card */}
      <div className="card">
        <div className="flex items-start space-x-6">
          {/* Avatar */}
          <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
            <User className="text-gray-600" size={48} />
          </div>

          {/* Info Grid */}
          <div className="flex-1 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Status */}
            <div className="flex items-start space-x-3">
              <div className="p-2 bg-gray-100 rounded-lg">
                <Activity size={20} className="text-gray-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Status</p>
                <span
                  className={clsx(
                    'inline-block mt-1 px-2 py-0.5 text-xs font-medium rounded-full',
                    getStatusColor(worker.status)
                  )}
                >
                  {worker.status === 'active' && 'ทำงาน'}
                  {worker.status === 'on_break' && 'พักผ่อน'}
                  {worker.status === 'inactive' && 'ไม่ได้ทำงาน'}
                </span>
              </div>
            </div>

            {/* Shift */}
            <div className="flex items-start space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Clock size={20} className="text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Shift</p>
                <p className="font-semibold text-gray-900 mt-1">{getShiftLabel(worker.shift)}</p>
              </div>
            </div>

            {/* Role */}
            <div className="flex items-start space-x-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Briefcase size={20} className="text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Role</p>
                <p className="font-semibold text-gray-900 mt-1">{worker.role}</p>
              </div>
            </div>

            {/* Department */}
            <div className="flex items-start space-x-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Building size={20} className="text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Department</p>
                <p className="font-semibold text-gray-900 mt-1">{worker.department}</p>
              </div>
            </div>

            {/* Registered Date */}
            <div className="flex items-start space-x-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Calendar size={20} className="text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Registered</p>
                <p className="font-semibold text-gray-900 mt-1">
                  {new Date(worker.registered_at).toLocaleDateString('th-TH')}
                </p>
              </div>
            </div>

            {/* Face Registered */}
            <div className="flex items-start space-x-3">
              <div className={clsx('p-2 rounded-lg', worker.face_registered ? 'bg-green-100' : 'bg-red-100')}>
                <User size={20} className={worker.face_registered ? 'text-green-600' : 'text-red-600'} />
              </div>
              <div>
                <p className="text-sm text-gray-600">Face Recognition</p>
                <p className="font-semibold text-gray-900 mt-1">
                  {worker.face_registered ? 'Registered' : 'Not Registered'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Sessions</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{worker.total_sessions}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <Activity size={24} className="text-blue-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Work Hours</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{worker.total_work_hours.toFixed(1)}</p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <Clock size={24} className="text-green-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Hours/Session</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {worker.total_sessions > 0
                  ? (worker.total_work_hours / worker.total_sessions).toFixed(1)
                  : '0.0'}
              </p>
            </div>
            <div className="p-3 bg-yellow-100 rounded-lg">
              <TrendingUp size={24} className="text-yellow-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Current Time Tracking */}
      {worker.status !== 'inactive' && (
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">Current Session</h2>
          <TimeTrackingCard timeTracking={timeTracking} loading={false} />
        </div>
      )}

      {worker.status === 'inactive' && !timeTracking && (
        <div className="card text-center py-12">
          <Clock className="mx-auto mb-4 text-gray-400" size={48} />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Active Session</h3>
          <p className="text-gray-600">This worker is not currently clocked in</p>
        </div>
      )}

      {/* Edit Modal */}
      <WorkerModal
        worker={worker}
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSubmit={handleUpdateWorker}
      />
    </div>
  )
}
