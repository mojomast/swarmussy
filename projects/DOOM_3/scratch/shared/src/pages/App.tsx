import React from 'react'
import { Link } from 'react-router-dom'
import LevelEditor from '../components/LevelEditor'
import HealthDashboard from '../components/HealthDashboard'
import Viewer from './Viewer'
import IntegrationTest from './IntegrationTest'

type AppProps = { page?: 'home' | 'editor' | 'viewer' | 'tests' }

const App: React.FC<AppProps> = ({ page = 'home' }) => {
  const isHome = page === 'home'
  const showEditor = page === 'editor'
  const showViewer = page === 'viewer'
  const showTests = page === 'tests'

  return (
    <div className="app-shell">
      <header className="app-header" aria-label="Main header">
        <h1 className="brand">Pixel Forge Studio</h1>
        <nav className="nav" aria-label="Main navigation">
          <Link to="/" className="nav-link">Home</Link>
          <Link to="/editor" className="nav-link">Editor</Link>
          <Link to="/viewer" className="nav-link">Viewer</Link>
          <Link to="/tests" className="nav-link">Tests</Link>
        </nav>
      </header>
      <main className="app-content">
        {isHome && (
          <section className="hero" aria-label="home-hero" style={{ textAlign: 'center' }}>
            <h2>Frontend Scaffold</h2>
            <p>A minimal, production-ready React + TypeScript frontend with routes, canvas viewer, and editor skeleton.</p>
          </section>
        )}
        {showEditor && <LevelEditor />}
        {showViewer && <Viewer />}
        {showTests && <IntegrationTest />}
      </main>
      <HealthDashboard />
      <footer className="app-footer" aria-label="Footer">
        Pixel Forge Studio
      </footer>
    </div>
  )
}

export default App
