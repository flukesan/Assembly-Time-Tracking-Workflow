import { Outlet, Link, useLocation } from 'react-router-dom'
import { Menu, X, Home, Users, BarChart3, FileText, Activity } from 'lucide-react'
import { useStore } from '@/utils/store'
import clsx from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Workers', href: '/workers', icon: Users },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Reports', href: '/reports', icon: FileText },
]

export default function Layout() {
  const location = useLocation()
  const { sidebarOpen, toggleSidebar } = useStore()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 fixed top-0 left-0 right-0 z-30">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center space-x-4">
            <button
              onClick={toggleSidebar}
              className="p-2 rounded-md hover:bg-gray-100 lg:hidden"
            >
              {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
            <div className="flex items-center space-x-3">
              <Activity className="text-primary-600" size={32} />
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  Assembly Time-Tracking
                </h1>
                <p className="text-xs text-gray-500">Version 4.2.0</p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden sm:flex items-center space-x-2 text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-gray-600">Connected</span>
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed top-16 left-0 bottom-0 w-64 bg-white border-r border-gray-200 transition-transform duration-300 z-20',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        <nav className="p-4 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            const Icon = item.icon

            return (
              <Link
                key={item.name}
                to={item.href}
                className={clsx(
                  'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700 font-medium'
                    : 'text-gray-700 hover:bg-gray-100'
                )}
              >
                <Icon size={20} />
                <span>{item.name}</span>
              </Link>
            )
          })}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
          <div className="text-xs text-gray-500 space-y-1">
            <p>Phase: 4C - Advanced Analytics</p>
            <p>Build: Production</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main
        className={clsx(
          'pt-16 transition-all duration-300',
          sidebarOpen ? 'lg:pl-64' : 'lg:pl-0'
        )}
      >
        <div className="min-h-[calc(100vh-4rem)]">
          <Outlet />
        </div>
      </main>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-10 lg:hidden"
          onClick={toggleSidebar}
        ></div>
      )}
    </div>
  )
}
