import type { TrainingFormData } from './TrainingForm'
import type { Dataset } from '../../services/datasetService'

interface Props {
  values: Pick<TrainingFormData, 'experimentName' | 'description' | 'trainingData' | 'validationData' | 'samplingRate' | 'segmentDuration'>
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void
  datasets: Dataset[]
}

export default function DataConfigSection({ values, onChange, datasets }: Props) {
  return (
    <div className="form-card">
      <h3 className="form-section-title">Data Configuration</h3>

      <div className="form-field">
        <label htmlFor="experimentName">Experiment Name</label>
        <input
          id="experimentName"
          name="experimentName"
          type="text"
          placeholder="Name for this experiment"
          value={values.experimentName}
          onChange={onChange}
          required
        />
      </div>

      <div className="form-field">
        <label htmlFor="description">
          Description
          <span className="field-optional">optional</span>
        </label>
        <textarea
          id="description"
          name="description"
          placeholder="Brief description of this experiment"
          value={values.description}
          onChange={onChange}
          rows={2}
        />
      </div>

      <div className="form-field">
        <label htmlFor="trainingData">Training Data</label>
        <select id="trainingData" name="trainingData" value={values.trainingData} onChange={onChange} required>
          <option value="">Select a dataset</option>
          {datasets.map(ds => (
            <option key={ds.id} value={ds.s3_prefix}>{ds.name}</option>
          ))}
        </select>
      </div>

      <div className="form-field">
        <label htmlFor="validationData">
          Validation Data
          <span className="field-optional">optional</span>
        </label>
        <select id="validationData" name="validationData" value={values.validationData} onChange={onChange}>
          <option value="">None</option>
          {datasets.map(ds => (
            <option key={ds.id} value={ds.s3_prefix}>{ds.name}</option>
          ))}
        </select>
      </div>

      <div className="form-row">
        <div className="form-field">
          <label htmlFor="samplingRate">Sampling Rate (Hz)</label>
          <input
            id="samplingRate"
            name="samplingRate"
            type="number"
            placeholder="e.g. 22050"
            min={1}
            step={1}
            value={values.samplingRate}
            onChange={onChange}
            required
          />
        </div>

        <div className="form-field">
          <label htmlFor="segmentDuration">Segment Duration (s)</label>
          <input
            id="segmentDuration"
            name="segmentDuration"
            type="number"
            placeholder="e.g. 1.5"
            min={0.01}
            step={0.01}
            value={values.segmentDuration}
            onChange={onChange}
            required
          />
        </div>
      </div>
    </div>
  )
}
