import { useState } from 'react'
import './App.css'
import SideNav from './components/SideNav'
import Training from './pages/Training'
import Evaluation from './pages/Evaluation'

type Page = 'training' | 'evaluation'

function App() {
  const [activePage, setActivePage] = useState<Page>('training')

  return (
    <div className="app-shell">
      <SideNav activePage={activePage} onNavigate={setActivePage} />
      {activePage === 'training' ? <Training /> : <Evaluation />}
    </div>
  )
}

export default App
