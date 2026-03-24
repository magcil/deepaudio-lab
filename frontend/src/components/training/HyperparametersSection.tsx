import type { TrainingFormData } from './TrainingForm'

interface Props {
  values: Pick<TrainingFormData, 'epochs' | 'patience' | 'learningRate' | 'workers' | 'batchSize' | 'device' | 'gpuIndex'>
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  onToggle: () => void
}

export default function HyperparametersSection({ values, onChange, onToggle }: Props) {
  return (
    <div className="form-card">
      <h3 className="form-section-title">Hyperparameters</h3>

      <div className="form-row">
        <div className="form-field">
          <label htmlFor="epochs">Epochs</label>
          <input
            id="epochs"
            name="epochs"
            type="number"
            placeholder="e.g. 100"
            min={1}
            step={1}
            value={values.epochs}
            onChange={onChange}
            required
          />
        </div>

        <div className="form-field">
          <label htmlFor="patience">Patience</label>
          <input
            id="patience"
            name="patience"
            type="number"
            placeholder="e.g. 10"
            min={1}
            step={1}
            value={values.patience}
            onChange={onChange}
            required
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-field">
          <label htmlFor="learningRate">Learning Rate</label>
          <input
            id="learningRate"
            name="learningRate"
            type="number"
            placeholder="e.g. 0.001"
            min={0}
            step={0.0001}
            value={values.learningRate}
            onChange={onChange}
            required
          />
        </div>

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
        </div>
      </div>

      <div className="form-row">
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
        </div>

        <div className="form-field">
          <label>Device</label>
          <div className="toggle-group">
            <button
              type="button"
              className={`toggle-btn ${values.device === 'cpu' ? 'active' : ''}`}
              onClick={onToggle}
            >
              CPU
            </button>
            <button
              type="button"
              className={`toggle-btn ${values.device === 'gpu' ? 'active' : ''}`}
              onClick={onToggle}
            >
              GPU
            </button>
          </div>
        </div>
      </div>

      {values.device === 'gpu' && (
        <div className="form-field">
          <label htmlFor="gpuIndex">GPU Index</label>
          <input
            id="gpuIndex"
            name="gpuIndex"
            type="number"
            placeholder="e.g. 0"
            min={0}
            step={1}
            value={values.gpuIndex}
            onChange={onChange}
            required
          />
        </div>
      )}
    </div>
  )
}
