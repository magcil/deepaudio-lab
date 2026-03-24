import TrainingForm from '../components/training/TrainingForm'

export default function Training() {
  return (
    <div className="page-content">
      <p className="eyebrow">Deep Audio Lab</p>
      <h1 className="page-title">Training</h1>
      <p className="page-summary">
        Configure and run model training jobs.
      </p>

      <TrainingForm />
    </div>
  )
}
