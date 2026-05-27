import client from '../api/client'

interface PresignedItem {
  path: string
  key: string
  url: string
}

interface PresignResponse {
  dataset_id: string
  urls: PresignedItem[]
}

export interface Dataset {
  id: number
  name: string
  description: string
  status: string
  size_bytes: number | null
  num_files: number | null
  created_at: string
}

export function getDatasets(): Promise<Dataset[]> {
  return client.get<Dataset[]>('/datasets?user_id=default')
}

export function getPresignedUrls(paths: string[], totalBytes: number, datasetName: string, description: string): Promise<PresignResponse> {
  return client.post<PresignResponse>('/datasets/presigned', { user_id: 'default', dataset_name: datasetName, description, paths, total_bytes: totalBytes })
}

export function confirmDataset(datasetId: string, sizeBytes: number, numFiles: number): Promise<void> {
  return client.post<void>(`/datasets/${datasetId}/confirm`, { size_bytes: sizeBytes, num_files: numFiles })
}

export function markDatasetError(datasetId: string): Promise<void> {
  return client.patch(`/datasets/${datasetId}/error`)
}

export async function uploadFileToPresignedUrl(url: string, file: File): Promise<void> {
  const response = await fetch(url, { method: 'PUT', body: file, headers: { 'Content-Type': 'audio/wav' } })
  if (!response.ok) throw new Error(`Upload failed for ${file.name}: HTTP ${response.status}`)
}
