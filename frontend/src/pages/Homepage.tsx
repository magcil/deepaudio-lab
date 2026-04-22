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
  onSelectExperiment: (id: number) => void
}

export default function Home({ onSelectExperiment }: Props) {
  return (
    <div className="page-content">
      <p className="eyebrow">Deep Audio Lab</p>
      <h1 className="page-title">Welcome</h1>

      <section className="experiments-section">
        <h2 className="section-heading">Experiments</h2>
        <div className="experiment-grid">
          {experiments.map((exp) => (
            <div key={exp.id} className="experiment-card" onClick={() => onSelectExperiment(exp.id)}>
              <h3 className="experiment-card__name">{exp.name}</h3>
              <p className="experiment-card__description">{exp.description}</p>
              <div className="experiment-card__pills">
                {exp.hasTraining && <span className="pill pill--training">Training</span>}
                {exp.hasEvaluation && <span className="pill pill--evaluation">Evaluation</span>}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
