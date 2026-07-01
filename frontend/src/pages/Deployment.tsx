import { useEffect, useState } from 'react';
import { getRuns } from '../services/runService';
import type { Run } from '../services/runService';
import { createBundle, downloadBundle } from '../services/deploymentService';
import { ApiError } from '../api/client';
import './Deployment.css';

const TRAINING_SUCCESS = 'Successful';

export default function Deployment() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | ''>('');
  const [bundleName, setBundleName] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createSuccess, setCreateSuccess] = useState(false);
  const [downloading, setDownloading] = useState<number | null>(null);

  useEffect(() => {
    getRuns().then(setRuns);
  }, []);

  const deployableRuns = runs.filter((r) => r.training_status === TRAINING_SUCCESS);
  const bundledRuns = runs.filter((r) => r.deploy_artifact_key !== null);

  async function handleCreate() {
    if (!selectedRunId || !bundleName.trim()) return;
    setCreating(true);
    setCreateError(null);
    setCreateSuccess(false);
    try {
      await createBundle(Number(selectedRunId), bundleName.trim());
      setCreateSuccess(true);
      setBundleName('');
      setSelectedRunId('');
    } catch (err) {
      if (err instanceof ApiError) {
        try {
          const body = JSON.parse(err.message)
          setCreateError(typeof body?.detail === 'string' ? body.detail : 'Failed to start deployment')
        } catch {
          setCreateError('Failed to start deployment')
        }
      } else {
        setCreateError('Failed to start deployment')
      }
    } finally {
      setCreating(false);
    }
  }

  async function handleDownload(runId: number) {
    setDownloading(runId);
    try {
      await downloadBundle(runId);
    } catch (err) {
      console.error('Download failed', err);
    } finally {
      setDownloading(null);
    }
  }

  return (
    <div className="page-content">
      <p className="eyebrow">Deep Audio Lab</p>
      <h1 className="page-title">Deployment</h1>
      <p className="page-summary">
        Package a trained model into a self-contained inference bundle. Unzip it, build the Docker
        image, and run the inference server locally or on any machine.
      </p>

      <section className="deploy-section">
        <h2 className="section-heading">Create Bundle</h2>
        <div className="deploy-form">
          <div className="deploy-form__row">
            <label className="deploy-form__label">Experiment</label>
            <select
              className="deploy-form__select"
              value={selectedRunId}
              onChange={(e) => setSelectedRunId(e.target.value === '' ? '' : Number(e.target.value))}
            >
              <option value="">Select a successful experiment…</option>
              {deployableRuns.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </div>

          <div className="deploy-form__row">
            <label className="deploy-form__label">Bundle Name</label>
            <input
              className="deploy-form__input"
              type="text"
              placeholder="e.g. gtzan-classifier-v1"
              value={bundleName}
              onChange={(e) => setBundleName(e.target.value)}
              maxLength={128}
            />
          </div>

          {createError && <p className="deploy-form__error">{createError}</p>}
          {createSuccess && (
            <p className="deploy-form__success">
              Bundle creation started — check Activity Monitor for progress.
            </p>
          )}

          <button
            className="deploy-form__btn"
            onClick={handleCreate}
            disabled={creating || !selectedRunId || !bundleName.trim()}
          >
            {creating ? 'Starting…' : 'Create Bundle'}
          </button>
        </div>
      </section>

      <section className="deploy-section">
        <h2 className="section-heading">Available Bundles</h2>
        {bundledRuns.length === 0 ? (
          <p className="deploy-empty">No bundles have been built yet.</p>
        ) : (
          <table className="deploy-table">
            <thead>
              <tr>
                <th>Experiment</th>
                <th>Bundle Name</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {bundledRuns.map((run) => (
                <tr key={run.id} className="deploy-row">
                  <td className="deploy-row__name">{run.name}</td>
                  <td className="deploy-row__bundle">{run.deploy_name ?? '—'}</td>
                  <td>
                    <button
                      className="deploy-row__download"
                      onClick={() => handleDownload(run.id)}
                      disabled={downloading === run.id}
                    >
                      {downloading === run.id ? 'Preparing…' : 'Download'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
