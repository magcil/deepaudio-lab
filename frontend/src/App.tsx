import { useState } from 'react'
import './App.css'
import SideNav from './components/SideNav'
import Homepage from './pages/Homepage'
import Training from './pages/Training'
import Evaluation from './pages/Evaluation'
import ExperimentDetail from './pages/ExperimentDetail'
import ActivityMonitor from './pages/ActivityMonitor'

type Page = 'homepage' | 'training' | 'evaluation' | 'experiment' | 'activity-monitor'

function App() {
  const [activePage, setActivePage] = useState<Page>('homepage')
  const [selectedExperimentId, setSelectedExperimentId] = useState<number | null>(null)

  function handleSelectExperiment(id: number) {
    setSelectedExperimentId(id)
    setActivePage('experiment')
  }

  return (
    <div className="app-shell">
      <SideNav activePage={activePage} onNavigate={setActivePage} />
      {activePage === 'homepage' && <Homepage onSelectExperiment={handleSelectExperiment} />}
      {activePage === 'training' && <Training />}
      {activePage === 'evaluation' && <Evaluation />}
      {activePage === 'experiment' && <ExperimentDetail id={selectedExperimentId!} onBack={() => setActivePage('homepage')} />}
      {activePage === 'activity-monitor' && <ActivityMonitor />}
    </div>
  )
}

export default App
