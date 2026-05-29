import type { TrainingFormData } from './TrainingForm'

interface Props {
  values: Pick<TrainingFormData, 'backbone' | 'poolingMethod' | 'pretrained' | 'freezeBackbone' | 'modelSamplingRate' | 'checkpoint'>
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void
  onToggle: (name: keyof TrainingFormData) => void
  backbones: string[]
  poolingMethods: string[]
}

export default function ModelSettingsSection({ values, onChange, onToggle, backbones, poolingMethods }: Props) {
  return (
    <div className="form-card">
      <h3 className="form-section-title">Model Settings</h3>

      <div className="form-field">
        <label htmlFor="backbone">Backbone</label>
        <select id="backbone" name="backbone" value={values.backbone} onChange={onChange}>
          {backbones.map(b => (
            <option key={b} value={b}>{b}</option>
          ))}
        </select>
      </div>

      <div className="form-field">
        <label htmlFor="poolingMethod">Pooling Method</label>
        <select id="poolingMethod" name="poolingMethod" value={values.poolingMethod} onChange={onChange}>
          {poolingMethods.map(p => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>

      <div className="form-row">
        <div className="form-field">
          <label>Pretrained</label>
          <div className="toggle-group">
            <button type="button" className={`toggle-btn ${values.pretrained ? 'active' : ''}`} onClick={() => onToggle('pretrained')}>Yes</button>
            <button type="button" className={`toggle-btn ${!values.pretrained ? 'active' : ''}`} onClick={() => onToggle('pretrained')}>No</button>
          </div>
        </div>

        <div className="form-field">
          <label>Freeze Backbone</label>
          <div className="toggle-group">
            <button type="button" className={`toggle-btn ${values.freezeBackbone ? 'active' : ''}`} onClick={() => onToggle('freezeBackbone')}>Yes</button>
            <button type="button" className={`toggle-btn ${!values.freezeBackbone ? 'active' : ''}`} onClick={() => onToggle('freezeBackbone')}>No</button>
          </div>
        </div>
      </div>

      <div className="form-field">
        <label htmlFor="modelSamplingRate">Sampling Rate (Hz)</label>
        <input
          id="modelSamplingRate"
          name="modelSamplingRate"
          type="number"
          placeholder="e.g. 22050"
          min={1}
          step={1}
          value={values.modelSamplingRate}
          onChange={onChange}
          required
        />
      </div>

      <div className="form-field">
        <label htmlFor="checkpoint">
          Checkpoint
        </label>
        <input
          id="checkpoint"
          name="checkpoint"
          type="text"
          placeholder="Name of the model to be stored as .pt file"
          value={values.checkpoint}
          onChange={onChange}
          required
        />
      </div>
    </div>
  )
}
