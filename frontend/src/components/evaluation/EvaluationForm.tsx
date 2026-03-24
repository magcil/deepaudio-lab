import { useState } from 'react'
import EvalDataConfigSection from './EvalDataConfigSection'
import EvalModelSection from './EvalModelSection'
import EvalHyperparametersSection from './EvalHyperparametersSection'
import '../training/TrainingForm.css'

export interface EvaluationFormData {
  // Data config
  evaluationData: string
  samplingRate: string
  segmentDuration: string
  // Model
  modelCheckpoint: string
  // Hyperparameters
  batchSize: string
  workers: string
  device: 'cpu' | 'gpu'
  gpuIndex: string
}

export default function EvaluationForm() {
  const [form, setForm] = useState<EvaluationFormData>({
    evaluationData: '',
    samplingRate: '',
    segmentDuration: '',
    modelCheckpoint: '',
    batchSize: '',
    workers: '',
    device: 'cpu',
    gpuIndex: '',
  })

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  function handleDeviceToggle() {
    setForm(prev => ({ ...prev, device: prev.device === 'cpu' ? 'gpu' : 'cpu', gpuIndex: '' }))
  }

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const config = {
      evaluationData: form.evaluationData,
      samplingRate: parseInt(form.samplingRate),
      segmentDuration: parseFloat(form.segmentDuration),
      modelCheckpoint: form.modelCheckpoint,
      batchSize: parseInt(form.batchSize),
      workers: parseInt(form.workers),
      device: form.device,
      gpuIndex: form.device === 'gpu' ? parseInt(form.gpuIndex) : null,
    }
    console.log('Evaluation config:', config)
  }

  return (
    <form className="training-form" onSubmit={handleSubmit}>
      <EvalDataConfigSection values={form} onChange={handleChange} />
      <EvalModelSection values={form} onChange={handleChange} />
      <EvalHyperparametersSection values={form} onChange={handleChange} onDeviceToggle={handleDeviceToggle} />

      <div className="form-actions">
        <button type="submit" className="btn-primary">Run Evaluation</button>
      </div>
    </form>
  )
}
