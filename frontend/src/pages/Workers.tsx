import { useEffect, useState } from 'react'
import { Users, Search, Filter, UserPlus, RefreshCw } from 'lucide-react'
import WorkerListItem from '@/components/WorkerListItem'
import WorkerModal from '@/components/WorkerModal'
import { useStore } from '@/utils/store'
import { workerAPI } from '@/services/api'
import type { Worker } from '@/types/api'

export default function Workers() {
  const { workers, setWorkers } = useStore()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedWorker, setSelectedWorker] = useState<Worker | null>(null)

  // Filter state
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [shiftFilter, setShiftFilter] = useState<string>('all')
  const [departmentFilter, setDepartmentFilter] = useState<string>('all')

  // Fetch workers
  const fetchWorkers = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await workerAPI.list()
      setWorkers(data)
    } catch (err) {
      console.error('Error fetching workers:', err)
      setError('Failed to load workers')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWorkers()
  }, [])

  // Handle worker actions
  const handleAddWorker = () => {
    setSelectedWorker(null)
    setIsModalOpen(true)
  }

  const handleEditWorker = (worker: Worker) => {
    setSelectedWorker(worker)
    setIsModalOpen(true)
  }

  const handleViewWorker = (worker: Worker) => {
    window.location.href = `/workers/${worker.worker_id}`
  }

  const handleDeleteWorker = async (worker: Worker) => {
    if (!confirm(`Are you sure you want to delete ${worker.name}?`)) {
      return
    }

    try {
      await workerAPI.delete(worker.worker_id)
      await fetchWorkers() // Refresh list
    } catch (err) {
      console.error('Error deleting worker:', err)
      alert('Failed to delete worker')
    }
  }

  const handleSubmitWorker = async (data: Partial<Worker>) => {
    if (selectedWorker) {
      // Update existing worker
      await workerAPI.update(selectedWorker.worker_id, data)
    } else {
      // Create new worker
      await workerAPI.create(data as Omit<Worker, 'registered_at' | 'face_registered' | 'total_sessions' | 'total_work_hours' | 'status'>)
    }
    await fetchWorkers() // Refresh list
  }

  // Filter workers
  const filteredWorkers = workers.filter((worker) => {
    // Search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      const matchesSearch =
        worker.name.toLowerCase().includes(query) ||
        worker.worker_id.toLowerCase().includes(query) ||
        worker.role.toLowerCase().includes(query) ||
        worker.department.toLowerCase().includes(query)

      if (!matchesSearch) return false
    }

    // Status filter
    if (statusFilter !== 'all' && worker.status !== statusFilter) {
      return false
    }

    // Shift filter
    if (shiftFilter !== 'all' && worker.shift !== shiftFilter) {
      return false
    }

    // Department filter
    if (departmentFilter !== 'all' && worker.department !== departmentFilter) {
      return false
    }

    return true
  })

  // Get unique departments for filter
  const departments = Array.from(new Set(workers.map(w => w.department))).sort()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <RefreshCw className="animate-spin mx-auto mb-4 text-primary-600" size={48} />
          <p className="text-gray-600">Loading workers...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="text-red-600 mb-4">⚠️</div>
          <p className="text-gray-900 font-semibold mb-2">Error</p>
          <p className="text-gray-600">{error}</p>
          <button onClick={fetchWorkers} className="mt-4 btn btn-primary">
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Worker Management</h1>
          <p className="text-gray-600 mt-1">
            Manage worker profiles and track attendance
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchWorkers}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <RefreshCw size={16} />
            <span>Refresh</span>
          </button>

          <button
            onClick={handleAddWorker}
            className="btn btn-primary flex items-center space-x-2"
          >
            <UserPlus size={16} />
            <span>Add Worker</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Search */}
          <div className="lg:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Search workers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active</option>
              <option value="on_break">On Break</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>

          {/* Shift Filter */}
          <div>
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

          {/* Department Filter */}
          <div>
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="all">All Departments</option>
              {departments.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Active Filters Summary */}
        {(searchQuery || statusFilter !== 'all' || shiftFilter !== 'all' || departmentFilter !== 'all') && (
          <div className="mt-4 flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Showing {filteredWorkers.length} of {workers.length} workers
            </div>
            <button
              onClick={() => {
                setSearchQuery('')
                setStatusFilter('all')
                setShiftFilter('all')
                setDepartmentFilter('all')
              }}
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              Clear Filters
            </button>
          </div>
        )}
      </div>

      {/* Workers List */}
      <div className="space-y-3">
        {filteredWorkers.length === 0 ? (
          <div className="card text-center py-12">
            <Users className="mx-auto mb-4 text-gray-400" size={48} />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Workers Found</h3>
            <p className="text-gray-600 mb-4">
              {searchQuery || statusFilter !== 'all' || shiftFilter !== 'all' || departmentFilter !== 'all'
                ? 'Try adjusting your filters'
                : 'Get started by adding your first worker'}
            </p>
            {workers.length === 0 && (
              <button onClick={handleAddWorker} className="btn btn-primary">
                <UserPlus size={16} className="mr-2" />
                Add First Worker
              </button>
            )}
          </div>
        ) : (
          filteredWorkers.map((worker) => (
            <WorkerListItem
              key={worker.worker_id}
              worker={worker}
              onView={handleViewWorker}
              onEdit={handleEditWorker}
              onDelete={handleDeleteWorker}
            />
          ))
        )}
      </div>

      {/* Statistics Summary */}
      {workers.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card text-center">
            <div className="text-3xl font-bold text-gray-900">{workers.length}</div>
            <div className="text-sm text-gray-600 mt-1">Total Workers</div>
          </div>

          <div className="card text-center">
            <div className="text-3xl font-bold text-green-600">
              {workers.filter(w => w.status === 'active').length}
            </div>
            <div className="text-sm text-gray-600 mt-1">Active</div>
          </div>

          <div className="card text-center">
            <div className="text-3xl font-bold text-yellow-600">
              {workers.filter(w => w.status === 'on_break').length}
            </div>
            <div className="text-sm text-gray-600 mt-1">On Break</div>
          </div>

          <div className="card text-center">
            <div className="text-3xl font-bold text-gray-600">
              {workers.filter(w => w.status === 'inactive').length}
            </div>
            <div className="text-sm text-gray-600 mt-1">Inactive</div>
          </div>
        </div>
      )}

      {/* Worker Modal */}
      <WorkerModal
        worker={selectedWorker}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleSubmitWorker}
      />
    </div>
  )
}
