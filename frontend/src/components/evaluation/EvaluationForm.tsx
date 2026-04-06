import { useState, useEffect } from 'react'
import EvalDataConfigSection from './EvalDataConfigSection'
import EvalModelSection from './EvalModelSection'
import EvalHyperparametersSection from './EvalHyperparametersSection'
import { startEvaluation, getEvaluationOptions } from '../../services/evaluationService'
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
  device: 'cpu' | 'gpu'
  gpuIndex: string
}

export default function EvaluationForm() {
  const [gpuIndexes, setGpuIndexes] = useState<number[]>([])

  useEffect(() => {
    getEvaluationOptions()
      .then(data => setGpuIndexes(data.gpuIndexes))
      .catch(console.error)
  }, [])

  const [form, setForm] = useState<EvaluationFormData>({
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
  })

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  function handleDeviceChange(device: 'cpu' | 'gpu') {
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
  }

  return (
    <form className="training-form" onSubmit={handleSubmit}>
      <EvalDataConfigSection values={form} onChange={handleChange} />
      <EvalModelSection values={form} onChange={handleChange} />
      <EvalHyperparametersSection values={form} onChange={handleChange} onDeviceChange={handleDeviceChange} gpuIndexes={gpuIndexes} />

      <div className="form-actions">
        <button type="submit" className="btn-primary">Run Evaluation</button>
      </div>
    </form>
  )
}
