import type { EvaluationFormData } from './EvaluationForm'

interface Props {
  values: Pick<EvaluationFormData, 'batchSize' | 'workers' | 'device' | 'gpuIndex'>
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  onDeviceToggle: () => void
}

export default function EvalHyperparametersSection({ values, onChange, onDeviceToggle }: Props) {
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
        </div>
      </div>

      <div className="form-row">
        <div className="form-field">
          <label>Device</label>
          <div className="toggle-group">
            <button
              type="button"
              className={`toggle-btn ${values.device === 'cpu' ? 'active' : ''}`}
              onClick={onDeviceToggle}
            >
              CPU
            </button>
            <button
              type="button"
              className={`toggle-btn ${values.device === 'gpu' ? 'active' : ''}`}
              onClick={onDeviceToggle}
            >
              GPU
            </button>
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
    </div>
  )
}
