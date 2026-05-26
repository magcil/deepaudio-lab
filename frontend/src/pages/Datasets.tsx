import { useState } from 'react'
import DatasetUpload, { type FileEntry } from '../components/dataset/DatasetUpload'
import UploadProgress from '../components/dataset/UploadProgress'
import { getPresignedUrls, uploadFileToPresignedUrl } from '../services/datasetService'
import { ApiError } from '../api/client'
import './Datasets.css'
import type { DatasetMeta } from '../components/dataset/DatasetUpload'

export default function Datasets() {
  const [progress, setProgress] = useState<{ uploaded: number; total: number } | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)

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

    await Promise.all(
      data.urls.map(({ url, path }) => {
        const entry = entries.find(e => e.path === path)!
        return (async () => {
          await uploadFileToPresignedUrl(url, entry.file)
          setProgress(prev => prev && { ...prev, uploaded: prev.uploaded + 1 })
        })()
      })
    )

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
    </div>
  )
}
