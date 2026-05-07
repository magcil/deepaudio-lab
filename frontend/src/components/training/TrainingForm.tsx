import React, { useState, useEffect } from 'react'
import DataConfigSection from './DataConfigSection'
import ModelSettingsSection from './ModelSettingsSection'
import HyperparametersSection from './HyperparametersSection'
import { startTraining, getTrainingOptions, type TrainingOptions } from '../../services/trainingService'
import './TrainingForm.css'

export interface TrainingFormData {
  // Data config
  experimentName: string
  description: string
  trainingData: string
  classMapping: string
  validationData: string
  samplingRate: string
  segmentDuration: string
  // Model settings
  backbone: string
  poolingMethod: string
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
  device: 'cpu' | 'gpu' | 'mps'
  gpuIndex: string
}

const INITIAL_FORM: TrainingFormData = {
  experimentName: '',
  description: '',
  trainingData: '',
  classMapping: '',
  validationData: '',
  samplingRate: '',
  segmentDuration: '',
  backbone: 'beats',
  poolingMethod: '',
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
}

export default function TrainingForm() {
  const [options, setOptions] = useState<TrainingOptions>({ backbones: [], poolingMethods: [], gpuIndexes: [], cudaAvailable: false, mpsAvailable: false })
  const [started, setStarted] = useState(false)

  useEffect(() => {
    getTrainingOptions()
      .then(data => {
        console.log('Training options:', data)
        setOptions(data)
      })
      .catch(console.error)
  }, [])

  const [form, setForm] = useState<TrainingFormData>(INITIAL_FORM)

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  function handleToggle(name: keyof TrainingFormData) {
    setForm(prev => ({ ...prev, [name]: !prev[name] }))
  }

  function handleDeviceChange(device: 'cpu' | 'gpu' | 'mps') {
    setForm(prev => ({ ...prev, device, gpuIndex: '' }))
  }

  async function handleSubmit(e: React.SubmitEvent<HTMLFormElement>) {
    e.preventDefault()
    const payload = {
      experimentName: form.experimentName,
      description: form.description || null,
      trainingData: form.trainingData,
      classMapping: form.classMapping || null,
      validationData: form.validationData || null,
      samplingRate: form.samplingRate ? parseInt(form.samplingRate) : undefined,
      segmentDuration: form.segmentDuration ? parseFloat(form.segmentDuration) : null,
      backbone: form.backbone,
      pooling: form.poolingMethod || null,
      pretrained: form.pretrained,
      freezeBackbone: form.freezeBackbone,
      numClasses: parseInt(form.numClasses),
      checkpoint: form.checkpoint || null,
      epochs: form.epochs ? parseInt(form.epochs) : undefined,
      patience: form.patience ? parseInt(form.patience) : undefined,
      learningRate: form.learningRate ? parseFloat(form.learningRate) : undefined,
      workers: form.workers ? parseInt(form.workers) : undefined,
      batchSize: form.batchSize ? parseInt(form.batchSize) : undefined,
      device: form.device,
      gpuIndex: form.device === 'gpu' ? parseInt(form.gpuIndex) : null,
    }

    const { task_id } = await startTraining(payload)
    console.log('Training started, task_id:', task_id)
    setForm(INITIAL_FORM)
    setStarted(true)
    setTimeout(() => setStarted(false), 8000)
  }

  return (
    <form className="training-form" onSubmit={handleSubmit}>
      <DataConfigSection values={form} onChange={handleChange} />
      <ModelSettingsSection values={form} onChange={handleChange} onToggle={handleToggle} backbones={options.backbones} poolingMethods={options.poolingMethods} />
      <HyperparametersSection values={form} onChange={handleChange} onDeviceChange={handleDeviceChange} gpuIndexes={options.gpuIndexes} cudaAvailable={options.cudaAvailable} mpsAvailable={options.mpsAvailable} />

      <div className="form-actions">
        <button type="submit" className="btn-primary">Start Training</button>
        {started && <p className="training-started-msg">Training has started</p>}
      </div>
    </form>
  )
}
