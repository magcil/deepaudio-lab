import './UploadProgress.css'

interface Props {
  uploaded: number
  total: number
}

export default function UploadProgress({ uploaded, total }: Props) {
  const pct = Math.round((uploaded / total) * 100)

  return (
    <div className="upload-progress">
      <div className="upload-progress-track">
        <div className="upload-progress-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="upload-progress-label">{uploaded} of {total} files uploaded</span>
    </div>
  )
}
