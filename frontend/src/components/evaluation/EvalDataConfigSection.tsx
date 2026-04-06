import type { EvaluationFormData } from './EvaluationForm'

interface Props {
  values: Pick<EvaluationFormData, 'evaluationData' | 'classMapping' | 'samplingRate' | 'segmentDuration'>
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
}

export default function EvalDataConfigSection({ values, onChange }: Props) {
  return (
    <div className="form-card">
      <h3 className="form-section-title">Data Configuration</h3>

      <div className="form-field">
        <label htmlFor="evaluationData">Evaluation Data</label>
        <input
          id="evaluationData"
          name="evaluationData"
          type="text"
          placeholder="Full path to test data"
          value={values.evaluationData}
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
