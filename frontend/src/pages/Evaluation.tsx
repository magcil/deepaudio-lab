import EvaluationForm from '../components/evaluation/EvaluationForm'

export default function Evaluation() {
  return (
    <div className="page-content">
      <p className="eyebrow">Deep Audio Lab</p>
      <h1 className="page-title">Evaluation</h1>
      <p className="page-summary">
        Benchmark trained models against test sets. Compare metrics and export evaluation reports.
      </p>

      <EvaluationForm />
    </div>
  )
}
