import { useState } from 'react'
import DataConfigSection from './DataConfigSection'
import ModelSettingsSection from './ModelSettingsSection'
import HyperparametersSection from './HyperparametersSection'
import { startTraining } from '../../services/trainingService'
import './TrainingForm.css'

export interface TrainingFormData {
  // Data config
  trainingData: string
  classMapping: string
  validationData: string
  samplingRate: string
  segmentDuration: string
  // Model settings
  backbone: string
  pretrained: boolean
  freezeBackbone: boolean
  modelSamplingRate: string
  numClasses: string
  checkpoint: string
  // Hyperparameters
  epochs: string
  patience: string
  learningRate: string
  workers: string
  batchSize: string
  device: 'cpu' | 'gpu'
  gpuIndex: string
}

export default function TrainingForm() {
  const [form, setForm] = useState<TrainingFormData>({
    trainingData: '',
    classMapping: '',
    validationData: '',
    samplingRate: '',
    segmentDuration: '',
    backbone: 'beats',
    pretrained: true,
    freezeBackbone: false,
    modelSamplingRate: '',
    numClasses: '',
    checkpoint: '',
    epochs: '',
    patience: '',
    learningRate: '',
    workers: '',
    batchSize: '',
    device: 'cpu',
    gpuIndex: '',
  })

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  function handleToggle(name: keyof TrainingFormData) {
    setForm(prev => ({ ...prev, [name]: !prev[name] }))
  }

  function handleDeviceToggle() {
    setForm(prev => ({ ...prev, device: prev.device === 'cpu' ? 'gpu' : 'cpu', gpuIndex: '' }))
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const payload = {
      trainingData: form.trainingData,
      classMapping: form.classMapping || null,
      validationData: form.validationData || null,
      samplingRate: parseInt(form.samplingRate),
      segmentDuration: parseFloat(form.segmentDuration),
      backbone: form.backbone,
      pretrained: form.pretrained,
      freezeBackbone: form.freezeBackbone,
      modelSamplingRate: parseInt(form.modelSamplingRate),
      numClasses: parseInt(form.numClasses),
      checkpoint: form.checkpoint || null,
      epochs: parseInt(form.epochs),
      patience: parseInt(form.patience),
      learningRate: parseFloat(form.learningRate),
      workers: parseInt(form.workers),
      batchSize: parseInt(form.batchSize),
      device: form.device,
      gpuIndex: form.device === 'gpu' ? parseInt(form.gpuIndex) : null,
    }

    console.log('Submitting training with payload:', payload)
    await startTraining(payload)

  }

  return (
    <form className="training-form" onSubmit={handleSubmit}>
      <DataConfigSection values={form} onChange={handleChange} />
      <ModelSettingsSection values={form} onChange={handleChange} onToggle={handleToggle} />
      <HyperparametersSection values={form} onChange={handleChange} onToggle={handleDeviceToggle} />

      <div className="form-actions">
        <button type="submit" className="btn-primary">Start Training</button>
      </div>
    </form>
  )
}
