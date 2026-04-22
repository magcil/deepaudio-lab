import './Homepage.css'

const experiments = [
  {
    id: 1,
    name: "Baseline CNN – UrbanSound8K",
    description: "Initial convolutional baseline trained on UrbanSound8K with mel-spectrogram inputs.",
    hasTraining: true,
    hasEvaluation: false,
  },
  {
    id: 2,
    name: "ResNet50 + Attention – ESC-50",
    description: "ResNet50 backbone with a self-attention pooling head evaluated on the ESC-50 dataset.",
    hasTraining: true,
    hasEvaluation: true,
  },
  {
    id: 3,
    name: "EfficientNet – DCASE 2023",
    description: "Lightweight EfficientNet variant fine-tuned for acoustic scene classification on DCASE 2023.",
    hasTraining: false,
    hasEvaluation: true,
  },
]

interface Props {
  id: number
  onBack: () => void
}

export default function ExperimentDetail({ id, onBack }: Props) {
  const experiment = experiments.find((e) => e.id === id)

  if (!experiment) {
    return (
      <div className="page-content">
        <p className="eyebrow">Deep Audio Lab</p>
        <h1 className="page-title">Experiment not found</h1>
        <button className="back-button" onClick={onBack}>← Back</button>
      </div>
    )
  }

  return (
    <div className="page-content">
      <p className="eyebrow">Deep Audio Lab</p>
      <button className="back-button" onClick={onBack}>← Back</button>
      <h1 className="page-title">{experiment.name}</h1>
      <div className="experiment-card__pills" style={{ marginBottom: '24px' }}>
        {experiment.hasTraining && <span className="pill pill--training">Training</span>}
        {experiment.hasEvaluation && <span className="pill pill--evaluation">Evaluation</span>}
      </div>
      <p className="page-summary">{experiment.description}</p>
    </div>
  )
}
