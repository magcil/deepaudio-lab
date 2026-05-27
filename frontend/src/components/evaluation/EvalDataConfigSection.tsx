import type { EvaluationFormData } from './EvaluationForm'
import type { Dataset } from '../../services/datasetService'

interface Props {
  values: Pick<EvaluationFormData, 'evaluationData'>
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void
  datasets: Dataset[]
}

export default function EvalDataConfigSection({ values, onChange, datasets }: Props) {
  return (
    <div className="form-card">
      <h3 className="form-section-title">Data Configuration</h3>

      <div className="form-field">
        <label htmlFor="evaluationData">Evaluation Data</label>
        <select id="evaluationData" name="evaluationData" value={values.evaluationData} onChange={onChange} required>
          <option value="">Select a dataset</option>
          {datasets.map(ds => (
            <option key={ds.id} value={ds.s3_prefix}>{ds.name}</option>
          ))}
        </select>
      </div>

    </div>
  )
}
