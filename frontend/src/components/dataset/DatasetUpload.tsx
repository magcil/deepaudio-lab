import { useRef, useState } from 'react'
import './DatasetUpload.css'
import DatasetUploadModal from './DatasetUploadModal'

export interface FileEntry {
  path: string
  file: File
}

export interface DatasetMeta {
  name: string
  description: string
}

interface Props {
  onFilesSelected?: (entries: FileEntry[], meta: DatasetMeta) => void
}

export default function DatasetUpload({ onFilesSelected }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const pendingMeta = useRef<DatasetMeta | null>(null)

  function openModal() {
    setName('')
    setDescription('')
    setModalOpen(true)
  }

  function handleContinue() {
    pendingMeta.current = { name: name.trim(), description: description.trim() }
    setModalOpen(false)
    inputRef.current?.click()
  }

  function handleFolderSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? [])
    const entries = files
      .filter(f => f.name.toLowerCase().endsWith('.wav'))
      .map(f => ({ path: f.webkitRelativePath, file: f }))
    if (pendingMeta.current) {
      onFilesSelected?.(entries, pendingMeta.current)
      pendingMeta.current = null
    }
    e.target.value = ''
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

      <button className="btn-upload" onClick={openModal}>
        Upload Dataset
      </button>

      {modalOpen && (
        <DatasetUploadModal
          name={name}
          description={description}
          onNameChange={setName}
          onDescriptionChange={setDescription}
          onContinue={handleContinue}
          onCancel={() => setModalOpen(false)}
        />
      )}
    </>
  )
}
