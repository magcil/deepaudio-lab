import { useState } from 'react'
import DatasetUpload, { type FileEntry } from '../components/dataset/DatasetUpload'
import UploadProgress from '../components/dataset/UploadProgress'
import { getPresignedUrls, uploadFileToPresignedUrl } from '../services/datasetService'

export default function Datasets() {
  const [progress, setProgress] = useState<{ uploaded: number; total: number } | null>(null)

  async function handleFilesSelected(entries: FileEntry[]) {
    const paths = entries.map(e => e.path)
    console.log(paths)

    const data = await getPresignedUrls(paths, 'default')
    console.log(data)

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
  }

  return (
    <div className="page-content">
      <p className="eyebrow">Deep Audio Lab</p>
      <h1 className="page-title">Datasets</h1>

      <p className="page-summary">
        Upload Datasets for easy accesss on experiments.
      </p>

      <DatasetUpload onFilesSelected={handleFilesSelected} />

      {progress && (
        <UploadProgress uploaded={progress.uploaded} total={progress.total} />
      )}
    </div>
  )
}
