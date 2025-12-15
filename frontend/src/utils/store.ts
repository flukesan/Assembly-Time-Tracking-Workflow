import { create } from 'zustand'
import type { Worker, MetricsSnapshot, RealtimeEvent, Alert } from '@/types/api'

interface AppState {
  // Workers
  workers: Worker[]
  setWorkers: (workers: Worker[]) => void
  addWorker: (worker: Worker) => void
  updateWorker: (workerId: string, worker: Partial<Worker>) => void
  removeWorker: (workerId: string) => void

  // Metrics
  metrics: MetricsSnapshot | null
  setMetrics: (metrics: MetricsSnapshot) => void

  // Real-time events
  realtimeEvents: RealtimeEvent[]
  addRealtimeEvent: (event: RealtimeEvent) => void
  clearRealtimeEvents: () => void

  // Alerts
  alerts: Alert[]
  addAlert: (alert: Alert) => void
  removeAlert: (index: number) => void
  clearAlerts: () => void

  // UI State
  sidebarOpen: boolean
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void

  // Selected items
  selectedWorker: Worker | null
  setSelectedWorker: (worker: Worker | null) => void
}

export const useStore = create<AppState>((set) => ({
  // Workers
  workers: [],
  setWorkers: (workers) => set({ workers }),
  addWorker: (worker) => set((state) => ({ workers: [...state.workers, worker] })),
  updateWorker: (workerId, worker) =>
    set((state) => ({
      workers: state.workers.map((w) => (w.worker_id === workerId ? { ...w, ...worker } : w)),
    })),
  removeWorker: (workerId) =>
    set((state) => ({
      workers: state.workers.filter((w) => w.worker_id !== workerId),
    })),

  // Metrics
  metrics: null,
  setMetrics: (metrics) => set({ metrics }),

  // Real-time events
  realtimeEvents: [],
  addRealtimeEvent: (event) =>
    set((state) => ({
      realtimeEvents: [event, ...state.realtimeEvents].slice(0, 100), // Keep last 100 events
    })),
  clearRealtimeEvents: () => set({ realtimeEvents: [] }),

  // Alerts
  alerts: [],
  addAlert: (alert) =>
    set((state) => ({
      alerts: [alert, ...state.alerts].slice(0, 50), // Keep last 50 alerts
    })),
  removeAlert: (index) =>
    set((state) => ({
      alerts: state.alerts.filter((_, i) => i !== index),
    })),
  clearAlerts: () => set({ alerts: [] }),

  // UI State
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  // Selected items
  selectedWorker: null,
  setSelectedWorker: (worker) => set({ selectedWorker: worker }),
}))
