import { useState, FormEvent } from 'react'
import { X } from 'lucide-react'
import type { Worker } from '@/types/api'

interface WorkerModalProps {
  worker?: Worker | null
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: Partial<Worker>) => Promise<void>
}

export default function WorkerModal({ worker, isOpen, onClose, onSubmit }: WorkerModalProps) {
  const [formData, setFormData] = useState<Partial<Worker>>({
    worker_id: worker?.worker_id || '',
    name: worker?.name || '',
    shift: worker?.shift || 'morning',
    role: worker?.role || '',
    department: worker?.department || '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      await onSubmit(formData)
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save worker')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">
            {worker ? 'Edit Worker' : 'Register New Worker'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          {/* Worker ID */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Worker ID *
            </label>
            <input
              type="text"
              required
              disabled={!!worker}
              value={formData.worker_id}
              onChange={(e) => setFormData({ ...formData, worker_id: e.target.value })}
              className="input"
              placeholder="W001"
            />
          </div>

          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input"
              placeholder="นายสมชาย ใจดี"
            />
          </div>

          {/* Shift */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Shift *
            </label>
            <select
              required
              value={formData.shift}
              onChange={(e) => setFormData({ ...formData, shift: e.target.value as any })}
              className="input"
            >
              <option value="morning">กะเช้า (Morning)</option>
              <option value="afternoon">กะบ่าย (Afternoon)</option>
              <option value="night">กะดึก (Night)</option>
            </select>
          </div>

          {/* Role */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Role *
            </label>
            <input
              type="text"
              required
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="input"
              placeholder="Assembler"
            />
          </div>

          {/* Department */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Department *
            </label>
            <input
              type="text"
              required
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              className="input"
              placeholder="Assembly Line 1"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Saving...' : worker ? 'Update' : 'Register'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
