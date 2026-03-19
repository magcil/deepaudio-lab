import { useState } from 'react'
import './App.css'
import SideNav from './components/SideNav'
import Homepage from './pages/Homepage'
import Training from './pages/Training'
import Evaluation from './pages/Evaluation'

type Page = 'homepage' | 'training' | 'evaluation'

function App() {
  const [activePage, setActivePage] = useState<Page>('homepage')

  return (
    <div className="app-shell">
      <SideNav activePage={activePage} onNavigate={setActivePage} />
      {activePage === 'homepage' && <Homepage />}
      {activePage === 'training' && <Training />}
      {activePage === 'evaluation' && <Evaluation />}
    </div>
  )
}

export default App
