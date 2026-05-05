import { useState } from 'react'
import './SideNav.css'

type Page = 'training' | 'evaluation' | 'homepage' | 'experiment' | 'activity-monitor'


interface SideNavProps {
  activePage: Page
  onNavigate: (page: Page) => void
}

export default function SideNav({ activePage, onNavigate }: SideNavProps) {
  const [isOpen, setIsOpen] = useState(false)

  const handleNav = (page: Page) => {
    onNavigate(page)
    setIsOpen(false)
  }

  return (
    <>
      {/* Hamburger button */}
      <button
        className="hamburger"
        onClick={() => setIsOpen(prev => !prev)}
        aria-label="Toggle navigation"
        aria-expanded={isOpen}
      >
        {/* Hamburger icon lines */}
        <span className={`hamburger-line ${isOpen ? 'open' : ''}`} />
        <span className={`hamburger-line ${isOpen ? 'open' : ''}`} />
        <span className={`hamburger-line ${isOpen ? 'open' : ''}`} />
      </button>
      
      {isOpen && <div className="nav-overlay" onClick={() => setIsOpen(false)} />}

      <nav className={`side-nav ${isOpen ? 'nav-open' : ''}`}>
        <div className="brand">
          <div className="brand-dot" />
          DeepAudioLab
        </div>

        <div className="nav-group">
          {/* Homepage */}
          <button
            className={`nav-item ${activePage === 'homepage' ? 'is-active' : ''}`}
            onClick={() => handleNav('homepage')}
          >
            Homepage
            {activePage === 'homepage' && <span className="pill">Active</span>}
          </button>

          {/* Training */}
          <button
            className={`nav-item ${activePage === 'training' ? 'is-active' : ''}`}
            onClick={() => handleNav('training')}
          >
            Training
            {activePage === 'training' && <span className="pill">Active</span>}
          </button>

          {/* Evaluation */}
          <button
            className={`nav-item ${activePage === 'evaluation' ? 'is-active' : ''}`}
            onClick={() => handleNav('evaluation')}
          >
            Evaluation
            {activePage === 'evaluation' && <span className="pill">Active</span>}
          </button>

          {/* Activity Monitor */}
          <button
            className={`nav-item ${activePage === 'activity-monitor' ? 'is-active' : ''}`}
            onClick={() => handleNav('activity-monitor')}
          >
            Activity Monitor
            {activePage === 'activity-monitor' && <span className="pill">Active</span>}
          </button>

        </div>
      </nav>
    </>
  )
}
