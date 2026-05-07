import { useState, useEffect } from 'react'
import EvalDataConfigSection from './EvalDataConfigSection'
import EvalHyperparametersSection from './EvalHyperparametersSection'
import { startEvaluation, getEvaluationOptions, getTrainRuns, type TrainRun } from '../../services/evaluationService'
import '../training/TrainingForm.css'
import './EvaluationForm.css'

export interface EvaluationFormData {
  evaluationData: string
  batchSize: string
  workers: string
  device: 'cpu' | 'gpu' | 'mps'
  gpuIndex: string
}

const INITIAL_FORM: EvaluationFormData = {
  evaluationData: '',
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
  const [selectedExperiment, setSelectedExperiment] = useState<string | null>(null)
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

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  function handleDeviceChange(device: 'cpu' | 'gpu' | 'mps') {
    setForm(prev => ({ ...prev, device, gpuIndex: '' }))
  }

  async function handleSubmit(e: React.SyntheticEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!selectedExperiment) {
      setExperimentError(true)
      return
    }
    const payload = {
      evaluationData: form.evaluationData,
      trainName: selectedExperiment,
      batchSize: form.batchSize ? parseInt(form.batchSize) : undefined,
      workers: form.workers ? parseInt(form.workers) : undefined,
      device: form.device,
      gpuIndex: form.device === 'gpu' ? parseInt(form.gpuIndex) : null,
    }

    const { task_id } = await startEvaluation(payload)
    console.log('Evaluation started, task_id:', task_id)
    setForm(INITIAL_FORM)
    setSelectedExperiment(null)
    setStarted(true)
    setTimeout(() => setStarted(false), 8000)
  }

  function handleSelectExperiment(name: string) {
    setSelectedExperiment(name)
    setExperimentError(false)
    setOpen(false)
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
          {selectedExperiment && (
            <span className="experiment-selected-label">{selectedExperiment}</span>
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
                onClick={() => handleSelectExperiment(run.name)}
              >
                {run.name}
              </div>
            ))}
          </div>
        )}
      </div>

      <EvalDataConfigSection values={form} onChange={handleChange} />
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
