import { useState, useEffect } from 'react'
import DatasetUpload, { type FileEntry } from '../components/dataset/DatasetUpload'
import UploadProgress from '../components/dataset/UploadProgress'
import { getPresignedUrls, uploadFileToPresignedUrl, confirmDataset, markDatasetError, getDatasets, type Dataset } from '../services/datasetService'
import { ApiError } from '../api/client'
import './Datasets.css'
import '../pages/Homepage.css'
import type { DatasetMeta } from '../components/dataset/DatasetUpload'

function formatSize(bytes: number | null): string {
  if (bytes === null) return '—'
  if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(1)} GB`
  return `${(bytes / 1_048_576).toFixed(1)} MB`
}

export default function Datasets() {
  const [progress, setProgress] = useState<{ uploaded: number; total: number } | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [datasets, setDatasets] = useState<Dataset[]>([])

  function fetchDatasets() {
    getDatasets().then(setDatasets).catch(() => {})
  }

  useEffect(() => { fetchDatasets() }, [])

  async function handleFilesSelected(entries: FileEntry[], meta: DatasetMeta) {
    setUploadError(null)
    const paths = entries.map(e => e.path)
    const totalBytes = entries.reduce((sum, e) => sum + e.file.size, 0)
    console.log('presigned request', { user_id: 'default', dataset_name: meta.name, description: meta.description, paths, total_bytes: totalBytes })

    let data
    try {
      data = await getPresignedUrls(paths, totalBytes, meta.name, meta.description)
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 409) setUploadError('A dataset with that name already exists.')
        else if (err.status === 413) setUploadError('No more space for dataset uploading.')
        else setUploadError(err.message)
      } else {
        setUploadError('An unexpected error occurred.')
      }
      return
    }
    
    console.log('presigned response', data)

    setProgress({ uploaded: 0, total: data.urls.length })

    try {
      await Promise.all(
        data.urls.map(({ url, path }) => {
          const entry = entries.find(e => e.path === path)!
          return (async () => {
            await uploadFileToPresignedUrl(url, entry.file)
            setProgress(prev => prev && { ...prev, uploaded: prev.uploaded + 1 })
          })()
        })
      )
      await confirmDataset(data.dataset_id, totalBytes, entries.length)
      fetchDatasets()
    } catch {
      await markDatasetError(data.dataset_id)
      setProgress(null)
      setUploadError('Upload failed. Please try again.')
      return
    }

    setTimeout(() => setProgress(null), 1500)
  }

  return (
    <div className="page-content">
      <p className="eyebrow">Deep Audio Lab</p>
      <h1 className="page-title">Datasets</h1>

      <p className="page-summary">
        Upload Datasets for easy accesss on experiments.
      </p>

      <DatasetUpload onFilesSelected={handleFilesSelected} />

      {uploadError && (
        <div className="alert alert-danger alert-danger-dark alert-dismissible fade show mt-3" role="alert">
          {uploadError}
          <button type="button" className="btn-close" onClick={() => setUploadError(null)} aria-label="Close" />
        </div>
      )}

      {progress && (
        <UploadProgress uploaded={progress.uploaded} total={progress.total} />
      )}

      {datasets.length > 0 && (
        <div className="experiments-section">
          <h2 className="section-heading">Your Datasets</h2>
          <div className="experiment-grid">
            {datasets.map(ds => (
              <div key={ds.dataset_id} className="experiment-card">
                <div className="experiment-card__header">
                  <p className="experiment-card__name">{ds.name}</p>
                </div>
                <p className="experiment-card__description">{ds.description || '—'}</p>
                <div className="experiment-card__pills" style={{ marginTop: 14 }}>
                  <span className="pill pill--training">{ds.num_files ?? '—'} files</span>
                  <span className="pill pill--training">{formatSize(ds.size_bytes)}</span>
                  <span className="pill pill--evaluation">{new Date(ds.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
