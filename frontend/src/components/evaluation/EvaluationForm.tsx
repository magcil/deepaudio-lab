import { useState, useEffect } from 'react'
import EvalDataConfigSection from './EvalDataConfigSection'
import EvalModelSection from './EvalModelSection'
import EvalHyperparametersSection from './EvalHyperparametersSection'
import { startEvaluation, getEvaluationOptions, type EvaluationOptions } from '../../services/evaluationService'
import '../training/TrainingForm.css'

export interface EvaluationFormData {
  // Data config
  evaluationData: string
  classMapping: string
  samplingRate: string
  segmentDuration: string
  // Model
  modelCheckpoint: string
  numClasses: string
  // Hyperparameters
  batchSize: string
  workers: string
  device: 'cpu' | 'gpu' | 'mps'
  gpuIndex: string
}

const INITIAL_FORM: EvaluationFormData = {
  evaluationData: '',
  classMapping: '',
  samplingRate: '',
  segmentDuration: '',
  modelCheckpoint: '',
  numClasses: '',
  batchSize: '',
  workers: '',
  device: 'cpu',
  gpuIndex: '',
}

export default function EvaluationForm() {
  const [options, setOptions] = useState<EvaluationOptions>({ gpuIndexes: [], cudaAvailable: false, mpsAvailable: false })
  const [form, setForm] = useState<EvaluationFormData>(INITIAL_FORM)
  const [started, setStarted] = useState(false)

  useEffect(() => {
    getEvaluationOptions()
      .then(setOptions)
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
    const payload = {
      evaluationData: form.evaluationData,
      classMapping: form.classMapping,
      samplingRate: form.samplingRate ? parseInt(form.samplingRate) : undefined,
      segmentDuration: form.segmentDuration ? parseFloat(form.segmentDuration) : null,
      modelCheckpoint: form.modelCheckpoint,
      numClasses: parseInt(form.numClasses),
      batchSize: form.batchSize ? parseInt(form.batchSize) : undefined,
      workers: form.workers ? parseInt(form.workers) : undefined,
      device: form.device,
      gpuIndex: form.device === 'gpu' ? parseInt(form.gpuIndex) : null,
    }

    await startEvaluation(payload)
    setForm(INITIAL_FORM)
    setStarted(true)
    setTimeout(() => setStarted(false), 8000)
  }

  return (
    <form className="training-form" onSubmit={handleSubmit}>
      <EvalDataConfigSection values={form} onChange={handleChange} />
      <EvalModelSection values={form} onChange={handleChange} />
      <EvalHyperparametersSection
        values={form}
        onChange={handleChange}
        onDeviceChange={handleDeviceChange}
        gpuIndexes={options.gpuIndexes}
        cudaAvailable={options.cudaAvailable}
        mpsAvailable={options.mpsAvailable}
      />

      <div className="form-actions">
        <button type="submit" className="btn-primary">Run Evaluation</button>
        {started && <p className="training-started-msg">Evaluation has started</p>}
      </div>
    </form>
  )
}
