import client from '../api/client'

interface PresignedItem {
  path: string
  key: string
  url: string
}

interface PresignResponse {
  urls: PresignedItem[]
}

export function getPresignedUrls(paths: string[], totalBytes: number, datasetName: string, description: string): Promise<PresignResponse> {
  return client.post<PresignResponse>('/datasets/presigned', { user_id: 'default', dataset_name: datasetName, description, paths, total_bytes: totalBytes })
}

export async function uploadFileToPresignedUrl(url: string, file: File): Promise<void> {
  const response = await fetch(url, { method: 'PUT', body: file, headers: { 'Content-Type': 'audio/wav' } })
  if (!response.ok) throw new Error(`Upload failed for ${file.name}: HTTP ${response.status}`)
}
