import { useRef } from 'react'
import './DatasetUpload.css'

export interface FileEntry {
  path: string
  file: File
}

interface Props {
  onFilesSelected?: (entries: FileEntry[]) => void
}

export default function DatasetUpload({ onFilesSelected }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)

  function handleFolderSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? [])
    const entries = files
      .filter(f => f.name.toLowerCase().endsWith('.wav'))
      .map(f => ({ path: f.webkitRelativePath, file: f }))
    onFilesSelected?.(entries)
  }

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        style={{ display: 'none' }}
        onChange={handleFolderSelect}
        {...{ webkitdirectory: '' } as React.InputHTMLAttributes<HTMLInputElement>}
      />

      <button className="btn-upload" onClick={() => inputRef.current?.click()}>
        Upload Dataset
      </button>
    </>
  )
}
