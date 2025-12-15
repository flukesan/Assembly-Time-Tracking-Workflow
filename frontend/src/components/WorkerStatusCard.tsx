import { User, Clock, TrendingUp } from 'lucide-react'
import clsx from 'clsx'
import type { Worker } from '@/types/api'
import { getStatusColor, getShiftLabel } from '@/utils/format'

interface WorkerStatusCardProps {
  worker: Worker
  productivity?: number
}

export default function WorkerStatusCard({ worker, productivity }: WorkerStatusCardProps) {
  return (
    <div className="card hover:shadow-md transition-shadow cursor-pointer">
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3">
          <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
            <User className="text-gray-600" size={24} />
          </div>

          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h3 className="font-semibold text-gray-900">{worker.name}</h3>
              <span
                className={clsx(
                  'px-2 py-0.5 text-xs font-medium rounded-full',
                  getStatusColor(worker.status)
                )}
              >
                {worker.status === 'active' && 'ทำงาน'}
                {worker.status === 'on_break' && 'พักผ่อน'}
                {worker.status === 'inactive' && 'ไม่ได้ทำงาน'}
              </span>
            </div>

            <p className="text-sm text-gray-600 mt-1">
              {worker.worker_id} • {worker.role}
            </p>

            <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
              <div className="flex items-center space-x-1">
                <Clock size={14} />
                <span>{getShiftLabel(worker.shift)}</span>
              </div>

              {productivity !== undefined && (
                <div className="flex items-center space-x-1">
                  <TrendingUp size={14} />
                  <span>{productivity.toFixed(1)}%</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {productivity !== undefined && (
          <div className="text-right">
            <div
              className={clsx(
                'text-2xl font-bold',
                productivity >= 80 && 'text-green-600',
                productivity >= 60 && productivity < 80 && 'text-yellow-600',
                productivity < 60 && 'text-red-600'
              )}
            >
              {productivity.toFixed(0)}
            </div>
            <div className="text-xs text-gray-500">Productivity</div>
          </div>
        )}
      </div>
    </div>
  )
}
