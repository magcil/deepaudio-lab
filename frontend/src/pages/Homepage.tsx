import { useEffect, useState } from 'react'
import { getRuns } from '../services/runService'
import type { Run } from '../services/runService'
import './Homepage.css'

interface Props {
  onSelectExperiment: (id: number) => void
}

export default function Home({ onSelectExperiment }: Props) {
  const [runs, setRuns] = useState<Run[]>([])

  useEffect(() => {
    getRuns().then(setRuns)
  }, [])

  return (
    <div className="page-content">
      <p className="eyebrow">Deep Audio Lab</p>
      <h1 className="page-title">Welcome</h1>

      <section className="experiments-section">
        <h2 className="section-heading">Experiments</h2>
        <div className="experiment-grid">
          {runs.map((run) => (
            <div key={run.id} className="experiment-card" onClick={() => onSelectExperiment(run.id)}>
              <h3 className="experiment-card__name">{run.name}</h3>
              <p className="experiment-card__description">{run.description}</p>
              <div className="experiment-card__pills">
                {run.task_type === 'train' && <span className="pill pill--training">Training</span>}
                {run.task_type === 'evaluation' && <span className="pill pill--evaluation">Evaluation</span>}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
