import type { TrainingFormData } from './TrainingForm'

interface Props {
  values: Pick<TrainingFormData, 'experimentName' | 'description' | 'trainingData' | 'classMapping' | 'validationData' | 'samplingRate' | 'segmentDuration'>
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void
}

export default function DataConfigSection({ values, onChange }: Props) {
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
        <input
          id="trainingData"
          name="trainingData"
          type="text"
          placeholder="Path or identifier for training dataset"
          value={values.trainingData}
          onChange={onChange}
          required
        />
      </div>

      <div className="form-field">
        <label htmlFor="classMapping">Class Mapping</label>
        <input
          id="classMapping"
          name="classMapping"
          type="text"
          placeholder="Path or identifier for class mapping"
          value={values.classMapping}
          onChange={onChange}
          required
        />
      </div>

      <div className="form-field">
        <label htmlFor="validationData">
          Validation Data
          <span className="field-optional">optional</span>
        </label>
        <input
          id="validationData"
          name="validationData"
          type="text"
          placeholder="Path or identifier for validation dataset"
          value={values.validationData}
          onChange={onChange}
        />
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
