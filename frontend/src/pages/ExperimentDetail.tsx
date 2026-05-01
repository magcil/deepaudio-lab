import { useEffect, useState } from 'react'
import { getRunById, deleteRun } from '../services/runService'
import type { RunDetail } from '../services/runService'
import LossCharts from '../components/LossCharts'
import './Homepage.css'

interface Props {
  id: number
  onBack: () => void
}

export default function ExperimentDetail({ id, onBack }: Props) {
  const [run, setRun] = useState<RunDetail | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [confirming, setConfirming] = useState(false)

  useEffect(() => {
    getRunById(id)
      .then((data) => {
        setRun(data)
      })
      .catch(() => setNotFound(true))
  }, [id])

  async function handleDelete() {
    await deleteRun(id)
    onBack()
  }

  if (notFound) {
    return (
      <div className="page-content">
        <p className="eyebrow">Deep Audio Lab</p>
        <h1 className="page-title">Experiment not found</h1>
        <button className="back-button" onClick={onBack}>← Back</button>
      </div>
    )
  }

  if (!run) {
    return (
      <div className="page-content">
        <p className="eyebrow">Deep Audio Lab</p>
        <p>Loading…</p>
      </div>
    )
  }

  return (
    <div className="page-content">
      <p className="eyebrow">Deep Audio Lab</p>
      <div className="detail-actions">
        <button className="back-button" onClick={onBack}>← Back</button>
        {confirming ? (
          <div className="experiment-card__confirm">
            <span className="experiment-card__confirm-label">Delete?</span>
            <button className="experiment-card__confirm-yes" onClick={handleDelete}>Yes</button>
            <button className="experiment-card__confirm-cancel" onClick={() => setConfirming(false)}>Cancel</button>
          </div>
        ) : (
          <button className="detail-delete-button" onClick={() => setConfirming(true)}>Delete experiment</button>
        )}
      </div>
      <h1 className="page-title">{run.name}</h1>
      <div className="experiment-card__pills" style={{ marginBottom: '24px' }}>
        {run.task_type === 'train' && <span className="pill pill--training">Training</span>}
        {run.task_type === 'evaluation' && <span className="pill pill--evaluation">Evaluation</span>}
      </div>
      <p className="page-summary">{run.description}</p>
      <LossCharts losses={run.losses} />
      {run.train_params && (
        <section className="experiments-section">
          <h2 className="section-heading">Training Parameters</h2>
          <pre className="json-block">{JSON.stringify(run.train_params, null, 2)}</pre>
        </section>
      )}
    </div>
  )
}
