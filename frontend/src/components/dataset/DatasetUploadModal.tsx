import '../training/TrainingForm.css'
import './DatasetUploadModal.css'

interface Props {
  name: string
  description: string
  onNameChange: (value: string) => void
  onDescriptionChange: (value: string) => void
  onContinue: () => void
  onCancel: () => void
}

export default function DatasetUploadModal({
  name,
  description,
  onNameChange,
  onDescriptionChange,
  onContinue,
  onCancel,
}: Props) {
  return (
    <div className="ds-modal-overlay" onClick={onCancel}>
      <div className="ds-modal" onClick={e => e.stopPropagation()}>
        <h2 className="ds-modal-title">New Dataset</h2>

        <div className="ds-modal-fields">
          <div className="form-field">
            <label htmlFor="ds-name">Name</label>
            <input
              id="ds-name"
              type="text"
              placeholder="e.g. Urban Sounds v1"
              value={name}
              onChange={e => onNameChange(e.target.value)}
              autoFocus
            />
          </div>

          <div className="form-field">
            <label htmlFor="ds-desc">
              Description
              <span className="field-optional">optional</span>
            </label>
            <textarea
              id="ds-desc"
              rows={3}
              placeholder="Describe the dataset contents"
              value={description}
              onChange={e => onDescriptionChange(e.target.value)}
            />
          </div>
        </div>

        <div className="ds-modal-actions">
          <button className="btn-modal-cancel" onClick={onCancel}>
            Cancel
          </button>
          <button
            className="btn-primary"
            onClick={onContinue}
            disabled={!name.trim()}
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  )
}
