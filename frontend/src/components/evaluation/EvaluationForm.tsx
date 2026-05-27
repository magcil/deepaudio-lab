import { useState, useEffect } from 'react'
import EvalHyperparametersSection from './EvalHyperparametersSection'
import { startEvaluation, getEvaluationOptions, getTrainRuns, type TrainRun } from '../../services/evaluationService'
import { getDatasetSplits } from '../../services/datasetService'
import '../training/TrainingForm.css'
import './EvaluationForm.css'

export interface EvaluationFormData {
  testSet: string
  batchSize: string
  workers: string
  device: 'cpu' | 'gpu' | 'mps'
  gpuIndex: string
}

const INITIAL_FORM: EvaluationFormData = {
  testSet: '',
  batchSize: '',
  workers: '',
  device: 'cpu',
  gpuIndex: '',
}

export default function EvaluationForm() {
  const [gpuIndexes, setGpuIndexes] = useState<number[]>([])
  const [cudaAvailable, setCudaAvailable] = useState(false)
  const [mpsAvailable, setMpsAvailable] = useState(false)
  const [trainRuns, setTrainRuns] = useState<TrainRun[]>([])
  const [selectedRun, setSelectedRun] = useState<TrainRun | null>(null)
  const [splits, setSplits] = useState<string[]>([])
  const [experimentError, setExperimentError] = useState(false)
  const [open, setOpen] = useState(false)
  const [started, setStarted] = useState(false)
  const [form, setForm] = useState<EvaluationFormData>(INITIAL_FORM)

  useEffect(() => {
    getEvaluationOptions()
      .then(data => {
        setGpuIndexes(data.gpuIndexes)
        setCudaAvailable(data.cudaAvailable)
        setMpsAvailable(data.mpsAvailable)
      })
      .catch(console.error)

    getTrainRuns()
      .then(setTrainRuns)
      .catch(console.error)
  }, [])

  useEffect(() => {
    if (selectedRun?.dataset_id == null) {
      setSplits([])
      return
    }
    getDatasetSplits(selectedRun.dataset_id).then(setSplits).catch(() => setSplits([]))
  }, [selectedRun])

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  function handleDeviceChange(device: 'cpu' | 'gpu' | 'mps') {
    setForm(prev => ({ ...prev, device, gpuIndex: '' }))
  }

  async function handleSubmit(e: React.SyntheticEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!selectedRun) {
      setExperimentError(true)
      return
    }
    const payload = {
      testSet: form.testSet,
      trainRunId: selectedRun.id,
      batchSize: form.batchSize ? parseInt(form.batchSize) : undefined,
      workers: form.workers ? parseInt(form.workers) : undefined,
      device: form.device,
      gpuIndex: form.device === 'gpu' ? parseInt(form.gpuIndex) : null,
    }

    const { task_id } = await startEvaluation(payload)
    console.log('Evaluation started, task_id:', task_id)
    setForm(INITIAL_FORM)
    setSelectedRun(null)
    setStarted(true)
    setTimeout(() => setStarted(false), 8000)
  }

  function handleSelectExperiment(run: TrainRun) {
    setSelectedRun(run)
    setExperimentError(false)
    setOpen(false)
    setForm(prev => ({ ...prev, testSet: '' }))
  }

  return (
    <form className="training-form" onSubmit={handleSubmit}>
      <div className="experiment-picker">
        <div className="experiment-picker-row">
          <button
            type="button"
            className={`btn-dropdown${open ? ' open' : ''}${experimentError ? ' error' : ''}`}
            onClick={() => setOpen(o => !o)}
          >
            Choose Experiment
            <span className="chevron">▼</span>
          </button>
          {selectedRun && (
            <span className="experiment-selected-label">{selectedRun.name}</span>
          )}
        </div>
        {experimentError && (
          <p className="experiment-picker-error">Please select an experiment before running evaluation.</p>
        )}
        {open && (
          <div className="experiment-dropdown">
            {trainRuns.map(run => (
              <div
                key={run.id}
                className="experiment-dropdown-item"
                onClick={() => handleSelectExperiment(run)}
              >
                {run.name}
              </div>
            ))}
          </div>
        )}
        {selectedRun && splits.length > 0 && (
          <div className="form-field" style={{ marginTop: '12px' }}>
            <label htmlFor="testSet">Test Set</label>
            <select id="testSet" name="testSet" value={form.testSet} onChange={handleChange} required>
              <option value="">Select a split</option>
              {splits.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      <EvalHyperparametersSection
        values={form}
        onChange={handleChange}
        onDeviceChange={handleDeviceChange}
        gpuIndexes={gpuIndexes}
        cudaAvailable={cudaAvailable}
        mpsAvailable={mpsAvailable}
      />

      <div className="form-actions">
        <button type="submit" className="btn-primary">Run Evaluation</button>
        {started && <p className="training-started-msg">Evaluation has started</p>}
      </div>
    </form>
  )
}
