import type { EvaluationFormData } from './EvaluationForm'

interface Props {
  values: Pick<EvaluationFormData, 'modelCheckpoint'>
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
    </div>
  )
}
