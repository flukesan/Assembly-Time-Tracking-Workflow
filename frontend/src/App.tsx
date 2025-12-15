import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Workers from './pages/Workers'
import WorkerDetail from './pages/WorkerDetail'
import Analytics from './pages/Analytics'

// Placeholder pages
const Reports = () => <div className="p-6"><h1 className="text-2xl font-bold">Reports</h1></div>

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="workers" element={<Workers />} />
          <Route path="workers/:workerId" element={<WorkerDetail />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="reports" element={<Reports />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App
