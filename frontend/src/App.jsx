import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Header from './components/Layout/Header'
import Sidebar from './components/Layout/Sidebar'
import Dashboard from './pages/Dashboard'
import Analysis from './pages/Analysis'
import Optimizer from './pages/Optimizer'

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <div className="app-layout">
      <Header />
      <div className="app-body">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
        <main
          className="app-content"
          style={{
            marginLeft: sidebarCollapsed ? 'var(--sidebar-collapsed)' : 'var(--sidebar-width)',
          }}
        >
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/optimizer" element={<Optimizer />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default App
