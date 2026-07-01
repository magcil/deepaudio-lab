import { useState, useEffect } from 'react'
import EvalHyperparametersSection from './EvalHyperparametersSection'
import { startEvaluation, getEvaluationOptions, getEvaluationLimits, getTrainRuns, type TrainRun, type EvaluationLimits } from '../../services/evaluationService'
import { getDatasetSplits } from '../../services/datasetService'
import { ApiError } from '../../api/client'
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
  const [limits, setLimits] = useState<EvaluationLimits | null>(null)
  const [trainRuns, setTrainRuns] = useState<TrainRun[]>([])
  const [selectedRun, setSelectedRun] = useState<TrainRun | null>(null)
  const [splits, setSplits] = useState<string[]>([])
  const [experimentError, setExperimentError] = useState(false)
  const [open, setOpen] = useState(false)
  const [started, setStarted] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [form, setForm] = useState<EvaluationFormData>(INITIAL_FORM)

  useEffect(() => {
    getEvaluationOptions()
      .then(data => {
        setGpuIndexes(data.gpuIndexes)
        setCudaAvailable(data.cudaAvailable)
        setMpsAvailable(data.mpsAvailable)
      })
      .catch(console.error)

    getEvaluationLimits().then(setLimits).catch(console.error)

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
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
    setFieldErrors(prev => {
      if (!prev[name]) return prev
      const next = { ...prev }
      delete next[name]
      return next
    })
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

    // Client-side validation via Constraint Validation API
    const formEl = e.currentTarget
    const clientErrors: Record<string, string> = {}
    for (const el of Array.from(formEl.elements)) {
      if (
        (el instanceof HTMLInputElement || el instanceof HTMLSelectElement) &&
        el.name &&
        !el.validity.valid
      ) {
        clientErrors[el.name] = el.validationMessage
      }
    }
    if (Object.keys(clientErrors).length > 0) {
      setFieldErrors(clientErrors)
      setSubmitError(null)
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

    setSubmitError(null)
    setFieldErrors({})
    try {
      const { task_id } = await startEvaluation(payload)
      console.log('Evaluation started, task_id:', task_id)
      setForm(INITIAL_FORM)
      setSelectedRun(null)
      setStarted(true)
      setTimeout(() => setStarted(false), 8000)
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 429 || err.status === 503) {
          setSubmitError(err.message)
        } else if (err.status === 422) {
          try {
            const body = JSON.parse(err.message)
            if (Array.isArray(body?.detail)) {
              const errors: Record<string, string> = {}
              for (const d of body.detail as { loc: string[]; msg: string }[]) {
                const field = d.loc.at(-1)
                if (field) errors[String(field)] = d.msg
              }
              setFieldErrors(errors)
            } else {
              setSubmitError('Validation error. Please check your inputs.')
            }
          } catch {
            setSubmitError('Validation error. Please check your inputs.')
          }
        } else {
          setSubmitError('Could not start evaluation. Please try again.')
        }
      } else {
        setSubmitError('Could not start evaluation. Please try again.')
      }
    }
  }

  function handleSelectExperiment(run: TrainRun) {
    setSelectedRun(run)
    setExperimentError(false)
    setOpen(false)
    setForm(prev => ({ ...prev, testSet: '' }))
  }

  return (
    <form className="training-form" onSubmit={handleSubmit} noValidate>
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
          {selectedRun && splits.length > 0 && (
            <select id="testSet" name="testSet" className="test-set-select" value={form.testSet} onChange={handleChange} required>
              <option value="">Test set</option>
              {splits.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          )}
        </div>
        {fieldErrors.testSet && (
          <span className="field-error">{fieldErrors.testSet}</span>
        )}
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
      </div>

      <EvalHyperparametersSection
        values={form}
        onChange={handleChange}
        onDeviceChange={handleDeviceChange}
        gpuIndexes={gpuIndexes}
        cudaAvailable={cudaAvailable}
        mpsAvailable={mpsAvailable}
        limits={limits}
        fieldErrors={fieldErrors}
      />

      <div className="form-actions">
        <button type="submit" className="btn-primary" disabled={!selectedRun || !form.testSet}>Run Evaluation</button>
        {started && <p className="training-started-msg">Evaluation has started</p>}
        {submitError && <p className="training-error-msg">{submitError}</p>}
      </div>
    </form>
  )
}
