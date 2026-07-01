import React, { useState, useEffect } from 'react'
import DataConfigSection from './DataConfigSection'
import ModelSettingsSection from './ModelSettingsSection'
import HyperparametersSection from './HyperparametersSection'
import { startTraining, getTrainingOptions, getTrainingLimits, type TrainingOptions, type TrainingLimits } from '../../services/trainingService'
import { getDatasets, type Dataset } from '../../services/datasetService'
import { ApiError } from '../../api/client'
import './TrainingForm.css'

export interface TrainingFormData {
  // Data config
  experimentName: string
  description: string
  datasetId: number | null
  trainingSet: string
  validationSet: string
  samplingRate: string
  segmentDuration: string
  // Model settings
  backbone: string
  poolingMethod: string
  pretrained: boolean
  freezeBackbone: boolean
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
  datasetId: null,
  trainingSet: '',
  validationSet: '',
  samplingRate: '',
  segmentDuration: '',
  backbone: 'beats',
  poolingMethod: '',
  pretrained: true,
  freezeBackbone: false,
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
  const [limits, setLimits] = useState<TrainingLimits | null>(null)
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [started, setStarted] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    getTrainingOptions()
      .then(data => {
        console.log('Training options:', data)
        setOptions(data)
      })
      .catch(console.error)
    getTrainingLimits().then(setLimits).catch(console.error)
    getDatasets().then(setDatasets).catch(console.error)
  }, [])

  const [form, setForm] = useState<TrainingFormData>(INITIAL_FORM)

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
    setFieldErrors(prev => {
      if (!prev[name]) return prev
      const next = { ...prev }
      delete next[name]
      return next
    })
  }

  function handleToggle(name: keyof TrainingFormData) {
    setForm(prev => ({ ...prev, [name]: !prev[name] }))
  }

  function handleDeviceChange(device: 'cpu' | 'gpu' | 'mps') {
    setForm(prev => ({ ...prev, device, gpuIndex: '' }))
  }

  function handleDatasetChange(id: number | null) {
    setForm(prev => ({ ...prev, datasetId: id, trainingSet: '', validationSet: '' }))
    setFieldErrors(prev => {
      const next = { ...prev }
      delete next['datasetId']
      delete next['trainingSet']
      return next
    })
  }

  async function handleSubmit(e: React.SyntheticEvent<HTMLFormElement>) {
    e.preventDefault()

    // Client-side validation via Constraint Validation API
    const formEl = e.currentTarget
    const clientErrors: Record<string, string> = {}
    for (const el of Array.from(formEl.elements)) {
      if (
        (el instanceof HTMLInputElement || el instanceof HTMLSelectElement || el instanceof HTMLTextAreaElement) &&
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
      experimentName: form.experimentName,
      description: form.description || null,
      datasetId: form.datasetId,
      trainingSet: form.trainingSet,
      validationSet: form.validationSet || null,
      samplingRate: form.samplingRate ? parseInt(form.samplingRate) : undefined,
      segmentDuration: form.segmentDuration ? parseFloat(form.segmentDuration) : null,
      backbone: form.backbone,
      pooling: form.poolingMethod || null,
      pretrained: form.pretrained,
      freezeBackbone: form.freezeBackbone,
      checkpoint: form.checkpoint || null,
      epochs: form.epochs ? parseInt(form.epochs) : undefined,
      patience: form.patience ? parseInt(form.patience) : undefined,
      learningRate: form.learningRate ? parseFloat(form.learningRate) : undefined,
      workers: form.workers ? parseInt(form.workers) : undefined,
      batchSize: form.batchSize ? parseInt(form.batchSize) : undefined,
      device: form.device,
      gpuIndex: form.device === 'gpu' ? parseInt(form.gpuIndex) : null,
    }

    setSubmitError(null)
    setFieldErrors({})
    try {
      const { task_id } = await startTraining(payload)
      console.log('Training started, task_id:', task_id)
      setForm(INITIAL_FORM)
      setStarted(true)
      setTimeout(() => setStarted(false), 8000)
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 429 || err.status === 503) {
          setSubmitError(err.message)
        } else if (err.status === 409) {
          try {
            const body = JSON.parse(err.message)
            const msg = typeof body?.detail === 'string' ? body.detail : 'An experiment with this name already exists.'
            setFieldErrors({ experimentName: msg })
          } catch {
            setFieldErrors({ experimentName: 'An experiment with this name already exists.' })
          }
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
          setSubmitError('Could not start training. Please try again.')
        }
      } else {
        setSubmitError('Could not start training. Please try again.')
      }
    }
  }

  return (
    <form className="training-form" onSubmit={handleSubmit} noValidate>
      <DataConfigSection values={form} onChange={handleChange} onDatasetChange={handleDatasetChange} datasets={datasets} limits={limits} fieldErrors={fieldErrors} />
      <ModelSettingsSection values={form} onChange={handleChange} onToggle={handleToggle} backbones={options.backbones} poolingMethods={options.poolingMethods} fieldErrors={fieldErrors} />
      <HyperparametersSection values={form} onChange={handleChange} onDeviceChange={handleDeviceChange} gpuIndexes={options.gpuIndexes} cudaAvailable={options.cudaAvailable} mpsAvailable={options.mpsAvailable} limits={limits} fieldErrors={fieldErrors} />

      <div className="form-actions">
        <button type="submit" className="btn-primary">Start Training</button>
        {started && <p className="training-started-msg">Training has started</p>}
        {submitError && <p className="training-error-msg">{submitError}</p>}
      </div>
    </form>
  )
}
