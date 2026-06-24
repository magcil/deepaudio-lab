import { useState, useEffect } from 'react'
import type { TrainingFormData } from './TrainingForm'
import type { Dataset } from '../../services/datasetService'
import type { TrainingLimits } from '../../services/trainingService'
import { getDatasetSplits } from '../../services/datasetService'

interface Props {
  values: Pick<TrainingFormData, 'experimentName' | 'description' | 'datasetId' | 'trainingSet' | 'validationSet' | 'samplingRate' | 'segmentDuration'>
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void
  onDatasetChange: (id: number | null) => void
  datasets: Dataset[]
  limits: TrainingLimits | null
}

export default function DataConfigSection({ values, onChange, onDatasetChange, datasets, limits }: Props) {
  const [splits, setSplits] = useState<string[]>([])

  useEffect(() => {
    if (values.datasetId === null) {
      setSplits([])
      return
    }
    getDatasetSplits(values.datasetId).then(setSplits).catch(() => setSplits([]))
  }, [values.datasetId])

  return (
    <div className="form-card">
      <h3 className="form-section-title">Data Configuration</h3>

      <div className="form-field">
        <label htmlFor="experimentName">Experiment Name</label>
        <input
          id="experimentName"
          name="experimentName"
          type="text"
          placeholder="Name for this experiment"
          value={values.experimentName}
          onChange={onChange}
          required
        />
      </div>

      <div className="form-field">
        <label htmlFor="description">
          Description
          <span className="field-optional">optional</span>
        </label>
        <textarea
          id="description"
          name="description"
          placeholder="Brief description of this experiment"
          value={values.description}
          onChange={onChange}
          rows={2}
          maxLength={500}
        />
      </div>

      <div className="form-field">
        <label htmlFor="datasetId">Select Dataset</label>
        <select
          id="datasetId"
          value={values.datasetId ?? ''}
          onChange={e => onDatasetChange(e.target.value ? Number(e.target.value) : null)}
          required
        >
          <option value="">Select a dataset</option>
          {datasets.filter(ds => ds.status === 'ready').map(ds => (
            <option key={ds.id} value={ds.id}>{ds.name}</option>
          ))}
        </select>
      </div>

      {values.datasetId !== null && (
        <div className="form-field">
          <label htmlFor="trainingSet">Training Set</label>
          <select id="trainingSet" name="trainingSet" value={values.trainingSet} onChange={onChange} required>
            <option value="">Select a split</option>
            {splits.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      )}

      {values.datasetId !== null && (
        <div className="form-field">
          <label htmlFor="validationSet">
            Validation Set
            <span className="field-optional">optional</span>
          </label>
          <select id="validationSet" name="validationSet" value={values.validationSet} onChange={onChange}>
            <option value="">None</option>
            {splits.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      )}

      <div className="form-row">
        <div className="form-field">
          <label htmlFor="samplingRate">Sampling Rate (Hz)</label>
          <input
            id="samplingRate"
            name="samplingRate"
            type="number"
            placeholder="e.g. 22050"
            min={1}
            max={44100}
            step={1}
            value={values.samplingRate}
            onChange={onChange}
            required
          />
        </div>

        <div className="form-field">
          <label htmlFor="segmentDuration">
            Segment Duration (s)
            {limits && <span className="field-hint">max {limits.max_segment_duration}s</span>}
          </label>
          <input
            id="segmentDuration"
            name="segmentDuration"
            type="number"
            placeholder="e.g. 1.5"
            min={0.01}
            max={limits?.max_segment_duration}
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
