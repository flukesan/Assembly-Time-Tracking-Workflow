import { Eye, Edit, Trash2, User } from 'lucide-react'
import clsx from 'clsx'
import type { Worker } from '@/types/api'
import { getStatusColor, getShiftLabel } from '@/utils/format'

interface WorkerListItemProps {
  worker: Worker
  onView: (worker: Worker) => void
  onEdit: (worker: Worker) => void
  onDelete: (worker: Worker) => void
}

export default function WorkerListItem({ worker, onView, onEdit, onDelete }: WorkerListItemProps) {
  return (
    <div className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
      {/* Worker Info */}
      <div className="flex items-center space-x-4 flex-1">
        <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
          <User className="text-gray-600" size={24} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <h3 className="font-semibold text-gray-900 truncate">{worker.name}</h3>
            <span
              className={clsx(
                'px-2 py-0.5 text-xs font-medium rounded-full flex-shrink-0',
                getStatusColor(worker.status)
              )}
            >
              {worker.status === 'active' && 'Active'}
              {worker.status === 'on_break' && 'Break'}
              {worker.status === 'inactive' && 'Inactive'}
            </span>
          </div>

          <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
            <span className="font-mono">{worker.worker_id}</span>
            <span>•</span>
            <span>{worker.role}</span>
            <span>•</span>
            <span>{getShiftLabel(worker.shift)}</span>
          </div>

          <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
            <span>{worker.department}</span>
            {worker.face_registered && (
              <>
                <span>•</span>
                <span className="text-green-600">✓ Face registered</span>
              </>
            )}
          </div>
        </div>

        {/* Stats */}
        <div className="hidden md:flex items-center space-x-6 text-sm">
          <div className="text-center">
            <div className="font-semibold text-gray-900">{worker.total_sessions}</div>
            <div className="text-xs text-gray-500">Sessions</div>
          </div>
          <div className="text-center">
            <div className="font-semibold text-gray-900">
              {worker.total_work_hours.toFixed(1)}
            </div>
            <div className="text-xs text-gray-500">Hours</div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center space-x-2 ml-4">
        <button
          onClick={() => onView(worker)}
          className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          title="View details"
        >
          <Eye size={18} />
        </button>
        <button
          onClick={() => onEdit(worker)}
          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          title="Edit worker"
        >
          <Edit size={18} />
        </button>
        <button
          onClick={() => onDelete(worker)}
          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          title="Delete worker"
        >
          <Trash2 size={18} />
        </button>
      </div>
    </div>
  )
}
