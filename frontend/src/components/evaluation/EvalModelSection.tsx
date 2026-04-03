import type { EvaluationFormData } from './EvaluationForm'

interface Props {
  values: Pick<EvaluationFormData, 'modelCheckpoint' | 'numClasses'>
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
}

export default function EvalModelSection({ values, onChange }: Props) {
  return (
    <div className="form-card">
      <h3 className="form-section-title">Model</h3>

      <div className="form-field">
        <label htmlFor="modelCheckpoint">Model Checkpoint</label>
        <input
          id="modelCheckpoint"
          name="modelCheckpoint"
          type="text"
          placeholder="Path to AudioClassifier .pt file"
          value={values.modelCheckpoint}
          onChange={onChange}
          required
        />
      </div>

      <div className="form-field">
        <label htmlFor="numClasses">Number of Classes</label>
        <input
          id="numClasses"
          name="numClasses"
          type="number"
          placeholder="e.g. 10"
          min={1}
          step={1}
          value={values.numClasses}
          onChange={onChange}
          required
        />
      </div>
    </div>
  )
}
