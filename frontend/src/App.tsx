import { useState } from 'react'
import './App.css'
import SideNav from './components/SideNav'
import Homepage from './pages/Homepage'
import Training from './pages/Training'
import Evaluation from './pages/Evaluation'
import ExperimentDetail from './pages/ExperimentDetail'
import ActivityMonitor from './pages/ActivityMonitor'
import Datasets from './pages/Datasets'
import Deployment from './pages/Deployment'
import keycloak from './auth/keycloak'

type Page = 'homepage' | 'training' | 'evaluation' | 'experiment' | 'activity-monitor' | 'datasets' | 'deployment'

function App() {
  const [activePage, setActivePage] = useState<Page>('homepage')
  const [selectedExperimentId, setSelectedExperimentId] = useState<number | null>(null)

  function handleSelectExperiment(id: number) {
    setSelectedExperimentId(id)
    setActivePage('experiment')
  }

  const username = keycloak.tokenParsed?.preferred_username as string | undefined

  return (
    <div className="app-shell">
      <SideNav activePage={activePage} onNavigate={setActivePage} />
      {activePage === 'homepage' && <Homepage onSelectExperiment={handleSelectExperiment} />}
      {activePage === 'training' && <Training />}
      {activePage === 'evaluation' && <Evaluation />}
      {activePage === 'experiment' && <ExperimentDetail id={selectedExperimentId!} onBack={() => setActivePage('homepage')} />}
      {activePage === 'activity-monitor' && <ActivityMonitor />}
      {activePage === 'datasets' && <Datasets />}
      {activePage === 'deployment' && <Deployment />}
      <div className="user-bar">
        {username && <span className="user-bar__name">{username}</span>}
        <button
          className="user-bar__logout"
          onClick={() => keycloak.logout({ redirectUri: window.location.origin })}
        >
          Logout
        </button>
      </div>
    </div>
  )
}

export default App
