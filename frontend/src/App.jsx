import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Header from './components/Layout/Header'
import Sidebar from './components/Layout/Sidebar'
import Dashboard from './pages/Dashboard'
import Analysis from './pages/Analysis'
import Optimizer from './pages/Optimizer'

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [selectedCity, setSelectedCity] = useState('Delhi NCR')

  return (
    <div className="app-layout">
      <Header selectedCity={selectedCity} />
      <div className="app-body">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          selectedCity={selectedCity}
          onCityChange={setSelectedCity}
        />
        <main
          className="app-content"
          style={{
            marginLeft: sidebarCollapsed ? 'var(--sidebar-collapsed)' : 'var(--sidebar-width)',
          }}
        >
          <Routes>
            <Route path="/" element={<Dashboard selectedCity={selectedCity} />} />
            <Route path="/analysis" element={<Analysis selectedCity={selectedCity} />} />
            <Route path="/optimizer" element={<Optimizer selectedCity={selectedCity} />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default App
