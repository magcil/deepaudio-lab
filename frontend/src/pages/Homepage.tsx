import { useEffect, useState } from 'react'
import { getRuns, deleteRun } from '../services/runService'
import type { Run } from '../services/runService'
import { downloadBundle } from '../services/deploymentService'
import './Homepage.css'

interface Props {
  onSelectExperiment: (id: number) => void
}

export default function Home({ onSelectExperiment }: Props) {
  const [runs, setRuns] = useState<Run[]>([])
  const [confirmingId, setConfirmingId] = useState<number | null>(null)
  const [downloadingId, setDownloadingId] = useState<number | null>(null)

  useEffect(() => {
    getRuns().then(data =>
      setRuns([...data].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()))
    )
  }, [])

  async function handleDownload(e: React.MouseEvent, id: number) {
    e.stopPropagation()
    setDownloadingId(id)
    try {
      await downloadBundle(id)
    } finally {
      setDownloadingId(null)
    }
  }

  async function handleDelete(e: React.MouseEvent, id: number) {
    e.stopPropagation()
    await deleteRun(id)
    setConfirmingId(null)
    setRuns((prev) => prev.filter((r) => r.id !== id))
  }

  function handleConfirmClick(e: React.MouseEvent, id: number) {
    e.stopPropagation()
    setConfirmingId(id)
  }

  function handleCancel(e: React.MouseEvent) {
    e.stopPropagation()
    setConfirmingId(null)
  }

  return (
    <div className="page-content">
      <p className="eyebrow">Deep Audio Lab</p>
      <h1 className="page-title">Welcome</h1>

      <section className="experiments-section">
        <h2 className="section-heading">Experiments</h2>
        <div className="experiment-grid">
          {runs.map((run) => (
            <div key={run.id} className="experiment-card" onClick={() => onSelectExperiment(run.id)}>
              <div className="experiment-card__header">
                <h3 className="experiment-card__name">{run.name}</h3>
                {confirmingId === run.id ? (
                  <div className="experiment-card__confirm" onClick={(e) => e.stopPropagation()}>
                    <span className="experiment-card__confirm-label">Delete?</span>
                    <button className="experiment-card__confirm-yes" onClick={(e) => handleDelete(e, run.id)}>Yes</button>
                    <button className="experiment-card__confirm-cancel" onClick={handleCancel}>Cancel</button>
                  </div>
                ) : (
                  <button className="experiment-card__delete" title="Delete experiment" onClick={(e) => handleConfirmClick(e, run.id)}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="3 6 5 6 21 6" />
                      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                      <path d="M10 11v6M14 11v6" />
                      <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
                    </svg>
                  </button>
                )}
              </div>
              <p className="experiment-card__description">{run.description}</p>
              <p className="experiment-card__timestamp">{new Date(run.created_at).toLocaleString()}</p>
              <div className="experiment-card__pills">
                <span className="pill pill--training">Training</span>
                {run.has_evaluation && <span className="pill pill--evaluation">Evaluated</span>}
                {run.deploy_artifact_key && (
                  <button
                    className="experiment-card__download"
                    title={`Download bundle: ${run.deploy_name ?? 'bundle'}`}
                    onClick={(e) => handleDownload(e, run.id)}
                    disabled={downloadingId === run.id}
                  >
                    {downloadingId === run.id ? '…' : (
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                      </svg>
                    )}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
