import type { EvaluationFormData } from './EvaluationForm'

interface Props {
  values: Pick<EvaluationFormData, 'evaluationData'>
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

    </div>
  )
}
