import type { EvaluationFormData } from './EvaluationForm'

interface Props {
  values: Pick<EvaluationFormData, 'batchSize' | 'workers' | 'device' | 'gpuIndex'>
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void
  onDeviceChange: (device: 'cpu' | 'gpu' | 'mps') => void
  gpuIndexes: number[]
  cudaAvailable: boolean
  mpsAvailable: boolean
  fieldErrors: Record<string, string>
}

export default function EvalHyperparametersSection({ values, onChange, onDeviceChange, gpuIndexes, cudaAvailable, mpsAvailable, fieldErrors }: Props) {
  const deviceUnavailableMessage =
    values.device === 'gpu' && !cudaAvailable
      ? 'No CUDA GPU detected on this machine. Evaluation will fall back to CPU.'
      : values.device === 'mps' && !mpsAvailable
      ? 'MPS is not available on this machine. Evaluation will fall back to CPU.'
      : null

  return (
    <div className="form-card">
      <h3 className="form-section-title">Evaluation Hyperparameters</h3>

      <div className="form-row">
        <div className="form-field">
          <label htmlFor="batchSize">Batch Size</label>
          <input
            id="batchSize"
            name="batchSize"
            type="number"
            placeholder="e.g. 32"
            min={1}
            step={1}
            value={values.batchSize}
            onChange={onChange}
            required
          />
          {fieldErrors.batchSize && <span className="field-error">{fieldErrors.batchSize}</span>}
        </div>

        <div className="form-field">
          <label htmlFor="workers">Workers</label>
          <input
            id="workers"
            name="workers"
            type="number"
            placeholder="1 – 8"
            min={1}
            max={8}
            step={1}
            value={values.workers}
            onChange={onChange}
            required
          />
          {fieldErrors.workers && <span className="field-error">{fieldErrors.workers}</span>}
        </div>
      </div>

      <div className="form-row">
        <div className="form-field">
          <label>Device</label>
          <div className="toggle-group">
            <button
              type="button"
              className={`toggle-btn ${values.device === 'cpu' ? 'active' : ''}`}
              onClick={() => onDeviceChange('cpu')}
            >
              CPU
            </button>
            <button
              type="button"
              className={`toggle-btn ${values.device === 'gpu' ? 'active' : ''}`}
              onClick={() => onDeviceChange('gpu')}
              title={!cudaAvailable ? 'No CUDA GPU detected' : undefined}
            >
              GPU
            </button>
            <button
              type="button"
              className={`toggle-btn ${values.device === 'mps' ? 'active' : ''}`}
              onClick={() => onDeviceChange('mps')}
              title={!mpsAvailable ? 'MPS not available' : undefined}
            >
              MPS
            </button>
          </div>
        </div>
      </div>

      {deviceUnavailableMessage && (
        <p className="device-unavailable-msg">{deviceUnavailableMessage}</p>
      )}

      {values.device === 'gpu' && (
        <div className="form-field">
          <label htmlFor="gpuIndex">GPU Index</label>
          <select
            id="gpuIndex"
            name="gpuIndex"
            value={values.gpuIndex}
            onChange={onChange}
            required
          >
            <option value="" disabled>Select GPU</option>
            {gpuIndexes.map(i => (
              <option key={i} value={i}>{i}</option>
            ))}
          </select>
          {fieldErrors.gpuIndex && <span className="field-error">{fieldErrors.gpuIndex}</span>}
        </div>
      )}
    </div>
  )
}
